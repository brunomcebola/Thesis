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
    - CameraAlreadyInstantiatedError: Raised when the camera is already instantiated.
"""

# pylint: disable=pointless-string-statement

from __future__ import annotations

import queue
import threading
from enum import Enum
from typing import NamedTuple, Callable, Union
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


class CameraUnavailableError(Exception):
    """
    Exception raised when the camera is not available.
    """


class PipelineRunningError(Exception):
    """
    Exception raised when the pipeline is running.
    """


class CameraAlreadyInstantiatedError(Exception):
    """
    Exception raised when the camera is already instantiated.
    """


# Helper Classes
"""
██╗  ██╗███████╗██╗     ██████╗ ███████╗██████╗      ██████╗██╗      █████╗ ███████╗███████╗███████╗███████╗
██║  ██║██╔════╝██║     ██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██╔════╝██╔════╝
███████║█████╗  ██║     ██████╔╝█████╗  ██████╔╝    ██║     ██║     ███████║███████╗███████╗█████╗  ███████╗
██╔══██║██╔══╝  ██║     ██╔═══╝ ██╔══╝  ██╔══██╗    ██║     ██║     ██╔══██║╚════██║╚════██║██╔══╝  ╚════██║
██║  ██║███████╗███████╗██║     ███████╗██║  ██║    ╚██████╗███████╗██║  ██║███████║███████║███████╗███████║
╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝     ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝
"""


class StreamType(Enum):
    """
    An enumeration of the different types of streams that can be captured by the camera.

    Attributes:
    -----------
        - COLOR: Color stream.
        - DEPTH: Depth stream.
        - FISHEYE: Fisheye stream.
        - INFRARED: Infrared stream.
        - POSE: Pose stream.

    """

    COLOR = rs.stream.color  # type: ignore
    DEPTH = rs.stream.depth  # type: ignore
    FISHEYE = rs.stream.fisheye  # type: ignore
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


class Frame(NamedTuple):
    """
    Named tuple containing the data of a frame.
    """

    COLOR = Union[np.ndarray, None]
    DEPTH = Union[np.ndarray, None]
    FISHEYE = Union[np.ndarray, None]
    INFRARED = Union[np.ndarray, None]
    POSE = Union[np.ndarray, None]


# Main Classes
"""
███╗   ███╗ █████╗ ██╗███╗   ██╗     ██████╗██╗      █████╗ ███████╗███████╗███████╗███████╗
████╗ ████║██╔══██╗██║████╗  ██║    ██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██╔════╝██╔════╝
██╔████╔██║███████║██║██╔██╗ ██║    ██║     ██║     ███████║███████╗███████╗█████╗  ███████╗
██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║     ██║     ██╔══██║╚════██║╚════██║██╔══╝  ╚════██║
██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ╚██████╗███████╗██║  ██║███████║███████║███████╗███████║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝     ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝
"""


class RealSenseCamera:
    """
    A class to abstract the interaction with Intel Realsense cameras.

    Attributes:
        - serial_number: The serial number of the camera.
        - frames_queue: The queue of frames.
        - control_signal: The signal used to control the stream.
        - is_stopped: Whether the camera is stopped.
        - is_streaming: The status of the camera stream.

    Instance Methods:
        - start_streaming: Starts the camera stream.
        - pause_streaming: Pauses the camera stream.

    Class Methods:
        - list_connected_cameras: Returns a list with the serial numbers of the connected cameras.

    """

    # Class attributes
    _cameras: list[str] = []

    # Instance attributes
    _device: rs.device  # type: ignore
    _config: rs.config  # type: ignore
    _pipeline: rs.pipeline  # type: ignore

    _alignment_method: Callable
    _frames_splitter: Callable
    _frames_queue: queue.Queue[Frame]

    _control_signal: threading.Event
    _kill_signal: threading.Event
    _stream_thread: threading.Thread

    # Instance constructor and destructor

    def __init__(
        self,
        serial_number: str,
        stream_configs: list[StreamConfig],
        alignment: StreamType | None = None,
        control_signal: threading.Event | None = None,
    ) -> None:
        """
        RealSenseCamera constructor.

        Args:
            - serial_number: The serial number of the camera.
            - stream_configs: The configuration of the streams.
            - alignment: The stream type to align the frames.
            - control_signal: The signal to control the stream.

        Raises:
            - CameraUnavailableError: If the camera is not available.
            - CameraAlreadyInstantiatedError: If the camera is already instantiated.
            - StreamConfigError: If there is an error in the configuration of the video stream.

        Notes:
            - The alignment stream must be one of the streams enabled in the stream_configs.
              If None is passed, no alignment will be done.
            - If no control_signal is passed, a new one will be created. This signal can be used
              to control multiple cameras at the same time.
        """

        context = rs.context()  # type: ignore
        devices = context.query_devices()

        # gets the camera device
        for device in devices:
            if device.get_info(rs.camera_info.serial_number) == serial_number:  # type: ignore
                self._device = device

        # checks if camera is available
        if not self._device:
            raise CameraUnavailableError(f"Camera {serial_number} is not available.")

        # checks if camera is already instanciated
        if serial_number in RealSenseCamera._cameras:
            raise CameraAlreadyInstantiatedError(
                f"Trying to instantiate camera {serial_number} twice."
            )

        # initializes the control signal
        if control_signal is None:
            self._control_signal = threading.Event()
            self._control_signal.clear()
        else:
            self._control_signal = control_signal

        # initializes the kill signal
        self._kill_signal = threading.Event()
        self._kill_signal.clear()

        # applies stream configs
        self._config = rs.config()  # type: ignore
        self._config.enable_device(serial_number)
        self._config.disable_all_streams()
        for stream_config in stream_configs:
            self._config.enable_stream(
                stream_config.type.value,
                stream_config.resolution.value[0],
                stream_config.resolution.value[1],
                stream_config.format.value,
                stream_config.fps.value,
            )

            # checks if added config is valid
            if not self._config.can_resolve(rs.pipeline()):  # type: ignore
                raise StreamConfigError(
                    f"Stream config for stream type {stream_config.type.name} is not valid."
                )

        # initializes the frames queue
        self._frames_queue = queue.Queue()

        # defines the alignment method
        if alignment is None:
            self._alignment_method = lambda x: x
        else:
            # check if desired alignment is an enabled stream
            if alignment not in [stream_config.type for stream_config in stream_configs]:
                raise StreamConfigError(
                    f"Alignment to stream type {alignment.name} is not possible as {alignment.name} stream is not enabled."  # pylint: disable=line-too-long
                )

            self._alignment_method = lambda x: rs.align(alignment.value).process(x)  # type: ignore

        # defines the frames_splitter method
        self._frames_splitter = lambda x: Frame(
            *[
                (
                    np.array(getattr(x, f"get_{str(s_type).lower()}_frame")().get_data())
                    if any(stream_config.type == s_type for stream_config in stream_configs)
                    else None
                )
                for s_type in StreamType
            ]
        )

        # starts the pipeline and allows for some auto exposure to happen
        self._pipeline = rs.pipeline()  # type: ignore
        self._pipeline.start(self._config)
        for _ in range(30):
            self._pipeline.wait_for_frames()

        # Launches the stream thread
        self._stream_thread = threading.Thread(target=self.__stream_thread_target)
        self._stream_thread.daemon = True
        self._stream_thread.start()

        # adds camera sn to the list of cameras
        RealSenseCamera._cameras.append(serial_number)

    def __del__(self):
        """
        RealSenseCamera destructor.
        """

        if self._stream_thread and self._stream_thread.is_alive():
            self._kill_signal.set()
            self._stream_thread.join()
            self._pipeline.stop()
            RealSenseCamera._cameras.remove(self._device.get_info(rs.camera_info.serial_number))  # type: ignore # pylint: disable=line-too-long

    # Instance properties

    @property
    def serial_number(self) -> str:
        """
        Returns the serial number of the camera.
        """

        return self._device.get_info(rs.camera_info.serial_number)  # type: ignore

    @property
    def frames_queue(self) -> queue.Queue[Frame]:
        """
        Returns the queue of frames.
        """

        return self._frames_queue

    @property
    def control_signal(self) -> threading.Event:
        """
        Returns the signals used to control the stream.
        """

        return self._control_signal

    @property
    def is_stopped(self) -> bool:
        """
        Returns whether the camera is stopped.
        """

        return self._stream_thread.is_alive()

    @property
    def is_streaming(self) -> bool:
        """
        Returns the status of the camera stream.
        """

        return self._control_signal.is_set() and self._stream_thread.is_alive()

    # Instance private methods

    def __stream_thread_target(self) -> None:
        """
        Target function of the acquisition threads.
        """

        nb_errors = 0
        max_nb_errors = 5

        while not self._kill_signal.is_set():
            self._control_signal.wait()  # type: ignore

            try:
                frames = self._pipeline.wait_for_frames()

                frames = self._alignment_method(frames)

                self._frames_queue.put(self._frames_splitter(frames))

                nb_errors = 0

            except Exception:  # pylint: disable=broad-except
                nb_errors += 1

                if nb_errors >= max_nb_errors:
                    break

    # Instance public methods
    def start_streaming(self) -> None:
        """
        Starts the camera stream.

        Note:
            If a control_signal was passed during initialization,
            all streams using that signal will be started.
        """

        self._control_signal.set()

    def pause_streaming(self) -> None:
        """
        Pauses the camera stream.

        Note:
            If a control_signal was passed during initialization,
            all streams using that signal will be paused.
        """

        self._control_signal.clear()

    # Class public methods

    @classmethod
    def list_connected_cameras(cls) -> list[str]:
        """
        Returns a list with the serial numbers of the connected cameras.
        """
        cameras_sn = []

        context = rs.context()  # type: ignore
        devices = context.query_devices()

        for device in devices:
            cameras_sn.append(device.get_info(rs.camera_info.serial_number))  # type: ignore

        return cameras_sn
