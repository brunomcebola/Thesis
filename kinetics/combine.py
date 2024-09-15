"""
Script to combine npy files
"""

import numpy as np
from PIL import Image
import imageio
import os

# Function to load and combine multiple npy files
def combine_multiple_npy_files(npy_files, output_npy_path):
    # Load the first npy file to initialize the combined array
    combined_arr = np.load(npy_files[0])

    # Ensure the shape of the first array is as expected
    assert combined_arr.shape[0] == 1, "Arrays must have the shape (1, X, 224, 224, 3)"

    # Iterate through the rest of the npy files and concatenate them
    for npy_file in npy_files[1:]:
        arr = np.load(npy_file)
        assert arr.shape[0] == 1, "Arrays must have the shape (1, X, 224, 224, 3)"
        combined_arr = np.concatenate((combined_arr, arr), axis=1)

    # Save combined array as npy
    np.save(output_npy_path, combined_arr)

    return combined_arr

# Function to save combined npy as a GIF
def save_as_gif(npy_data, output_gif_path):
    # Remove the batch dimension (1) and convert to list of images
    image_sequence = [Image.fromarray((frame.astype(np.uint8))) for frame in npy_data[0]]

    # Save as GIF
    imageio.mimsave(output_gif_path, image_sequence, format='GIF', duration=0.1)

# List of input npy file paths
npy_files = ['input1.npy', 'input2.npy', 'input3.npy']  # Add as many npy files as needed
output_npy_path = 'combined_output.npy'
output_gif_path = 'output.gif'

# Combine the npy files and save the result
combined_data = combine_multiple_npy_files(npy_files, output_npy_path)

# Save the combined data as a GIF
save_as_gif(combined_data, output_gif_path)

print(f"Combined .npy saved as: {output_npy_path}")
print(f"GIF saved as: {output_gif_path}")
