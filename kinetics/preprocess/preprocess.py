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

    video: VideoFileClip = VideoFileClip(os.path.join(INPUT_DIR, video_name))

    # Sample frames at 25 FPS
    video = video.set_fps(25)

    frames = []
    w, h = video.size
    for frame in video.iter_frames():
        if h < w:
            new_h = 256
            new_w = int(w * (256 / h))
        else:
            new_w = 256
            new_h = int(h * (256 / w))
        frames.append(cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR))
    frames = np.array(frames)

    process_rgb(frames, os.path.splitext(video_name)[0])
    process_flow(frames, os.path.splitext(video_name)[0])


def process_rgb(frames: np.ndarray, video_name: str) -> None:
    """
    Preprocess RGB frames

    Args:
        frames (np.ndarray): Array of frames
        video_name (str): Name of the video
    """

    # Normalize pixel values between -1 and 1 «
    frames = ((frames / frames.max()) * 2) - 1

    # Crop the center 224x224
    h, w = frames.shape[1:3]
    top = (h - 224) // 2
    left = (w - 224) // 2
    frames = frames[:, top : top + 224, left : left + 224, :]

    # Lose initial frame to match flow
    frames = frames[1:]

    # Add batch dimension
    frames = np.expand_dims(frames, axis=0)

    # Save RGB frames
    np.save(os.path.join(OUTPUT_DIR, f"{video_name}_rgb.npy"), frames)

    # Save as gif
    frames_for_gif = (((frames[0] + 1) / 2) * 256).astype(np.uint8)
    frames_for_gif = [Image.fromarray(frame) for frame in frames_for_gif]
    frames_for_gif[0].save(
        os.path.join(OUTPUT_DIR, f"{video_name}_rgb.gif"),
        format="GIF",
        append_images=frames_for_gif[1:],
        save_all=True,
        duration=40,
        loop=0,
    )

    print(f"RGB frames saved as {video_name}_rgb.npy and {video_name}_rgb.gif")
    print(f"Shape of RGB frames: {frames.shape}")


def process_flow(frames: np.ndarray, video_name: str) -> None:
    """
    Preprocess optical flow frames

    Args:
        frames (np.ndarray): Array of frames
        video_name (str): Name of the video
    """

    frames = np.array([cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) for frame in frames])

    tvl1 = cv2.optflow.createOptFlow_DualTVL1()

    flows = []

    for i in tqdm(range(1, len(frames)), desc="Generating flow frames"):
        # Apply TV-L1 optical flow algorithm
        flow = tvl1.calc(frames[i - 1], frames[i], None)  # type: ignore

        # Truncate pixel values to the range [-20, 20]
        flow = np.clip(flow, -20, 20)

        # Rescale pixel values between -1 and 1
        flow = flow / 20.0

        flows.append(flow)

    flows = np.array(flows)

    # Crop the center 224x224
    h, w = flows.shape[1:3]
    top = (h - 224) // 2
    left = (w - 224) // 2
    flows = flows[:, top : top + 224, left : left + 224, :]

    # Add batch dimension
    flows = np.expand_dims(flows, axis=0)

    # Save optical flow frames
    np.save(os.path.join(OUTPUT_DIR, f"{video_name}_flow.npy"), flows)

    # Save as gif
    frames_for_gif = flows[0]
    frames_for_gif = np.concatenate(
        [
            frames_for_gif,
            np.zeros(
                (frames_for_gif.shape[0], frames_for_gif.shape[1], frames_for_gif.shape[2], 1)
            ),
        ],
        axis=-1,
    )
    frames_for_gif = frames_for_gif + 0.5
    frames_for_gif = (
        (frames_for_gif - np.min(frames_for_gif))
        / (np.max(frames_for_gif) - np.min(frames_for_gif))
        * 255
    ).astype(np.uint8)
    frames_for_gif = [Image.fromarray(frame) for frame in frames_for_gif]
    frames_for_gif[0].save(
        os.path.join(OUTPUT_DIR, f"{video_name}_flow.gif"),
        format="GIF",
        append_images=frames_for_gif[1:],
        save_all=True,
        duration=40,
        loop=0,
    )
    print(f"Flow frames saved as {video_name}_flow.npy and {video_name}_flow.gif")
    print(f"Shape of Flow frames: {flows.shape}")

for file in os.listdir(INPUT_DIR):
    if file.endswith(".mp4"):
        preprocess_video(file)
