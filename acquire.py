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
import logging
import calendar
import threading
import keyboard
import pyrealsense2.pyrealsense2 as rs


import intel
import utils

_LOG_FILE = "logs/aquire.log"

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

    def __init__(  # pylint: disable=super-init-not-called
        self,
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


class AcquireThreadsManager:
    """
    This class manages the threads of the acquire mode.

    Attributes:
    -----------
        - MAX_RESTART_ATTEMPTS (int):
            The maximum number of restart attempts.
        - captured_frames (dict[str, int]):
            The number of captured frames for each camera.
        - stored_frames (dict[str, int]):
            The number of stored frames for each camera.

    Methods:
    --------
        - launch: Lauhes the acquire mode threads.
        - terminate: Stops the acquire mode threads.
    """

    MAX_RESTART_ATTEMPTS = 3

    # type hints

    __args: AcquireNamespace
    __storage_thread: threading.Thread | None
    __error_thread: threading.Thread | None
    __acquisition_threads: dict[str, threading.Thread | None]

    __data_queues: dict[str, list[intel.Frame]]

    __cameras_ready: dict[str, bool]
    __stop_acquiring: bool
    __pause_storage: bool
    __terminate: bool
    __nb_restart_attempts: int

    __capture_error: bool

    # class constructor

    def __init__(self, args: AcquireNamespace):
        self.__args = args
        self.__logger = utils.Logger("Threads Manager", _LOG_FILE)

        # threads

        self.__storage_thread = None
        self.__error_thread = None
        self.__acquisition_threads = {camera.serial_number: None for camera in self.__args.cameras}

        # data

        self.__data_queues = {camera.serial_number: [] for camera in self.__args.cameras}

        # control flags

        self.__cameras_ready = {camera.serial_number: False for camera in self.__args.cameras}
        self.__stop_acquiring = False
        self.__pause_storage = False
        self.__terminate = False
        self.__nb_restart_attempts = 0

        # error flags

        self.__capture_error = False

    # set default values

    def __reset_default_values(self) -> None:
        """
        Sets the default values of the threads manager.
        """

        # threads

        self.__storage_thread = None
        self.__error_thread = None
        self.__acquisition_threads = {camera.serial_number: None for camera in self.__args.cameras}

        # data

        self.__data_queues = {camera.serial_number: [] for camera in self.__args.cameras}

        # control flags

        self.__cameras_ready = {camera.serial_number: False for camera in self.__args.cameras}
        self.__stop_acquiring = False
        self.__pause_storage = False
        self.__terminate = False
        self.__nb_restart_attempts = 0

        # error flags

        self.__capture_error = False

    # start threads

    def __start_storage_thread(self) -> None:
        """
        Starts the storage thread.
        """
        if self.__storage_thread:
            raise AcquireError("The storage thread is already running.")

        self.__storage_thread = threading.Thread(target=self.__storage_target)
        self.__storage_thread.start()

        self.__logger.info("Storage Thread started.")

    def __start_error_thread(self) -> None:
        """
        Starts the error thread.
        """
        if self.__error_thread:
            raise AcquireError("The storage thread is already running.")

        self.__error_thread = threading.Thread(target=self.__error_target)
        self.__error_thread.start()

        self.__logger.info("Error Thread started.")

    def __start_acquisition_threads(self) -> None:
        """
        Starts the acquisition threads.
        """

        if any(self.__acquisition_threads.values()):
            raise AcquireError("The acquisition threads are already running.")

        for camera in self.__args.cameras:
            thread = threading.Thread(target=self.__acquisition_target, args=(camera,))
            self.__acquisition_threads[camera.serial_number] = thread
            self.__cameras_ready[camera.serial_number] = False
            thread.start()

            self.__logger.info("%s Thread started.", camera.name)

    # targets for the threads

    def __acquisition_target(self, camera: intel.Camera) -> None:
        """
        Target function of the acquisition threads.
        """

        logger = utils.Logger(f"{camera.name} Thread", _LOG_FILE)

        camera.start()
        logger.info("Camera started.")

        # allow for some auto exposure to happen
        for _ in range(30):
            camera.capture()

        self.__cameras_ready[camera.serial_number] = True
        logger.info("Camera ready.")

        while not all(self.__cameras_ready.values()):
            continue

        while not self.__terminate and not self.__stop_acquiring:
            try:
                frame = camera.capture()

                ply = rs.save_to_ply(str(frame.get_timestamp()).replace(".", "_") + ".ply")

                ply.set_option(rs.save_to_ply.option_ply_binary, False)
                ply.set_option(rs.save_to_ply.option_ply_normals, True)

                ply.process(frame)

                print("Frame captured.")
            except Exception as e:
                self.__capture_error = True
                logger.error("Error capturing frame.")
                raise e

            # self.__data_queues[camera.serial_number].append(frame)

        camera.stop()
        logger.info("Camera stopped.")

    def __storage_target(self) -> None:
        """
        Target function of the storage thread.
        """

        logger = utils.Logger("Storage Thread", _LOG_FILE)

        while True:
            has_data_to_store = all([len(queue) != 0 for queue in self.__data_queues.values()])

            if self.__terminate and not has_data_to_store:
                break

            elif has_data_to_store and not self.__pause_storage:
                for camera in self.__args.cameras:
                    frame = self.__data_queues[camera.serial_number].pop(0)
                    intel.Frame.create_instance(
                        frame,
                        os.path.join(
                            self.__args.output_folder,
                            camera.serial_number,
                            str(frame.get_timestamp()).replace(".", "_") + ".ply",  # type: ignore
                        ),
                        camera.stream_type,
                    ).save()
                    # logger.info("Frame from %s Thread stored.", camera.name)

    def __error_target(self) -> None:
        """
        Target function of the error thread.
        """

        logger = utils.Logger("Error Thread", _LOG_FILE)

        while (
            not self.__terminate
            or self.__storage_thread
            or any(self.__acquisition_threads.values())
        ):
            if not self.__terminate:
                if self.__nb_restart_attempts >= AcquireThreadsManager.MAX_RESTART_ATTEMPTS:
                    self.__terminate = True

                    if self.__storage_thread:
                        self.__storage_thread.join()
                        self.__storage_thread = None

                    for camera in self.__args.cameras:
                        thread = self.__acquisition_threads[camera.serial_number]
                        if thread:
                            thread.join()
                        self.__acquisition_threads[camera.serial_number] = None

                    self.__error_thread = None

                    self.__terminate = False

                    break

                if self.__capture_error:
                    logger.info("Catched error. Restarting acquisition threads...")

                    self.__capture_error = False

                    self.__stop_acquiring = True
                    self.__pause_storage = True

                    for camera in self.__args.cameras:
                        thread = self.__acquisition_threads[camera.serial_number]
                        if thread:
                            thread.join()
                        self.__acquisition_threads[camera.serial_number] = None

                    max_data_len = min(
                        [
                            len(self.__data_queues[camera.serial_number])
                            for camera in self.__args.cameras
                        ]
                    )

                    for camera in self.__args.cameras:
                        self.__data_queues[camera.serial_number] = self.__data_queues[
                            camera.serial_number
                        ][:max_data_len]

                    self.__stop_acquiring = False
                    self.__pause_storage = False

                    self.__start_acquisition_threads()
                    self.__nb_restart_attempts += 1

    # lauch and terminate threads

    def launch(self) -> None:
        """
        Lauhes the acquire mode threads.
        """

        self.__logger.info("Launching acquire mode threads.")

        self.__reset_default_values()

        # self.__start_error_thread()
        # self.__start_storage_thread()
        self.__start_acquisition_threads()

    def terminate(self) -> None:
        """
        Stops the acquire mode threads.
        """

        self.__terminate = True

        self.__logger.info("Terminating acquire mode threads.")

        for camera in self.__args.cameras:
            thread = self.__acquisition_threads[camera.serial_number]
            if thread:
                thread.join()
            self.__acquisition_threads[camera.serial_number] = None

        if self.__storage_thread:
            self.__storage_thread.join()
            self.__storage_thread = None

        if self.__error_thread:
            self.__error_thread.join()
            self.__error_thread = None

        self.__terminate = False

        self.__logger.info("Acquire mode threads terminated.")

    # class destructor

    def __del__(self) -> None:
        self.terminate()


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
        self.__args = args
        self.__thread_manager = AcquireThreadsManager(self.__args)
        self.__logger = utils.Logger("Root", _LOG_FILE)

        self.__logger.info("Acquire mode initialized:\n%s", self.__args)

    def __set_storage_folders(self) -> None:
        string = ""

        for camera in self.__args.cameras:
            path = os.path.join(self.__args.output_folder, camera.serial_number)

            if not os.path.exists(path):
                os.makedirs(path)
            string += "\t" + os.path.abspath(path) + "\n"

        self.__logger.info("Output folders:\n%s", string.rstrip())

    def run(self) -> None:
        """
        Runs the acquire mode.
        """

        self.__logger.info("Acquire mode terminated.")

        utils.print_info("Creating output folders...")
        self.__set_storage_folders()
        utils.print_success("Output folders created successfully!\n")

        self.__thread_manager.launch()

        print("To stop data acquisition press Ctrl + C.\n")

        try:
            while True:
                pass

        except KeyboardInterrupt:
            print("\rCtrl + C pressed.\n")

        self.__thread_manager.terminate()

        self.__logger.info("Acquire mode terminated.")


# pylint: disable=invalid-name
if __name__ == "__main__":
    raise RuntimeError("This file is not meant to be executed directly.")
