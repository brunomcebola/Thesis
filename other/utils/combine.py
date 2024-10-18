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
with open(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "combine.yaml"), "r", encoding="utf-8"
) as file:
    config = yaml.safe_load(file)

for cfg in config:
    cls = cfg["label"]
    output_path = cfg["output"]

    for tp in ("color", "depth"):
        output_folder = f"{output_path}/{tp}/{cls}"

        os.makedirs(output_folder, exist_ok=True)

        start_id = (
            np.max([int(i.split(".")[0]) for i in os.listdir(output_folder)]) + 1
            if len(os.listdir(output_folder)) > 0
            else 0
        )


        npy_files = sorted([f for f in os.listdir(cfg["path"]) if f.endswith(".npy") and tp in f])

        tmp_frame = np.load(os.path.join(cfg["path"], npy_files[0]))

        height, width = tmp_frame.shape[:2]  # type: ignore

        created_videos = []

        for i, group in tqdm(
            enumerate(cfg["groups"], start=start_id),
            total=len(cfg["groups"]),
            desc=f"Creating {cls} {tp} videos",
        ):
            try:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore

                output_file = os.path.join(output_folder, f"{i}.mp4")

                video_writer = cv2.VideoWriter(output_file, fourcc, FRAME_RATE, (width, height))

                for frame in npy_files[group[0] - 1 : group[1]]:
                    frame = np.load(os.path.join(cfg["path"], frame))

                    if tp == "depth":
                        frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)  # type: ignore
                        frame = np.uint8(frame)  # type: ignore
                        frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)  # type: ignore

                    video_writer.write(frame.astype(np.uint8))  # type: ignore

                video_writer.release()

                created_videos.append(output_file)
            except Exception as e: # pylint: disable=broad-except
                print(f"Error creating video {i} ({group}): {e}")

        print("Videos created:")
        for video in created_videos:
            print(f"\t{video}")
        print()
