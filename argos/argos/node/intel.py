"""
This module allows the abstract use of the realsense cameras.

Classes:
--------
    - RealSenseCamera: Class to abstract the use of the realsense cameras
    - StreamType: Enum to represent the type of video stream
    - StreamConfig: Named tuple to represent the configuration of the video stream

Exceptions:
-----------
    - StreamConfigError: Raised when there is an error in the configuration of the video stream.
    - CameraUnavailableError: Raised when the camera is not available.
    - PipelineRunningError: Raised when the pipeline is running.
    - CameraAlreadyExistsError: Raised when the camera is already instantiated.
"""

# pylint: disable=pointless-string-statement

from __future__ import annotations

import os
import queue
import threading
from enum import Enum
from typing import NamedTuple, Callable
import numpy as np
import pyrealsense2 as rs

# Exceptions
"""
███████╗██╗  ██╗ ██████╗███████╗██████╗ ████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
█████╗   ╚███╔╝ ██║     █████╗  ██████╔╝   ██║   ██║██║   ██║██╔██╗ ██║███████╗
██╔══╝   ██╔██╗ ██║     ██╔══╝  ██╔═══╝    ██║   ██║██║   ██║██║╚██╗██║╚════██║
███████╗██╔╝ ██╗╚██████╗███████╗██║        ██║   ██║╚██████╔╝██║ ╚████║███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
"""


class StreamConfigError(Exception):
    """
    Exception raised when there is an error in the configuration of the video stream.
    """


class AlignmentError(Exception):
    """
    Exception raised when there is an error in the alignment of the video stream.
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


# Main content
"""
███╗   ███╗ █████╗ ██╗███╗   ██╗     ██████╗ ██████╗ ███╗   ██╗████████╗███████╗███╗   ██╗████████╗
████╗ ████║██╔══██╗██║████╗  ██║    ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║╚══██╔══╝
██╔████╔██║███████║██║██╔██╗ ██║    ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║   ██║
██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║   ██║
██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗██║ ╚████║   ██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝   ╚═╝
"""


class StreamType(Enum):
    """
    An enumeration of the different types of streams that can be captured by the camera.

    Attributes:
    -----------
        - ANY: Any stream type.
        - ACCEL: Accelerometer data.
        - COLOR: Color data.
        - CONFIDENCE: Confidence data.
        - DEPTH: Depth data.
        - FISHEYE: Fisheye data.
        - GPIO: GPIO data.
        - GYRO: Gyroscope data.
        - INFRARED: Infrared data.
        - POSE: Pose data.

    """

    ANY = rs.stream.any  # type: ignore
    ACCEL = rs.stream.accel  # type: ignore
    COLOR = rs.stream.color  # type: ignore
    CONFIDENCE = rs.stream.confidence  # type: ignore
    DEPTH = rs.stream.depth  # type: ignore
    FISHEYE = rs.stream.fisheye  # type: ignore
    GPIO = rs.stream.gpio  # type: ignore
    GYRO = rs.stream.gyro  # type: ignore
    INFRARED = rs.stream.infrared  # type: ignore
    POSE = rs.stream.pose  # type: ignore

    def __str__(self) -> str:
        return self.name


class StreamFormat(Enum):
    """
    An enumeration of the different formats of the camera stream.

    Attributes:
    -----------
        - ANY: Any format.
        - BGR8: 8-bit per pixel, BGRA color format.
        - BGRA8: 8-bit per pixel, BGRA color format.
        - DISPARITY16: 16-bit per pixel, disparity format.
        - DISPARITY32: 32-bit per pixel, disparity format.
        - DISTANCE: 32-bit per pixel, distance in meters format.
        - GPIO_RAW: 8-bit per pixel, raw GPIO data format.
        - INVI: 8-bit per pixel, infrared format.
        - INZI: 16-bit per pixel, infrared format.
        - MJPEG: 8-bit per pixel, compressed format.
        - MOTION_RAW: 32-bit per pixel, motion data format.
        - MOTION_XYZ32F: 32-bit per pixel, motion data format.
        - RAW10: 10-bit per pixel, raw format.
        - RAW16: 16-bit per pixel, raw format.
        - RAW8: 8-bit per pixel, raw format.
        - RGB8: 8-bit per pixel, RGB color format.
        - RGBA8: 8-bit per pixel, RGBA color format.
        - SIX_DOF: 32-bit per pixel, 6 degrees of freedom format.
        - UYVY: 8-bit per pixel, compressed format.
        - W10: 10-bit per pixel, compressed format.
        - XYZ32F: 32-bit per pixel, XYZ format.
        - Y10BPACK: 10-bit per pixel, compressed format.
        - Y12I: 12-bit per pixel, infrared format.
        - Y16: 16-bit per pixel, infrared format.
        - Y8: 8-bit per pixel, infrared format.
        - Y8I: 8-bit per pixel, infrared format.
        - YUYV: 8-bit per pixel, compressed format.
        - Z16: 16-bit per pixel, depth format.
        - Z16H: 16-bit per pixel, depth format.
    """

    ANY = rs.format.any  # type: ignore
    BGR8 = rs.format.bgr8  # type: ignore
    BGRA8 = rs.format.bgra8  # type: ignore
    DISPARITY16 = rs.format.disparity16  # type: ignore
    DISPARITY32 = rs.format.disparity32  # type: ignore
    DISTANCE = rs.format.distance  # type: ignore
    GPIO_RAW = rs.format.gpio_raw  # type: ignore
    INVI = rs.format.invi  # type: ignore
    INZI = rs.format.inzi  # type: ignore
    MJPEG = rs.format.mjpeg  # type: ignore
    MOTION_RAW = rs.format.motion_raw  # type: ignore
    MOTION_XYZ32F = rs.format.motion_xyz32f  # type: ignore
    RAW10 = rs.format.raw10  # type: ignore
    RAW16 = rs.format.raw16  # type: ignore
    RAW8 = rs.format.raw8  # type: ignore
    RGB8 = rs.format.rgb8  # type: ignore
    RGBA8 = rs.format.rgba8  # type: ignore
    SIX_DOF = rs.format.six_dof  # type: ignore
    UYVY = rs.format.uyvy  # type: ignore
    W10 = rs.format.w10  # type: ignore
    XYZ32F = rs.format.xyz32f  # type: ignore
    Y10BPACK = rs.format.y10bpack  # type: ignore
    Y12I = rs.format.y12i  # type: ignore
    Y16 = rs.format.y16  # type: ignore
    Y8 = rs.format.y8  # type: ignore
    Y8I = rs.format.y8i  # type: ignore
    YUYV = rs.format.yuyv  # type: ignore
    Z16 = rs.format.z16  # type: ignore
    Z16H = rs.format.z16h  # type: ignore

    def __str__(self) -> str:
        return self.name


class StreamResolution(Enum):
    """
    An enumeration of the different resolutions of the camera stream.

    Attributes:
    ------------
        - X1920_Y1080: 1920 x 1080
        - X1280_Y720: 1280 x 720
        - X960_Y540: 960 x 540
        - X848_Y480: 848 x 480
        - X640_Y480: 640 x 480
        - X640_Y360: 640 x 360
        - X480_Y270: 480 x 270
        - X424_Y240: 424 x 240
        - X320_Y240: 320 x 240
        - X320_Y180: 320 x 180
    """

    X1920_Y1080 = (1920, 1080)
    X1280_Y720 = (1280, 720)
    X960_Y540 = (960, 540)
    X848_Y480 = (848, 480)
    X640_Y480 = (640, 480)
    X640_Y360 = (640, 360)
    X480_Y270 = (480, 270)
    X424_Y240 = (424, 240)
    X320_Y240 = (320, 240)
    X320_Y180 = (320, 180)

    def __str__(self) -> str:
        return self.name


class StreamFPS(Enum):
    """
    An enumeration of the different frame rates of the camera stream.

    Attributes:
    ------------
        - FPS_6: 6 frames per second
        - FPS_15: 15 frames per second
        - FPS_30: 30 frames per second
        - FPS_60: 60 frames per second
        - FPS_90: 90 frames per second
    """

    FPS_6 = 6
    FPS_15 = 15
    FPS_30 = 30
    FPS_60 = 60
    FPS_90 = 90

    def __str__(self) -> str:
        return self.name


class StreamConfig(NamedTuple):
    """
    Named tuple representing the format of the stream configuration.

    Attributes:
    -----------
        - type: The type of the camera stream.
        - format: The format of the camera stream.
        - resolution: The resolution of the camera stream.
        - fps: The speed of the camera stream.
    """

    type: StreamType
    format: StreamFormat
    resolution: StreamResolution
    fps: StreamFPS

    def __str__(self) -> str:
        return f"type = {self.type}, format = {self.format}, resolution = {self.resolution}, fps = {self.fps}"  # pylint: disable=line-too-long


class StreamSignals(NamedTuple):
    """
    Named tuple representing the signals used to control the stream.

    Attributes:
    -----------
        - start: The signal to indicate that all threads are ready.
        - pause: The signal to pause the stream.
        - terminate: The signal to terminate the stream.
    """

    run: threading.Event = threading.Event()
    stop: threading.Event = threading.Event()
    error: threading.Event = threading.Event()


class RealSenseCamera:
    """
    A class to abstract the interaction with Intel Realsense cameras.

    Attributes:
    -----------
        - serial_number: The serial number of the camera.
        - stream_configs: The configuration of the streams.
        - is_streaming: The status of the camera stream.
        - frames_streamed: The number of frames streamed.
        - frames_queue: The queue of frames streamed.
        - stream_signals: The signals used to control the stream.


    Instance Methods:
    --------
        - start_streaming:
            Starts the camera stream.
        - stop_streaming:
            Stops the camera stream.
        - capture:
            Captures a frame from the camera.

    Class Methods:
    --------------
        - get_available_cameras_serial_numbers:
            Returns a list with the serial numbers of the available cameras
            or an empty list if no cameras are available.
        - is_camera_available:
            Checks if camera is available.

    """

    # Class attributes
    _cameras: list[str] = []

    # Instance attributes
    _serial_number: str
    _stream_configs: list[StreamConfig]
    _align_to: StreamType | None

    _pipeline: rs.pipeline  # type: ignore
    _config: rs.config  # type: ignore
    _align_method: Callable

    _is_streaming: bool
    _frames_streamed: int
    _frames_queue: queue.Queue[list[Frame]] | None
    _stream_signals: StreamSignals | None
    _stream_thread: threading.Thread | None

    # Instance constructor and destructor

    def __init__(
        self,
        serial_number: str,
        stream_configs: list[StreamConfig],
        align_to: StreamType | None = None,
    ) -> None:
        """
        RealSenseCamera constructor.

        Args:
        -----
            - serial_number: The serial number of the camera.
            - stream_configs: The configuration of the streams.

        Raises:
        -------
            - CameraUnavailableError: If the camera is not available.
            - CameraAlreadyExistsError: If the camera is already instanciated.
            - StreamConfigError: If the configuration is not correct.
        """

        # checks if camera is available
        if not RealSenseCamera.is_camera_available(serial_number):
            raise CameraUnavailableError(f"Camera {serial_number} is not available.")

        # checks if camera is already instanciated
        if serial_number in RealSenseCamera._cameras:
            raise CameraAlreadyExistsError(
                f"Camera with serial number {serial_number} already exists."
            )

        # Initializes attributes
        self._serial_number = serial_number
        self._stream_configs = stream_configs

        self._pipeline = rs.pipeline()  # type: ignore
        self._config = rs.config()  # type: ignore
        self._config.enable_device(self._serial_number)
        self._align_to = align_to

        if self._align_to is not None:
            # check if align_to is in stream_configs
            if self._align_to not in [stream_config.type for stream_config in self._stream_configs]:
                raise StreamConfigError(
                    f"Alignment to stream type {self._align_to.name} is not possible as {self._align_to.name} is not being streamed."  # pylint: disable=line-too-long
                )

            self._align_method = lambda x: rs.align(self._align_to.value).process(x)  # type: ignore

        else:
            self._align_method = lambda x: x

        self._is_streaming = False
        self._frames_streamed = 0
        self._frames_queue = None
        self._stream_signals = None
        self._stream_thread = None

        # applies stream configs explicitly
        self.__apply_stream_configs()

        # adds camera sn to the list of cameras
        RealSenseCamera._cameras.append(self._serial_number)

    def __del__(self):
        """
        RealSenseCamera destructor.
        """

        if hasattr(self, "is_streaming") and self.is_streaming:
            try:
                self._pipeline.stop()
            except Exception:  # pylint: disable=broad-except
                pass

        if hasattr(self, "serial_number"):
            try:
                RealSenseCamera._cameras.remove(self.serial_number)
            except Exception:  # pylint: disable=broad-except
                pass

    # Instance properties

    @property
    def serial_number(self) -> str:
        """
        Returns the serial number of the camera.
        """

        return self._serial_number

    @property
    def stream_configs(self) -> list[StreamConfig]:
        """
        Returns the configuration of the streams.
        """

        return self._stream_configs

    @stream_configs.setter
    def stream_configs(self, stream_configs: list[StreamConfig]) -> None:
        """
        Sets the configuration of the streams.

        Raises:
        -------
            - StreamConfigError: If the configuration is not correct.
            - PipelineRunningError: If the pipeline is running.
        """
        old_configs = self._stream_configs

        try:
            self._stream_configs = stream_configs
            self.__apply_stream_configs()
        except Exception:
            self._stream_configs = old_configs
            self.__apply_stream_configs()
            raise

    @property
    def is_streaming(self) -> bool:
        """
        Returns the status of the camera stream.
        """

        return self._is_streaming

    @property
    def frames_streamed(self) -> int:
        """
        Returns the number of frames streamed.
        """

        return self._frames_streamed

    @property
    def frames_queue(self) -> queue.Queue[list[Frame]]:
        """
        Returns the queue of frames.
        """

        if self._frames_queue is None:
            self._frames_queue = queue.Queue()

        return self._frames_queue

    @property
    def stream_signals(self) -> StreamSignals | None:
        """
        Returns the signals used to control the stream.
        """

        return self._stream_signals

    @property
    def align_to(self) -> StreamType | None:
        """
        Returns the stream type to align to.
        """

        return self._align_to

    # Instance private methods

    def __apply_stream_configs(self):
        """
        Applies the stream configurations.

        Raises:
        -------
            - StreamConfigError: If the configuration is not correct.
            - PipelineRunningError: If the pipeline is running.
        """

        if not self.is_streaming:
            # checks if all configs are valid
            for stream_config in self._stream_configs:
                test_config = rs.config()  # type: ignore

                test_config.enable_device(self._serial_number)

                test_config.enable_stream(
                    stream_config.type.value,
                    stream_config.resolution.value[0],
                    stream_config.resolution.value[1],
                    stream_config.format.value,
                    stream_config.fps.value,
                )

                if not test_config.can_resolve(rs.pipeline()):  # type: ignore
                    raise StreamConfigError(
                        f"Stream config for stream type {stream_config.type.name} is not valid."
                    )

            # applies configs if all are valid
            self._config.disable_all_streams()

            for stream_config in self._stream_configs:
                self._config.enable_stream(
                    stream_config.type.value,
                    stream_config.resolution.value[0],
                    stream_config.resolution.value[1],
                    stream_config.format.value,
                    stream_config.fps.value,
                )

        else:
            raise PipelineRunningError()

    def __stream_thread_target(self) -> None:
        """
        Target function of the acquisition threads.
        """

        nb_errors = 0
        max_nb_errors = 5

        while not self._stream_signals.stop.is_set():  # type: ignore
            self._stream_signals.run.wait()  # type: ignore

            try:
                frames = self._pipeline.wait_for_frames()

                frames = self._align_method(frames)

                self._frames_queue.put(  # type: ignore
                    [
                        Frame.from_intel_frame(frames, stream_config.type)
                        for stream_config in self._stream_configs
                    ]
                )

                self._frames_streamed += 1

                nb_errors = 0

            except Exception as e:  # pylint: disable=broad-except
                print(e)
                nb_errors += 1

                if nb_errors >= max_nb_errors:
                    self._stream_signals.error.set()  # type: ignore
                    break

        self._pipeline.stop()
        self._is_streaming = False

    # Instance public methods

    def start_streaming(self, signals: StreamSignals | None = None) -> None:
        """
        Starts the camera stream.
        """

        if self.is_streaming:
            raise PipelineRunningError()

        self._is_streaming = True
        self._frames_streamed = 0
        self._frames_queue = queue.Queue()

        if signals is None:
            self._stream_signals = StreamSignals()

            self._stream_signals.stop.clear()
            self._stream_signals.error.clear()

            self._stream_signals.run.set()

        else:
            self._stream_signals = signals

        self._pipeline.start(self._config)

        # allow for some auto exposure to happen
        for _ in range(30):
            self._pipeline.wait_for_frames()

        self._stream_thread = threading.Thread(target=self.__stream_thread_target)

        self._stream_thread.start()

    def stop_streaming(self) -> None:
        """
        Stops the camera stream.

        Note:
            If a signals class was passed to the start_streaming method,
            all streams using that signals class will be stopped.
        """

        if self._is_streaming and self._stream_thread:
            self._stream_signals.stop.set()  # type: ignore

            self._stream_thread.join()

    def capture(self) -> list[Frame]:  # type: ignore
        """
        Captures a frame from the camera.

        Returns:
        --------
            A list of the different frames captured from the camera in that instant.
        """

        if self.is_streaming:
            raise PipelineRunningError()

        self._is_streaming = True
        self._pipeline.start(self._config)

        frames = self._pipeline.wait_for_frames()

        self._pipeline.stop()
        self._is_streaming = False

        return [
            Frame.from_intel_frame(frames, stream_config.type)
            for stream_config in self._stream_configs
        ]

    # Class public methods

    @classmethod
    def get_available_cameras_serial_numbers(cls) -> list[str]:
        """
        Returns a list with the serial numbers of the available cameras
        or an empty list if no cameras are available.
        """
        cameras_sn = []

        context = rs.context()  # type: ignore
        devices = context.query_devices()

        for device in devices:
            cameras_sn.append(device.get_info(rs.camera_info.serial_number))  # type: ignore

        return cameras_sn

    @classmethod
    def is_camera_available(cls, sn: str) -> bool:
        """
        Checks if camera is available.

        Args:
        -----
            - sn: The serial number of the camera.
        """

        context = rs.context()  # type: ignore
        devices = context.query_devices()

        for device in devices:
            if device.get_info(rs.camera_info.serial_number) == sn:  # type: ignore
                return True

        return False


class Frame:
    """
    A class to represent a frame from the camera.
    """

    _data: np.ndarray
    _timestamp: str
    _frame_type: StreamType

    # Instance constructor

    def __init__(self, data: np.ndarray, timestamp: str, frame_type: StreamType) -> None:
        """
        Frame constructor.

        Args:
        -----
            - data: The data of the frame.
            - timestamp: The timestamp of the frame.
        """
        self._data = data
        self._timestamp = timestamp
        self._frame_type = frame_type

    # Instance properties

    @property
    def data(self) -> np.ndarray:
        """
        Returns the data of the frame.
        """

        return self._data

    @property
    def timestamp(self) -> str:
        """
        Returns the timestamp of the frame.
        """

        return self._timestamp

    @property
    def frame_type(self) -> StreamType:
        """
        Returns the type of the frame.
        """

        return self._frame_type

    # Instance public methods

    def save(self, folder: str) -> None:
        """
        Saves the frame in the specified folder with the timestamp and type as name.

        Example: 1705944438145_0425_depth.npy
        """

        np.save(
            os.path.join(
                folder,
                self._timestamp + "_" + self.frame_type.name.lower() + ".npy",
            ),
            self.data,
        )

    # Class public methods

    @classmethod
    def from_intel_frame(
        cls,
        intel_frame: rs.composite_frame,  # type: ignore
        frame_type: StreamType,
    ) -> Frame:
        """
        Creates a frame from an intel frame.
        """
        get_frame_method = getattr(intel_frame, f"get_{frame_type.name.lower()}_frame", None)

        if get_frame_method is None:
            raise ValueError("Invalid frame type.")

        return cls(
            np.array(get_frame_method().get_data()),
            str(intel_frame.get_timestamp()).replace(".", "_"),
            frame_type,
        )

    @classmethod
    def from_file(
        cls,
        path: str,
        frame_type: StreamType,
    ) -> Frame:
        """
        Creates a frame from a file.

        Note:
            If an attempt is made to resave the frame, the result will be
            a file named "_<type>.npy" as no timestamp is available.

        Raises:
        -------
            - OSError: If the input file does not exist or cannot be read.
        """

        return cls(np.load(path), "", frame_type)