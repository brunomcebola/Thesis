"""
Module to preprocess the videos.
"""

import os
import pathlib
from moviepy.editor import VideoFileClip
from PIL import Image
import numpy as np
import imageio

INPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), "input")
OUTPUT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), "output")


def sample_frames(input_path: str, output_path):
    """
    Function to sample frames from the video.

    Args:
        video_path (str): Path to the video.
        fps (int): Frames per second to sample.

    Returns:
        list: List of sampled frames.
    """

    def resize(frame, new_size):
        pil_image = Image.fromarray(frame)
        resized_image = pil_image.resize(new_size, Image.BILINEAR)  # type: ignore # pylint: disable=no-member
        return np.array(resized_image)

    def frames_to_numpy_array(clip):
        frames = []
        for frame in clip.iter_frames(fps=clip.fps, dtype="uint8"):
            frames.append(frame)
        return np.array(frames)

    # Remove the output file if it already exists
    if os.path.exists(output_path):
        os.remove(output_path)

    # Load the video file
    video = VideoFileClip(input_path)

    # Resize the video
    if video.size[0] < video.size[1]:
        scale_factor = 256 / video.size[0]
    else:
        scale_factor = 256 / video.size[1]
    new_size = (int(video.size[0] * scale_factor), int(video.size[1] * scale_factor))

    video = video.fl_image(lambda f: resize(f, new_size))

    # Change frame rate
    video = video.set_fps(25)

    # Crop video to central 224x224 region
    video = video.crop(
        x_center=video.size[0] // 2, y_center=video.size[1] // 2, width=224, height=224
    )

    # Convert video to numpy array
    video = frames_to_numpy_array(video)
    video = video[:-1]

    # Rescale pixel values between -1 and 1
    video = video / 256
    video = video * 2 - 1

    # Save video as npy with an extra layer for the batch
    video = np.expand_dims(video, axis=0)
    output_npy_path = os.path.splitext(output_path)[0] + ".npy"
    np.save(output_npy_path, video)
    print(f"Saved video as npy: {output_npy_path}")
    print(f"Shape of video numpy array: {video.shape}")

    # Save video as gif
    video = (video[0] + 1) / 2
    video = video * 256
    video = video.astype(np.uint8)
    output_gif_path = os.path.splitext(output_path)[0] + ".gif"
    frames = [Image.fromarray(frame) for frame in video]
    frames[0].save(
        output_gif_path,
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=40,
        loop=0,
    )
    print(f"Saved video as gif: {output_gif_path}")


def main():
    """
    Main function to preprocess the videos.
    """

    # Get the list of videos
    videos = [f for f in os.listdir(INPUT_DIR) if f.endswith(".mp4")]

    for video in videos:
        print(f"\033[1;34mProcessing video: {video}\033[0m")
        sample_frames(os.path.join(INPUT_DIR, video), os.path.join(OUTPUT_DIR, video))
        print()


if __name__ == "__main__":
    main()
