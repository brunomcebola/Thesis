"""
This module allows the abstract use of the realsense cameras.

Classes:
--------
    - Camera: Class to abstract the use of the realsense cameras
    - StreamType: Enum to represent the type of video stream
    - StreamConfig: Named tuple to represent the configuration of the video stream

Exceptions:
-----------
    - StreamConfigError: Raised when there is an error in the configuration of the video stream.



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
    -----------
        - DEPTH (0): A stream of depth data.
        - COLOR (1): A stream of color data.
        - DEPTH_N_COLOR (2): A stream of both depth and color data.
    """

    DEPTH = 0
    COLOR = 1
    DEPTH_N_COLOR = 2

    def __str__(self) -> str:
        return self.name


class StreamConfig(NamedTuple):
    """
    Named tuple representing the configuration of the stream.

    Attributes:
    -----------
        - width: The width of the camera stream.
        - height: The height of the camera stream.
        - fps: The frames per second of the camera stream.
        - format: The format of the camera stream.
    """

    width: int
    height: int
    fps: int
    format: rs.format

    def __str__(self) -> str:
        return f"{{width={self.width}, height={self.height}, fps={self.fps}, format={self.format}}}"


# TODO: prevent the same camera to be instantiated twice
# TODO: allow to change only one of the configs (depth to depth n color if color config is set)
# TODO: check config must verify if the config is valid for the camera model
class Camera:
    """
    A class to abstract the intecartion with Intel Realsense cameras.

    Class Attributes:
    -----------
        - configs: A dictionary with the default configurations for the different cameras.

    Instance Methods:
    --------
        - change_config(stream_type, depth_config, color_config) -> None:
            Changes the configuration of the camera.
        - start_pipeline() -> None:
            Starts the pipeline object to capture frames.
        - stop_pipeline() -> None:
            Stops the pipeline object.
        - get_frames() -> rs.composite_frame:
            Captures and returns a frame from the camera.
        - get_serial_number() -> str:
            Returns the serial number of the camera.
        - get_name() -> str:
            Returns the name of the camera.

    Class Methods:
    --------------
        - get_available_cameras() -> list[str]:
            Returns a list with the serial numbers of the available cameras
            or an empty list if no cameras are available.
        - is_camera_available(sn) -> bool:
            Checks if camera is available.
        - get_camera_model(sn) -> str:
            Returns the camera model.
        - get_camera_default_config(camera_model) -> dict[str, StreamConfig]:
            Returns the default configuration for the given camera model.

    Examples:
    ----------

    - Get the available cameras::

        >>> Camera.get_available_cameras()
        ['123456789', '987654321']

    - Check if a camera is available::

        >>> Camera.is_camera_available('123456789')
        True

    - Create a camera object::

        camera = Camera(
            name="camera1",
            serial_number="123456789",
            stream_type=StreamType.DEPTH_N_COLOR,
            depth_config=StreamConfig(640, 480, 30, rs.format.z16),
            color_config=StreamConfig(640, 480, 30, rs.format.rgb8),
        )


    - Change the configuration of the camera::

        camera.change_config(
            stream_type=StreamType.DEPTH,
            depth_config=StreamConfig(640, 480, 30, rs.format.z16),
        )
    """

    configs = {
        "D435": {
            "depth": StreamConfig(640, 480, 30, rs.format.z16),
            "color": StreamConfig(640, 480, 30, rs.format.rgb8),
        },
    }

    def __init__(
        self,
        name: str,
        serial_number: str,
        stream_type: StreamType,
        depth_config: StreamConfig | None = None,
        color_config: StreamConfig | None = None,
    ) -> None:
        """
        Initializes a Camera object with the given parameters.

        Args:
        -----
            - name: The name of the camera.
            - serial_number: The serial number of the camera.
            - stream_type: The type of stream to capture.
            - depth_config: The configuration for the depth stream.
            - color_config: The configuration for the color stream.

        Raises:
        -------
            - StreamConfigError: If the configuration is not correct.
        """

        self.__name = name
        self.__serial_number = serial_number

        self.__stream_type = stream_type
        self.__depth_config = depth_config
        self.__color_config = color_config
        self.__check_config()

        self.__pipeline = None

    def __del__(self):
        """
        Stops the pipeline object when the Camera object is deleted.
        """

        if self.__pipeline is not None:
            self.__pipeline.stop()

    def __check_config(self):
        """
        Checks if the given configuration is valid for the given stream type.
        """

        if self.__stream_type == StreamType.DEPTH and self.__depth_config is None:
            raise StreamConfigError("Depth stream config must be set when in depth stream type.")
        elif self.__stream_type == StreamType.COLOR and self.__color_config is None:
            raise StreamConfigError("Color stream config is not set.")
        elif self.__stream_type == StreamType.DEPTH_N_COLOR and (
            self.__depth_config is None or self.__color_config is None
        ):
            raise StreamConfigError("Depth and color streams configs are not set.")

    # Public instace methods

    def change_config(
        self,
        stream_type: StreamType,
        depth_config: StreamConfig | None = None,
        color_config: StreamConfig | None = None,
    ) -> None:
        """
        Changes the stream configuration of the camera.

        Args:
            - stream_type: The type of stream to capture.
            - depth_config: The configuration for the depth stream.
            - color_config: The configuration for the color stream.

        Raises:
            - StreamConfigError: If the configuration is not correct.
        """

        old_stream_type = self.__stream_type
        old_depth_config = self.__depth_config
        old_color_config = self.__color_config

        self.__stream_type = stream_type
        self.__depth_config = depth_config
        self.__color_config = color_config

        try:
            self.__check_config()
        except StreamConfigError:
            self.__stream_type = old_stream_type
            self.__depth_config = old_depth_config
            self.__color_config = old_color_config
            raise

    def start_pipeline(self) -> None:
        """
        Starts the pipeline object to capture frames.
        """

        config = rs.config()

        config.enable_device(self.__serial_number)

        # set config according to stream_type
        if (
            self.__stream_type == StreamType.DEPTH or self.__stream_type == StreamType.DEPTH_N_COLOR
        ) and self.__depth_config is not None:
            config.enable_stream(
                rs.stream.depth,
                self.__depth_config.width,
                self.__depth_config.height,
                self.__depth_config.format,
                self.__depth_config.fps,
            )
        elif (
            self.__stream_type == StreamType.COLOR or self.__stream_type == StreamType.DEPTH_N_COLOR
        ) and self.__color_config is not None:
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
        """

        if self.__pipeline is not None:
            frames = self.__pipeline.wait_for_frames()
            return frames
        else:
            return []

    def get_serial_number(self) -> str:
        """
        Returns the serial number of the camera.
        """

        return self.__serial_number

    def get_name(self) -> str:
        """
        Returns the name of the camera.
        """

        return self.__name

    # Public class methods
    @classmethod
    def get_available_cameras(cls) -> list[str]:
        """
        Returns a list with the serial numbers of the available cameras
        or an empty list if no cameras are available.
        """
        cameras_sn = []

        context = rs.context()
        devices = context.query_devices()

        for device in devices:
            cameras_sn.append(device.get_info(rs.camera_info.serial_number))

        return cameras_sn

    @classmethod
    def is_camera_available(cls, sn: str) -> bool:
        """
        Checks if camera is available.

        Args:
        -----
            - sn: The serial number of the camera.
        """

        context = rs.context()
        devices = context.query_devices()

        for device in devices:
            if device.get_info(rs.camera_info.serial_number) == sn:
                return True

        return False

    @classmethod
    def get_camera_model(cls, sn: str) -> str:
        """
        Returns the camera model.
        """

        context = rs.context()
        devices = context.query_devices()

        for device in devices:
            if device.get_info(rs.camera_info.serial_number) == sn:
                return device.get_info(rs.camera_info.name).split(" ")[-1][:4]

        return ""

    @classmethod
    def get_camera_default_config(cls, camera_model: str) -> dict[str, StreamConfig]:
        """
        Returns the default configuration for the given camera model.

        Args:
        -----
            - camera_model: The model of the camera.
        """

        return cls.configs.get(camera_model, {})
