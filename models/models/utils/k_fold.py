"""
K-Fold cross validation training
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order

from __future__ import annotations

import os
import shutil
import numpy as np

from tqdm import tqdm
from typing import Callable, Any
from sklearn.model_selection import StratifiedKFold

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)


def create_dataset(
    npy_samples_paths: list[str],
    labels: list[int],
    batch_size: int = 1,
) -> tf.data.Dataset:
    """
    Create a TensorFlow dataset from the given npy samples paths and labels

    Args:
        npy_samples_paths: List of samples paths
        labels: List of labels
        batch_size: Batch size

    Returns:
        dataset
    """

    def _load_data():
        for path, label in zip(npy_samples_paths, labels):
            data = np.load(path)
            data = np.squeeze(data, axis=0)
            data = tf.convert_to_tensor(data, dtype=tf.float32)

            label = tf.convert_to_tensor(label, dtype=tf.int32)

            yield data, label

    # TODO: review squeeze and shapes
    dataset = tf.data.Dataset.from_generator(
        _load_data,
        output_signature=(
            tf.TensorSpec(shape=(None, 7, 7, 1024), dtype=tf.float32),  # type: ignore
            tf.TensorSpec(shape=(), dtype=tf.int32),  # type: ignore
        ),
    )

    dataset = dataset.shuffle(buffer_size=1000)
    dataset = dataset.padded_batch(
        batch_size=batch_size,
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
    loss_fn: tf.losses.Loss,
    score: tf.keras.metrics.Metric,
) -> tuple[float, float]:
    """
    Train the model using the given data

    Args:
        model: Model to train
        dataset: Dataset containing training data
        optimizer: Optimizer
        loss_fn: Loss function
        score: Score to track

    Returns:
        (mean loss value, score value)

        where:
            mean loss value: Mean loss value
            score value: Score value
    """

    loss = tf.keras.metrics.Mean()

    # Perform training step
    for batch_samples, batch_labels in dataset:
        with tf.GradientTape() as tape:
            # Get model predictions
            logits, _ = model(batch_samples)

            # Calculate loss
            loss_value = loss_fn(batch_labels, logits)

        # Calculate gradients
        grads = tape.gradient(loss_value, model.trainable_variables)

        # Update model weights
        optimizer.apply_gradients(zip(grads, model.trainable_variables))

        # Update metrics
        loss.update_state(loss_value)
        score.update_state(batch_labels, logits)

    return loss.result().numpy(), score.result().numpy()  # type: ignore


def validation_step(
    model,
    dataset: tf.data.Dataset,
    loss_fn: tf.losses.Loss,
    score: tf.keras.metrics.Metric,
) -> tuple[float, float]:
    """
    Validate the model using the given data

    Args:
        model: Model to validate
        dataset: Dataset containing validation data
        loss_fn: Loss function
        score: Score to track

    Returns:
        (mean loss value, score value)

        where:
            mean loss value: Mean loss value
            score value: Score value
    """

    loss = tf.keras.metrics.Mean()

    # Perform validation step
    for batch_samples, batch_labels in dataset:
        # Get model predictions
        logits, _ = model(batch_samples)

        # Calculate loss
        loss_value = loss_fn(batch_labels, logits)

        # Update metrics
        loss.update_state(loss_value)
        score.update_state(batch_labels, logits)

    return loss.result().numpy(), score.result().numpy()  # type: ignore


def finetune(
    samples: list[str],
    labels: list[int],
    model_generator: Callable[[],],
    optimizer_generator: Callable[[], tf.optimizers.Optimizer],
    loss_fn_generator: Callable[[], tf.losses.Loss],
    score_generator: Callable[[], tf.keras.metrics.Metric],
    tmp_dir: str,
    kfolds: int,
    epochs: int,
    batch_size: int,
) -> tuple[Any, tuple[list[list[float]], list[list[float]], list[list[float]], list[list[float]]]]:
    """
    Function to finetune a checkpointed I3D model on a custom dataset

    Args:
        samples: List of samples paths
        labels: List of labels
        model_generator: Model generator
        optimizer_generator: Function to generate an optimizer
        loss_fn_generator: Function to generate a loss function
        score_generator: Function to generate a score tracker
        tmp_dir: Temporary directory to save necessary files
        kfolds: Number of K Folds
        epochs: Number of epochs
        batch_size: Batch size

    Returns:
        (model, (train_losses, train_scores, validation_losses, validation_scores))

        where:
            model: Finetuned model
            train_losses: List of training losses for each K Fold epoch
            train_scores: List of training scores for each K Fold epoch
            validation_losses: List of validation losses for each K Fold epoch
            validation_scores: List of validation scores for each K Fold epoch
    """

    # Set seed
    np.random.seed(42)
    tf.random.set_seed(42)

    # Set destination to save best model
    best_model_dest = os.path.join(tmp_dir, "finetuned", "model.ckpt")

    # Convert samples paths and labels to numpy arrays
    samples = np.array(samples)
    labels = np.array(labels)

    # Create metrics
    train_losses: list[list[float]] = []
    train_scores: list[list[float]] = []

    validation_losses: list[list[float]] = []
    validation_scores: list[list[float]] = []

    best_kfold = 0
    best_epoch = 0
    best_score = 0

    # Train model
    print(f"Training model on {kfolds} KFolds for {epochs} epochs with {len(labels)} samples")
    skf = StratifiedKFold(n_splits=kfolds, shuffle=True, random_state=42)
    for kfold, (train_index, val_index) in enumerate(skf.split(samples, labels)):
        # Initialize kfold metrics
        train_losses.append([])
        train_scores.append([])

        validation_losses.append([])
        validation_scores.append([])

        # Create model
        model = model_generator()

        # Create datasets
        train_samples, train_labels = samples[train_index], labels[train_index]
        val_samples, val_labels = samples[val_index], labels[val_index]

        train_dataset = create_dataset(train_samples, train_labels, batch_size=batch_size)
        validation_dataset = create_dataset(val_samples, val_labels, batch_size=batch_size)

        # Set optimizer
        train_optimizer = optimizer_generator()

        for epoch in tqdm(range(epochs), desc=f"Training K Fold {kfold + 1}"):
            # Train model
            train_loss, train_score = train_step(
                model,
                train_dataset,
                train_optimizer,
                loss_fn_generator(),
                score_generator(),
            )

            train_losses[kfold].append(train_loss)
            train_scores[kfold].append(train_score)

            # Validate model
            validation_loss, validation_score = validation_step(
                model,
                validation_dataset,
                loss_fn_generator(),
                score_generator(),
            )

            validation_losses[kfold].append(validation_loss)
            validation_scores[kfold].append(validation_score)

            # Save best model
            if validation_score > best_score:
                best_score = validation_score
                best_epoch = epoch + 1
                best_kfold = kfold + 1

                shutil.rmtree(os.path.dirname(best_model_dest), ignore_errors=True)
                os.makedirs(os.path.dirname(best_model_dest), exist_ok=True)

                tf.train.Checkpoint(model=model).write(best_model_dest)

    print(
        f"Best model found at K Fold {best_kfold} in Epoch {best_epoch} with Metric {best_score}"
    )

    # Load best model
    model = model_generator()
    tf.train.Checkpoint(model=model).restore(best_model_dest).expect_partial()

    return model, (train_losses, train_scores, validation_losses, validation_scores)
