"""
Scrip to test the I3D model on specific data
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order

from __future__ import annotations

import gc
import os
import math
import shutil
import argparse
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from tqdm import tqdm
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    fbeta_score,
)

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

import i3d

###

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CHECKPOINTS = os.path.join(BASE_DIR, "finetuned_checkpoints")
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "tests")

###


def generate_sub_samples(sample: tf.Tensor) -> list[tf.Tensor]:
    """
    Sub-sample the video into smaller clips of 224 frames
    """
    sub_samples = []

    transposed = False
    if sample.shape[2] > sample.shape[3]:  # type: ignore
        sample = tf.transpose(sample, (0, 1, 3, 2, 4))
        transposed = True

    final = sample.shape[3] - 224 + 1  # type: ignore
    step = int((sample.shape[3] - 224) / math.floor(sample.shape[3] / 224)) - 1  # type: ignore
    for i in range(0, final, step if step > 0 else 1):
        sub_samples.append(sample[:, :, :, i : i + 224, :])  # type: ignore

    if transposed:
        for i, sample in enumerate(sub_samples):
            sub_samples[i] = tf.transpose(sample, (0, 1, 3, 2, 4))

    return sub_samples


def main():
    """
    Main function to evaluate I3D on Kinetics.
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

    print("Testing Google Inception-v1 Inflated 3D ConvNet\n")

    # Get combination of checkpoints
    checkpoints_groups: dict[str, dict[str, str]] = {}
    for checkpoint in os.listdir(CHECKPOINTS):
        base, stream = checkpoint.split(".")
        if args.data in base:
            checkpoint_path = os.path.join(CHECKPOINTS, checkpoint)

            checkpoints_groups[base] = checkpoints_groups.get(base, {})
            checkpoints_groups[base][stream] = os.path.join(checkpoint_path, "model.ckpt")

    # Get the test data
    test_data_dir = os.path.join(DATA_DIR, args.data)

    classes = {dir: i for i, dir in enumerate(sorted(os.listdir(test_data_dir)))}

    samples_dirs = []
    labels = []
    for dirpath, _, filenames in os.walk(test_data_dir):
        if filenames:
            samples_dirs.append(dirpath)

            for cls in classes:
                if cls in dirpath:
                    labels.append(classes[cls])
                    break

    # Print number of samples per class
    class_counts = []
    for cls, count in zip(classes, np.bincount(labels)):
        class_counts.append(count)
        print(f"Class '{cls}': {count} samples")
    print()

    # Perform the inferences for each combination of checkpoints
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    for group, checkpoints in checkpoints_groups.items():
        print(f"Evaluating checkpoints group '{group}'")

        models = {}
        predictions = {}

        # Create models
        for stream, checkpoint in checkpoints.items():
            model = i3d.InceptionI3d(len(classes), final_endpoint="Logits")
            tf.train.Checkpoint(model=model).restore(checkpoint).expect_partial()

            models[stream] = model

        # Perform inferences
        for sample_dir in tqdm(samples_dirs):
            sample_logits = {}

            for stream, model in models.items():
                sample = tf.convert_to_tensor(
                    np.load(os.path.join(sample_dir, f"{stream}.npy")), dtype=tf.float32
                )
                sub_samples = generate_sub_samples(sample)

                logits, _ = model(sub_samples[0])
                if len(sub_samples) > 1:
                    for sub_sample in sub_samples[1:]:
                        logits += model(sub_sample)[0]

                sample_logits[stream] = logits

                del sample, sub_samples
                gc.collect()

            if len(sample_logits) > 1:
                sample_logits["joint"] = sum(sample_logits.values())

            for stream, logits in sample_logits.items():
                probabilities = tf.nn.softmax(logits)[0]
                prediction = np.argsort(probabilities)[::-1][0]
                probability = probabilities[prediction]

                predictions[stream] = predictions.get(stream, [])
                predictions[stream].append((prediction, probability.numpy()))  # type: ignore

            del sample_logits
            gc.collect()

        tf.keras.backend.clear_session()
        gc.collect()

        true_labels = np.array(labels)

        # Ensure empty output directory
        output_dir = os.path.join(OUTPUT_DIR, group)
        os.makedirs(output_dir, exist_ok=True)

        print(f"Saving results to '{output_dir}'\n")

        # Save confusion matrix
        for stream, stream_predictions in predictions.items():
            # Generate confusion matrix
            cm = confusion_matrix(true_labels, np.array([i[0] for i in stream_predictions]))

            _, ax = plt.subplots(figsize=(10, 10))
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False)
            ax.set_title(f"Confusion matrix for '{group}' ({stream})")
            ax.set_xlabel("Predicted")
            ax.set_ylabel("True")

            plt.savefig(os.path.join(output_dir, f"{stream}.png"))

        # Save predictions
        with open(os.path.join(output_dir, "predictions.txt"), "w", encoding="utf-8") as file:
            for i, (sample_dir, label) in enumerate(zip(samples_dirs, labels)):
                file.write(f"Sample '{sample_dir}'\n")
                file.write(f"True: {label}\n")
                file.write("------\n")

                for stream, stream_predictions in predictions.items():
                    file.write(f"{stream}: {stream_predictions[i]}\n")

                file.write("\n")

        # Save statistics
        betas = [2, 2, 0.5]
        class_weights = np.array(class_counts) / len(labels)

        with open(os.path.join(output_dir, "statistics.txt"), "w", encoding="utf-8") as file:
            for stream, stream_predictions in predictions.items():
                pred_labels = np.array([i[0] for i in stream_predictions])

                class_accuracies = []
                class_precisions = []
                class_recalls = []
                class_fscores = []

                # Compute metrics for each class
                for i in range(len(classes)):
                    true_labels_class = tf.cast(tf.equal(true_labels, i), tf.int32)
                    pred_labels_class = tf.cast(tf.equal(pred_labels, i), tf.int32)
                    class_accuracies.append(accuracy_score(true_labels_class, pred_labels_class))
                    class_precisions.append(precision_score(true_labels_class, pred_labels_class))
                    class_recalls.append(recall_score(true_labels_class, pred_labels_class))
                    class_fscores.append(
                        fbeta_score(true_labels_class, pred_labels_class, beta=betas[i])
                    )

                # Compute overall metrics
                overall_accuracy = np.average(class_accuracies, weights=class_weights)
                overall_precision = np.average(class_precisions, weights=class_weights)
                overall_recall = np.average(class_recalls, weights=class_weights)
                overall_fscore = np.average(class_fscores, weights=class_weights)

                # Write to file
                file.write(f"Stream '{stream}'\n")
                file.write("------\n")
                file.write(f"Overall Accuracy: {overall_accuracy}\n")
                file.write(f"Overall Precision: {overall_precision}\n")
                file.write(f"Overall Recall: {overall_recall}\n")
                file.write(f"Overall F-Score: {overall_fscore}\n")

                for i, cls in enumerate(classes):
                    file.write("------\n")
                    file.write(f"Class '{list(classes.keys())[i]}'\n")
                    file.write(f"Accuracy: {class_accuracies[i]}\n")
                    file.write(f"Precision: {class_precisions[i]}\n")
                    file.write(f"Recall: {class_recalls[i]}\n")
                    file.write(f"F-Score: {class_fscores[i]}\n")

                file.write("\n")


if __name__ == "__main__":
    main()
