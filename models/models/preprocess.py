"""
Script to preprocess the videos
"""

import os
import shutil
import argparse
import numpy as np

from tqdm import tqdm
from typing import Callable

from . import kinetics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


MODELS_MAP: dict[str, Callable] = {
    "kinetics": kinetics.preprocess,
}


def main():
    """
    Main function to preprocess videos
    """

    parser = argparse.ArgumentParser(description="Preprocess videos")
    parser.add_argument(
        "--model",
        type=str,
        choices=[*MODELS_MAP.keys()],
        required=True,
        help="Model to train",
    )
    parser.add_argument(
        "--data",
        type=str,
        choices=["color", "depth"],
        default="color",
        help="Data type to preprocess",
    )
    args = parser.parse_args()

    input_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "videos", args.data))
    output_dir = os.path.abspath(os.path.join(BASE_DIR, args.model, "data", args.data))

    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Clear output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    for cls in os.listdir(input_dir):
        if os.path.isdir(os.path.join(input_dir, cls)):
            print(f"Processing class: {cls}")
            os.makedirs(os.path.join(output_dir, cls), exist_ok=True)

            for video in tqdm(os.listdir(os.path.join(input_dir, cls))):
                video_id = video.split(".")[0]
                video_in = os.path.join(input_dir, cls, video)

                frames = MODELS_MAP[args.model](video_in)

                video_out = os.path.join(output_dir, cls, video_id)
                os.makedirs(video_out, exist_ok=True)

                for frame_name, frame in frames.items():
                    np.save(os.path.join(video_out, f"{frame_name}.npy"), frame)

            print()


if __name__ == "__main__":
    main()
