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
from __future__ import annotations

import os
import re
import calendar
import threading
import datetime

import helpers.intel as intel
import helpers.utils as utils

_LOG_FILE = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../logs/aquire.log")

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
███╗   ███╗ █████╗ ██╗███╗   ██╗     ██████╗ ██████╗ ███╗   ██╗████████╗███████╗███╗   ██╗████████╗
████╗ ████║██╔══██╗██║████╗  ██║    ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║╚══██╔══╝
██╔████╔██║███████║██║██╔██╗ ██║    ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║   ██║
██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║   ██║
██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗██║ ╚████║   ██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝   ╚═╝
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
        - cameras (list[intel.RealSenseCamera]):
            The list with the cameras to be used.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        output_folder: str,
        op_times: list[tuple[int, int]] | None = None,
        serial_numbers: list[str] | None = None,
        names: list[str] | None = None,
        stream_types: list[intel.StreamType] | None = None,
        stream_configs: list[dict[intel.StreamType, intel.StreamConfig]] | None = None,
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

        # type definitions
        self.output_folder: str = ""
        self.op_times: list[tuple[int, int]] = []
        self.cameras: list[intel.RealSenseCamera] = []

        # output_folder validations
        output_folder = output_folder.strip()

        if output_folder == "":
            raise OutputFolderError("The output folder cannot be a empty string.")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        self.output_folder = os.path.abspath(output_folder)

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

            serial_numbers = intel.RealSenseCamera.get_available_cameras_sn()

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

        elif len(stream_types) == 1:
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
                intel.RealSenseCamera.get_default_config(intel.RealSenseCamera.get_camera_model(sn))
                for sn in serial_numbers
            ]

        elif len(stream_configs) == 1:
            utils.print_warning("Using the specified stream config for all cameras.")

            stream_configs = stream_configs * len(serial_numbers)

        elif original_nb_serial_numbers == 0:
            utils.print_warning(
                "No cameras especified. Ignoring stream configs and using default stream configs "
                + "for each camera model instead."
            )

            stream_configs = [
                intel.RealSenseCamera.get_default_config(intel.RealSenseCamera.get_camera_model(sn))
                for sn in serial_numbers
            ]

        elif len(stream_configs) != len(serial_numbers):
            raise StreamConfigError(
                "The number of stream configs must be equal to the number of cameras."
            )

        # create list of camera instances
        self.cameras = [
            intel.RealSenseCamera(sn, st, sc, nm)
            for sn, st, sc, nm in zip(serial_numbers, stream_types, stream_configs, names)
        ]

    def __str__(self) -> str:
        string = ""

        string += f"\tOutput folder: {self.output_folder}\n"
        string += f"\tOperation time: {[(list(calendar.day_abbr)[i], op[0], op[1]) for i, op in enumerate(self.op_times)]}\n"  # pylint: disable=line-too-long
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


class Acquire(utils.Mode):
    """
    This class holds the tools to acquire data from the realsense cameras.

    Methods:
    --------
        - run: Runs the acquire mode (in a blocking way).

    """

    MAX_RESTART_ATTEMPTS = 3
    IDLE_THRESHOLD_MINUTES = 5

    # type hints

    __args: AcquireNamespace

    __cameras_storage: dict[str, str]

    __storage_thread: threading.Thread | None
    __acquisition_threads: dict[str, threading.Thread | None]

    __data_queues: dict[str, list[tuple[int, list[intel.Frame], str]]]
    __captured_frames: dict[str, int]
    __stored_frames: dict[str, int]

    __cameras_ready: dict[str, bool]
    __stop_acquiring: bool
    __terminate: bool
    __root_idle: threading.Event
    __acquire_threads_idle: threading.Event
    __storage_thread_idle: threading.Event
    __root_idling: bool
    __acquire_threads_idling: bool
    __storage_thread_idling: bool
    __nb_restart_attempts: int

    __capture_error: bool

    def __init__(self, args: AcquireNamespace) -> None:
        """
        Acquire constructor.

        Args:
        -----
            - args: The arguments for the acquire mode (matching the constructor of
                    AcquireNamespace).

        """

        self.__args = args

        self.__set_default_values(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))

    # set default values

    def __set_default_values(self, date: str) -> None:
        """
        Sets the default values of the threads manager.
        """

        # storage directories

        self.__cameras_storage = {
            camera.serial_number: os.path.abspath(
                os.path.join(self.__args.output_folder, camera.serial_number, date)
            )
            for camera in self.__args.cameras
        }

        # threads

        self.__storage_thread = None
        self.__acquisition_threads = {camera.serial_number: None for camera in self.__args.cameras}

        # data

        self.__data_queues = {camera.serial_number: [] for camera in self.__args.cameras}
        self.__captured_frames = {camera.serial_number: 0 for camera in self.__args.cameras}
        self.__stored_frames = {camera.serial_number: 0 for camera in self.__args.cameras}

        # control flags

        self.__cameras_ready = {camera.serial_number: False for camera in self.__args.cameras}
        self.__stop_acquiring = False
        self.__terminate = False
        self.__root_idle = threading.Event()
        self.__acquire_threads_idle = threading.Event()
        self.__storage_thread_idle = threading.Event()

        self.__nb_restart_attempts = 0

        self.__root_idle.set()
        self.__storage_thread_idle.set()

        self.__root_idling = False
        self.__acquire_threads_idling = False
        self.__storage_thread_idling = False

        # error flags

        self.__capture_error = False

    def __create_storage_folders(self) -> str:
        """
        Creates the output folders for the cameras.

        Returns:
        --------
        A string with the paths to the output folders.
        """

        string = ""

        for camera in self.__args.cameras:
            path = self.__cameras_storage[camera.serial_number]

            if not os.path.exists(path):
                os.makedirs(path)

            string += "\t" + path + "\n"

        return string.rstrip()

    # targets for the threads

    def __acquisition_target(self, camera: intel.RealSenseCamera) -> None:
        """
        Target function of the acquisition threads.
        """

        def get_start_hour(now: datetime.datetime) -> datetime.datetime:
            dt = now

            # current operation time
            if dt.hour < self.__args.op_times[now.weekday()][1]:
                ref_weekday = now.weekday()
            # next operation time
            else:
                ref_weekday = now.weekday() + 1 if now.weekday() < 6 else 0
                dt += datetime.timedelta(days=1)

            if self.__args.op_times[ref_weekday][0] == 0:
                dt += datetime.timedelta(days=-1)
                hour = 23
            else:
                hour = self.__args.op_times[ref_weekday][0] - 1

            return dt.replace(
                hour=hour,
                minute=60 - Acquire.IDLE_THRESHOLD_MINUTES,
                second=0,
            )

        def get_finish_hour(now: datetime.datetime) -> datetime.datetime:
            dt = now

            # current operation time
            if now.hour < self.__args.op_times[now.weekday()][1]:
                ref_weekday = now.weekday()
            # next operation time
            else:
                ref_weekday = now.weekday() + 1 if now.weekday() < 6 else 0
                dt += datetime.timedelta(days=1)

            if self.__args.op_times[ref_weekday][1] == 24:
                dt += datetime.timedelta(days=1)
                hour = 0
            else:
                hour = self.__args.op_times[ref_weekday][1]

            return dt.replace(
                hour=hour,
                minute=0,
                second=0,
            )

        logger = utils.Logger(f"{camera.name} Thread", _LOG_FILE)

        logger.info("Started.")

        camera.start()
        logger.info("Camera started.")

        # do calculation shere to avoid time drift between cameras
        now = datetime.datetime.now()

        start = get_start_hour(now)
        finish = get_finish_hour(now)

        # allow for some auto exposure to happen
        for _ in range(30):
            camera.capture()

        logger.info("Camera ready.")
        self.__cameras_ready[camera.serial_number] = True

        while not all(self.__cameras_ready.values()):
            continue

        try:
            while not self.__terminate and not self.__stop_acquiring:
                now = datetime.datetime.now()

                if not start <= now < finish:
                    start = get_start_hour(now)
                    finish = get_finish_hour(now)

                    idle_time = (start - now).total_seconds() + Acquire.IDLE_THRESHOLD_MINUTES * 60

                    logger.info("Idling for %s seconds.", datetime.timedelta(seconds=idle_time))

                    self.__storage_thread_idle.clear()
                    self.__root_idle.clear()

                    self.__root_idling = True
                    self.__storage_thread_idling = True
                    self.__acquire_threads_idling = True

                    self.__acquire_threads_idle.wait(idle_time)

                    self.__root_idle.set()
                    self.__storage_thread_idle.set()

                    self.__root_idling = False
                    self.__storage_thread_idling = False
                    self.__acquire_threads_idling = False

                    logger.info("Woke up!")

                    continue

                frame = camera.capture()

                self.__captured_frames[camera.serial_number] += 1

                self.__data_queues[camera.serial_number].append(
                    (
                        self.__captured_frames[camera.serial_number],
                        intel.Frame.create_instances(frame, camera.stream_type),
                        frame.get_timestamp(),  # type: ignore
                    )
                )
        except Exception:
            self.__capture_error = True

            logger.error("Error capturing frame.")

        finally:
            camera.stop()
            logger.info("Camera stopped.")

            logger.info("Stopped.")

    def __storage_target(self) -> None:
        """
        Target function of the storage thread.
        """

        logger = utils.Logger("Storage Thread", _LOG_FILE)

        logger.info("Started.")

        while not all(self.__cameras_ready.values()):
            continue

        while True:
            self.__storage_thread_idle.wait()

            has_data_to_store = all([len(queue) != 0 for queue in self.__data_queues.values()])

            if self.__terminate and not has_data_to_store:
                break

            elif has_data_to_store:
                for camera in self.__args.cameras:
                    i, frames, timestamp = self.__data_queues[camera.serial_number].pop(0)

                    for frame in frames:
                        frame.save_as_npy(
                            self.__cameras_storage[camera.serial_number],
                            str(i) + "_" + str(timestamp).replace(".", "_"),
                        )

                    self.__stored_frames[camera.serial_number] += 1

        logger.info("Stopped.")

    # main function of the class

    def run(self) -> None:
        """
        Runs the acquire mode (in a blocking way).
        """

        logger = utils.Logger("Root", _LOG_FILE)

        today = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info("\nStarting acquire mode (%s).", today)

        logger.info("Acquire mode started with following args:\n%s", self.__args)

        # perform reset of internal values

        self.__set_default_values(today)
        logger.info("Performed reset of internal values.")

        # create storage folders

        path = self.__create_storage_folders()
        logger.info("Defined storage folders:\n%s", path)

        # instantiate threads

        self.__storage_thread = threading.Thread(target=self.__storage_target)
        logger.info("Storage Thread created.")

        for camera in self.__args.cameras:
            thread = threading.Thread(target=self.__acquisition_target, args=(camera,))
            self.__acquisition_threads[camera.serial_number] = thread
            logger.info("%s Thread created.", camera.name)

        # start threads

        self.__storage_thread.start()

        for camera in self.__args.cameras:
            self.__acquisition_threads[camera.serial_number].start()  # type: ignore

        while not all(self.__cameras_ready.values()):
            continue

        utils.print_info("To stop data acquisition press Ctrl + C!\n")

        try:
            while True:
                self.__root_idle.wait()

                if self.__capture_error:
                    if self.__nb_restart_attempts == Acquire.MAX_RESTART_ATTEMPTS:
                        logger.info("Maximum number of restart attempts reached.")

                        break

                    self.__stop_acquiring = True
                    self.__storage_thread_idle.clear()
                    self.__storage_thread_idling = True

                    self.__capture_error = False
                    self.__nb_restart_attempts += 1

                    logger.info(
                        "Catched capture error. Restarting acquisition threads [%d].",
                        self.__nb_restart_attempts,
                    )

                    for camera in self.__args.cameras:
                        self.__acquisition_threads[camera.serial_number].join()  # type: ignore
                        self.__acquisition_threads[camera.serial_number] = None

                        logger.info("%s Thread deleted.", camera.name)

                    max_data_len = min(
                        [
                            len(self.__data_queues[camera.serial_number])
                            for camera in self.__args.cameras
                        ]
                    )

                    for camera in self.__args.cameras:
                        l = len(self.__data_queues[camera.serial_number])

                        logger.info(
                            "Droping %d frames from %s Thread.", l - max_data_len, camera.name
                        )

                        self.__data_queues[camera.serial_number] = self.__data_queues[
                            camera.serial_number
                        ][:max_data_len]

                    self.__cameras_ready = {
                        camera.serial_number: False for camera in self.__args.cameras
                    }
                    self.__stop_acquiring = False
                    self.__storage_thread_idle.set()
                    self.__storage_thread_idling = False

                    for camera in self.__args.cameras:
                        thread = threading.Thread(target=self.__acquisition_target, args=(camera,))
                        self.__acquisition_threads[camera.serial_number] = thread
                        logger.info("%s Thread created.", camera.name)

                    for camera in self.__args.cameras:
                        self.__acquisition_threads[camera.serial_number].start()  # type: ignore

        except KeyboardInterrupt:
            print("\rCtrl + C pressed\n")

            logger.info("Ctrl + C pressed.")

        self.__terminate = True

        if self.__root_idling:
            try:
                self.__root_idle.set()
            except Exception:
                pass

        if self.__storage_thread_idling:
            try:
                self.__storage_thread_idle.set()
            except Exception:
                pass

        if self.__acquire_threads_idling:
            try:
                self.__acquire_threads_idle.set()
            except Exception:
                pass

        logger.info("Stopping acquire mode...")

        for camera in self.__args.cameras:
            self.__acquisition_threads[camera.serial_number].join()  # type: ignore
            self.__acquisition_threads[camera.serial_number] = None

            logger.info("%s Thread deleted.", camera.name)

        if self.__storage_thread:
            self.__storage_thread.join()
            self.__storage_thread = None

            logger.info("Storage Thread deleted.")

        stats = "Acquire statistics:\n\n"

        for camera in self.__args.cameras:
            logger.info(
                "%s captured %d frames.",
                camera.name,
                self.__captured_frames[camera.serial_number],
            )

            logger.info(
                "%s stored %d frames.",
                camera.name,
                self.__stored_frames[camera.serial_number],
            )

            dropped = (
                self.__captured_frames[camera.serial_number]
                - self.__stored_frames[camera.serial_number]
            )

            logger.info(
                "%s dropped %d frames.",
                camera.name,
                dropped,
            )

            stats += "\t - " + camera.name + ":\n"

            stats += f"\t\t Captured {self.__captured_frames[camera.serial_number]} frames.\n"

            stats += f"\t\t Stored {self.__stored_frames[camera.serial_number]} frames.\n"

            stats += f"\t\t Dropped {dropped} frames.\n"

        utils.print_info(stats)

        logger.info("Acquire mode terminated.")

        utils.print_info("Acquire mode terminated!\n")

    @classmethod
    def print_logs(cls) -> None:
        """
        Prints the acquire mode logs.
        """

        with open(_LOG_FILE, encoding="utf-8") as f:
            file = f.read()

        session_logs = file.split("\n\n")

        for session_log in session_logs:
            lines = re.split(r"\n(?=\d{4}-\d{2}-\d{2})", session_log)

            if lines[0] == "":
                lines.pop(0)

            utils.print_log(f"Session {lines[0].split('(')[1][:-2]}")

            for line in lines:
                date, level, source, message = line.split(" - ", 3)
                utils.print_log(message, date, source, level)

            print()

    @classmethod
    def export_logs(cls, file: str) -> None:
        """
        Exports the acquire mode logs to a file.
        """

        with open(
            _LOG_FILE,
            "r",
            encoding="utf-8",
        ) as origin, open(
            file,
            "w",
            encoding="utf-8",
        ) as destination:
            destination.write("".join(origin.readlines()[1:]))


# pylint: disable=invalid-name
if __name__ == "__main__":
    raise RuntimeError("This file is not meant to be executed directly.")
