import numpy as np
import cv2
import imageio

name = "basket"

# Load the NumPy array
npy_path = f'{name}_flow.npy'
optical_flow_np = np.load(npy_path)

# Ensure the shape is correct
assert optical_flow_np.shape == (1, 79, 224, 224, 2), "The shape of the loaded array is incorrect."

# Remove the first dimension to get the shape (79, 224, 224, 2)
optical_flow_np = optical_flow_np[0]

# Initialize list to hold flow visualizations
flow_vis_frames = []

for flow in optical_flow_np:
    # Compute magnitude and angle of the flow
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])

    # Create an HSV image
    hsv = np.zeros((224, 224, 3), dtype=np.uint8)
    hsv[..., 0] = ang * 180 / np.pi / 2  # Angle (Hue)
    hsv[..., 1] = 255  # Saturation
    hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)  # Magnitude (Value)

    # Convert HSV to RGB
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # Append to the list of frames
    flow_vis_frames.append(rgb)

# Save the frames as a GIF
gif_path = f'{name}_flow.gif'
imageio.mimsave(gif_path, flow_vis_frames, fps=10)

print("Optical flow GIF generated successfully.")
print("GIF saved to:", gif_path)
