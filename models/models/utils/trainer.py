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
from typing import Any
from abc import ABC, abstractmethod

from . import search
from . import funcs

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
        learning_rates: list[float],
        confidence_thresholds: list[float],
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

        self._learning_rates = learning_rates
        self._confidence_thresholds = confidence_thresholds

        self._results = {}
        self._model = self._gen_model()

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

    def search(self) -> None:
        """
        Train the model
        """

        self._results = search.stratified_k_fold(
            self._samples,
            self._labels,
            self._gen_model,
            self._gen_score,
            self._learning_rates,
            self._confidence_thresholds,
        )

    def train(self) -> None:
        dataset = funcs.create_dataset(np.array(self._samples), np.array(self._labels))

        optimizer = tf.optimizers.Adam(learning_rate=self._results["hyperparameters"][1])

        for _ in tqdm(range(self._results["hyperparameters"][0]), desc="Training model"):
            loss_fn = tf.losses.SparseCategoricalCrossentropy(from_logits=True)

            funcs.train_step(self._model, dataset, optimizer, loss_fn)


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

        # Save best hyperparameters
        with open(
            os.path.join(self._output_checkpoint_dir, "best_hyperparameters.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(str(self._results["hyperparameters"]))

        # Save scores
        np.save(os.path.join(self._output_checkpoint_dir, "scores.npy"), self._results["scores"])

        # Save scores plot
        plt.rc('font', size=20)
        plt.rc('axes', titlesize=20)
        plt.rc('axes', labelsize=20)
        plt.rc('xtick', labelsize=20)
        plt.rc('ytick', labelsize=20)
        plt.rc('legend', fontsize=20)
        _, axs = plt.subplots(1, 1, figsize=(12, 8))
        for hyperparameter, scores in self._results["scores"].items():
            axs.plot(range(len(scores)), scores, label=f"lr: {hyperparameter[0]} ; ct: {hyperparameter[1]}")
        axs.set_title("Validation Score Over Epochs")
        axs.set_xlabel("Epochs")
        axs.set_ylabel("Scores")
        axs.xaxis.set_major_locator(plt.MaxNLocator(integer=True))  # type: ignore
        axs.set_yticks([i * 0.1 for i in range(11)])
        axs.set_ylim(0, 1)
        axs.set_xlim(left=0, right=len(scores) - 1)
        axs.legend()
        axs.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(self._output_checkpoint_dir, "scores_plot.png"))

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
    def _gen_model(self) -> Any:
        """
        Generate model
        """

    @abstractmethod
    def _gen_score(self, confidence_threshold: float) -> tf.keras.metrics.Metric:
        """
        Generate metrics
        """

    @abstractmethod
    def _save_model(self) -> None:
        """
        Save the model
        """
