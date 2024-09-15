"""
Script to rotate all .npy files in a folder by 180 degrees.
"""

import os
import numpy as np
from tqdm import tqdm

# Function to rotate array 180 degrees
def rotate_180(array):
    return np.rot90(array, 2)

# Get the current working directory where the script is being run
folder_path = os.getcwd()

# List all .npy files in the current folder
npy_files = [f for f in os.listdir(folder_path) if f.endswith('.npy')]

# Loop through each .npy file with a progress bar
for filename in tqdm(npy_files, desc="Rotating .npy files", total=len(npy_files)):
    file_path = os.path.join(folder_path, filename)

    # Load the .npy file
    data = np.load(file_path)

    # Rotate by 180 degrees
    rotated_data = rotate_180(data)

    # Save the rotated array, overwriting the original file
    np.save(file_path, rotated_data)
