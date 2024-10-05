"""
Module to preprocess videos for kinetics-i3d
"""

import os
import shutil
import argparse
import numpy as np
import cv2
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_INPUT_DIR = os.path.join(BASE_DIR, "videos")
BASE_OUTPUT_DIR = os.path.join(BASE_DIR, "data")


def preprocess(video) -> tuple[list[cv2.cuda.GpuMat], list[cv2.cuda.GpuMat]]:
    """
    Function to preprocess videos for kinetics-i3d
    """

    video = cv2.VideoCapture(video)

    width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)

    # Calculate new dims
    if height < width:
        width = int(width * (224 / height))
        height = 224
    else:
        height = int(height * (224 / width))
        width = 224

    frame_dims = (width, height)

    # variables for rgb analysis
    rgb_frames = []
    rgb_divider = cv2.cuda.GpuMat(np.full((frame_dims[1], frame_dims[0], 3), 255, dtype=np.uint8))

    # variables for flow analysis
    flow_frames = []
    grey_frames = []
    flow_engine = cv2.cuda.OpticalFlowDual_TVL1.create(
        tau=0.25,
        nscales=5,
        warps=5,
        epsilon=0.01,
        iterations=10,
        scaleStep=0.8,
        gamma=0.0,
        useInitialFlow=False,
    )
    flow_min = cv2.cuda.GpuMat(np.full((frame_dims[1], frame_dims[0], 2), -20, dtype=np.float32))
    flow_max = cv2.cuda.GpuMat(np.full((frame_dims[1], frame_dims[0], 2), 20, dtype=np.float32))

    # Process video
    while True:
        ret, frame = video.read()
        if not ret:
            break

        # Process rgb

        rgb_frame = cv2.cuda.GpuMat(frame)
        rgb_frame = cv2.cuda.resize(rgb_frame, frame_dims, interpolation=cv2.INTER_LINEAR)
        rgb_frame = cv2.cuda.cvtColor(rgb_frame, cv2.COLOR_BGR2RGB)
        rgb_frame = cv2.cuda.divide(rgb_frame, rgb_divider)
        rgb_frames.append(rgb_frame)

        # Process flow

        grey_frame = cv2.cuda.GpuMat(frame)
        grey_frame = cv2.cuda.resize(grey_frame, frame_dims, interpolation=cv2.INTER_LINEAR)
        grey_frame = cv2.cuda.cvtColor(grey_frame, cv2.COLOR_RGB2GRAY)
        grey_frames.append(grey_frame)

        if len(grey_frames) >= 2:
            curr_frame = grey_frames[-1]
            prev_frame = grey_frames[-2]

            grey_frames = grey_frames[1:]

            flow_frame = flow_engine.calc(prev_frame, curr_frame, None)  # type: ignore

            flow_frame = cv2.cuda.max(flow_frame, flow_min)
            flow_frame = cv2.cuda.min(flow_frame, flow_max)
            flow_frame = cv2.cuda.divide(flow_frame, flow_max)

            flow_frames.append(flow_frame)

    video.release()

    return rgb_frames[:-1], flow_frames


def main():
    """
    Main function to preprocess videos
    """

    parser = argparse.ArgumentParser(description="Preprocess videos for kinetics-i3d")
    parser.add_argument(
        "--data",
        type=str,
        choices=["color", "depth"],
        default="color",
        help="Data type to preprocess",
    )
    args = parser.parse_args()

    input_dir = os.path.join(BASE_INPUT_DIR, args.data)
    output_dir = os.path.join(BASE_OUTPUT_DIR, args.data)

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

                rgb_frames, flow_frames = preprocess(video_in)

                rgb_frames = [frame.download() for frame in rgb_frames]
                flow_frames = [frame.download() for frame in flow_frames]

                rgb_frames = np.expand_dims(np.array(rgb_frames), axis=0)
                flow_frames = np.expand_dims(np.array(flow_frames), axis=0)

                video_out = os.path.join(output_dir, cls, video_id)
                os.makedirs(video_out, exist_ok=True)

                np.save(os.path.join(video_out, "rgb.npy"), np.array(rgb_frames))
                np.save(os.path.join(video_out, "flow.npy"), np.array(flow_frames))

            print()


if __name__ == "__main__":
    main()
