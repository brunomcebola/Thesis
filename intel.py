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
    - CameraUnavailableError: Raised when the camera is not available.
    - PipelineRunningError: Raised when the pipeline is running.
    - CameraAlreadyExistsError: Raised when the camera is already instantiated.
"""

from enum import Enum
from typing import NamedTuple
from abc import ABC, abstractmethod

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
    Named tuple representing the format of the stream configuration.

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
    IR = rs.stream.infrared

    # Composed types
    DEPTH_N_COLOR = None
    DEPTH_N_IR = None
    COLOR_N_IR = None
    DEPTH_N_COLOR_N_IR = None

    def __init__(self, *_, **__) -> None:
        if self.name == "DEPTH_N_COLOR":
            self._value_ = [self.DEPTH, self.COLOR]

        elif self.name == "DEPTH_N_IR":
            self._value_ = [self.DEPTH, self.IR]

        elif self.name == "COLOR_N_IR":
            self._value_ = [self.COLOR, self.IR]

        elif self.name == "DEPTH_N_COLOR_N_IR":
            self._value_ = [self.DEPTH, self.COLOR, self.IR]

    def __str__(self) -> str:
        return self.name


class Camera:
    """
    A class to abstract the interaction with Intel Realsense cameras.

    Class Methods:
    --------------
        - get_available_cameras:
            Returns a list with the serial numbers of the available cameras
            or an empty list if no cameras are available.
        - is_camera_available:
            Checks if camera is available.
        - get_camera_model:
            Returns the camera model.

    Instance Methods:
    --------
        - change_stream_configs:
            Changes the stream configurations.
        - start:
            Starts the camera stream.
        - is_streaming:
            Returns the status of the camera stream.
        - stop:
            Stops the camera stream.
        - get_serial_number:
            Returns the serial number of the camera.
        - get_name:
            Returns the name of the camera.

    Examples:
    ----------

    - Get the available cameras::

        >>> Camera.get_available_cameras()
        ['123456789', '987654321']

    - Check if a camera is available::

        >>> Camera.is_camera_available('123456789')
        True

    - Create a camera object::

        >>> camera = Camera(
                "135522077203",
                StreamType.DEPTH,
                {StreamType.DEPTH: StreamConfig(rs.format.z16, (640, 480), 30)},
                "My camera",
            )

    - Keep depth stream, but change resolution and framerate::

        >>> camera.change_config(
                {StreamType.DEPTH: StreamConfig(rs.format.z16, (1280, 720), 5)},
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
    __config: rs.config
    __running: bool

    def __init__(
        self,
        serial_number: str,
        stream_type: StreamType,
        stream_configs: dict[StreamType, StreamConfig],
        name: str | None = None,
    ) -> None:
        """
        Camera constructor.

        Args:
        -----
            - serial_number: The serial number of the camera.
            - stream_type: The type of data to stream.
            - stream_configs: The configuration of the streams.
            - name: The name of the camera. When None it defaults to the serial number.

        Raises:
        -------
            - StreamConfigError: If the configuration is not correct.
            - CameraUnavailableError: If the camera is not available.
            - CameraAlreadyExistsError: If the camera is already instanciated.
        """

        if serial_number in Camera.cameras:
            raise CameraAlreadyExistsError(
                f"Camera with serial number {serial_number} already exists."
            )

        self.__serial_number = serial_number
        self.__name = name if name else serial_number

        # Initializes attributes dependent on user parameters

        self.__stream_types = (
            stream_type.value if isinstance(stream_type.value, list) else [stream_type]
        )
        self.__stream_configs = stream_configs

        # initializes independent attributes
        self.__running = False
        self.__pipeline = rs.pipeline()
        self.__config = rs.config()

        # checks if camera is available
        if Camera.is_camera_available(self.__serial_number):
            self.__config.enable_device(self.__serial_number)
        else:
            raise CameraUnavailableError(f"Camera {self.__serial_number} is not available.")

        # check if stream configurations are valid and applies them if so
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

                if not valid:
                    self.__config.disable_all_streams()  # fail safe

                    raise StreamConfigError(
                        f"Stream config for stream type {stream_type.name} is not valid."
                    )

            self.__config.disable_all_streams()

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
        Camera destructor.
        """

        if hasattr(self, "_Camera__running") and self.__running:
            try:
                self.__pipeline.stop()
            except Exception:
                pass

        if hasattr(self, "_Camera__serial_number"):
            try:
                Camera.cameras.remove(self.__serial_number)
            except Exception:
                pass

        print("del")

    # Instace public methods

    def change_stream_configs(
        self,
        stream_type: StreamType | None = None,
        stream_configs: dict[StreamType, StreamConfig] | None = None,
    ) -> None:
        """
        Changes the stream configurations.

        It is possible to change only the stream type, only the stream configs or both.

        It necessary to guarantee that there is a matching stream config for each stream type,
        either set during instantiation or passed in this method.

        Args:
        -----
            - stream_type: The type of data to stream.
            - stream_configs: The configuration of the streams.

        Raises:
        -------
            - StreamConfigError: If the configuration is not correct.
            - PipelineRunningError: If the pipeline is running.
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

    def start(self) -> bool:
        """
        Starts the camera stream.

        Returns:
        --------
            - True if the pipeline was not running and was started
            - False if the pipelin was already running.
        """

        if self.__running:
            return False

        self.__pipeline.start(self.__config)
        self.__running = True

        return True

    def is_streaming(self) -> bool:
        """
        Returns the status of the camera stream.
        """

        return self.__running

    def stop(self) -> bool:
        """
        Stops the camera stream.

        Returns:
        --------
            - True if the pipeline was running and was stopped
            - False if the pipeline was already stopped.
        """

        if not self.__running:
            return False

        self.__pipeline.stop()
        self.__running = False

        return True

    def get_frames(self) -> rs.composite_frame:
        """
        Returns an object representing a frame from the camera.

        In order to access the frame data itself it is necessary to use a subclass of Frame.
        """

        if self.__running:
            return self.__pipeline.wait_for_frames()
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

        Args:
        -----
            - sn: The serial number of the camera.
        """

        context = rs.context()
        devices = context.query_devices()

        for device in devices:
            if device.get_info(rs.camera_info.serial_number) == sn:
                return device.get_info(rs.camera_info.name).split(" ")[-1][:4]

        return ""


class Frame(ABC):
    """
    # TODO: missing docstring for Frame
    """

    def __init__(
        self,
        frame: rs.composite_frame,
    ) -> None:
        """
        Frame constructor.

        Args:
        -----
            - stream_type: The type of data to stream.
            - frame: The actual frame captured by a camera.
        """

        self.frame = frame

    @abstractmethod
    def save(self):
        """
        Saves the frame to a ply file
        """

    @classmethod
    def create_instance(cls):
        # TODO: implement
        pass
