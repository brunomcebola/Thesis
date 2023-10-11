import pyrealsense2.pyrealsense2 as rs
from enum import IntEnum
from typing import NamedTuple


class StreamConfigError(ValueError):
    pass


class StreamType(IntEnum):
    DEPTH = 0
    COLOR = 1
    DEPTH_N_COLOR = 2


class StreamConfig(NamedTuple):
    width: int
    height: int
    fps: int
    format: rs.format


class Camera:
    """
    Class to abstract the use of the realsense cameras

    Methods:
        change_config: change the configuration of the camera
        start_pipeline: start the pipeline of the camera
        stop_pipeline: stop the pipeline of the camera
        get_frames: get the frames from the camera

    Raises:
        StreamConfigError: if the configuration is not correct

    """

    __colorizer = rs.colorizer()

    def __init__(
        self,
        serial_number: str,
        stream_type: StreamType,
        depth_config: StreamConfig | None = None,
        color_config: StreamConfig | None = None,
    ) -> None:
        """

        Args:
            serial_number (str): _description_
            stream_type (StreamType): _description_
            depth_config (StreamConfig | None, optional): _description_. Defaults to None.
            color_config (StreamConfig | None, optional): _description_. Defaults to None.
        """
        self.__serial_number = serial_number

        self.__check_config(stream_type, depth_config, color_config)
        self.__stream_type = stream_type
        self.__depth_config = depth_config
        self.__color_config = color_config

        self.__pipeline = None

    def __del__(self):
        if self.__pipeline is not None:
            self.__pipeline.stop()

    @staticmethod
    def __check_config(
        stream_type: StreamType, depth_config: StreamConfig | None = None, color_config: StreamConfig | None = None
    ) -> None:
        if stream_type == StreamType.DEPTH and depth_config is None:
            raise StreamConfigError("Depth stream config is not set.")
        elif stream_type == StreamType.COLOR and color_config is None:
            raise StreamConfigError("Color stream config is not set.")
        elif stream_type == StreamType.DEPTH_N_COLOR and (depth_config is None or color_config is None):
            raise StreamConfigError("Depth and color streams configs are not set.")

    def change_config(
        self, stream_type: StreamType, depth_config: StreamConfig | None = None, color_config: StreamConfig | None = None
    ) -> None:
        self.__check_config(stream_type, depth_config, color_config)
        self.__stream_type = stream_type
        self.__depth_config = depth_config
        self.__color_config = color_config

    def start_pipeline(self) -> None:
        config = rs.config()

        config.enable_device(self.__serial_number)

        # set config according to stream_type
        if self.__stream_type == StreamType.DEPTH:
            config.enable_stream(rs.stream.depth, self.__depth_config.width, self.__depth_config.height, self.__depth_config.format, self.__depth_config.fps)  # type: ignore
        elif self.__stream_type == StreamType.COLOR:
            config.enable_stream(rs.stream.color, self.__color_config.width, self.__color_config.height, self.__color_config.format, self.__color_config.fps)  # type: ignore
        elif self.__stream_type == StreamType.DEPTH_N_COLOR:
            config.enable_stream(rs.stream.depth, self.__depth_config.width, self.__depth_config.height, self.__depth_config.format, self.__depth_config.fps)  # type: ignore
            config.enable_stream(rs.stream.color, self.__color_config.width, self.__color_config.height, self.__color_config.format, self.__color_config.fps)  # type: ignore

        self.__pipeline = rs.pipeline()
        self.__pipeline.start(config)

        print(f"Camera {self.__serial_number} started.")

    def stop_pipeline(self) -> None:
        if self.__pipeline is not None:
            self.__pipeline = self.__pipeline.stop()
            print(f"Camera {self.__serial_number} stopped.")

    def get_frames(self) -> rs.composite_frame:
        if self.__pipeline is not None:
            frames = self.__pipeline.wait_for_frames()
            return frames
        else:
            return []
