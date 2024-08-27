"""
Module to preprocess videos for kinetics-i3d
"""

import os
import numpy as np
import cv2
from moviepy.editor import VideoFileClip
from PIL import Image
from tqdm import tqdm

INPUT_DIR = os.path.join(os.path.dirname(__file__), "input")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


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
    fps = video.get(cv2.CAP_PROP_FPS)
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Prepare for processing
    max_dim = max(width, height)
    top_pad = (max_dim - height) // 2
    bottom_pad = max_dim - height - top_pad
    left_pad = (max_dim - width) // 2
    right_pad = max_dim - width - left_pad

    frames_gpu = []

    # Read frames and process them
    while True:
        ret, frame = video.read()
        if not ret:
            break

        # Upload frame to GPU
        gpu_frame = cv2.cuda.GpuMat()
        gpu_frame.upload(frame)

        gpu_frame = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2RGB)

        # Apply padding on GPU
        gpu_frame = cv2.cuda.copyMakeBorder(
            gpu_frame,
            top_pad,
            bottom_pad,
            left_pad,
            right_pad,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0),
        )

        # Resize the frame on GPU
        gpu_frame = cv2.cuda.resize(gpu_frame, (224, 224))

        frames_gpu.append(gpu_frame)

    video.release()

    print("Video preprocessed")

    #
    # RGB analysis
    #

    print("Processing RGB frames")

    rgb_frames = []
    for gpu_frame in frames_gpu:
        frame = gpu_frame.download()
        rgb_frames.append(frame)

    rgb_frames = np.array(rgb_frames)

    # Normalize RGB frames between -1 and 1
    rgb_frames = ((rgb_frames / 255.0) * 2) - 1

    # Lose initial frame to match number of flow frames
    rgb_frames = rgb_frames[1:]

    # Add batch dimension
    rgb_frames = np.expand_dims(rgb_frames, axis=0)

    # Save RGB frames
    np.save(os.path.join(OUTPUT_DIR, f"{video_name}_rgb.npy"), rgb_frames)

    # Save as GIF
    # frames_for_gif = (((rgb_frames[0] + 1) / 2) * 255).astype(np.uint8)
    # frames_for_gif = [Image.fromarray(frame) for frame in frames_for_gif]
    # frames_for_gif[0].save(
    #     os.path.join(OUTPUT_DIR, f"{video_name}_rgb.gif"),
    #     format="GIF",
    #     append_images=frames_for_gif[1:],
    #     save_all=True,
    #     duration=int(1000 / fps),
    #     loop=0,
    # )

    print(f"RGB frames processed. Dims: {rgb_frames.shape}")

    #
    # Optical flow analysis
    #

    frames_gpu = np.array([cv2.cuda.cvtColor(frame, cv2.COLOR_RGB2GRAY) for frame in frames_gpu])

    optical_flow = cv2.cuda.FarnebackOpticalFlow.create(5, 0.5, False, 15, 3, 5, 1.2, 0)

    flows = []

    for i in tqdm(range(1, len(frames_gpu)), desc="Generating flow frames"):
        # Calculate optical flow between frames on GPU
        flow = optical_flow.calc(frames_gpu[i - 1], frames_gpu[i], None)  # type: ignore

        # Download the flow frame to CPU
        flow = flow.download()

        # Truncate pixel values to the range [-20, 20]
        flow = np.clip(flow, -20, 20)

        # Rescale pixel values between -1 and 1
        flow = flow / 20.0

        flows.append(flow)

    flows = np.array(flows)

    # Add batch dimension
    flows = np.expand_dims(flows, axis=0)

    # Save optical flow frames
    np.save(os.path.join(OUTPUT_DIR, f"{video_name}_flow.npy"), flows)

    # Save as GIF
    # frames_for_gif = flows[0]
    # frames_for_gif = np.concatenate(
    #     [
    #         frames_for_gif,
    #         np.zeros(
    #             (frames_for_gif.shape[0], frames_for_gif.shape[1], frames_for_gif.shape[2], 1)
    #         ),
    #     ],
    #     axis=-1,
    # )
    # frames_for_gif = frames_for_gif + 0.5
    # frames_for_gif = (
    #     (frames_for_gif - np.min(frames_for_gif))
    #     / (np.max(frames_for_gif) - np.min(frames_for_gif))
    #     * 255
    # ).astype(np.uint8)
    # frames_for_gif = [Image.fromarray(frame) for frame in frames_for_gif]
    # frames_for_gif[0].save(
    #     os.path.join(OUTPUT_DIR, f"{video_name}_flow.gif"),
    #     format="GIF",
    #     append_images=frames_for_gif[1:],
    #     save_all=True,
    #     duration=40,
    #     loop=0,
    # )

    print(f"Flow frames processed. Dims: {flows.shape}")


for file in os.listdir(INPUT_DIR):
    if file.endswith(".mp4"):
        preprocess_video(file)
