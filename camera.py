"""
This module provides a Camera class to abstract the use of the realsense cameras.

Classes:
    Camera: Class to abstract the use of the realsense cameras

Exceptions:
    StreamConfigError: Raised if the configuration is not correct

Enums:
    StreamType: Enum to represent the type of stream

Named Tuples:
    StreamConfig: Named tuple to represent the configuration of a stream

Methods:
    change_config: Change the configuration of the camera
    start_pipeline: Start the pipeline of the camera
    stop_pipeline: Stop the pipeline of the camera
    get_frames: Get the frames from the camera
"""

from enum import IntEnum
from typing import NamedTuple

import pyrealsense2.pyrealsense2 as rs


class StreamConfigError(ValueError):
    """
    Exception raised when there is an error in the configuration of the video stream.
    """


class StreamType(IntEnum):
    """
    An enumeration of the different types of streams that can be captured by the camera.

    Attributes:
        DEPTH (0): A stream of depth data.
        COLOR (1): A stream of color data.
        DEPTH_N_COLOR (2): A stream of both depth and color data.
    """

    DEPTH = 0
    COLOR = 1
    DEPTH_N_COLOR = 2


class StreamConfig(NamedTuple):
    """
    A named tuple representing the configuration of a camera stream.

    Attributes:
    -----------
    width : int
        The width of the camera stream.
    height : int
        The height of the camera stream.
    fps : int
        The frames per second of the camera stream.
    format : rs.format
        The format of the camera stream.
    """

    width: int
    height: int
    fps: int
    format: rs.format


class Camera:
    """
    A class representing a camera device.

    Attributes:
        __serial_number (str): The serial number of the camera.
        __stream_type (StreamType): The type of stream to capture.
        __depth_config (StreamConfig | None): The configuration for the depth stream.
        __color_config (StreamConfig | None): The configuration for the color stream.
        __pipeline (rs.pipeline | None): The pipeline object used to capture frames.

    Methods:
        __init__(self, serial_number: str, stream_type: StreamType, depth_config: StreamConfig | None = None, color_config: StreamConfig | None = None) -> None:
            Initializes a Camera object with the given parameters.
        __del__(self):
            Stops the pipeline object when the Camera object is deleted.
        set_defaults(self):
            Sets the default configuration for the camera.
        __check_config(stream_type: StreamType, depth_config: StreamConfig | None = None, color_config: StreamConfig | None = None) -> None:
            Checks if the given configuration is valid for the given stream type.
        change_config(self, stream_type: StreamType, depth_config: StreamConfig | None = None, color_config: StreamConfig | None = None) -> None:
            Changes the configuration of the camera.
        start_pipeline(self) -> None:
            Starts the pipeline object to capture frames.
        stop_pipeline(self) -> None:
            Stops the pipeline object.
        get_frames(self) -> rs.composite_frame:
            Captures and returns a frame from the camera.
    """

    def __init__(
        self,
        serial_number: str,
        stream_type: StreamType,
        depth_config: StreamConfig | None = None,
        color_config: StreamConfig | None = None,
    ) -> None:
        """
        Initializes a Camera object with the given parameters.

        Args:
            serial_number (str): The serial number of the camera.
            stream_type (StreamType): The type of stream to capture.
            depth_config (StreamConfig | None, optional): The configuration for the depth stream. Defaults to None.
            color_config (StreamConfig | None, optional): The configuration for the color stream. Defaults to None.
        """

        self.__serial_number = serial_number

        self.__stream_type = stream_type
        self.__depth_config = depth_config
        self.__color_config = color_config
        self.__check_config()

        self.__pipeline = None

        self.set_defaults()

    def __del__(self):
        """
        Stops the pipeline object when the Camera object is deleted.
        """
        if self.__pipeline is not None:
            self.__pipeline.stop()

    def set_defaults(self):
        """
        Sets the default configuration for the camera.
        """
        pass

    @staticmethod
    def __check_config(
        stream_type: StreamType,
        depth_config: StreamConfig | None = None,
        color_config: StreamConfig | None = None,
    ) -> None:
        """
        Checks if the given configuration is valid for the given stream type.

        Args:
            stream_type (StreamType): The type of stream to capture.
            depth_config (StreamConfig | None, optional): The configuration for the depth stream. Defaults to None.
            color_config (StreamConfig | None, optional): The configuration for the color stream. Defaults to None.
        """
        if stream_type == StreamType.DEPTH and depth_config is None:
            raise StreamConfigError("Depth stream config must be set when in depth stream type.")
        elif stream_type == StreamType.COLOR and color_config is None:
            raise StreamConfigError("Color stream config is not set.")
        elif stream_type == StreamType.DEPTH_N_COLOR and (
            depth_config is None or color_config is None
        ):
            raise StreamConfigError("Depth and color streams configs are not set.")

    def change_config(
        self,
        stream_type: StreamType,
        depth_config: StreamConfig | None = None,
        color_config: StreamConfig | None = None,
    ) -> None:
        """
        Changes the configuration of the camera.

        Args:
            stream_type (StreamType): The type of stream to capture.
            depth_config (StreamConfig | None, optional): The configuration for the depth stream. Defaults to None.
            color_config (StreamConfig | None, optional): The configuration for the color stream. Defaults to None.
        """
        self.__check_config(stream_type, depth_config, color_config)
        self.__stream_type = stream_type
        self.__depth_config = depth_config
        self.__color_config = color_config

    def start_pipeline(self) -> None:
        """
        Starts the pipeline object to capture frames.
        """
        config = rs.config()

        config.enable_device(self.__serial_number)

        # set config according to stream_type
        if self.__stream_type == StreamType.DEPTH or self.__stream_type == StreamType.DEPTH_N_COLOR:
            config.enable_stream(
                rs.stream.depth,
                self.__depth_config.width,
                self.__depth_config.height,
                self.__depth_config.format,
                self.__depth_config.fps,
            )
        elif (
            self.__stream_type == StreamType.COLOR or self.__stream_type == StreamType.DEPTH_N_COLOR
        ):
            config.enable_stream(
                rs.stream.color,
                self.__color_config.width,
                self.__color_config.height,
                self.__color_config.format,
                self.__color_config.fps,
            )

        self.__pipeline = rs.pipeline()
        self.__pipeline.start(config)

        print(f"Camera {self.__serial_number} started.")

    def stop_pipeline(self) -> None:
        """
        Stops the pipeline object.
        """
        if self.__pipeline is not None:
            self.__pipeline = self.__pipeline.stop()
            print(f"Camera {self.__serial_number} stopped.")

    def get_frames(self) -> rs.composite_frame:
        """
        Captures and returns a frame from the camera.

        Returns:
            rs.composite_frame: The captured frame.
        """
        if self.__pipeline is not None:
            frames = self.__pipeline.wait_for_frames()
            return frames
        else:
            return []
