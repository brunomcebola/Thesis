from __future__ import annotations

import os
import numpy as np

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)


def create_dataset(
    npy_samples_paths: list[str],
    labels: list[int],
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

    shape = np.load(npy_samples_paths[0]).shape # type: ignore
    shape = [None for _ in shape[1:]]

    dataset = tf.data.Dataset.from_generator(
        _load_data,
        output_signature=(
            tf.TensorSpec(shape=tuple(shape), dtype=tf.float32),  # type: ignore
            tf.TensorSpec(shape=(), dtype=tf.int32),  # type: ignore
        ),
    )

    dataset = dataset.shuffle(buffer_size=1000)
    dataset = dataset.padded_batch(
        batch_size=1,
        padded_shapes=(
            shape,
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
) -> None:
    """
    Train the model using the given data

    Args:
        model: Model to train
        dataset: Dataset containing training data
        optimizer: Optimizer
        loss_fn: Loss function
    """

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


def validation_step(
    model,
    dataset: tf.data.Dataset,
    score: tf.keras.metrics.Metric,
) -> float:
    """
    Validate the model using the given data

    Args:
        model: Model to validate
        dataset: Dataset containing validation data
        loss_fn: Loss function
        score: Score to track

    Returns:
        score value
    """

    # Perform validation step
    for batch_samples, batch_labels in dataset:
        # Get model predictions
        logits, _ = model(batch_samples)

        # Update metrics
        score.update_state(batch_labels, logits)

    return score.result().numpy()  # type: ignore

