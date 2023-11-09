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
from typing import NamedTuple, Type
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


class StreamFormat(Enum):
    """
    An enumeration of the different formats of the camera stream.

    Attributes:
    -----------
        - Z16: A 16-bit linear depth value.
        - RGB8: Red, Green, Blue channels with 8-bits per channel.
    """

    Z16 = rs.format.z16
    RGB8 = rs.format.rgb8


class StreamConfig(NamedTuple):
    """
    Named tuple representing the format of the stream configuration.

    Attributes:
    -----------
        - format: The format of the camera stream.
        - resolution: The resolution of the camera stream (width x height)
        - fps: The frames per second of the camera stream.
    """

    format: StreamFormat
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
        - IR: A stream of infrared data.
        - DEPTH_N_COLOR: A stream of both depth and color data.
        - DEPTH_N_IR: A stream of both depth and ir data.
        - COLOR_N_IF: A stream of both color and ir data.
        - DEPTH_N_COLOR_N_IR: A stream of depth, color and ir data.


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


# TODO: store StreamType besides the list of base types
class Camera:
    """
    A class to abstract the interaction with Intel Realsense cameras.

    Attributes:
    -----------
        - name: The name of the camera.
        - serial_number: The serial number of the camera.
        - is_running: The status of the camera stream.
        - stream_types: The type of data to stream.
        - stream_configs: The configuration of the streams.

    Class Methods:
    --------------
        - get_available_cameras:
            Returns a list with the serial numbers of the available cameras
            or an empty list if no cameras are available.
        - is_camera_available:
            Checks if camera is available.
        - get_camera_model:
            Returns the camera model.
        - get_default_config:
            Returns the default stream configurations for a given camera model.

    Instance Methods:
    --------
        - change_stream_configs:
            Changes the stream configurations.
        - start:
            Starts the camera stream.
        - stop:
            Stops the camera stream.
        - capture:
            Returns an object representing a frame from the camera.

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
                {StreamType.DEPTH: StreamConfig(StreamFormat.Z16, (640, 480), 30)},
                "My camera",
            )

    - Keep depth stream, but change resolution and framerate::

        >>> camera.change_config(
                {StreamType.DEPTH: StreamConfig(StreamFormat.Z16, (1280, 720), 5)},
            )
    """

    # Class attributes
    _cameras = []

    # Instance attributes
    _name: str
    _serial_number: str
    _is_running: bool
    _stream_type: StreamType
    _stream_types: list[StreamType]
    _stream_configs: dict[StreamType, StreamConfig]

    __pipeline: rs.pipeline
    __config: rs.config
    __device: rs.device

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

        if serial_number in Camera._cameras:
            raise CameraAlreadyExistsError(
                f"Camera with serial number {serial_number} already exists."
            )

        # Initializes attributes dependent on user parameters
        self._serial_number = serial_number
        self._name = name if name else self.serial_number
        self._stream_type = stream_type
        self._stream_configs = stream_configs

        # initializes independent attributes
        self._is_running = False
        self.__pipeline = rs.pipeline()
        self.__config = rs.config()

        # checks if camera is available
        if Camera.is_camera_available(self.serial_number):
            self.__config.enable_device(self.serial_number)
        else:
            raise CameraUnavailableError(f"Camera {self.serial_number} is not available.")

        # save device object
        context = rs.context()
        devices = context.query_devices()

        for device in devices:
            if device.get_info(rs.camera_info.serial_number) == self.serial_number:
                self.__device = device
                break

        # force camera reset
        self.__device.hardware_reset()

        # check if stream configurations are valid and applies them if so
        self.__apply_stream_configs()

        # adds camera sn to the list of cameras
        Camera._cameras.append(self.serial_number)

    @property
    def name(self) -> str:
        """
        Returns the name of the camera.
        """

        return self._name

    @property
    def serial_number(self) -> str:
        """
        Returns the serial number of the camera.
        """

        return self._serial_number

    @property
    def is_running(self) -> bool:
        """
        Returns the status of the camera stream.
        """

        return self._is_running

    @property
    def stream_type(self) -> StreamType:
        """
        Returns the type of data to stream.
        """

        return self._stream_type

    @stream_type.setter
    def stream_type(self, stream_type: StreamType) -> None:
        """
        Sets the type of data to stream.
        """
        self._stream_type = stream_type
        # TODO: missing change value implementation

    @property
    def stream_types(self) -> list[StreamType]:
        """
        Returns a list with the types of data to stream.
        """

        return (
            self._stream_type.value
            if isinstance(self._stream_type.value, list)
            else [self._stream_type]
        )

    @property
    def stream_configs(self) -> dict[StreamType, StreamConfig]:
        """
        Returns the configuration of the streams.
        """

        return self._stream_configs

    @stream_configs.setter
    def stream_configs(self, stream_configs: dict[StreamType, StreamConfig]) -> None:
        """
        Sets the configuration of the streams.
        """
        self._stream_configs = stream_configs
        # TODO: missing change value implementation

    # Instance private methods

    def __apply_stream_configs(self):
        """
        Applies the stream configurations.

        Raises:
        -------
            - StreamConfigError: If the configuration is not correct.
            - PipelineRunningError: If the pipeline is running.
        """

        if not self.is_running:
            # ensures that there are stream configs for all stream types
            for stream_type in self.stream_types:
                if stream_type not in self.stream_configs:
                    raise StreamConfigError(
                        f"Stream config for stream type {stream_type.name} is not set."
                    )

            self.__config.disable_all_streams()

            # checks if all configs are valid
            for stream_type, stream_config in self.stream_configs.items():
                self.__config.enable_stream(
                    stream_type.value,
                    stream_config.resolution[0],
                    stream_config.resolution[1],
                    stream_config.format.value,
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
            for stream_type in self.stream_types:
                self.__config.enable_stream(
                    stream_type.value,
                    self.stream_configs[stream_type].resolution[0],
                    self.stream_configs[stream_type].resolution[1],
                    self.stream_configs[stream_type].format.value,
                    self.stream_configs[stream_type].fps,
                )

        else:
            raise PipelineRunningError()

    def __del__(self):
        """
        Camera destructor.
        """

        if hasattr(self, "is_running") and self.is_running:
            try:
                self.__pipeline.stop()
            except Exception:
                pass

        if hasattr(self, "serial_number"):
            try:
                Camera._cameras.remove(self.serial_number)
            except Exception:
                pass

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

        old_stream_type = self._stream_type
        old_stream_configs = self._stream_configs

        if stream_type is not None:
            self._stream_type = stream_type

        if stream_configs is not None:
            self._stream_configs = stream_configs

        try:
            self.__apply_stream_configs()
        except StreamConfigError:
            self._stream_type = old_stream_type
            self._stream_configs = old_stream_configs
            self.__apply_stream_configs()

            raise
        except PipelineRunningError:
            self._stream_type = old_stream_type
            self._stream_configs = old_stream_configs

            raise

    def start(self) -> bool:
        """
        Starts the camera stream.

        Returns:
        --------
            - True if the pipeline was not running and was started
            - False if the pipelin was already running.
        """

        if self.is_running:
            return False

        self.__pipeline.start(self.__config)
        self._is_running = True

        return True

    def stop(self) -> bool:
        """
        Stops the camera stream.

        Returns:
        --------
            - True if the pipeline was running and was stopped
            - False if the pipeline was already stopped.
        """

        if not self.is_running:
            return False

        self.__pipeline.stop()
        self._is_running = False

        return True

    def capture(self) -> rs.composite_frame:
        """
        Returns an object representing a frame from the camera.

        It blocks the execution until a frame is available, if the camera is running.

        In order to access the frame data itself it is necessary to use a subclass of Frame.
        """

        if self.is_running:
            return self.__pipeline.wait_for_frames()
        else:
            return []

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

    @classmethod
    def get_default_config(cls, model: str) -> dict[StreamType, StreamConfig]:
        """
        Returns the default stream configurations for a given camera model.

        Args:
        -----
            - model: The camera model.
        """

        defaults = {
            "D435": {
                StreamType.DEPTH: StreamConfig(StreamFormat.Z16, (640, 480), 30),
                StreamType.COLOR: StreamConfig(StreamFormat.RGB8, (640, 480), 30),
            },
            "D455": {
                StreamType.DEPTH: StreamConfig(StreamFormat.Z16, (640, 480), 30),
                StreamType.COLOR: StreamConfig(StreamFormat.RGB8, (640, 480), 30),
            },
        }

        return defaults.get(model, {})


# TODO: make it possible to upload from ply file
class Frame(ABC):
    """
    # TODO: missing docstring for Frame
    """

    def __init__(
        self,
        frame: rs.composite_frame,
        location: str,
    ) -> None:
        """
        Frame constructor.

        Args:
        -----
            - frame: The actual frame captured by a camera.
        """

        self.frame = frame
        self.location = location

    # TODO: set return type
    @abstractmethod
    def get_data(self):
        """
        Returns the data to be stored.
        """

    def save(self) -> None:
        """
        Saves the frame.
        """
        ply = rs.save_to_ply(self.location)

        ply.set_option(rs.save_to_ply.option_ply_binary, False)
        ply.set_option(rs.save_to_ply.option_ply_normals, True)

        ply.process(self.frame)

    @classmethod
    def create_instance(
        cls, frame: rs.composite_frame, location: str, stream_type: StreamType | None = None
    ) -> "Frame":
        """
        Creates an instance of the class.
        """

        if stream_type == StreamType.DEPTH:
            return DepthFrame(frame, location)
        elif stream_type == StreamType.COLOR:
            return ColorFrame(frame, location)
        elif stream_type == StreamType.IR:
            return IRFrame(frame, location)
        else:
            return GeneralFrame(rs.composite_frame(), "")


class GeneralFrame(Frame):
    """
    # TODO: missing docstring for GeneralFrame
    """

    def get_data(self):
        return self.frame.get_data()


class DepthFrame(Frame):
    """
    # TODO: missing docstring for DepthFrame
    """

    def get_data(self):
        return self.frame.get_depth_frame().get_data()


class ColorFrame(Frame):
    """
    # TODO: missing docstring for ColorFrame
    """

    def get_data(self):
        return self.frame.get_color_frame().get_data()


class IRFrame(Frame):
    """
    # TODO: missing docstring for IRFrame
    """

    def get_data(self):
        return self.frame.get_infrared_frame().get_data()
