"""
This module holds the tools to acquire data from the realsense cameras.

Methods:
--------
- parse_acquire_yaml(file: str) -> dict:
    Parses a YAML file and returns its contents as a dictionary.

Classes:
--------
- AcquireNamespace: Holds the arguments for the acquire mode.
- Acquire: Holds the tools to acquire data from the realsense cameras.

Exceptions:
-----------
- AcquireNamespaceError: Exception raised when errors related to the acquire namespace occur.
- AcquireError: Exception raised when errors related to the acquire mode occur.

"""

# pylint: disable=pointless-string-statement
from __future__ import annotations

import os
import re
import calendar
import threading
import datetime
import yaml

from jsonschema import validate

from .. import intel
from .. import utils

_LOG_FILE = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../../logs/aquire.log")

# Exceptions
"""
███████╗██╗  ██╗ ██████╗███████╗██████╗ ████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
█████╗   ╚███╔╝ ██║     █████╗  ██████╔╝   ██║   ██║██║   ██║██╔██╗ ██║███████╗
██╔══╝   ██╔██╗ ██║     ██╔══╝  ██╔═══╝    ██║   ██║██║   ██║██║╚██╗██║╚════██║
███████╗██╔╝ ██╗╚██████╗███████╗██║        ██║   ██║╚██████╔╝██║ ╚████║███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
"""


class AcquireNamespaceError(utils.ModeNamespaceError):
    """
    Exception raised when errors related to the acquire namespace occur.
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


def parse_acquire_yaml(file: str) -> dict:
    """
    Parses a YAML file and returns its contents as a dictionary.

    Args:
    -----
        - file: The path to the YAML file to be parsed.

    Returns:
    --------
        The contents of the YAML file as a dictionary.
    """

    acquire_schema = {
        "type": "object",
        "properties": {
            "output_folder": {"type": "string"},
            "op_time": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "uniqueItems": True,
                "prefixItems": [
                    {"type": "integer", "minimum": 0, "maximum": 23},
                    {"type": "integer", "minimum": 1, "maximum": 24},
                ],
            },
            "op_times": {
                "type": "array",
                "minItems": 7,
                "maxItems": 7,
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "uniqueItems": True,
                    "prefixItems": [
                        {"type": "integer", "minimum": 0, "maximum": 23},
                        {"type": "integer", "minimum": 1, "maximum": 24},
                    ],
                },
            },
            "camera": {"anyOf": [{"type": "string"}, {"type": "number", "minimum": 0}]},
            "stream_type": {"enum": [type.name.lower() for type in intel.StreamType]},
            "cameras": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "sn": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "number", "minimum": 0},
                            ]
                        },
                        "name": {"type": "string", "minLength": 1},
                        "stream_type": {"enum": [type.name.lower() for type in intel.StreamType]},
                        "stream_config": {
                            "type": "object",
                            "patternProperties": {
                                f"^({'|'.join(list(filter(lambda v: '_n_' not in v, [type.name.lower() for type in intel.StreamType])))})$": {  # pylint: disable=line-too-long
                                    "type": "object",
                                    "properties": {
                                        "width": {"type": "integer", "minimum": 0},
                                        "height": {"type": "integer", "minimum": 0},
                                        "format": {
                                            "enum": [
                                                format.name.lower() for format in intel.StreamFormat
                                            ]
                                        },
                                        "fps": {"type": "number", "minimum": 0},
                                    },
                                    "required": ["width", "height", "format", "fps"],
                                    "additionalProperties": False,
                                },
                            },
                            "additionalProperties": False,
                        },
                    },
                    "required": ["sn", "stream_type", "stream_config"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["output_folder"],
        "allOf": [
            {"not": {"required": ["op_time", "op_times"]}},
            {"not": {"required": ["camera", "cameras"]}},
            {"not": {"required": ["stream_type", "cameras"]}},
        ],
        "additionalProperties": False,
    }

    try:
        with open(file, "r", encoding="utf-8") as f:
            args = yaml.safe_load(f)

            validate(args, acquire_schema)

            acquire_args = {}

            acquire_args["output_folder"] = args["output_folder"]

            if "op_time" in args:
                acquire_args["op_times"] = [args["op_time"]]
            elif "op_times" in args:
                acquire_args["op_times"] = args["op_times"]

            if "cameras" in args:
                acquire_args["serial_numbers"] = []
                acquire_args["names"] = []
                acquire_args["stream_types"] = []
                acquire_args["stream_configs"] = []

                for camera in args["cameras"]:
                    acquire_args["serial_numbers"].append(str(camera["sn"]))

                    acquire_args["names"].append(camera["name"] if "name" in camera else None)

                    acquire_args["stream_types"].append(
                        intel.StreamType[camera["stream_type"].upper()]
                    )

                    acquire_args["stream_configs"].append(
                        {
                            intel.StreamType[config.upper()]: intel.StreamConfig(
                                intel.StreamFormat[
                                    camera["stream_config"][config]["format"].upper()
                                ],
                                (
                                    camera["stream_config"][config]["width"],
                                    camera["stream_config"][config]["height"],
                                ),
                                camera["stream_config"][config]["fps"],
                            )
                            for config in camera["stream_config"]
                        }
                    )
            else:
                if "camera" in args:
                    acquire_args["serial_numbers"] = [args["camera"]]

                if "stream_type" in args:
                    acquire_args["stream_types"] = [intel.StreamType[args["stream_type"].upper()]]

            return acquire_args

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Specified YAML file not found ({file}).") from e
    except yaml.YAMLError as e:
        if hasattr(e, "problem_mark"):
            line = e.problem_mark.line + 1  # type: ignore
            raise SyntaxError(f"Wrong syntax on line {line} of the YAML file.") from e
        else:
            raise RuntimeError("Unknown problem on the specified YAML file.") from e


class AcquireNamespace(utils.ModeNamespace):
    """
    This class holds the arguments for the acquire mode.

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
            - AcquireNamespaceError: If any of the arguments is invalid.

        """

        # type definitions
        self.output_folder: str = ""
        self.op_times: list[tuple[int, int]] = []

        super().__init__(serial_numbers, stream_types, stream_configs, AcquireNamespaceError)

        # output_folder validations
        output_folder = output_folder.strip()

        if output_folder == "":
            raise AcquireNamespaceError("The output folder cannot be a empty string.")

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
            raise AcquireNamespaceError(
                "The specified operation time must be a list with 1 or 7 elements.",
            )

        for i, op_time in enumerate(op_times):
            if len(op_time) != 2:
                raise AcquireNamespaceError(
                    "The operation time must be expressed in the format "
                    + "(int, int). Ex: (8, 12) => 8:00 - 12:00.",
                    i,
                )

            if op_time[0] not in range(24):
                raise AcquireNamespaceError(
                    "The start hour must be a value between 0 and 23.",
                    i,
                )

            if op_time[1] not in range(1, 25):
                raise AcquireNamespaceError(
                    "The stop hour must be a value between 1 and 24.",
                    i,
                )

            if op_time[0] >= op_time[1]:
                raise AcquireNamespaceError(
                    "The start hour must be smaller than the stop hour.",
                    i,
                )

        self.op_times = op_times

    def __str__(self) -> str:
        string = ""

        string += f"\tOutput folder: {self.output_folder}\n"
        string += f"\tOperation time: {[(list(calendar.day_abbr)[i], op[0], op[1]) for i, op in enumerate(self.op_times)]}\n"  # pylint: disable=line-too-long

        string += super().__str__()

        return string.rstrip()


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

        self.__set_default_values()

    # set default values

    def __set_default_values(self) -> None:
        """
        Sets the default values of the threads manager.
        """

        # storage directories

        self.__cameras_storage = {
            camera.serial_number: os.path.abspath(
                os.path.join(self.__args.output_folder, camera.serial_number)
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
                            str(timestamp).replace(".", "_") + "_" + str(i),
                        )

                    self.__stored_frames[camera.serial_number] += 1

        logger.info("Stopped.")

    # main function of the class

    def run(self) -> None:
        """
        Runs the acquire mode (in a blocking way).
        """

        logger = utils.Logger("Root", _LOG_FILE)

        logger.info(
            "Starting acquire mode (%s).", datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        )

        logger.info("Acquire mode started with following args:\n%s", self.__args)

        # perform reset of internal values

        self.__set_default_values()
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

        logger.info("Acquire mode terminated.\n")

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
            if session_log == "":
                continue

            lines = re.split(r"\n(?=\d{4}-\d{2}-\d{2})", session_log)

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
