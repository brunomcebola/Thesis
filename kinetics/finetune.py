"""
Scrip to fine tune the I3D model on specific data
"""

from __future__ import absolute_import, division, print_function

import os
import glob
import numpy as np
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf  # pylint: disable=wrong-import-position
import i3d_logits  # pylint: disable=wrong-import-position


DATA_PATH = "data/rgb"

# Loss function and optimizer
CROSS_ENTROPY_LOSS = tf.losses.SparseCategoricalCrossentropy(from_logits=True)
OPTIMIZER = tf.optimizers.Adam()


# Create a generator that loads each sample from the disk as needed
def numpy_data_generator(file_paths, labels):
    """
    Generator function to load numpy arrays from disk
    """
    for file_path, label in zip(file_paths, labels):
        sample_data = np.load(file_path)  # Load the file, shape: (1, X, 7, 7, 1024)
        sample_data = np.squeeze(sample_data, axis=0)  # Remove the first dimension
        yield sample_data.astype(np.float32), label.astype(np.int64)


# Use TensorFlow's Dataset API to create a dataset that loads data dynamically
def create_tf_dataset(file_paths, labels, batch_size=64):
    """
    Creates a TensorFlow dataset that loads data dynamically from disk and pads sequences
    """
    dataset = tf.data.Dataset.from_generator(
        lambda: numpy_data_generator(file_paths, labels),  # Generator function
        output_signature=(
            tf.TensorSpec(shape=(None, 7, 7, 1024), dtype=tf.float32),  # type: ignore
            tf.TensorSpec(shape=(), dtype=tf.int64),  # type: ignore
        ),
    )
    # Apply padding to make all sequences in a batch the same length
    dataset = dataset.shuffle(buffer_size=1024)  # Shuffle the data
    dataset = dataset.padded_batch(
        batch_size=batch_size,
        padded_shapes=(
            [None, 7, 7, 1024],
            [],
        ),  # Pad each batch to the maximum X length in the batch
    )
    dataset = dataset.prefetch(tf.data.AUTOTUNE)  # Prefetch for efficient data loading
    return dataset


# Training step function
@tf.function
def train_step(model, inputs, labels):
    """
    Function to perform a single training step on a batch of data
    """

    with tf.GradientTape() as tape:
        logits, _ = model(inputs)
        loss_value = CROSS_ENTROPY_LOSS(labels, logits)
    gradients = tape.gradient(loss_value, model.trainable_variables)
    OPTIMIZER.apply_gradients(zip(gradients, model.trainable_variables))
    return loss_value


# Validation step function
@tf.function
def val_step(model, inputs, labels):
    """
    Function to perform a single validation step on a batch of data
    """

    logits, _ = model(inputs)
    loss_value = CROSS_ENTROPY_LOSS(labels, logits)
    return loss_value


def train_model(model, train_dataset, val_dataset, epochs):
    """
    Function to train a model on a dataset
    """

    train_losses, val_losses = [], []
    train_accuracies, val_accuracies = [], []

    for epoch in range(epochs):
        print(f"Starting epoch {epoch+1}")

        # Training loop

        epoch_loss_avg = tf.keras.metrics.Mean()
        epoch_accuracy = tf.keras.metrics.SparseCategoricalAccuracy()

        for _, (images, labels) in enumerate(train_dataset):
            loss_value = train_step(model, images, labels)
            epoch_loss_avg.update_state(loss_value)
            epoch_accuracy.update_state(labels, model(images)[0])

            # Clear GPU memory by deleting intermediate tensors
            del images, labels
            tf.keras.backend.clear_session()  # Clear any remaining GPU memory

        train_losses.append(epoch_loss_avg.result().numpy())  # type: ignore
        train_accuracies.append(epoch_accuracy.result().numpy())  # type: ignore

        # Validation loop
        val_loss_avg = tf.keras.metrics.Mean()
        val_accuracy = tf.keras.metrics.SparseCategoricalAccuracy()

        for _, (val_images, val_labels) in enumerate(val_dataset):
            val_loss_value = val_step(model, val_images, val_labels)
            val_loss_avg.update_state(val_loss_value)
            val_accuracy.update_state(val_labels, model(val_images)[0])

            # Clear GPU memory by deleting intermediate tensors
            del val_images, val_labels
            tf.keras.backend.clear_session()  # Clear any remaining GPU memory

        val_losses.append(val_loss_avg.result().numpy())  # type: ignore
        val_accuracies.append(val_accuracy.result().numpy())  # type: ignore

        print(
            f"Training Loss: {train_losses[-1]}, Validation Loss: {val_losses[-1]}\n"
            f"Training Accuracy: {train_accuracies[-1]}, Validation Accuracy: {val_accuracies[-1]}\n"
        )

    return train_losses, val_losses, train_accuracies, val_accuracies


def test_model(model, cls):
    # Load a single sample
    sample_data = np.load(os.path.join(DATA_PATH, "conflict", "0", "0_0_rgb.npy"))

    # Get the predicted logits
    logits, _ = model(sample_data)

    # Get the predicted probabilities
    predictions = tf.nn.softmax(logits)[0]

    # Get the predicted class index
    predicted_class_index = np.argsort(predictions)[::-1][0]

    # Get the predicted class name
    predicted_class_name = [k for k, v in cls.items() if v == predicted_class_index][0]

    # Get the predicted class probability
    predicted_class_probability = predictions[predicted_class_index]

    # Print the predicted class name and probabilities
    print(f"Predicted Class: {predicted_class_name} with probability {predicted_class_probability}")


def main():
    """
    Main function to train the model
    """
    
    # Set random seed
    tf.random.set_seed(42)
    np.random.seed(42)

    # Load the data
    file_paths = sorted(glob.glob(f"{DATA_PATH}/*/*/*_rgb.npy"))  # Path to multiple samples

    cls = sorted({file_path.split("/")[2] for file_path in file_paths})
    cls = {c: i for i, c in enumerate(cls)}
    num_classes = len(cls)

    labels = np.array([cls[file_path.split("/")[2]] for file_path in file_paths])

    # Split into training and validation sets
    train_files, val_files, train_labels, val_labels = train_test_split(
        file_paths, labels, test_size=0.2, random_state=42, stratify=labels
    )

    # Create TensorFlow datasets for training and validation
    train_dataset = create_tf_dataset(train_files, train_labels, batch_size=64)
    val_dataset = create_tf_dataset(val_files, val_labels, batch_size=64)

    # Instantiate the model
    model = i3d_logits.InceptionI3dLogits(num_classes=num_classes)

    # Test model before train
    test_model(model, cls)
    print()

    # Train the model for 10 epochs
    train_losses, val_losses, train_accuracies, val_accuracies = train_model(
        model, train_dataset, val_dataset, epochs=100
    )

    # Plotting accuracy and loss over epochs side by side
    fig, axs = plt.subplots(1, 2, figsize=(12, 6))

    # Plot Accuracy
    axs[0].plot(train_accuracies, label="Training Accuracy", color="blue")
    axs[0].plot(val_accuracies, label="Validation Accuracy", color="orange")
    axs[0].set_title("Model Accuracy Over Epochs")
    axs[0].set_xlabel("Epochs")
    axs[0].set_ylabel("Accuracy")
    axs[0].legend()
    axs[0].grid(True)

    # Plot Loss
    axs[1].plot(train_losses, label="Training Loss", color="blue")
    axs[1].plot(val_losses, label="Validation Loss", color="orange")
    axs[1].set_title("Model Loss Over Epochs")
    axs[1].set_xlabel("Epochs")
    axs[1].set_ylabel("Loss")
    axs[1].legend()
    axs[1].grid(True)

    plt.tight_layout()  # Adjust layout for better fit
    plt.show()

    # Test the model after train
    test_model(model, cls)


main()
