"""
Test of optical flow generation using Farneback method.
"""

import imageio
import numpy as np
import cv2

name = "basket"

# Load the GIF
gif_path = f'{name}.gif'
gif = imageio.mimread(gif_path)

# Convert the list of frames to a NumPy array
gif_np = np.array(gif)

# Initialize list to hold optical flow frames
flow_frames = []

# Calculate optical flow between consecutive frames
for i in range(len(gif_np) - 1):
    # Convert frames to grayscale
    prvs = cv2.cvtColor(gif_np[i], cv2.COLOR_BGR2GRAY)
    next = cv2.cvtColor(gif_np[i + 1], cv2.COLOR_BGR2GRAY)

    # Calculate optical flow
    flow = cv2.calcOpticalFlowFarneback(prvs, next, None, 0.5, 3, 15, 3, 5, 1.2, 0)

    # Resize optical flow to 224x224
    flow_resized = cv2.resize(flow, (224, 224))

    flow_frames.append(flow_resized)

# Convert list of flow frames to NumPy array
flow_np = np.array(flow_frames)

# Subsample to only 79 frames, taking every second frame from the beginning
subsampled_flow_np = flow_np[:79]

# Ensure we have exactly 79 frames
if subsampled_flow_np.shape[0] > 79:
    subsampled_flow_np = subsampled_flow_np[:79]

# Add an extra dimension to make the shape (1, 79, 224, 224, 2)
final_flow_np = np.expand_dims(subsampled_flow_np, axis=0)

# Save the NumPy array to a file
npy_path = f'{name}_flow.npy'
np.save(npy_path, final_flow_np)

print("Optical flow frames reshaped, subsampled, and saved successfully.")
print("Shape of the NumPy array:", final_flow_np.shape)
print("NumPy array saved to:", npy_path)
