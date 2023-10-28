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

from enum import Enum
from typing import NamedTuple
import pyrealsense2.pyrealsense2 as rs


class StreamConfigError(Exception):
    """
    Exception raised when there is an error in the configuration of the video stream.
    """


class CameraUnavailableError(Exception):
    """
    Exception raised when the camera is not available.
    """


class PipelineRunningError(Exception):
    """
    Exception raised when the pipeline is running.
    """


class CameraAlreadyExistsError(Exception):
    """
    Exception raised when the camera is already instantiated.
    """


class StreamConfig(NamedTuple):
    """
    Named tuple representing the format of the stream.

    Attributes:
    -----------
        - format: The format of the camera stream.
        - resolution: The resolution of the camera stream (width x height)
        - fps: The frames per second of the camera stream.
    """

    format: rs.format
    resolution: tuple[int, int]
    fps: int

    def __str__(self) -> str:
        return f"format={self.format}, resolution={self.resolution[0]} x {self.resolution[1]}, fps={self.fps}"  # pylint: disable=line-too-long


class StreamType(Enum):
    """
    An enumeration of the different types of streams that can be captured by the camera.

    Attributes with '_N_' are composed types, i.e., are lists of base types.

    Attributes:
    -----------
        - DEPTH: A stream of depth data.
        - COLOR: A stream of color data.
        - DEPTH_N_COLOR: A stream of both depth and color data.
    """

    # Base types
    DEPTH = rs.stream.depth
    COLOR = rs.stream.color

    # Composed types
    DEPTH_N_COLOR = None

    def __init__(self, *_, **__):
        if self.name == "DEPTH_N_COLOR":
            self._value_ = [self.DEPTH, self.COLOR]

    def __str__(self) -> str:
        return self.name


# TODO: use cameral name instead of sn to refer to it in errors
class Camera:
    # TODO: update docstring of Camera class
    """
    A class to abstract the intecartion with Intel Realsense cameras.

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

    DEFAULTS = {
        "D435": {
            StreamType.DEPTH: StreamConfig(rs.format.z16, (640, 480), 30),
            StreamType.COLOR: StreamConfig(rs.format.rgb8, (640, 480), 30),
        },
        "D455": {
            StreamType.DEPTH: StreamConfig(rs.format.z16, (640, 480), 30),
            StreamType.COLOR: StreamConfig(rs.format.rgb8, (640, 480), 30),
        },
    }

    cameras = []

    # Type definitions
    __name: str
    __serial_number: str
    __stream_types: list[StreamType]
    __stream_configs: dict[StreamType, StreamConfig]
    __pipeline: rs.pipeline
    __running: bool
    __config: rs.config

    def __init__(
        self,
        name: str,
        serial_number: str,
        stream_type: StreamType,
        stream_configs: dict[StreamType, StreamConfig],
    ) -> None:
        """
        Initializes a Camera object with the given parameters.

        Args:
        -----
            - name: The name of the camera.
            - serial_number: The serial number of the camera.
            - stream_type: The type of data to stream.
            - stream_configs: The configuration of the streams.

        Raises:
        -------
            - StreamConfigError: If the configuration is not correct.
            - CameraUnavailableError: If the camera is not available.
            - CameraAlreadyExistsError: If the camera is already instanciated.
        """

        if serial_number in Camera.cameras:
            raise CameraAlreadyExistsError(f"Camera {serial_number} already instanciated.")

        self.__running = False
        self.__pipeline = rs.pipeline()
        self.__config = rs.config()

        # Initializes attributes dependent on user parameters
        self.__name = name
        self.__serial_number = serial_number
        self.__stream_types = (
            stream_type.value if isinstance(stream_type.value, list) else [stream_type]
        )
        self.__stream_configs = stream_configs

        # initial configurations
        if Camera.is_camera_available(self.__serial_number):
            self.__config.enable_device(self.__serial_number)
        else:
            raise CameraUnavailableError(f"Camera {self.__serial_number} is not available.")

        # check if stream configurations are valid
        self.__apply_stream_configs()

        # adds camera sn to the list of cameras
        Camera.cameras.append(self.__serial_number)

    def __apply_stream_configs(self):
        """
        Applies the stream configurations.

        Raises:
        -------
            - StreamConfigError: If the configuration is not correct.
            - PipelineRunningError: If the pipeline is running.
        """

        if not self.__running:
            # ensures that there are stream configs for all stream types
            for stream_type in self.__stream_types:
                if stream_type not in self.__stream_configs:
                    raise StreamConfigError(
                        f"Stream config for stream type {stream_type.name} is not set."
                    )

            self.__config.disable_all_streams()

            # checks if all configs are valid
            for stream_type, stream_config in self.__stream_configs.items():
                self.__config.enable_stream(
                    stream_type.value,
                    stream_config.resolution[0],
                    stream_config.resolution[1],
                    stream_config.format,
                    stream_config.fps,
                )
                valid = self.__config.can_resolve(self.__pipeline)
                self.__config.disable_stream(stream_type.value)
                if not valid:
                    raise StreamConfigError(
                        f"Stream config for stream type {stream_type.name} is not valid."
                    )
            # enables needed streams
            for stream_type in self.__stream_types:
                self.__config.enable_stream(
                    stream_type.value,
                    self.__stream_configs[stream_type].resolution[0],
                    self.__stream_configs[stream_type].resolution[1],
                    self.__stream_configs[stream_type].format,
                    self.__stream_configs[stream_type].fps,
                )

        else:
            raise PipelineRunningError()

    def __del__(self):
        """
        Stops the pipeline object when the Camera object is deleted if it is running.
        """

        if "__running" in self.__dict__ and self.__running:
            self.__pipeline.stop()

        if "__serial_number" in self.__dict__:
            Camera.cameras.remove(self.__serial_number)

    # Instace public methods

    def change_stream_configs(
        self,
        stream_type: StreamType | None = None,
        stream_configs: dict[StreamType, StreamConfig] | None = None,
    ) -> None:
        """
        # TODO: update docstring of change_config method
        """

        if stream_type is None and stream_configs is None:
            raise StreamConfigError("No stream type or stream configs were specified.")

        old_stream_types = self.__stream_types
        old_stream_formats = self.__stream_configs

        if stream_type is not None:
            self.__stream_types = (
                stream_type.value if isinstance(stream_type.value, list) else [stream_type]
            )

        if stream_configs is not None:
            self.__stream_configs = stream_configs

        try:
            self.__apply_stream_configs()
        except StreamConfigError:
            self.__stream_types = old_stream_types
            self.__stream_configs = old_stream_formats
            self.__apply_stream_configs()

            raise
        except PipelineRunningError:
            self.__stream_types = old_stream_types
            self.__stream_configs = old_stream_formats

            raise

    # def start_pipeline(self) -> None:
    #     """
    #     Starts the pipeline object to capture frames.
    #     """

    #     config = rs.config()

    #     config.enable_device(self.__serial_number)

    #     if (
    #         self.__stream_type == StreamType.DEPTH or self.__stream_type == StreamType.DEPTH_N_COLOR
    #     ) and self.__depth_config is not None:
    #         config.enable_stream(
    #             rs.stream.depth,
    #             self.__depth_config.width,
    #             self.__depth_config.height,
    #             self.__depth_config.format,
    #             self.__depth_config.fps,
    #         )

    #     if (
    #         self.__stream_type == StreamType.COLOR or self.__stream_type == StreamType.DEPTH_N_COLOR
    #     ) and self.__color_config is not None:
    #         config.enable_stream(
    #             rs.stream.color,
    #             self.__color_config.width,
    #             self.__color_config.height,
    #             self.__color_config.format,
    #             self.__color_config.fps,
    #         )

    #     self.__pipeline = rs.pipeline()
    #     self.__pipeline.start(config)

    #     print(f"Camera {self.__serial_number} started.")

    # def stop_pipeline(self) -> None:
    #     """
    #     Stops the pipeline object.
    #     """

    #     if self.__pipeline is not None:
    #         self.__pipeline = self.__pipeline.stop()
    #         print(f"Camera {self.__serial_number} stopped.")

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

    # Class public methods
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
