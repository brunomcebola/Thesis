"""
Scrip to fine tune the I3D model on specific data
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=cell-var-from-loop

import os
import gc
import math
import shutil
import argparse
import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

import i3d
import i3d_logits
from utils import k_fold_finetune


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_CHECKPOINTS = os.path.join(BASE_DIR, "test")
OUTPUT_CHECKPOINTS = os.path.join(BASE_DIR, "finetuned_checkpoints")
DATA_DIR = os.path.join(BASE_DIR, "data")
TMP_DIR = os.path.join(BASE_DIR, "tmp")

###


class CustomScore(tf.keras.metrics.Metric):
    """
    Custom score metric
    """

    def __init__(self, betas: dict[int, float], **kwargs) -> None:
        """
        Initialize the metric

        Args:
            betas: Beta values for each class
        """
        super().__init__(**kwargs)

        assert len(betas) > 0

        self.num_classes = len(betas)

        # check betas
        for i in range(self.num_classes):
            assert i in betas

        self.betas = betas

        self.precision = [tf.keras.metrics.Precision() for _ in range(self.num_classes)]
        self.recall = [tf.keras.metrics.Recall() for _ in range(self.num_classes)]

    def update_state(self, y_true, y_pred, sample_weight=None):
        """
        Update the metric state

        Args:
            y_true: True labels
            y_pred: Predicted logits
            sample_weight: Sample weights
        """

        y_pred = tf.nn.softmax(y_pred)
        y_pred = tf.argmax(y_pred, axis=1)

        for i in range(self.num_classes):
            y_true_class = tf.cast(tf.equal(y_true, i), tf.int32)
            y_pred_class = tf.cast(tf.equal(y_pred, i), tf.int32)
            self.precision[i].update_state(y_true_class, y_pred_class, sample_weight=sample_weight)
            self.recall[i].update_state(y_true_class, y_pred_class, sample_weight=sample_weight)

    def result(self):
        """
        Get the metric result
        """

        def _f_beta_score(precision, recall, beta):
            if precision + recall == 0:
                return 0
            return (1 + beta**2) * (precision * recall) / (beta**2 * precision + recall)

        f_scores = []

        for i in range(self.num_classes):
            precision = self.precision[i].result().numpy()
            recall = self.recall[i].result().numpy()

            f_scores.append(_f_beta_score(precision, recall, beta=self.betas[i]))

        f_score = sum(f_scores) / self.num_classes

        f_score = tf.constant(f_score, dtype=tf.float32)

        return f_score


###


def generate_train_data(source_data_path: str, train_data_path: str, checkpoint_path: str):
    """
    Generate training data from samples

    Args:
        source_data_path: Path to the source data
        train_data_path: Path to save the training data
        checkpoint_path: Path to the checkpoint
    """

    stream, _, _ = os.path.basename(os.path.dirname(checkpoint_path)).split(".")

    # Delete previous data if any
    if os.path.exists(train_data_path):
        shutil.rmtree(train_data_path, ignore_errors=True)

    # Get all samples paths
    samples = []
    for dirpath, _, filenames in os.walk(source_data_path):
        if filenames:
            for f in filenames:
                if stream in f:
                    samples.append(os.path.join(dirpath, f))

    # Load the model
    model = i3d.InceptionI3d(400, spatial_squeeze=True, final_endpoint="Mixed_5c")
    tf.train.Checkpoint(model=model).restore(checkpoint_path).expect_partial()

    # Generate training data
    for sample in tqdm(samples, desc="Generating training data"):
        output_path = sample.replace(source_data_path, train_data_path)

        sample = tf.convert_to_tensor(np.load(sample), dtype=np.float32)

        # Transpose the sample if needed to apply horizontal sliding window
        transposed = False
        if sample.shape[2] > sample.shape[3]:  # type: ignore
            sample = tf.transpose(sample, (0, 1, 3, 2, 4))
            transposed = True

        rgb_sub_samples = []

        # Apply horizontal sliding window to create sub samples of 224x224
        final = sample.shape[3] - 224 + 1  # type: ignore
        step = int((sample.shape[3] - 224) / math.floor(sample.shape[3] / 224)) - 1  # type: ignore
        for i in range(0, final, step if step > 0 else 1):
            rgb_sub_samples.append(sample[:, :, :, i : i + 224, :])  # type: ignore

        # Transpose the sub samples back
        if transposed:
            for i, sample in enumerate(rgb_sub_samples):
                rgb_sub_samples[i] = tf.transpose(sample, (0, 1, 3, 2, 4))

        # Predict the sub samples
        for i, sub_sample in enumerate(rgb_sub_samples):
            out, _ = model(sub_sample)

            if out.numpy().shape[1] <= 1:
                continue

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            np.save(output_path.replace(".npy", f"_{i}.npy"), out.numpy())


def get_train_data(train_data_path: str):
    """
    Get training data

    Args:
        train_data_path: Path to the training data

    Returns:
        (samples, labels, classes)

        where:
            samples: List of samples paths
            labels: List of labels
            classes: Classes mapping
    """

    classes = {dir: i for i, dir in enumerate(sorted(os.listdir(train_data_path)))}

    samples = []
    labels = []
    for dirpath, _, filenames in os.walk(train_data_path):
        if filenames:
            for f in filenames:
                samples.append(os.path.join(dirpath, f))

                for cls in classes:
                    if cls in dirpath:
                        labels.append(classes[cls])
                        break

    return samples, labels, classes


def save(
    model,
    original_checkpoint_path: str,
    finetuned_checkpoint_path: str,
    classes: dict[str, int],
    metrics: tuple[list[list[float]], list[list[float]], list[list[float]], list[list[float]]],
) -> None:
    """
    Save training session

    Args:
        model: Model
        original_checkpoint_path: Path to the original checkpoint
        finetuned_checkpoint_path: Path to save the finetuned checkpoint
        classes: Classes mapping
        metrics: Metrics

    """

    print(f"Saving model to: {os.path.dirname(finetuned_checkpoint_path)}")

    # Cleanup previous data
    shutil.rmtree(os.path.dirname(finetuned_checkpoint_path), ignore_errors=True)
    os.makedirs(os.path.dirname(finetuned_checkpoint_path))

    # Create sample tensors
    channels = 3 if "rgb" in os.path.basename(os.path.dirname(original_checkpoint_path)) else 2
    input_sample = tf.convert_to_tensor(np.random.rand(1, 2, 224, 224, channels), dtype=tf.float32)  # type: ignore
    # TODO: check if the shape is correct for rgb and flow
    logits_sample = tf.convert_to_tensor(np.random.rand(1, 2, 7, 7, 1024), dtype=tf.float32)  # type: ignore

    # Create a new checkpoint with only the mixed_5c layer
    mixed_5c_model = i3d.InceptionI3d(num_classes=len(classes), final_endpoint="Mixed_5c")
    tf.train.Checkpoint(model=mixed_5c_model).restore(original_checkpoint_path).expect_partial()
    mixed_5c_model(input_sample)
    tf.train.Checkpoint(model=mixed_5c_model).write(os.path.join(TMP_DIR, "mixed_5c", "model.ckpt"))

    # Restore the full model from the mixed_5c checkpoint
    full_model = i3d.InceptionI3d(num_classes=len(classes), final_endpoint="Logits")
    tf.train.Checkpoint(model=full_model).restore(
        os.path.join(TMP_DIR, "mixed_5c", "model.ckpt")
    ).expect_partial()
    full_model(input_sample)

    # Update the full model with the finetuned logits
    model(logits_sample)
    model_variables = {var.name: var for var in model.trainable_variables}

    variables_to_replace_map = {
        "inception_i3d/Logits/Conv3d_0c_1x1/conv_3d/b:0": "inception_i3d_logits/Logits/Conv3d_0c_1x1/conv_3d/b:0",
        "inception_i3d/Logits/Conv3d_0c_1x1/conv_3d/w:0": "inception_i3d_logits/Logits/Conv3d_0c_1x1/conv_3d/w:0",
    }

    for i, var in enumerate(full_model.trainable_variables):
        if var.name in variables_to_replace_map:  # type: ignore
            full_model.trainable_variables[i].assign(  # type: ignore
                model_variables[variables_to_replace_map[var.name]]  # type: ignore
            )

    tf.train.Checkpoint(model=full_model).write(finetuned_checkpoint_path)

    # Save class labels
    with open(
        finetuned_checkpoint_path.replace("model.ckpt", "labels.txt"), "w", encoding="utf-8"
    ) as f:
        f.write("\n".join(classes.keys()))

    # Save training plot
    _, axs = plt.subplots(1, 2, figsize=(12, 6))

    for i, train_losses in enumerate(metrics[0], 1):
        axs[0].plot(range(1, len(train_losses) + 1), train_losses, label=f"K Fold {i}")
    axs[0].set_title("Train Loss Over Epochs")
    axs[0].set_xlabel("Epochs")
    axs[0].set_ylabel("Loss")
    axs[0].legend()
    axs[0].grid(True)

    for i, train_scores in enumerate(metrics[1], 1):
        axs[1].plot(range(1, len(train_scores) + 1), train_scores, label=f"K Fold {i}")
    axs[1].set_title("Train Score Over Epochs")
    axs[1].set_xlabel("Epochs")
    axs[1].set_ylabel("Scores")
    axs[1].legend()
    axs[1].grid(True)

    plt.tight_layout()
    plt.savefig(finetuned_checkpoint_path.replace("model.ckpt", "train_plot.png"))

    # Save validation plot
    _, axs = plt.subplots(1, 2, figsize=(12, 6))

    for i, validation_losses in enumerate(metrics[2], 1):
        axs[0].plot(range(1, len(validation_losses) + 1), validation_losses, label=f"K Fold {i}")
    axs[0].set_title("Validation Score Over Epochs")
    axs[0].set_xlabel("Epochs")
    axs[0].set_ylabel("Loss")
    axs[0].legend()
    axs[0].grid(True)

    for i, validation_scores in enumerate(metrics[3], 1):
        axs[1].plot(range(1, len(validation_scores) + 1), validation_scores, label=f"K Fold {i}")
    axs[1].set_title("Validation Score Over Epochs")
    axs[1].set_xlabel("Epochs")
    axs[1].set_ylabel("Scores")
    axs[1].legend()
    axs[1].grid(True)

    plt.tight_layout()
    plt.savefig(finetuned_checkpoint_path.replace("model.ckpt", "validation_plot.png"))


def cleanup():
    """
    Cleanup routine
    """

    shutil.rmtree(TMP_DIR, ignore_errors=True)
    tf.keras.backend.clear_session()
    gc.collect()


def main():
    """
    Main function
    """

    parser = argparse.ArgumentParser(description="Fine tune I3D model on custom data")
    parser.add_argument(
        "--data",
        type=str,
        choices=["color", "depth"],
        default="color",
        help="Data type to preprocess",
    )
    parser.add_argument(
        "--no-generate",
        dest="generate",
        action="store_false",
        help="Do not generate the training data",
    )
    parser.add_argument(
        "--no-train",
        dest="train",
        action="store_false",
        help="Do not train the model",
    )
    parser.add_argument(
        "--no-save",
        dest="save",
        action="store_false",
        help="Do not save the finetuned model",
    )
    parser.add_argument(
        "--no-cleanup",
        dest="cleanup",
        action="store_false",
        help="Do not cleanup the temporary data",
    )
    args = parser.parse_args()

    for checkpoint in os.listdir(INPUT_CHECKPOINTS):
        print(f"Finetuning model: {os.path.join(INPUT_CHECKPOINTS, checkpoint)}")

        if args.generate:
            generate_train_data(
                os.path.join(DATA_DIR, args.data),
                os.path.join(TMP_DIR, "train_data"),
                os.path.join(INPUT_CHECKPOINTS, checkpoint, "model.ckpt"),
            )

        if args.train:
            samples, labels, classes = get_train_data(os.path.join(TMP_DIR, "train_data"))

            model, metrics = k_fold_finetune(
                lambda: i3d_logits.InceptionI3dLogits(num_classes=len(classes)),
                samples,
                labels,
                5,
                lambda: tf.optimizers.Adam(learning_rate=0.001),
                lambda: tf.losses.SparseCategoricalCrossentropy(from_logits=True),
                lambda: CustomScore(betas={0: 1, 1: 1}),
                TMP_DIR,
                batch_size=1,
                epochs=5,
            )

        if args.save:
            _, base, _ = os.path.basename(
                os.path.dirname(os.path.join(INPUT_CHECKPOINTS, checkpoint, "model.ckpt"))
            ).split(".")

            save(
                model,
                os.path.join(INPUT_CHECKPOINTS, checkpoint, "model.ckpt"),
                os.path.join(
                    OUTPUT_CHECKPOINTS,
                    checkpoint.replace(base, f"{len(classes)}_{base}"),
                    "model.ckpt",
                ),
                classes,
                metrics,
            )

        if args.cleanup:
            cleanup()

        print()


if __name__ == "__main__":
    main()
