"""
This module holds the tools to acquire data from the realsense cameras.

Classes:
--------
- AcquireNamespace: Holds the arguments for the acquire mode.

Exceptions:
-----------
- OutputFolderError: Exception raised when errors related to the out_folder occur.
- OperationTimeError: Exception raised when errors related to the operation time occur.
- SerialNumberError: Exception raised when errors related to the serial number occur.
- NamesError: Exception raised when errors related to the names occur.
- StreamTypeError: Exception raised when errors related to the stream type occur.
- StreamConfigError: Exception raised when errors related to the stream config occur.
"""

# pylint: disable=pointless-string-statement

import os
import time
import copy
import ctypes
import logging
import calendar
import threading

from typing import Callable

import intel
import utils

# Constants
"""
 ██████╗ ██████╗ ███╗   ██╗███████╗████████╗ █████╗ ███╗   ██╗████████╗███████╗
██╔════╝██╔═══██╗████╗  ██║██╔════╝╚══██╔══╝██╔══██╗████╗  ██║╚══██╔══╝██╔════╝
██║     ██║   ██║██╔██╗ ██║███████╗   ██║   ███████║██╔██╗ ██║   ██║   ███████╗
██║     ██║   ██║██║╚██╗██║╚════██║   ██║   ██╔══██║██║╚██╗██║   ██║   ╚════██║
╚██████╗╚██████╔╝██║ ╚████║███████║   ██║   ██║  ██║██║ ╚████║   ██║   ███████║
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝
"""

WEEK_DAYS = list(calendar.day_name)
SHORT_WEEK_DAYS = list(calendar.day_abbr)

LOG_FILE = "/logs/aquire.log"

# Functions
"""
███████╗██╗   ██╗███╗   ██╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝██║   ██║████╗  ██║██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
█████╗  ██║   ██║██╔██╗ ██║██║        ██║   ██║██║   ██║██╔██╗ ██║███████╗
██╔══╝  ██║   ██║██║╚██╗██║██║        ██║   ██║██║   ██║██║╚██╗██║╚════██║
██║     ╚██████╔╝██║ ╚████║╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║███████║
╚═╝      ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝

"""

def _get_logger(name: str) -> logging.Logger:
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger

# Exceptions
"""
███████╗██╗  ██╗ ██████╗███████╗██████╗ ████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
█████╗   ╚███╔╝ ██║     █████╗  ██████╔╝   ██║   ██║██║   ██║██╔██╗ ██║███████╗
██╔══╝   ██╔██╗ ██║     ██╔══╝  ██╔═══╝    ██║   ██║██║   ██║██║╚██╗██║╚════██║
███████╗██╔╝ ██╗╚██████╗███████╗██║        ██║   ██║╚██████╔╝██║ ╚████║███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
"""
class OutputFolderError(Exception):
    """
    Exception raised when errors related to the out_folder occur.
    """


class OperationTimeError(Exception):
    """
    Exception raised when errors related to the operation time occur.

    It returns a tuple with information about the error.

    Tuple Structure:
    ----------------
        - error_message (str): A human-readable error message providing more
          details about the issue.
        - error_index (int | None): The index of the invalid operation time.

    Usage:
    ------
        try:
           # Code that may raise the exception
        except OperationTimeError as e:
           error_message, error_index = e.args
    """

    def __init__(self, error_message, error_index: int | None = None):
        super().__init__(error_message, error_index)


class SerialNumberError(Exception):
    """
    Exception raised when errors related to the serial number occur.
    """


class NamesError(Exception):
    """
    Exception raised when errors related to the names occur.
    """


class StreamTypeError(Exception):
    """
    Exception raised when errors related to the stream type occur.
    """


class StreamConfigError(Exception):
    """
    Exception raised when errors related to the stream config occur.
    """


class AcquireError(Exception):
    """
    Exception raised when errors related to the acquire mode occur.
    """


# Main content
"""
 ██████╗██╗      █████╗ ███████╗███████╗███████╗███████╗
██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██╔════╝██╔════╝
██║     ██║     ███████║███████╗███████╗█████╗  ███████╗
██║     ██║     ██╔══██║╚════██║╚════██║██╔══╝  ╚════██║
╚██████╗███████╗██║  ██║███████║███████║███████╗███████║
 ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝
"""

class AcquireNamespace(utils.ModeNamespace):
    """
    This class holds the arguments for the acquire mode.

    It can be initialized with explicit arguments or with a dictionary.

    Attributes:
    -----------
        - output_folder (str):
            The path to the output folder.
        - op_times (list[tuple[int, int]]):
            The time interval in which the cameras will be capturing data
            for each day of the week (Monday to Sunday).
        - cameras (list[intel.Camera]):
            The list with the cameras to be used.
    """

    def __init__(
        self,
        *args,
        output_folder: str,
        op_times: list[tuple[int, int]] | None = None,
        serial_numbers: list[str] | None = None,
        names: list[str] | None = None,
        stream_types: list[intel.StreamType] | None = None,
        stream_configs: list[dict[intel.StreamType, intel.StreamConfig]] | None = None,
        **kwargs,
    ):
        """
        AcquireNamespace constructor.

        Args:
        -----
            - output_folder: The path to the output folder.
            - op_times: The time interval in which the cameras will be capturing data
              for each day of the week (Monday to Sunday).
                - If None then cameras will be capturing data all the time.
                - If list with 1 element then the specified time interval will be used for all days.
                - If list with 7 elements then each element will be used for each day.
            - serial_numbers: The serial numbers of the cameras to be used.
                - If None then all connected cameras will be used.
                - If list with n elements then the specified cameras will be used.
            - names: The names of the cameras to be used.
                - If None then the cameras' serial numbers will be used as names.
                - If list with the same len as the serial_numbers list then the specified names
                  will be used.
            - stream_types: The stream types of the cameras to be used.
                - If None then depth stream will be used for all cameras.
                - If list with 1 element then the specified stream will be used for all cameras.
                - If list with the same len as the serial_numbers list then the specified streams
                  will be used.

        Raises:
        -------
            - OutputFolderError:
                - If the output folder does not exist.
            - OperationTimeError:
                - If the operation time is not a list with 1 or 7 elements.
                - If the operation time is not expressed in the format (int, int).
                - If the start hour is not a value between 0 and 23.
                - If the stop hour is not a value between 1 and 24.
                - If the start hour is greater than the stop hour.
            - SerialNumberError:
                - If the serial numbers are not unique.
            - NamesError:
                - If the number of names is not equal to the number of cameras, when cameras are
                specified.
            - StreamTypeError:
                - If the number of stream types is not equal to the number of cameras, when cameras
                are specified.
            - StreamConfigError:
                - If the number of stream configs is not equal to the number of cameras, when
                cameras are specified.
            - intel.CameraUnavailableError:
                - If no cameras are available.
                - If the specified cameras are not available.
            - intel.StreamConfigError:
                - If the specified stream config is not valid for the specified camera model.


        Examples:
        ---------
            >>> acquire_namespace = AcquireNamespace(
            ...     output_folder="./",
            ...     op_times=[(8, 12)],
            ...     serial_numbers=["123456789", "987654321"],
            ...     names=["front", "back"],
            ...     stream_types=[StreamType.DEPTH, StreamType.COLOR],
            ... )
            >>> print(acquire_namespace)
        """

        del args
        del kwargs

        # type definitions
        self.output_folder: str = ""
        self.op_times: list[tuple[int, int]] = []
        self.cameras: list[intel.Camera] = []

        # output_folder validations
        output_folder = output_folder.strip()

        if output_folder == "":
            raise OutputFolderError("The output folder cannot be a empty string.")

        if not os.path.exists(output_folder):
            raise OutputFolderError(f"The output folder '{output_folder}' does not exist.")

        self.output_folder = output_folder

        # op_times validations
        if op_times is None:
            utils.print_warning(
                "No operation time specified. Cameras will be capturing data all the time."
            )

            op_times = [(int(0), int(24))] * 7

        elif len(op_times) == 1:
            utils.print_warning(
                f"Using ({op_times[0][0]}h - {op_times[0][1]}h) as operation time for all days."
            )

            op_times = op_times * 7

        elif len(op_times) != 7:
            raise OperationTimeError(
                "The specified operation time must be a list with 1 or 7 elements.",
            )

        for i, op_time in enumerate(op_times):
            if len(op_time) != 2:
                raise OperationTimeError(
                    "The operation time must be expressed in the format "
                    + "(int, int). Ex: (8, 12) => 8:00 - 12:00.",
                    i,
                )

            if op_time[0] not in range(24):
                raise OperationTimeError(
                    "The start hour must be a value between 0 and 23.",
                    i,
                )

            if op_time[1] not in range(1, 25):
                raise OperationTimeError(
                    "The stop hour must be a value between 1 and 24.",
                    i,
                )

            if op_time[0] >= op_time[1]:
                raise OperationTimeError(
                    "The start hour must be smaller than the stop hour.",
                    i,
                )

        self.op_times = op_times

        # serial_numbers validations
        original_nb_serial_numbers = len(serial_numbers) if serial_numbers is not None else 0

        if serial_numbers is None:
            utils.print_warning("No camera specified. Using all connected cameras.")

            serial_numbers = intel.Camera.get_available_cameras_sn()

            if len(serial_numbers) == 0:
                raise intel.CameraUnavailableError("No available cameras.")

        if len(set(serial_numbers)) != len(serial_numbers):
            raise SerialNumberError("Duplicate serial numbers specified.")

        serial_numbers = [str(sn).strip() for sn in serial_numbers]

        # names validations
        if names is None:
            utils.print_warning("No names specified. Using serial numbers as camera names.")

            names = serial_numbers

        elif original_nb_serial_numbers == 0:
            utils.print_warning(
                "No cameras especified. Ignoring names and using serial numbers instead."
            )

            names = serial_numbers

        elif len(names) != len(serial_numbers):
            raise NamesError("The number of names must be equal to the number of cameras.")

        # stream_types validations
        if stream_types is None:
            utils.print_warning("No stream type specified. Setting depth as stream of all cameras.")

            stream_types = [intel.StreamType.DEPTH] * len(serial_numbers)

        elif len(stream_types) == 1 and not len(serial_numbers) == 1:
            utils.print_warning("Using the specified stream type for all cameras.")

            stream_types = stream_types * len(serial_numbers)

        elif original_nb_serial_numbers == 0:
            utils.print_warning(
                "No cameras especified. Ignoring stream types and using depth for all "
                + "cameras instead."
            )

            stream_types = [intel.StreamType.DEPTH] * len(serial_numbers)

        elif len(stream_types) != len(serial_numbers):
            raise StreamTypeError(
                "The number of stream types must be equal to the number of cameras."
            )

        # stream configs validations
        if stream_configs is None:
            utils.print_warning(
                "No stream configs specified. Using default stream configs for each camera model."
            )

            stream_configs = [
                intel.Camera.get_default_config(intel.Camera.get_camera_model(sn))
                for sn in serial_numbers
            ]

        elif len(stream_configs) == 1 and not len(serial_numbers) == 1:
            utils.print_warning("Using the specified stream config for all cameras.")

            stream_configs = stream_configs * len(serial_numbers)

        elif original_nb_serial_numbers == 0:
            utils.print_warning(
                "No cameras especified. Ignoring stream configs and using default stream configs "
                + "for each camera model instead."
            )

            stream_configs = [
                intel.Camera.get_default_config(intel.Camera.get_camera_model(sn))
                for sn in serial_numbers
            ]

        elif len(stream_configs) != len(serial_numbers):
            raise StreamConfigError(
                "The number of stream configs must be equal to the number of cameras."
            )

        # create list of camera instances
        self.cameras = [
            intel.Camera(sn, st, sc, nm)
            for sn, st, sc, nm in zip(serial_numbers, stream_types, stream_configs, names)
        ]

    def __str__(self) -> str:
        string = ""

        string += f"\tOutput folder: {self.output_folder}\n"
        string += f"\tOperation time: {[(SHORT_WEEK_DAYS[i], op[0], op[1]) for i, op in enumerate(self.op_times)]}\n"  # pylint: disable=line-too-long
        string += "\tCameras:"
        for camera in self.cameras:
            string += "\n"
            string += f"\t\tName:{camera.name}\n"
            string += f"\t\tSerial number:{camera.serial_number}\n"
            string += f"\t\tStream type:{camera.stream_type}\n"
            for key, value in camera.stream_configs.items():
                string += f"\t\t{key.name.capitalize()} stream config:{str(value)}\n"

        # align elements
        string = string.split(("Cameras:"))
        lines = string[1].split("\t\t")

        max_title = max([len(line.split(":")[0]) for line in lines])

        lines = [
            f":  {' ' * (max_title - len(line.split(':')[0]))}".join(line.split(":"))
            for line in lines
        ]

        lines = "\t\t".join(lines)

        return (string[0] + "Cameras:" + lines).rstrip()


class _AcquireMainThreadStatus:
    """
    Helper class to flag the Acquire Class that the data
    acquisition has started in the camera threads.

    Attributes:
    -----------
        - acquiring (bool):
            Flag to indicate if the data acquisition has started.
        - error (bool):
            Flag to indicate if an error occurred.
        - error_code (int):
            The error code. List of error codes:
            - 0: No error
            - 1: The acquire main thread is already instanciated.
            - 2: Error creating a camera thread.
        - error_message (str):
            The error message.
    """

    acquiring: bool = False
    error: bool = False
    error_code: int = 0


class _AcquireCameraThreadStatus:
    """
    Helper class to flag the Acquire Class that the data
    acquisition has started in the camera threads.

    Attributes:
    -----------
        - ready (bool):
            Flag to indicate if the camera is ready to start capturing data.
        - acquiring (bool):
            Flag to indicate if the data acquisition has started.
        - error (bool):
            Flag to indicate if an error occurred.
        - error_code (int):
            The error code. List of error codes:
            - 0: No error
            - 1: The acquire camera thread is already instanciated.
            - 2: Error acquiring data from camera.
        - error_message (str):
            The error message.

    """

    ready: bool
    acquiring: Callable[[], bool]
    error: bool
    error_code: int

    __ready: bool
    __acquiring: Callable[[], bool]
    __error: bool
    __error_code: int

    def __init__(self, func: Callable[[], bool]) -> None:
        self.ready = self.__ready = False
        self.acquiring = self.__acquiring = func
        self.error = self.__error = False
        self.error_code = self.__error_code = 0

    def reset(self) -> None:
        """
        Resets the status of the camera thread.
        """
        self.ready = self.__ready
        self.acquiring = self.__acquiring
        self.error = self.__error
        self.error_code = self.__error_code


class _AcquireCameraThread(threading.Thread):
    """
    This class holds the camera threads of the acquire mode.
    """

    __cameras_threads = []

    __camera: intel.Camera
    __queue: list
    __status: _AcquireCameraThreadStatus
    __logger: logging.Logger

    def __init__(
        self,
        camera: intel.Camera,
        queue: list,
        status: _AcquireCameraThreadStatus,
        log_dest: str,
    ):
        """
        AcquireCameraThread constructor.

        Args:
        -----
            - camera: The camera to be used.
            - queue: The queue to store the data.
            - status: The status of the camera thread.
            - log_dest: The path to the log file.
        """

        if camera.serial_number in _AcquireCameraThread.__cameras_threads:
            status.error = True
            status.error_code = 1

            raise Exception

        threading.Thread.__init__(self)

        self.__camera = camera
        self.__queue = queue
        self.__status = status

        self.name = f"{self.__camera.name} Thread"
        self.interval = 1
        self.daemon = True

        file_handler = logging.FileHandler(log_dest)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        )

        self.__logger = logging.getLogger(self.name)
        self.__logger.setLevel(logging.INFO)
        self.__logger.addHandler(file_handler)

        _AcquireCameraThread.__cameras_threads.append(self.__camera.serial_number)

        self.__logger.info("Created!")

    def run(self):
        """
        Target function of the thread class
        """

        try:
            self.__logger.info("Started")

            self.__camera.start()

            for _ in range(30):
                self.__camera.capture()

            self.__logger.info("Ready to acquire data!")
            self.__status.ready = True

            while not self.__status.acquiring():
                continue

            self.__logger.info("Started acquiring data!")

            i = 1
            while True:
                try:
                    frame = self.__camera.capture()
                except Exception:
                    self.__status.error = True
                    self.__status.error_code = 2

                    self.__logger.error("Error acquring data!")
                    self.__logger.info("Stopped due to Error!")

                    raise

                self.__queue.append(frame)

                self.__logger.info("Captured frame %d", i)

                i = i + 1

                # TODO: remove. Only her for quick debug
                # break

        except Exception as e:
            print(e)

        finally:
            self.__camera.stop()

            self.__logger.info("Stopped")

    def get_id(self) -> int:
        """
        Returns id of the respective thread
        """
        # returns id of the respective thread
        if hasattr(self, "_thread_id"):
            return int(self._thread_id)  # type: ignore
        for i, thread in threading._active.items():  # type: ignore # pylint: disable=protected-access
            if thread is self:
                return int(i)
        return -1

    def stop(self) -> bool:
        """
        Raises an exception in the thread to terminate it.

        Returns:
        --------
            - True if the thread was successfully terminated.
            - False if the thread was not running.
        """
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), ctypes.py_object(SystemExit)
        )
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)
            return False
        return True

    def __del__(self) -> None:
        self.stop()

        _AcquireCameraThread.__cameras_threads.remove(self.__camera.serial_number)

        self.__logger.info("Deleted!")


class _AcquireMainThread(threading.Thread):
    """
    This class holds the main thread of the acquire mode.

    Attributes:
    -----------
        - args (AcquireNamespace):
            The arguments for the acquire mode.
        - log_dest (str):
            The path to the log file.
        - acquiring (_AcquireStatus):
            The status of the acquire mode.
        - cameras_threads (dict[str, _AcquireCameraThread]):
            The camera threads of the acquire mode.
        - __cameras_statuses (dict[str, bool]):
            The is_ready of the camera threads of the acquire mode.
        - __cameras_queues (dict[str, list]):
            The queues of the camera threads of the acquire mode.
    """

    __instanciated = False

    __cameras_threads: dict[str, _AcquireCameraThread]
    __cameras_statuses: dict[str, _AcquireCameraThreadStatus]
    __cameras_queues: dict[str, list]
    __nb_restarts: int

    def __init__(self, args: AcquireNamespace, status: _AcquireMainThreadStatus, log_dest: str):
        """
        AcquireMainThread constructor.

        Args:
        -----
            - args: The arguments for the acquire mode.
            - status: The status of the acquire main thread.
            - log_dest: The path to the log file.
        """
        if _AcquireMainThread.__instanciated:
            status.error = True
            status.error_code = 1

            raise Exception

        threading.Thread.__init__(self)

        self.__args = args
        self.__log_dest = log_dest
        self.__status = status
        self.__nb_restarts = 0

        self.__cameras_threads = {}
        self.__cameras_statuses = {}
        self.__cameras_queues = {}

        self.name = "Main Thread"
        self.interval = 1
        self.daemon = True

        file_handler = logging.FileHandler(self.__log_dest)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        )

        self.__logger = logging.getLogger(self.name)
        self.__logger.setLevel(logging.INFO)
        self.__logger.addHandler(file_handler)

        _AcquireMainThread.__instanciated = True

        self.__logger.info("Created!")

    def run(self):
        """
        Target function of the thread class
        """

        """
            TODO
            implement op_times based on flags
            https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
        """

        try:
            self.__logger.info("Started")

            self.start_camera_threads()

            while True:
                for camera in self.__args.cameras:
                    if (
                        self.__cameras_statuses[camera.serial_number].error
                        and self.__cameras_statuses[camera.serial_number].error_code == 2
                    ):
                        self.__nb_restarts += 1

                        self.__logger.info("Restarting camera threads...")

                        self.stop_camera_threads()

                        time.sleep(10)

                        self.start_camera_threads()

                        break

                    else:
                        if len(self.__cameras_queues[camera.serial_number]) != 0:
                            frame = self.__cameras_queues[camera.serial_number].pop(0)
                            intel.Frame.create_instance(
                                frame,
                                os.path.join(
                                    self.__args.output_folder,
                                    camera.serial_number,
                                    str(frame.get_timestamp()).replace(".", "_") + ".ply",
                                ),
                                camera.stream_type,
                            ).save()

        except Exception as e:
            print(e)

        finally:
            self.stop_camera_threads()

            self.__logger.info("Stopped")

    def start_camera_threads(self) -> None:
        """
        Starts the camera threads.
        """
        for camera in self.__args.cameras:
            self.__logger.info("Creating %s Thread...", camera.name)

            self.__cameras_queues[camera.serial_number] = []
            self.__cameras_statuses[camera.serial_number] = _AcquireCameraThreadStatus(
                lambda: self.__status.acquiring
            )

            self.__cameras_statuses[camera.serial_number].acquiring = lambda: True

            thread = _AcquireCameraThread(
                camera,
                self.__cameras_queues[camera.serial_number],
                self.__cameras_statuses[camera.serial_number],
                self.__log_dest,
            )

            if self.__cameras_statuses[camera.serial_number].error:
                self.__cameras_queues = {}
                self.__cameras_threads = {}

                self.__status.error = True
                self.__status.error_code = 2

                self.__logger.error("Error creating %s Thread...", camera.name)

                raise Exception

            self.__cameras_threads[camera.serial_number] = thread

        for camera in self.__args.cameras:
            self.__logger.info("Starting %s...", self.__cameras_threads[camera.serial_number].name)

            self.__cameras_threads[camera.serial_number].start()

        time.sleep(1)

        self.__logger.info("Started all camera threads!")

        while not all([status.ready for status in self.__cameras_statuses.values()]):
            time.sleep(1)

        self.__logger.info("Syncing camera threads...")
        time.sleep(2)
        self.__logger.info("Camera threads synced!")

        self.__status.acquiring = True

    def stop_camera_threads(self) -> None:
        """
        Stops the camera threads.
        """
        for camera in self.__args.cameras:
            self.__logger.info("Stopping %s...", self.__cameras_threads[camera.serial_number].name)

            self.__cameras_threads[camera.serial_number].stop()

        for camera in self.__args.cameras:
            self.__cameras_threads[camera.serial_number].join()

        self.__logger.info("Stopped all camera threads!")
        self.__logger.info("Deleting all camera threads...")

        self.__cameras_threads = {}

        self.__logger.info("Flushing all acquired data...")

        for camera in self.__args.cameras:
            while len(self.__cameras_queues[camera.serial_number]) != 0:
                frame = self.__cameras_queues[camera.serial_number].pop(0)
                intel.Frame.create_instance(
                    frame,
                    os.path.join(
                        self.__args.output_folder,
                        camera.serial_number,
                        str(frame.get_timestamp()).replace(".", "_") + ".ply",
                    ),
                    camera.stream_type,
                ).save()

        self.__logger.info("Flushed all acquired data!")

    def get_id(self) -> int:
        """
        Returns id of the respective thread
        """
        # returns id of the respective thread
        if hasattr(self, "_thread_id"):
            return int(self._thread_id)  # type: ignore
        for i, thread in threading._active.items():  # type: ignore # pylint: disable=protected-access
            if thread is self:
                return int(i)
        return -1

    def stop(self) -> bool:
        """
        Raises an exception in the thread to terminate it.

        Returns:
        --------
            - True if the thread was successfully terminated.
            - False if the thread was not running.
        """
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), ctypes.py_object(SystemExit)
        )
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)
            return False
        return True

    def __del__(self) -> None:
        self.stop()

        _AcquireMainThread.__instanciated = False

        self.__logger.info("Deleted!")


class Acquire(utils.Mode):
    """
    This class holds the tools to acquire data from the realsense cameras.

    Attributes:
    -----------
        - args (AcquireNamespace):
            The arguments for the acquire mode.
        - main_thread (threading.Thread):
            The main thread of the acquire mode.
        - sub_threads (list[threading.Thread]):
            The list with all the sub threads of the acquire mode.

    """

    def __init__(self, args: AcquireNamespace) -> None:
        """
        Acquire constructor.

        Args:
        -----
            - args: The arguments for the acquire mode (matching the constructor of
                    AcquireNamespace).

        """
        self.__args = copy.deepcopy(args)

        print(_main_thread)

    def run(self) -> None:
        """
        Runs the acquire mode.
        """

        if self.__main_thread:
            raise AcquireError("The acquire mode is already running.")

        self.__logger.info("Started aquire mode!")
        utils.print_info("Started acquire mode!\n")

        self.__logger.info("Setting folders to store data...")
        utils.print_info("Setting folders to store data...\n")

        for camera in self.__args.cameras:
            path = os.path.join(self.__args.output_folder, camera.serial_number)

            self.__logger.info("Setting '%s' as destination for %s data...", path, camera.name)
            utils.print_info(f"Setting '{path}' as destination for {camera.name} data...")

            if not os.path.exists(path):
                os.mkdir(path)

            self.__logger.info("Set '%s' as destination for %s data!", path, camera.name)
            utils.print_success(f"Set '{path}' as destination for {camera.name} data!")
        print()

        self.__logger.info("All folders set!")
        utils.print_info("All folders set!\n")

        self.__logger.info("Creating Main Thread...")

        self.__main_thread = _AcquireMainThread(
            self.__args, self.__acquire_main_thread_status, self.__log_file
        )

        self.__logger.info("Starting %s...", self.__main_thread.name)

        self.__main_thread.start()

        while self.__acquire_main_thread_status.acquiring is False:
            continue

        utils.print_info("Started acquiring data!\n")

    def stop(self) -> None:
        """
        Stops the acquire mode.
        """
        if not self.__main_thread:
            raise AcquireError("The acquire mode is not running.")

        self.__logger.info("Stopping %s...", self.__main_thread.name)

        self.__main_thread.stop()
        self.__main_thread.join()

        self.__logger.info("Deleting Main Thread...")

        self.__main_thread = None

        time.sleep(5)

        self.__logger.info("Stopped acquire mode!")
        utils.print_info("Stopped acquire mode!\n")

    def __del__(self) -> None:
        if self.__main_thread:
            self.stop()

if __name__ == "__main__":
    raise RuntimeError("This file is not meant to be executed directly.")
else:
    _main_thread = None
    _camera_threads = 1
