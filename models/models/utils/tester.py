"""
Trainer interface
"""

# pylint: disable=wrong-import-order

import os
import gc
import shutil
import numpy as np
import seaborn as sns
import tensorflow as tf
import matplotlib.pyplot as plt

from tqdm import tqdm
from typing import Any
from abc import ABC, abstractmethod
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    fbeta_score,
)

class Tester(ABC):
    """
    Tester interface
    """

    def __init__(
        self,
        checkpoint_group: tuple[str, dict[str, str]],
        data_dir: str,
        output_dir: str,
        confidence_threshold: float,
        fallback_label: int,
    ) -> None:
        """
        Initialize the trainer
        """

        super().__init__()

        self._checkpoint_group = checkpoint_group

        self._output_dir = os.path.join(output_dir, checkpoint_group[0])
        shutil.rmtree(self._output_dir, ignore_errors=True)
        os.makedirs(self._output_dir, exist_ok=True)

        self._data_dir = data_dir

        self._classes = {dir: i for i, dir in enumerate(sorted(os.listdir(self._data_dir)))}
        self._num_classes = len(self._classes)
        self._class_counts = []

        self._samples = []
        self._labels = []

        self._models = {}
        self._predictions = {}

        self._confidence_threshold = confidence_threshold
        self._fallback_label = fallback_label

    def initialize(self) -> None:
        """
        Initialize the trainer
        """

        # Get samples
        samples = []
        labels = []
        for dirpath, _, filenames in os.walk(self._data_dir):
            if filenames:
                samples.append(dirpath)

                for cls in self._classes:
                    if cls in dirpath:
                        labels.append(self._classes[cls])
                        break

        self._samples = samples
        self._labels = labels

        for cls, count in zip(self._classes, np.bincount(labels)):
            self._class_counts.append(count)
            print(f"Class '{cls}': {count} samples")

        # Create models
        for stream, checkpoint in self._checkpoint_group[1].items():
            model = self._gen_model(checkpoint)
            self._models[stream] = model

    def test(self) -> None:
        """
        Test the models
        """

        # Perform inferences
        for sample_path in tqdm(self._samples, desc="Testing"):
            sample_logits = {}

            for stream, model in self._models.items():
                sample = np.load(os.path.join(sample_path, f"{stream}.npy"))
                sub_samples = self._gen_sub_samples(sample) # type: ignore
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

                if probability < self._confidence_threshold:
                    prediction = self._fallback_label

                self._predictions[stream] = self._predictions.get(stream, [])
                self._predictions[stream].append((prediction, probability.numpy()))  # type: ignore

            del sample_logits
            gc.collect()

        gc.collect()

    def save(self) -> None:
        """
        Save test session
        """

        for stream, stream_predictions in self._predictions.items():
            # Generate confusion matrix
            cm = confusion_matrix(np.array(self._labels), np.array([i[0] for i in stream_predictions])).T

            # Plot confusion matrix
            plt.rc('font', size=20)
            plt.rc('axes', titlesize=20)
            plt.rc('axes', labelsize=20)
            plt.rc('xtick', labelsize=20)
            plt.rc('ytick', labelsize=20)
            plt.rc('legend', fontsize=20)
            _, ax = plt.subplots(figsize=(10, 10))
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False)
            ax.set_title(f"Confusion matrix for '{self._checkpoint_group[0]}' ({stream})")
            ax.set_xlabel("True")
            ax.set_ylabel("Predicted")
            ax.set_xticklabels(self._classes.keys())
            ax.set_yticklabels(self._classes.keys())
            ax.invert_yaxis()

            plt.tight_layout()
            plt.savefig(os.path.join(self._output_dir, f"{stream}.png"))

        # Save predictions
        with open(os.path.join(self._output_dir, "predictions.txt"), "w", encoding="utf-8") as file:
            for i, (sample_dir, label) in enumerate(zip(self._samples, self._labels)):
                file.write(f"Sample '{sample_dir}'\n")
                file.write(f"True: {label}\n")
                file.write("------\n")

                for stream, stream_predictions in self._predictions.items():
                    file.write(f"{stream}: {stream_predictions[i]}\n")

                file.write("\n")

        # Save statistics
        betas = [2, 2, 0.5, 0.5]
        class_weights = np.array(self._class_counts) / len(self._labels)

        with open(os.path.join(self._output_dir, "statistics.txt"), "w", encoding="utf-8") as file:
            for stream, stream_predictions in self._predictions.items():
                pred_labels = np.array([i[0] for i in stream_predictions])

                class_accuracies = []
                class_precisions = []
                class_recalls = []
                class_fscores = []

                # Compute metrics for each class
                for i in range(self._num_classes):
                    true_labels_class = tf.cast(tf.equal(np.array(self._labels), i), tf.int32)
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

                for i, cls in enumerate(self._classes):
                    file.write("------\n")
                    file.write(f"Class '{list(self._classes.keys())[i]}'\n")
                    file.write(f"Accuracy: {class_accuracies[i]}\n")
                    file.write(f"Precision: {class_precisions[i]}\n")
                    file.write(f"Recall: {class_recalls[i]}\n")
                    file.write(f"F-Score: {class_fscores[i]}\n")

                file.write("\n")

    #
    # Abstract methods
    #

    @abstractmethod
    def _gen_model(self, checkpoint) -> Any:
        """
        Generate model
        """

    @abstractmethod
    def _gen_sub_samples(self, sample: np.ndarray) -> list[np.ndarray]:
        """
        Generate sub-samples
        """