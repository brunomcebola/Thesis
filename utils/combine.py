"""
Script to combine npy files
"""

import os
import yaml
import numpy as np
import cv2
from tqdm import tqdm

FRAME_RATE = 30

# Load the coombination file
with open("combine.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

for cfg in config:
    cls = cfg["label"]

    for tp in ("color", "depth"):
        output_folder = f"videos/{tp}/{cls}"

        os.makedirs(output_folder, exist_ok=True)

        npy_files = sorted([f for f in os.listdir(cfg["path"]) if f.endswith(".npy") and tp in f])

        tmp_frame = np.load(os.path.join(cfg["path"], npy_files[0]))

        height, width = tmp_frame.shape[:2]  # type: ignore

        created_videos = []

        for i, group in tqdm(
            enumerate(cfg["groups"]),
            total=len(cfg["groups"]),
            desc=f"Creating {cls} {tp} videos",
        ):

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore

            output_file = os.path.join(output_folder, f"{i}.mp4")

            video_writer = cv2.VideoWriter(output_file, fourcc, FRAME_RATE, (width, height))

            for frame in npy_files[group[0] : group[1]]:
                frame = np.load(os.path.join(cfg["path"], frame))

                if tp == "depth":
                    frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)  # type: ignore
                    frame = np.uint8(frame)  # type: ignore
                    frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)  # type: ignore

                video_writer.write(frame.astype(np.uint8))  # type: ignore

            video_writer.release()

            created_videos.append(output_file)

        print("Videos created:")
        for video in created_videos:
            print(f"\t{video}")
        print()
