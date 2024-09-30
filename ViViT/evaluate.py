import os
import numpy as np
import torch

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf  # pylint: disable=wrong-import-position
from transformers import VivitModel  # type: disable=wrong-import-position

np.random.seed(0)

# Check if CUDA is available and set the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load video of shape (1, F, 224, 224, 3) from numpy file
video = np.load("v_CricketShot_g04_c01_rgb.npy")

# Resample video to 32 frames
video = video[:, np.linspace(0, video.shape[1] - 1, 32, dtype=int), :, :, :]


# Normalize from -1 to 1 to 0 to 1
video = (video + 1) / 2  # type: ignore

inputs = {"pixel_values": torch.tensor(video).permute(0, 1, 4, 2, 3).to(device)}

print("Inputs shape:", inputs["pixel_values"].shape)

# Load model
print("Loading model...")
model = VivitModel.from_pretrained("models/kinetics400").to(device)

# Make prediction
print("Making prediction...")
with torch.no_grad():
    outputs = model(**inputs)






with open("labels.txt", encoding="utf-8") as f:
    labels = f.readlines()

# Print label and probability
predictions = tf.nn.softmax(logits.cpu())[0]
predicted_class_index = np.argsort(predictions)[::-1][0]
predicted_class_name = labels[predicted_class_index].strip()
predicted_class_probability = predictions[predicted_class_index]

# Print the predicted class name and probabilities
print(f"Predicted Class: {predicted_class_name} with probability {predicted_class_probability}")