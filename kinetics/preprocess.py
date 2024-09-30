"""
Module to preprocess videos for kinetics-i3d
"""

import os
import numpy as np
import cv2
from tqdm import tqdm


def preprocess(video) -> tuple[list[cv2.cuda.GpuMat], list[cv2.cuda.GpuMat]]:
    """
    Function to preprocess videos for kinetics-i3d
    """

    video = cv2.VideoCapture(video)

    width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)

    frame_dims = (224, int(height * (224 / width)))

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

    videos = [
        os.path.join("/home/brunomcebola/Desktop/Thesis/videos", video)
        for video in os.listdir("/home/brunomcebola/Desktop/Thesis/videos")
    ]

    for video in tqdm(videos):
        rgb_frames, flow_frames = preprocess(video)

        rgb_frames = [frame.download() for frame in rgb_frames]
        flow_frames = [frame.download() for frame in flow_frames]

        np.save(video.replace(".mp4", "_rgb.npy"), np.array(rgb_frames))
        np.save(video.replace(".mp4", "_flow.npy"), np.array(flow_frames))



if __name__ == "__main__":
    main()
