"""
Scrip to fine tune the I3D model on specific data
"""

from __future__ import absolute_import, division, print_function

import os
import glob
import numpy as np
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from tqdm import tqdm

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import tensorflow as tf  # pylint: disable=wrong-import-position
import i3d_logits  # pylint: disable=wrong-import-position
import i3d  # pylint: disable=wrong-import-position

DATA_PATH = "data/color"
TYPE = "flow"

LOGITS_I3D_CHECKPOINT = f"checkpoints/{TYPE}_400_logits/model.ckpt"
MIXED_5C_CHECKPOINT = f"checkpoints/{TYPE}_400_mixed_5c/model.ckpt"
TUNED_I3D_CHECKPOINT = f"checkpoints/{TYPE}_CLS_logits/model.ckpt"

# Loss function and optimizer
CROSS_ENTROPY_LOSS = tf.losses.SparseCategoricalCrossentropy(from_logits=True)
OPTIMIZER = tf.optimizers.Adam()


def numpy_data_generator(file_paths, labels):
    """
    Generator function to load numpy arrays from disk
    """
    for file_path, label in zip(file_paths, labels):
        sample_data = np.load(file_path)  # Load the file, shape: (1, X, 7, 7, 1024)
        sample_data = np.squeeze(sample_data, axis=0)  # Remove the first dimension
        yield sample_data.astype(np.float32), label.astype(np.int64)


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

    for _ in tqdm(range(epochs), desc="Training epochs"):
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

    return train_losses, val_losses, train_accuracies, val_accuracies


def ensure_mixed_5c_checkpoint():
    model = i3d.InceptionI3d(num_classes=3, spatial_squeeze=True, final_endpoint="Mixed_5c")
    tf.train.Checkpoint(model=model).restore(LOGITS_I3D_CHECKPOINT).expect_partial()
    model(tf.convert_to_tensor(np.random.rand(1, 64, 224, 224, 3 if TYPE == "rgb" else 2), dtype=tf.float32))
    tf.train.Checkpoint(model=model).write(MIXED_5C_CHECKPOINT)


def save_model(model, cls, train_accuracies, val_accuracies, train_losses, val_losses):
    """
    Save the model
    """
    model_variables = {var.name: var for var in model.trainable_variables}

    variables_to_replace_map = {
        "inception_i3d/Logits/Conv3d_0c_1x1/conv_3d/b:0": "inception_i3d_logits/Logits/Conv3d_0c_1x1/conv_3d/b:0",
        "inception_i3d/Logits/Conv3d_0c_1x1/conv_3d/w:0": "inception_i3d_logits/Logits/Conv3d_0c_1x1/conv_3d/w:0",
    }

    i3d_model = i3d.InceptionI3d(
        num_classes=len(cls), spatial_squeeze=True, final_endpoint="Logits"
    )
    i3d_model(tf.convert_to_tensor(np.random.rand(1, 64, 224, 224, 3 if TYPE == "rgb" else 2), dtype=tf.float32))
    tf.train.Checkpoint(model=i3d_model).restore(MIXED_5C_CHECKPOINT).expect_partial()

    for i, var in enumerate(i3d_model.trainable_variables):
        if var.name in variables_to_replace_map:  # type: ignore
            i3d_model.trainable_variables[i].assign(  # type: ignore
                model_variables[variables_to_replace_map[var.name]]  # type: ignore
            )

    destination = TUNED_I3D_CHECKPOINT.replace("CLS", str(len(cls)))

    tf.train.Checkpoint(model=i3d_model).write(destination)

    with open(destination.replace(".ckpt", ".txt"), "w") as f:
        f.write("\n".join(cls.keys()))

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
    plt.savefig(destination.replace(".ckpt", ".png"))


def main():
    """
    Main function to train the model
    """

    # Set random seed
    tf.random.set_seed(42)
    np.random.seed(42)

    # Ensure the checkpoint for Mixed_5c is created
    ensure_mixed_5c_checkpoint()

    # Load the data

    cls = {c: i for i, c in enumerate(sorted(os.listdir(f"{DATA_PATH}")))}

    samples = sorted(glob.glob(f"{DATA_PATH}/*/*/*_{TYPE}.npy"))  # Path to multiple samples
    labels = np.array([cls[sample.split("/")[2]] for sample in samples])

    # Split into training and validation sets
    train_files, val_files, train_labels, val_labels = train_test_split(
        samples, labels, test_size=0.2, random_state=42, stratify=labels
    )

    # Create TensorFlow datasets for training and validation
    train_dataset = create_tf_dataset(train_files, train_labels, batch_size=64)
    val_dataset = create_tf_dataset(val_files, val_labels, batch_size=64)

    # Instantiate the model
    model = i3d_logits.InceptionI3dLogits(num_classes=len(cls))

    # Train the model for 10 epochs
    train_losses, val_losses, train_accuracies, val_accuracies = train_model(
        model, train_dataset, val_dataset, epochs=100
    )

    # Save the model
    save_model(model, cls, train_accuracies, val_accuracies, train_losses, val_losses)


main()
