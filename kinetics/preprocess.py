"""
Module to preprocess videos for kinetics-i3d
"""

import os
import numpy as np
import cv2
from tqdm import tqdm

INPUT_DIR = os.path.join(os.path.dirname(__file__), "videos/depth/swipe_card")
BASE_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "npy/depth/swipe_card")


def preprocess_video(video_name: str) -> None:
    """
    Preprocess a video for kinetics-i3d

    Args:
        video_name (str): Name of the video
    """

    #
    # Preprocess video
    #

    print(f"Preprocessing video: {video_name}")

    video = cv2.VideoCapture(os.path.join(INPUT_DIR, video_name))

    # Read video properties
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Calculate new dims
    if height < width:
        width = int(width * (224 / height))
        height = 224
    else:
        height = int(height * (224 / width))
        width = 224

    # Read frames and process them
    rgb_frames = []
    flow_frames = []
    while True:
        ret, frame = video.read()
        if not ret:
            break

        # Create GPU mats
        rgb_frame = cv2.cuda.GpuMat()
        flow_frame = cv2.cuda.GpuMat()

        # Populate GPU mats
        rgb_frame.upload(frame)
        flow_frame.upload(frame)

        # Convert colors
        rgb_frame = cv2.cuda.cvtColor(rgb_frame, cv2.COLOR_BGR2RGB)
        flow_frame = cv2.cuda.cvtColor(flow_frame, cv2.COLOR_RGB2GRAY)

        # Resize the frame
        rgb_frame = cv2.cuda.resize(rgb_frame, (width, height), interpolation=cv2.INTER_LINEAR)
        flow_frame = cv2.cuda.resize(flow_frame, (width, height), interpolation=cv2.INTER_LINEAR)

        # Append to list
        rgb_frames.append(rgb_frame)
        flow_frames.append(flow_frame)

    video.release()

    print("Video preprocessed")

    #
    # RGB analysis
    #

    print("Processing RGB frames")

    rgb_frames = np.array([frame.download() for frame in rgb_frames])

    # Normalize RGB frames between -1 and 1
    rgb_frames = rgb_frames / 255

    # Lose initial frame to match number of flow frames
    rgb_frames = rgb_frames[1:]

    # Add batch dimension
    rgb_frames = np.expand_dims(rgb_frames, axis=0)

    print(f"RGB frames processed. Dims: {rgb_frames.shape}")

    #
    # Optical flow analysis
    #

    print("Processing flow frames")

    optical_flow = cv2.cuda.OpticalFlowDual_TVL1.create(
        tau=0.25,
        nscales=5,
        warps=5,
        epsilon=0.01,
        iterations=10,
        scaleStep=0.8,
        gamma=0.0,
        useInitialFlow=False,
    )

    tmp = []
    for i in tqdm(range(1, len(flow_frames)), desc="Generating flow frames"):
        # Calculate optical flow between frames on GPU
        flow = optical_flow.calc(flow_frames[i - 1], flow_frames[i], None)  # type: ignore

        tmp.append(flow)

    flow_frames = np.array([frame.download() for frame in tmp])

    # Truncate flow frames between -20 and 20
    flow_frames = np.clip(flow_frames, -20, 20)

    # Normalize flow frames between -1 and 1
    flow_frames = flow_frames / 20

    # Add batch dimension
    flow_frames = np.expand_dims(flow_frames, axis=0)

    print(f"Flow frames processed. Dims: {flow_frames.shape}")

    # Save npy files
    name = video_name.split(".")[0]
    output_dir = os.path.join(BASE_OUTPUT_DIR, name)
    os.makedirs(output_dir, exist_ok=True)

    np.save(os.path.join(output_dir, f"{name}_rgb.npy"), rgb_frames)
    np.save(os.path.join(output_dir, f"{name}_flow.npy"), flow_frames)


for file in os.listdir(INPUT_DIR):
    if file.endswith(".mp4"):
        preprocess_video(file)
        print()
