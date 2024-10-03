"""
Scrip to fine tune the I3D model on specific data
"""

from __future__ import absolute_import, division, print_function

import os
import gc
import math
import shutil
import argparse
import numpy as np
from sklearn.model_selection import StratifiedKFold
import matplotlib.pyplot as plt
from tqdm import tqdm

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf  # pylint: disable=wrong-import-position
import i3d_logits  # pylint: disable=wrong-import-position
import i3d  # pylint: disable=wrong-import-position

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_CHECKPOINTS = os.path.join(BASE_DIR, "test")
OUTPUT_CHECKPOINTS = os.path.join(BASE_DIR, "finetuned_checkpoints")
BASE_DATA_DIR = os.path.join(BASE_DIR, "npy")
TRAIN_DATA_DIR = os.path.join(BASE_DIR, "data")

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


def create_dataset(samples, labels):
    """
    Create a TensorFlow dataset from the given samples and labels
    """

    def _load_data():
        for path, label in zip(samples, labels):
            data = np.load(path)
            data = np.squeeze(data, axis=0)
            data = tf.convert_to_tensor(data, dtype=tf.float32)

            label = tf.convert_to_tensor(label, dtype=tf.int32)

            yield data, label

    dataset = tf.data.Dataset.from_generator(
        _load_data,
        output_signature=(
            tf.TensorSpec(shape=(None, 7, 7, 1024), dtype=tf.float32),  # type: ignore
            tf.TensorSpec(shape=(), dtype=tf.int32),  # type: ignore
        ),
    )

    dataset = dataset.shuffle(buffer_size=1000)
    dataset = dataset.padded_batch(
        batch_size=1,
        padded_shapes=(
            [None, 7, 7, 1024],
            [],
        ),
    )

    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset


def train_step(
    model,
    dataset: tf.data.Dataset,
    optimizer: tf.optimizers.Optimizer,
    betas: dict[int, float],
) -> tuple[tf.keras.metrics.Metric, tf.keras.metrics.Metric]:
    """
    Train the model using the given data

    Args:
        model: Model to train
        dataset: Dataset containing training data
        optimizer: Optimizer
        betas: Beta values for each class

    Returns:
        loss: Loss metric
        score: Score metric
    """

    loss = tf.keras.metrics.Mean()
    score = CustomScore(betas)

    for batch_samples, batch_labels in dataset:
        with tf.GradientTape() as tape:
            # Get model predictions
            logits, _ = model(batch_samples)

            # Calculate loss
            loss_value = tf.losses.SparseCategoricalCrossentropy(from_logits=True)(
                batch_labels, logits
            )

        # Calculate gradients
        grads = tape.gradient(loss_value, model.trainable_variables)

        # Update model weights
        optimizer.apply_gradients(zip(grads, model.trainable_variables))

        # Update metrics
        loss.update_state(loss_value)
        score.update_state(batch_labels, logits)

    return loss, score


def validation_step(
    model, dataset: tf.data.Dataset, betas: dict[int, float]
) -> tuple[tf.keras.metrics.Metric, tf.keras.metrics.Metric]:
    """
    Validate the model using the given data

    Args:
        model: Model to validate
        dataset: Dataset containing validation data
        betas: Beta values for each class

    Returns:
        loss: Loss metric
        score: Score metric
    """

    loss = tf.keras.metrics.Mean()
    score = CustomScore(betas)

    for batch_samples, batch_labels in dataset:
        # Get model predictions
        logits, _ = model(batch_samples)

        # Calculate loss
        loss_value = tf.losses.SparseCategoricalCrossentropy(from_logits=True)(batch_labels, logits)

        # Update metrics
        loss.update_state(loss_value)
        score.update_state(batch_labels, logits)

    return loss, score


def kfold(
    model,
    samples: np.ndarray,
    labels: np.ndarray,
    train_index: list[int],
    val_index: list[int],
    betas: dict[int, float],
    epochs: int,
    learning_rate: float,
    fold_id: int,
) -> tuple[list[float], list[float], list[float], list[float]]:
    """
    K-Fold cross validation

    Args:
        model: Model to train
        samples: Samples
        labels: Labels
        train_index: Train index
        val_index: Validation index
        betas: Beta values for each class
        epochs: Number of epochs
        learning_rate: Learning rate
        fold_id: Fold ID

    Returns:
        train_losses: Train losses
        train_scores: Train scores
        validation_losses: Validation losses
        validation_scores: Validation scores
    """

    train_samples, train_labels = samples[train_index], labels[train_index]
    val_samples, val_labels = samples[val_index], labels[val_index]

    train_dataset = create_dataset(train_samples, train_labels)
    validation_dataset = create_dataset(val_samples, val_labels)

    train_optimizer = tf.optimizers.Adam(learning_rate=learning_rate)

    train_losses = []
    train_scores = []

    validation_losses = []
    validation_scores = []

    for _ in tqdm(range(epochs), desc=f"Training K Fold {fold_id}"):

        epoch_train_loss, epoch_train_score = train_step(
            model,
            train_dataset,
            train_optimizer,
            betas,
        )

        train_losses.append(epoch_train_loss.result().numpy())  # type: ignore
        train_scores.append(epoch_train_score.result().numpy())  # type: ignore

        epoch_val_loss, epoch_val_score = validation_step(
            model,
            validation_dataset,
            betas,
        )

        validation_losses.append(epoch_val_loss.result().numpy())  # type: ignore
        validation_scores.append(epoch_val_score.result().numpy())  # type: ignore

    return train_losses, train_scores, validation_losses, validation_scores


###


def generate_train_data(data_type, checkpoint):
    """
    Generate training data from samples
    """

    stream, _, _ = checkpoint.split(".")
    base_data_path = os.path.join(BASE_DATA_DIR, data_type)

    # Delete previous data if any
    if os.path.exists(TRAIN_DATA_DIR):
        shutil.rmtree(TRAIN_DATA_DIR, ignore_errors=True)

    # Get all samples paths
    samples = []
    for dirpath, _, filenames in os.walk(base_data_path):
        if filenames:
            for f in filenames:
                if stream in f:
                    samples.append(os.path.join(dirpath, f))

    # Load the model
    model = i3d.InceptionI3d(400, spatial_squeeze=True, final_endpoint="Mixed_5c")
    checkpoint = os.path.join(INPUT_CHECKPOINTS, checkpoint, "model.ckpt")
    tf.train.Checkpoint(model=model).restore(checkpoint).expect_partial()

    # Generate training data
    for sample in tqdm(samples, desc="Generating training data"):
        output_path = sample.replace(BASE_DATA_DIR, TRAIN_DATA_DIR)

        sample = tf.convert_to_tensor(np.load(sample), dtype=np.float32)

        transposed = False
        if sample.shape[2] > sample.shape[3]:  # type: ignore
            sample = tf.transpose(sample, (0, 1, 3, 2, 4))
            transposed = True

        rgb_sub_samples = []

        final = sample.shape[3] - 224 + 1  # type: ignore
        step = int((sample.shape[3] - 224) / math.floor(sample.shape[3] / 224)) - 1  # type: ignore
        for i in range(0, final, step if step > 0 else 1):
            rgb_sub_samples.append(sample[:, :, :, i : i + 224, :])  # type: ignore

        if transposed:
            for i, sample in enumerate(rgb_sub_samples):
                rgb_sub_samples[i] = tf.transpose(sample, (0, 1, 3, 2, 4))

        for i, sub_sample in enumerate(rgb_sub_samples):
            out, _ = model(sub_sample)

            if out.numpy().shape[1] <= 1:
                continue

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            np.save(output_path.replace(".npy", f"_{i}.npy"), out.numpy())


def cleanup():
    """
    Cleanup routine
    """

    shutil.rmtree(TRAIN_DATA_DIR, ignore_errors=True)
    tf.keras.backend.clear_session()
    gc.collect()


def finetune(data_type: str, checkpoint: str):
    """
    Function to finetune a checkpointed I3D model on a custom dataset
    """

    np.random.seed(42)
    tf.random.set_seed(42)

    epochs = 100
    n_splits = 5
    learning_rate = 0.001
    stream, _, _ = checkpoint.split(".")
    train_data_path = os.path.join(TRAIN_DATA_DIR, data_type)

    # Get class labels
    cls = {c: i for i, c in enumerate(sorted(os.listdir(train_data_path)))}

    # Set betas
    betas = {cls[label]: 1.0 for label in cls}

    # Get all samples paths
    samples = []
    for dirpath, _, filenames in os.walk(train_data_path):
        if filenames:
            for f in filenames:
                if stream in f:
                    samples.append(os.path.join(dirpath, f))
    samples = np.array(samples)

    # Create labels array
    labels = []
    for sample in samples:
        label = os.path.dirname(os.path.dirname(sample)).replace(train_data_path, "").strip("/")
        labels.append(cls[label])
    labels = np.array(labels)

    print(f"Total samples: {len(samples)}")

    # Split data
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    print(f"K Folds: {n_splits}")

    skf_train_losses = []
    skf_train_scores = []

    skf_validation_losses = []
    skf_validation_scores = []

    for fold_id, (train_index, val_index) in enumerate(skf.split(samples, labels), 1):
        model = i3d_logits.InceptionI3dLogits(num_classes=len(cls))

        train_losses, train_scores, validation_losses, validation_scores = kfold(
            model,
            samples,
            labels,
            train_index,
            val_index,
            betas,
            epochs,
            learning_rate,
            fold_id,
        )

        skf_train_losses.append(train_losses)
        skf_train_scores.append(train_scores)

        skf_validation_losses.append(validation_losses)
        skf_validation_scores.append(validation_scores)

    # Save training plot
    fig, axs = plt.subplots(2, 2, figsize=(12, 6))

    for i, train_losses in enumerate(skf_train_losses):
        axs[0][0].plot(train_losses, label=f"K Fold {i}")
    axs[0][0].set_title("Model Loss Over Epochs - Train")
    axs[0][0].set_xlabel("Epochs")
    axs[0][0].set_ylabel("Loss")
    axs[0][0].legend()
    axs[0][0].grid(True)

    for i, train_scores in enumerate(skf_train_scores):
        axs[0][1].plot(train_scores, label=f"K Fold {i}")
    axs[0][1].set_title("Model Accuracy Over Epochs - Train")
    axs[0][1].set_xlabel("Epochs")
    axs[0][1].set_ylabel("Scores")
    axs[0][1].legend()
    axs[0][1].grid(True)

    for i, validation_losses in enumerate(skf_validation_losses):
        axs[1][0].plot(validation_losses, label=f"K Fold {i}")
    axs[1][0].set_title("Model Loss Over Epochs - Validation")
    axs[1][0].set_xlabel("Epochs")
    axs[1][0].set_ylabel("Loss")
    axs[1][0].legend()
    axs[1][0].grid(True)

    for i, validation_scores in enumerate(skf_validation_scores):
        axs[1][1].plot(validation_scores, label=f"K Fold {i}")
    axs[1][1].set_title("Model Accuracy Over Epochs - Validation")
    axs[1][1].set_xlabel("Epochs")
    axs[1][1].set_ylabel("Scores")
    axs[1][1].legend()
    axs[1][1].grid(True)

    plt.tight_layout()
    plt.show()


###


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
    args = parser.parse_args()
    args = parser.parse_args()

    for checkpoint in os.listdir(INPUT_CHECKPOINTS):
        print(f"Finetuning model: {checkpoint}")

        # generate_train_data(args.data, checkpoint)

        finetune(args.data, checkpoint)

        # cleanup()

        print()


if __name__ == "__main__":
    main()
