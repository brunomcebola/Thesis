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

from enum import Enum
from typing import NamedTuple
import numpy as np
import pyrealsense2 as rs
import matplotlib.pyplot as plt

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


class StreamFrameRate(Enum):
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
        - format: The format of the camera stream.
        - resolution: The resolution of the camera stream (width x height)
        - fps: The frames per second of the camera stream.
    """

    type: StreamType
    format: StreamFormat
    resolution: StreamResolution
    fps: StreamFrameRate

    def __str__(self) -> str:
        return f"format={self.format}, resolution={self.resolution}, fps={self.fps}"


class RealSenseCamera:
    """
    A class to abstract the interaction with Intel Realsense cameras.

    Attributes:
    -----------
        - serial_number: The serial number of the camera.
        - is_streaming: The status of the camera stream.
        - stream_configs: The configuration of the streams.

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

    Class Methods:
    --------------
        - get_available_cameras_sn:
            Returns a list with the serial numbers of the available cameras
            or an empty list if no cameras are available.
        - is_camera_available:
            Checks if camera is available.
        - get_camera_model:
            Returns the camera model.

    """

    # Class attributes
    _cameras: list[str] = []

    # Instance attributes
    _serial_number: str
    _is_streaming: bool
    _stream_configs: list[StreamConfig]

    _pipeline: rs.pipeline  # type: ignore
    _config: rs.config  # type: ignore

    # Instance constructor and destructor

    def __init__(self, serial_number: str, stream_configs: list[StreamConfig]) -> None:
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
        self._is_streaming = False
        self._pipeline = rs.pipeline()  # type: ignore
        self._config = rs.config()  # type: ignore
        self._config.enable_device(self._serial_number)

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
            except Exception:
                pass

        if hasattr(self, "serial_number"):
            try:
                RealSenseCamera._cameras.remove(self.serial_number)
            except Exception:
                pass

    # Instance properties

    @property
    def serial_number(self) -> str:
        """
        Returns the serial number of the camera.
        """

        return self._serial_number

    @property
    def is_streaming(self) -> bool:
        """
        Returns the status of the camera stream.
        """

        return self._is_streaming

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

    # Instance public methods

    # TODO: make this a stream with threads
    def start(self) -> bool:
        """
        Starts the camera stream.

        Returns:
        --------
            - True if the pipeline was not running and was started
            - False if the pipelin was already running.
        """

        if self.is_streaming:
            return False

        self._pipeline.start(self._config)
        self._is_streaming = True

        return True

    # TODO: perhaps remove this
    def stop(self) -> bool:
        """
        Stops the camera stream.

        Returns:
        --------
            - True if the pipeline was running and was stopped
            - False if the pipeline was already stopped.
        """

        if not self.is_streaming:
            return False

        self._pipeline.stop()
        self._is_streaming = False

        return True

    # TODO: make this capture a frame and stop. Ensure no stream happening
    def capture(self) -> rs.composite_frame:  # type: ignore
        """
        Returns an object representing a frame from the camera.

        It blocks the execution until a frame is available, if the camera is running.

        In order to access the frame data itself it is necessary to use a subclass of Frame.
        """

        if self.is_streaming:
            return self._pipeline.wait_for_frames()
        else:
            return []

    # Class public methods

    @classmethod
    def get_available_cameras_sn(cls) -> list[str]:
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

    @classmethod
    def get_camera_model(cls, sn: str) -> str:
        """
        Returns the camera model.

        Args:
        -----
            - sn: The serial number of the camera.
        """

        context = rs.context()  # type: ignore
        devices = context.query_devices()

        for device in devices:
            if device.get_info(rs.camera_info.serial_number) == sn:  # type: ignore
                return device.get_info(rs.camera_info.name).split(" ")[-1][:4]  # type: ignore

        return ""


# TODO: iprove this classes
class Frame:
    """
    Abstract class to represent a frame captured by a camera.

    Not to be instantiated directly.
    """

    def __init__(self, frame: rs.composite_frame | None = None) -> None:  # type: ignore
        """
        Frame constructor.

        Args:
        -----
            - frame: The actual frame captured by a camera.
        """

        if frame is not None:
            self.data = np.array(frame.get_data())
        else:
            self.data = None

    def save_as_npy(self, folder: str, name: str) -> str:
        """
        Saves the frame.
        """

        if self.data is not None:
            path = os.path.join(
                folder, name + "_" + type(self).__name__.replace("Frame", "").lower() + ".npy"
            )

            np.save(path, self.data)

            return path

        else:
            return ""

    def load_from_npy(self, path: str) -> None:
        """
        Loads the frame.
        """

        try:
            self.data = np.load(path)
        except Exception:
            pass

    def show(self) -> None:
        """
        Show the frame.
        """
        if self.data is not None:
            plt.figure()
            plt.imshow(self.data)
            plt.show()

    @classmethod
    def create_instances(cls, frame: rs.composite_frame, stream_type: StreamType) -> list["Frame"]:  # type: ignore
        """
        Return a list of Frame objects based on the stream type.
        """

        instances_list: list[Frame] = []
        types_list = stream_type.value if isinstance(stream_type.value, list) else [stream_type]

        for t in types_list:
            if t == StreamType.DEPTH:
                instances_list.append(DepthFrame(frame))
            elif t == StreamType.COLOR:
                instances_list.append(ColorFrame(frame))
            else:
                instances_list.append(IRFrame(frame))

        return instances_list


class DepthFrame(Frame):
    """
    Subclass of Frame to represent a depth frame captured by a camera.
    """

    def __init__(self, frame: rs.composite_frame) -> None:  # type: ignore
        super().__init__(frame.get_depth_frame())


class ColorFrame(Frame):
    """
    Subclass of Frame to represent a color frame captured by a camera.
    """

    def __init__(self, frame: rs.composite_frame) -> None:  # type: ignore
        super().__init__(frame.get_color_frame())


class IRFrame(Frame):
    """
    Subclass of Frame to represent an infrared frame captured by a camera.
    """

    def __init__(self, frame: rs.composite_frame) -> None:  # type: ignore
        super().__init__(frame.get_infrared_frame())
