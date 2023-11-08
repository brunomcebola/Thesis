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
import os
import time
import ctypes
import logging
import calendar
import threading

from types import SimpleNamespace

import intel
import utils

WEEK_DAYS = list(calendar.day_name)
SHORT_WEEK_DAYS = list(calendar.day_abbr)

# pylint: disable=pointless-string-statement
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


class AcquireMainThreadError(Exception):
    """
    Exception raised when errors related to the acquire main thread occur.
    """


class AcquireCameraThreadError(Exception):
    """
    Exception raised when errors related to the acquire camera threads occur.
    """


# pylint: disable=pointless-string-statement
"""
███╗   ███╗ █████╗ ██╗███╗   ██╗     ██████╗ ██████╗ ███╗   ██╗████████╗███████╗███╗   ██╗████████╗
████╗ ████║██╔══██╗██║████╗  ██║    ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║╚══██╔══╝
██╔████╔██║███████║██║██╔██╗ ██║    ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║   ██║
██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║   ██║
██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗██║ ╚████║   ██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝   ╚═╝
"""


class AcquireNamespace(SimpleNamespace):
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

            serial_numbers = intel.Camera.get_available_cameras()

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

        string += f"\tOutput folder: '{self.output_folder}'\n"
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


class _AcquireMainThread(threading.Thread):
    """
    This class holds the main thread of the acquire mode.
    """

    __instanciated = False

    def __init__(self, args: AcquireNamespace, log_dest: str):
        """
        AcquireMainThread constructor.

        Args:
        -----
            - args: The arguments for the acquire mode.
            - log_dest: The path to the log file.

        Raises:
        -------
            - AcquireMainThreadError: If the acquire main thread is already instanciated.
            - AcquireCameraThreadError: If the acquire camera thread is already instanciated.
        """
        if self.__instanciated:
            raise AcquireMainThreadError("The acquire main thread is already instanciated.")

        threading.Thread.__init__(self)
        self.name = "Main Thread"
        self.interval = 1
        self.daemon = True
        self.__instanciated = True

        self.args = args
        self.log_dest = log_dest

        self.camera_threads = {}
        self.camera_queues = {}

        file_handler = logging.FileHandler(self.log_dest)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(message)s"))

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)

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
            for camera in self.args.cameras:
                self.camera_queues[camera.serial_number] = []

                try:
                    thread = _AcquireCameraThread(
                        camera,
                        self.camera_queues[camera.serial_number],
                        self.log_dest,
                    )
                except Exception as e:
                    raise AcquireCameraThreadError("The acquire mode is already running.") from e

                self.camera_threads[camera.serial_number] = thread

            i = 1
            while True:
                self.logger.info(i)
                i = i + 1

        finally:
            self.args.cameras[0].stop()

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
        print(f"{self.name} terminated")
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)
            return False
        return True


class _AcquireCameraThread(threading.Thread):
    """
    This class holds the camera threads of the acquire mode.
    """

    __camera_threads = []

    def __init__(self, camera: intel.Camera, queue: list, log_dest: str):
        """
        AcquireCameraThread constructor.

        Args:
        -----
            - camera: The camera to be used.
            - log_dest: The path to the log file.

        Raises:
        -------
            - AcquireCameraThreadError: If the acquire main thread is already instanciated.
        """

        if camera.serial_number in self.__camera_threads:
            raise AcquireCameraThreadError("The acquire main thread is already instanciated.")

        threading.Thread.__init__(self)

        self.camera = camera
        self.queue = queue

        self.name = f"Camera Thread ({self.camera.name})"
        self.interval = 1
        self.daemon = True
        self.__camera_threads.append(self.camera.serial_number)

        file_handler = logging.FileHandler(log_dest)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(message)s"))

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)

    def run(self):
        """
        Target function of the thread class
        """

        try:
            self.camera.start()

            # TODO: skipp some frames to allow auto exposure to adjust

            i = 1
            while True:
                self.camera.capture()

                self.logger.info(i)
                i = i + 1

        finally:
            self.camera.stop()

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
        print(f"{self.name} terminated")
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)
            return False
        return True


class Acquire:
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

    def __init__(self, **args) -> None:
        """
        Acquire constructor.

        Args:
        -----
            - args: The arguments for the acquire mode (matching the constructor of
                    AcquireNamespace).
        """
        utils.print_info("Entering acquire mode...")
        print()

        self.main_thread = None
        self.__log_file = "logs/acquire.log"

        try:
            self.args = AcquireNamespace(**args)
        except Exception as e:
            # TODO: handle exception
            raise e

        file_handler = logging.FileHandler(self.__log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

        self.logger = logging.getLogger("Acquire mode")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)

        print()
        utils.print_info("Acquire mode settings:")
        print(self.args)
        print()

    def run(self) -> None:
        """
        Runs the acquire mode.
        """

        try:
            thread = _AcquireMainThread(self.args, self.__log_file)
        except Exception as e:
            # TODO: handle exception
            raise e

        self.main_thread = thread

        self.logger.info("Starting data acquisition ...")
        utils.print_info("Starting data acquisition...")

        self.main_thread.start()

        self.logger.info("Data acquisition started.")
        utils.print_success("Data acquisition started.")
        print()

    def stop(self) -> None:
        """
        Stops the acquire mode.
        """
        if not self.main_thread:
            raise AcquireMainThreadError("The acquire mode is not running.")

        self.logger.info("Stopping acquire mode...")
        utils.print_info("Stopping acquire mode...")

        self.main_thread.stop()
        self.main_thread.join()
        self.main_thread = None

        self.logger.info("Acquire mode stopped.")
        utils.print_success("Acquire mode stopped.")
        print()

    def __del__(self) -> None:
        utils.print_info("Exiting acquire mode...")

        if self.main_thread:
            self.stop()
