"""
Convert a GIF to a NumPy array.
"""

import imageio
import numpy as np
import cv2

name = "test"

# Load the GIF
gif_path = f'{name}.gif'
gif = imageio.mimread(gif_path)

# Convert the list of frames to a NumPy array
gif_np = np.array(gif)

# Reshape each frame to 224x224 pixels
reshaped_frames = [cv2.resize(frame, (224, 224)) for frame in gif_np]

# Convert the list of reshaped frames back to a NumPy array
reshaped_np = np.array(reshaped_frames)

# Subsample to only 79 frames, taking every second frame from the beginning
subsampled_np = reshaped_np[:79]

# Ensure we have exactly 79 frames
if subsampled_np.shape[0] > 79:
    subsampled_np = subsampled_np[:79]

# Add an extra dimension to make the shape (1, 79, 224, 224, 3)
final_np = np.expand_dims(subsampled_np, axis=0)

# Save the NumPy array to a file
npy_path = f'{name}_rgb.npy'
np.save(npy_path, final_np)

print("GIF frames reshaped, subsampled, and saved successfully.")
print("Shape of the NumPy array:", final_np.shape)
print("NumPy array saved to:", npy_path)
