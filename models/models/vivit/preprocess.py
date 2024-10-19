"""
Module to preprocess videos for kinetics-i3d
"""

import os
import numpy as np
import cv2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_INPUT_DIR = os.path.join(BASE_DIR, "../videos")
BASE_OUTPUT_DIR = os.path.join(BASE_DIR, "data")


def preprocess(video) -> dict[str, np.ndarray]:
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

    video.release()

    rgb_frames = np.array([frame.download() for frame in rgb_frames])
    rgb_frames = np.expand_dims(np.array(rgb_frames), axis=0)
    rgb_frames = rgb_frames[:, np.linspace(0, rgb_frames.shape[1] - 1, 32, dtype=int), :, :, :]
    rgb_frames = rgb_frames.transpose(0, 1, 4, 2, 3)

    return {"rgb": rgb_frames}
