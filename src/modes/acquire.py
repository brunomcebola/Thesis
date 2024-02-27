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
import calendar
import threading
from datetime import datetime

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


def convert_weekday_time_to_seconds(weekday: str, time: str) -> int:
    """
    Convert a weekday and a time to seconds.

    It is mandatory to pass a the hours and minutes in the time. The seconds are optional.

    Ex: (Mon, 00:00:00) -> 0
    """

    day = [
        index
        for index in range(len(list(calendar.day_abbr)))
        if list(calendar.day_abbr)[index] == weekday.capitalize()
    ][0]

    split_time = time.split(":")

    hour = int(split_time[0])
    minute = int(split_time[1])
    second = int(split_time[2]) if len(split_time) == 3 else 0

    return (3600 * (24 * day + hour)) + (minute * 60) + second


def convert_seconds_interval_to_string(interval: tuple[int, int]):
    """
    Convert a time interval in seconds to a string.

    Ex: [0, 3600] -> Mon, 00h00 - Mon, 01h00
    """

    start_day = list(calendar.day_abbr)[interval[0] // 86400]
    start_hour = interval[0] // 3600 % 24
    start_minute = interval[0] // 60 % 60

    stop_day = list(calendar.day_abbr)[interval[1] // 86400]
    stop_hour = interval[1] // 3600 % 24
    stop_minute = interval[1] // 60 % 60

    return f"({start_day}, {start_hour:02d}h{start_minute:02d} - {stop_day}, {stop_hour:02d}h{stop_minute:02d})"  # pylint: disable=line-too-long


class AcquireNamespace(utils.ModeNamespace):
    """
    This class holds the arguments for the acquire mode.

    Attributes:
    -----------
        - output_folder (str):
            The path to the output folder.
        - op_times (list[tuple[int, int]] | None):
            The time intervals in which the cameras will be capturing data.
        - cameras (list[intel.RealSenseCamera]):
            The list with the cameras to be used.
    """

    # type hints
    output_folder: str
    op_times: list[tuple[int, int]] | None

    def __init__(
        self,
        output_folder: str,
        op_times: list[dict[str, str]] | None = None,
        serial_numbers: list[str] | None = None,
        stream_configs: list[list[intel.StreamConfig]] | None = None,
        **kwargs,
    ):
        """
        AcquireNamespace constructor.

        Args:
        -----
            - output_folder: The path to the output folder.
            - op_times: The time intervals in which the cameras will be capturing data.
                - It can be None, in which case the cameras will be capturing data all the time.
                - Or it can be a list of dicts specifying time frames.
            - serial_numbers: The serial numbers of the cameras to be used.
                - It can be None, in which case all the connected cameras will be used.
                - Or it can be a list with the serial numbers of the cameras to be used.
            - stream_configs: The stream configurations of the cameras to be used.
                - It can be None, in which case the default configurations will be used.
                - Or it can be a list with the stream configurations of the cameras to be used.

        Raises:
        -------
            - AcquireNamespaceError: If any of the arguments is invalid.

        """

        del kwargs

        super().__init__(serial_numbers, stream_configs, AcquireNamespaceError)

        # output_folder validations
        if output_folder is None:
            raise AcquireNamespaceError("The output folder must be specified.")

        output_folder = output_folder.strip()

        if output_folder == "":
            raise AcquireNamespaceError("The output folder cannot be a empty string.")

        self.output_folder = os.path.abspath(output_folder)

        # op_times validations
        if op_times is None:
            utils.print_warning(
                "No operation time specified. Cameras will be capturing data all the time."
            )

            self.op_times = None

        else:
            if len(op_times) == 0:
                raise AcquireNamespaceError(
                    "At least one operation time must be specified.",
                )

            if (
                len(op_times) == 1
                and op_times[0]["start_day"] == op_times[0]["stop_day"]
                and op_times[0]["start_time"] == op_times[0]["stop_time"]
            ):
                self.op_times = None

            else:
                for op_time in op_times:
                    if op_time["start_day"].capitalize() not in list(calendar.day_abbr):
                        raise AcquireNamespaceError(
                            "The start day must be one of the following: mon, tue, wed, thu, fri, sat, sun."  # pylint: disable=line-too-long
                        )

                    if op_time["stop_day"].lower().capitalize() not in list(calendar.day_abbr):
                        raise AcquireNamespaceError(
                            "The stop day must be one of the following: mon, tue, wed, thu, fri, sat, sun."  # pylint: disable=line-too-long
                        )

                    if int(op_time["start_time"].split(":")[0]) not in range(24):
                        raise AcquireNamespaceError(
                            "The start hour must be a value between 0 and 23.",
                        )

                    if int(op_time["stop_time"].split(":")[0]) not in range(24):
                        raise AcquireNamespaceError(
                            "The stop hour must be a value between 0 and 23.",
                        )

                    if int(op_time["start_time"].split(":")[1]) not in range(60):
                        raise AcquireNamespaceError(
                            "The start minute must be a value between 0 and 59.",
                        )

                    if int(op_time["stop_time"].split(":")[1]) not in range(60):
                        raise AcquireNamespaceError(
                            "The stop minute must be a value between 0 and 59.",
                        )

                converted_op_times = sorted(
                    [
                        (
                            convert_weekday_time_to_seconds(
                                op_time["start_day"], op_time["start_time"]
                            ),
                            convert_weekday_time_to_seconds(
                                op_time["stop_day"], op_time["stop_time"]
                            ),
                        )
                        for op_time in op_times
                    ],
                    key=lambda x: (x[0], x[1]),
                )

                for idx, op_tinterval in enumerate(converted_op_times):
                    current_start_time = op_tinterval[0]
                    current_stop_time = op_tinterval[1]

                    if current_start_time >= current_stop_time:
                        raise AcquireNamespaceError(
                            "The start time must be before the stop time.",
                        )

                    if idx % len(converted_op_times):
                        next_start_time = converted_op_times[idx + 1][0]

                        # Check if current end time is after next start time
                        if current_stop_time > next_start_time:
                            raise AcquireNamespaceError(
                                "The operation times must not overlap.",
                            )

                joint_op_times = [converted_op_times[0]]

                for i in range(1, len(converted_op_times)):
                    if joint_op_times[-1][1] == converted_op_times[i][0]:
                        joint_op_times[-1] = (joint_op_times[-1][0], converted_op_times[i][1])
                    else:
                        joint_op_times.append(converted_op_times[i])

                self.op_times = joint_op_times

    def __str__(self) -> str:
        string = ""

        string += f"\tOutput folder: {self.output_folder}\n"

        if self.op_times is not None:
            string += f"\tOperation time: {', '.join([convert_seconds_interval_to_string(op_time) for op_time in self.op_times])}\n"  # pylint: disable=line-too-long
        else:
            string += "\tOperation time: Allways\n"

        string += super().__str__()

        return string.rstrip()

    @classmethod
    def from_yaml(cls, file: str) -> AcquireNamespace:
        try:
            return cls(**cls._get_yaml_args(file))
        except Exception as e:
            raise AcquireNamespaceError(str(e).split("\n", maxsplit=1)[0]) from e

    @classmethod
    def _get_specific_yaml_schema(cls) -> dict:
        return {
            "output_folder": {"type": "string"},
            "op_times": {
                "anyOf": [
                    {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "start_day": {
                                    "enum": [day.lower() for day in list(calendar.day_abbr)]
                                    + [day.capitalize() for day in list(calendar.day_abbr)]
                                },
                                "start_time": {
                                    "type": "string",
                                    "pattern": r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
                                },
                                "stop_day": {
                                    "enum": [day.lower() for day in list(calendar.day_abbr)]
                                    + [day.capitalize() for day in list(calendar.day_abbr)]
                                },
                                "stop_time": {
                                    "type": "string",
                                    "pattern": r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
                                },
                            },
                            "required": ["start_day", "start_time", "stop_day", "stop_time"],
                            "additionalProperties": False,
                        },
                    },
                    {"type": "null"},
                ],
            },
        }


class Acquire(utils.Mode):
    """
    This class holds the tools to acquire data from the realsense cameras.

    Methods:
    --------
        - run: Runs the acquire mode (in a blocking way).

    """

    # type hints

    _args: AcquireNamespace

    # operation time

    _op_time_handler_thread: threading.Thread | None

    # storage

    _storage_handler_threads: dict[str, threading.Thread | None]  # serial_number: thread
    _storage_folders: dict[str, str]  # serial_number: folder
    _stored_frames: dict[str, int]  # serial_number: nb_frames

    # control flags

    _stream_signals: intel.StreamSignals
    _op_time_signal: threading.Event

    # logger

    _logger: utils.Logger

    def __init__(self, args: AcquireNamespace) -> None:
        """
        Acquire constructor.

        Args:
        -----
            - args: The arguments for the acquire mode (matching the constructor of
                    AcquireNamespace).

        """

        self._args = args

        self._logger = utils.Logger("", _LOG_FILE)

        self._set_default_values()

    # set default values

    def _set_default_values(self) -> None:
        """
        Sets the default values of the threads manager.
        """

        # operation time

        self._op_time_handler_thread = None

        # storage

        self._storage_handler_threads = {}
        self._storage_folders = {}
        self._stored_frames = {}

        for camera in self._args.cameras:
            self._storage_handler_threads[camera.serial_number] = None
            self._storage_folders[camera.serial_number] = os.path.abspath(
                os.path.join(self._args.output_folder, camera.serial_number)
            )
            self._stored_frames[camera.serial_number] = 0

        # control flags

        self._stream_signals = intel.StreamSignals()
        self._op_time_signal = threading.Event()

    def _create_storage_folders(self) -> str:
        """
        Creates the output folders for the cameras.

        Returns:
        --------
        A string with the paths to the output folders.
        """

        string = ""

        for camera in self._args.cameras:
            path = self._storage_folders[camera.serial_number]

            if not os.path.exists(path):
                os.makedirs(path)

            string += "\t" + path + "\n"

        return string.rstrip()

    # targets for the threads

    def _storage_target(self, frame: intel.Frame, folder: str) -> None:
        """
        Target function of the storage thread.
        """
        frame.save(folder)

    def _storage_handler_target(self, camera: intel.RealSenseCamera) -> None:
        """
        Target function of the storage handler thread.
        """

        self._stream_signals.run.wait()

        serial_number = camera.serial_number
        frames_queue = camera.frames_queue
        folder = self._storage_folders[serial_number]

        while not self._stream_signals.stop.is_set():
            if frames_queue.empty():  # type: ignore
                self._stream_signals.run.wait()

            try:
                frames = frames_queue.get(timeout=5)  # type: ignore

                for frame in frames:
                    threading.Thread(target=self._storage_target, args=(frame, folder)).start()

                self._stored_frames[serial_number] += 1
            except Exception:  # pylint: disable=broad-except
                continue

        while not frames_queue.empty():  # type: ignore
            try:
                frames = frames_queue.get(timeout=5)  # type: ignore

                for frame in frames:
                    threading.Thread(target=self._storage_target, args=(frame, folder)).start()

                self._stored_frames[serial_number] += 1
            except Exception:  # pylint: disable=broad-except
                continue

    def _op_time_handler_target(self) -> None:
        """
        Target function of the operation time handler thread.
        """

        if self._args.op_times is None:
            return

        self._stream_signals.run.wait()

        # determine the current interval

        now = datetime.now()

        now = convert_weekday_time_to_seconds(now.strftime("%a"), now.strftime("%H:%M:%S"))

        interval = 0

        in_interval = False

        for idx, op_time in enumerate(self._args.op_times):
            if now < op_time[1]:
                interval = idx

                if now > op_time[0]:
                    in_interval = True

                break

        # main looop

        while not self._stream_signals.stop.is_set():

            now = datetime.now()

            now = convert_weekday_time_to_seconds(now.strftime("%a"), now.strftime("%H:%M:%S"))

            idle_time = self._args.op_times[interval][in_interval] - now

            # if the idle time is negative, it means that the next interval is in the next week
            if idle_time < 0:
                idle_time += 604800

            if in_interval:
                self._logger.info("Starting stream.")

                self._stream_signals.run.set()

                interval = (interval + 1) % len(self._args.op_times)

            else:
                self._logger.info("Pausing stream for %d seconds.", idle_time)

                self._stream_signals.run.clear()

            self._op_time_signal.wait(idle_time)

            if self._stream_signals.stop.is_set():
                break

            in_interval = not in_interval

    # main function of the class

    def run(self) -> None:
        """
        Runs the acquire mode (in a blocking way).
        """
        try:
            self._logger.info(
                "New acquisition session (%s) started with:\n%s",
                datetime.now().strftime("%Y%m%d_%H%M%S"),
                self._args,
            )

            utils.print_info("New acquisition session started!\n")

            # perform reset of internal values

            self._set_default_values()
            self._logger.info("Performed reset of internal values.")

            # create storage folders

            path = self._create_storage_folders()
            self._logger.info("Defined storage folders:\n%s", path)

            # Launch all threads

            if self._args.op_times is not None:
                self._op_time_handler_thread = threading.Thread(
                    target=self._op_time_handler_target,
                )
                self._op_time_handler_thread.start()

            for camera in self._args.cameras:
                # start camera stream
                camera.start_streaming(self._stream_signals)

                # start storage handler thread for the camera
                self._storage_handler_threads[camera.serial_number] = threading.Thread(
                    target=self._storage_handler_target, args=(camera,)
                )
                self._storage_handler_threads[camera.serial_number].start()  # type: ignore

            self._stream_signals.run.set()

            # main loop

            utils.print_info("To stop data acquisition press Ctrl + C!\n")

            self._stream_signals.error.wait()

            utils.print_error("Error in one of the camera streams.")

            self._logger.error("Error in one of the camera streams.")

        except KeyboardInterrupt:
            utils.print_info("\rCtrl + C pressed\n")

            self._logger.info("Ctrl + C pressed.")

        self._stream_signals.stop.set()
        self._stream_signals.run.set()
        self._op_time_signal.set()

        for camera in self._args.cameras:
            camera.stop_streaming()

            if self._storage_handler_threads[camera.serial_number] is not None:
                self._storage_handler_threads[camera.serial_number].join()  # type: ignore
                self._storage_handler_threads[camera.serial_number] = None

        stats = "Acquire statistics:\n\n"

        for camera in self._args.cameras:
            self._logger.info(
                "%s captured %d frames.",
                camera.serial_number,
                camera.frames_streamed,
            )

            self._logger.info(
                "%s stored %d frames.",
                camera.serial_number,
                self._stored_frames[camera.serial_number],
            )

            dropped = camera.frames_streamed - self._stored_frames[camera.serial_number]

            self._logger.info(
                "%s dropped %d frames.",
                camera.serial_number,
                dropped,
            )

            stats += "\t - " + camera.serial_number + ":\n"
            stats += f"\t\t Captured {camera.frames_streamed} frames.\n"
            stats += f"\t\t Stored {self._stored_frames[camera.serial_number]} frames.\n"
            stats += f"\t\t Dropped {dropped} frames.\n"

        utils.print_info(stats)

        self._logger.info("Acquisition session finished.\n")

        utils.print_info("Acquire mode terminated!\n")


# pylint: disable=invalid-name
if __name__ == "__main__":
    raise RuntimeError("This file is not meant to be executed directly.")
