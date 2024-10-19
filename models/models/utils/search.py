"""
K-Fold cross validation training
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order

from __future__ import annotations

import os
import numpy as np

from tqdm import tqdm
from typing import Callable, Any
from sklearn.model_selection import StratifiedKFold

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from . import funcs


def stratified_k_fold(
    samples: list[str],
    labels: list[int],
    model_generator: Callable[[],],
    score_generator: Callable[[float, ], tf.keras.metrics.Metric],
    learning_rates: list[float],
    confidence_thresholds: list[float],
) -> dict[str, Any]:
    """
    Function to search for the best hyperparameters combination

    Args:
        samples: List of samples paths
        labels: List of labels
        model_generator: Model generator
        score_generator: Function to generate a score tracker
        tmp_dir: Temporary directory to save necessary files
        learning_rates: List of learning rates to search
        confidence_thresholds: List of confidence thresholds to search

    Returns:
        {
            "hyperparameters": (epochs, learning_rate, confidence_threshold),
            "scores": {
                (learning_rate, confidence_threshold): list[float]
            }
        }
    """

    # Initialize variables
    kfolds = 5
    epochs = 100

    # Set seed
    np.random.seed(42)
    tf.random.set_seed(42)

    # Convert samples paths and labels to numpy arrays
    samples = np.array(samples)
    labels = np.array(labels)

    # Create split
    skf = StratifiedKFold(n_splits=kfolds, shuffle=True, random_state=42)
    skf_split = list(skf.split(samples, labels))

    # Create combinations of hyperparameters
    hyperparameters = [(lr, ct) for lr in learning_rates for ct in confidence_thresholds]

    # Initialize scores
    scores = {hyperparameter: [] for hyperparameter in hyperparameters}

    # Perform search
    print(f"Performing search on {len(hyperparameters)} hyperparameters combinations with {len(labels)} samples")
    for learning_rate, confidence_threshold in hyperparameters:
        print(f"Testing: {learning_rate}, {confidence_threshold}")

        scores[(learning_rate, confidence_threshold)] = []

        for fold, (train_index, val_index) in enumerate(skf_split):
            # Initialize kfold metrics
            scores[(learning_rate, confidence_threshold)].append([])

            # Create model
            model = model_generator()

            # Create datasets
            train_samples, train_labels = samples[train_index], labels[train_index]
            val_samples, val_labels = samples[val_index], labels[val_index]

            train_dataset = funcs.create_dataset(train_samples, train_labels)
            validation_dataset = funcs.create_dataset(val_samples, val_labels)

            # Set optimizer
            train_optimizer = tf.optimizers.Adam(learning_rate=learning_rate)

            # Get initial score
            score = funcs.validation_step(
                model,
                validation_dataset,
                score_generator(confidence_threshold),
            )

            scores[(learning_rate, confidence_threshold)][-1].append(score)

            for _ in tqdm(range(epochs), desc=f"Fold {fold + 1}"):
                # Train model
                funcs.train_step(
                    model,
                    train_dataset,
                    train_optimizer,
                    tf.losses.SparseCategoricalCrossentropy(from_logits=True),
                )

                # Validate model
                score = funcs.validation_step(
                    model,
                    validation_dataset,
                    score_generator(confidence_threshold),
                )

                scores[(learning_rate, confidence_threshold)][-1].append(score)

        scores[(learning_rate, confidence_threshold)] = np.mean(scores[(learning_rate, confidence_threshold)], axis=0)

    # Get best hyperparameters
    best_combination = (0, 0)
    best_epoch = 0
    best_value = 0
    for key, values in scores.items():
        for index, value in enumerate(values):
            # 1. look into the score
            if value > best_value:
                best_value = value
                best_combination = key
                best_epoch = index
            # 2. look into the confidence threshold
            elif value == best_value and key[1] > best_combination[1]:
                best_value = value
                best_combination = key
                best_epoch = index
            # 3. look into the learning rate
            elif value == best_value and key[1] == best_combination[1] and key[0] > best_combination[0]:
                best_value = value
                best_combination = key
                best_epoch = index



    print(f"Result: {best_combination} at epoch {best_epoch} with {best_value} score")

    return {
        "hyperparameters": (best_epoch, *best_combination),
        "scores": scores,
    }

