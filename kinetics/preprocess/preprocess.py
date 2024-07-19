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
        for frame in clip.iter_frames(fps=clip.fps, dtype='uint8'):
            frames.append(frame)
        return np.array(frames)

    # Remove the output file if it already exists
    if os.path.exists(output_path):
        os.remove(output_path)

    # Load the video file
    video = VideoFileClip(input_path)

    # Get original characteristics
    original_width, original_height = video.size
    orignal_fps = video.fps

    # Resize the video
    if original_width < original_height:
        scale_factor = 256 / original_width
    else:
        scale_factor = 256 / original_height

    video = video.fl_image(
        lambda f: resize(
            f, (int(original_width * scale_factor), int(original_height * scale_factor))
        )
    )
    result_width, result_height = video.size

    # Change frame rate

    video = video.set_fps(25)
    result_fps = video.fps

    # Crop video to central 224x224 region
    video = video.crop(
        x_center=result_width // 2, y_center=result_height // 2, width=224, height=224
    )
    result_width, result_height = video.size

    # Write the resized video to the output file
    # video.write_videofile(output_path)

    print(
        f"\033[1;32mConverted from {original_width}x{original_height}@{orignal_fps} to {result_width}x{result_height}@{result_fps}\033[0m"
    )

    # Convert video to numpy array
    video_npy = frames_to_numpy_array(video)
    print(f"Shape of video numpy array: {video_npy.shape}")

    # Save video_npy as gif
    output_gif_path = os.path.splitext(output_path)[0] + ".gif"
    frames = [Image.fromarray(frame) for frame in video_npy]
    frames[0].save(output_gif_path, format='GIF', append_images=frames[1:], save_all=True, duration=40)
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
