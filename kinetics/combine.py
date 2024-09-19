"""
Script to combine npy files
"""

import os
import numpy as np
import cv2
from tqdm import tqdm

TYPES = ["color", "depth"]
CLASSES = ["bag_on_floor", "conflict", "swipe_card"]

TYPE = TYPES[1]
CLASS = CLASSES[2]

INPUT_FOLDER = "/home/brunomcebola/Desktop/Thesis/argos/argos_master/data/datasets/RPi_1/raw"
OUTPUT_FOLDER = f"videos/{TYPE}/{CLASS}"
FRAME_RATE = 30

npy_files = sorted([f for f in os.listdir(INPUT_FOLDER) if f.endswith(".npy") and TYPE in f])

first_frame = np.load(os.path.join(INPUT_FOLDER, npy_files[0]))

height, width = first_frame.shape[:2]  # type: ignore

#
#
#

output_videos = [
    npy_files[53:62],
    npy_files[105:117],
]

created_videos = []

for i, frames in tqdm(enumerate(output_videos, start=3), total=len(output_videos)):

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    output_file = os.path.join(OUTPUT_FOLDER, f"{i}.mp4")
    created_videos.append(output_file)

    video_writer = cv2.VideoWriter(output_file, fourcc, FRAME_RATE, (width, height))

    # Loop through each .npy file and write the frames to the video
    for frame in frames:  # Skip the first file since it was already written
        frame = np.load(os.path.join(INPUT_FOLDER, frame))

        if TYPE == "depth":
            frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
            frame = np.uint8(frame)
            frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)

        # Write the frame to the video
        video_writer.write(frame.astype(np.uint8))

    # Release the video writer
    video_writer.release()
print()

print("Videos created:")
for video in created_videos:
    print(f"\t{video}")
