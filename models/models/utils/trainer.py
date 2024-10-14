"""
Trainer interface
"""

# pylint: disable=wrong-import-order

import os
import gc
import shutil
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from tqdm import tqdm
from abc import ABC, abstractmethod

from . import k_fold_finetune

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Trainer(ABC):
    """
    Trainer interface
    """

    def __init__(
        self,
        input_checkpoint_dir: str,
        output_checkpoint_dir: str,
        source_data_dir: str,
        tmp_dir: str,
        k_folds: int,
        epochs: int,
        batch_size: int,
    ) -> None:
        """
        Initialize the trainer
        """

        super().__init__()

        self._input_checkpoint_dir = input_checkpoint_dir
        self._input_checkpoint = os.path.join(input_checkpoint_dir, "model.ckpt")

        self._output_checkpoint_dir = output_checkpoint_dir
        shutil.rmtree(self._output_checkpoint_dir, ignore_errors=True)
        os.makedirs(self._output_checkpoint_dir, exist_ok=True)

        self._source_data_dir = source_data_dir

        self._tmp_dir = tmp_dir
        shutil.rmtree(self._tmp_dir, ignore_errors=True)
        os.makedirs(self._tmp_dir, exist_ok=True)

        self._train_data_dir = os.path.join(self._tmp_dir, "train_data")
        shutil.rmtree(self._train_data_dir, ignore_errors=True)
        os.makedirs(self._train_data_dir, exist_ok=True)

        self._classes = {dir: i for i, dir in enumerate(sorted(os.listdir(self._source_data_dir)))}
        self._num_classes = len(self._classes)

        self._samples = []
        self._labels = []

        self._k_folds = k_folds
        self._epochs = epochs
        self._batch_size = batch_size

        self._best_model = None
        self._metrics = None

    def initialize(self) -> None:
        """
        Initialize the trainer
        """

        # Get source samples
        source_samples = self._get_source_samples()

        # Generate training data
        train_samples = []
        train_labels = []
        for source_sample in tqdm(source_samples, desc="Generating training data"):
            output_path = source_sample.replace(self._source_data_dir, self._train_data_dir)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            for i, entry in enumerate(self._process_source_sample(source_sample)):
                train_sample_path = output_path.replace(".npy", f"_{i}.npy")

                np.save(train_sample_path, entry)

                train_samples.append(train_sample_path)
                train_labels.append(
                    self._classes[train_sample_path.replace(self._train_data_dir, "").split("/")[1]]
                )

        self._samples = train_samples
        self._labels = train_labels

    def train(self) -> None:
        """
        Train the model
        """

        model, metrics = k_fold_finetune(
            self._samples,
            self._labels,
            self._gen_model,
            self._gen_optimizer,
            self._gen_loss,
            self._gen_score,
            self._tmp_dir,
            self._k_folds,
            self._epochs,
            self._batch_size,
        )

        self._best_model = model
        self._metrics = metrics

    def save(self) -> None:
        """
        Save training session
        """

        self._save_model()

        # Save class labels
        with open(
            os.path.join(self._output_checkpoint_dir, "labels.txt"), "w", encoding="utf-8"
        ) as f:
            f.write("\n".join(self._classes.keys()))

        # Save training plot
        _, axs = plt.subplots(1, 2, figsize=(12, 6))

        for i, train_losses in enumerate(self._metrics[0], 1):
            axs[0].plot(range(1, len(train_losses) + 1), train_losses, label=f"K Fold {i}")
        axs[0].set_title("Train Loss Over Epochs")
        axs[0].set_xlabel("Epochs")
        axs[0].set_ylabel("Loss")
        axs[0].legend()
        axs[0].grid(True)

        for i, train_scores in enumerate(self._metrics[1], 1):
            axs[1].plot(range(1, len(train_scores) + 1), train_scores, label=f"K Fold {i}")
        axs[1].set_title("Train Score Over Epochs")
        axs[1].set_xlabel("Epochs")
        axs[1].set_ylabel("Scores")
        axs[1].legend()
        axs[1].grid(True)

        plt.tight_layout()
        plt.savefig(os.path.join(self._output_checkpoint_dir, "train_plot.png"))

        # Save validation plot
        _, axs = plt.subplots(1, 2, figsize=(12, 6))

        for i, validation_losses in enumerate(self._metrics[2], 1):
            axs[0].plot(
                range(1, len(validation_losses) + 1), validation_losses, label=f"K Fold {i}"
            )
        axs[0].set_title("Validation Score Over Epochs")
        axs[0].set_xlabel("Epochs")
        axs[0].set_ylabel("Loss")
        axs[0].legend()
        axs[0].grid(True)

        for i, validation_scores in enumerate(self._metrics[3], 1):
            axs[1].plot(
                range(1, len(validation_scores) + 1), validation_scores, label=f"K Fold {i}"
            )
        axs[1].set_title("Validation Score Over Epochs")
        axs[1].set_xlabel("Epochs")
        axs[1].set_ylabel("Scores")
        axs[1].legend()
        axs[1].grid(True)

        plt.tight_layout()
        plt.savefig(os.path.join(self._output_checkpoint_dir, "validation_plot.png"))

    def cleanup(self) -> None:
        """
        Cleanup the trainer
        """

        shutil.rmtree(self._tmp_dir, ignore_errors=True)
        gc.collect()
        tf.keras.backend.clear_session()

    #
    # Abstract methods
    #

    @abstractmethod
    def _get_source_samples(self) -> list:
        """
        Get all source samples
        """

    @abstractmethod
    def _process_source_sample(self, sample: str) -> list:
        """
        Generate training sample
        """

    @abstractmethod
    def _gen_model(self):
        """
        Generate model
        """

    @abstractmethod
    def _gen_optimizer(self):
        """
        Generate optimizer
        """

    @abstractmethod
    def _gen_loss(self):
        """
        Generate loss
        """

    @abstractmethod
    def _gen_score(self):
        """
        Generate metrics
        """

    @abstractmethod
    def _save_model(self):
        """
        Save the model
        """
