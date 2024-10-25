"""
Script to preprocess the videos
"""

# pylint: disable=wrong-import-position

import os
import shutil
import argparse
import numpy as np

from tqdm import tqdm
from typing import Callable

from . import kinetics
from . import vivit
from . import hmm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


MODELS_MAP: dict[str, Callable] = {
    "kinetics": kinetics.preprocess,
    "vivit": vivit.preprocess,
    "hmm": hmm.preprocess,
}


def main():
    """
    Main function to preprocess videos
    """

    parser = argparse.ArgumentParser(description="Preprocess videos")
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        choices=[*MODELS_MAP.keys()],
        required=True,
        help="Model to train",
    )
    args = parser.parse_args()

    input_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "videos"))
    output_dir = os.path.abspath(os.path.join(BASE_DIR, args.model, "data"))

    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Clear output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    for dirpath, _, filenames in os.walk(input_dir):
        if filenames:
            print(f"Processing: {dirpath}")
            print(f"Output: {dirpath.replace(input_dir, output_dir)}")
            os.makedirs(dirpath.replace(input_dir, output_dir), exist_ok=True)

            for video in tqdm(filenames):
                video_id = video.split(".")[0]
                video_in = os.path.join(dirpath, video)

                frames = MODELS_MAP[args.model](video_in)

                video_out = os.path.join(
                    dirpath.replace(input_dir, output_dir), video_id
                )
                os.makedirs(video_out, exist_ok=True)

                for frame_name, frame in frames.items():
                    np.save(os.path.join(video_out, f"{frame_name}.npy"), frame)

            print()

if __name__ == "__main__":
    main()
