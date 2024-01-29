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
from datetime import datetime, timedelta

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

    # type hints
    output_folder: str
    op_times: list[tuple[int, int]]

    def __init__(
        self,
        output_folder: str,
        op_times: list[tuple[int, int]] | None = None,
        serial_numbers: list[str] | None = None,
        stream_configs: list[list[intel.StreamConfig]] | None = None,
    ):
        """
        AcquireNamespace constructor.

        Args:
        -----
            - output_folder: The path to the output folder.
            - op_times: The time interval in which the cameras will be capturing data
              for each day of the week (Monday to Sunday).
                - It can be None, in which case the cameras will be capturing data all the time.
                - Or it can be a list with 7 elements, one for each day of the week.
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

        if serial_numbers is None:
            utils.print_warning("No cameras specified. Using all available cameras.")

            serial_numbers = intel.RealSenseCamera.get_available_cameras_serial_numbers()

            if len(serial_numbers) == 0:
                raise AcquireNamespaceError("No cameras available.")

        if stream_configs is None:
            utils.print_warning("No stream configurations specified. Using default configurations.")

            stream_configs = [
                [
                    intel.StreamConfig(
                        intel.StreamType.DEPTH,
                        intel.StreamFormat.Z16,
                        intel.StreamResolution.X640_Y480,
                        intel.StreamFPS.FPS_30,
                    )
                ]
                for _ in range(len(serial_numbers))
            ]

        super().__init__(serial_numbers, stream_configs, AcquireNamespaceError)

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

    @classmethod
    def get_specific_yaml_schema(cls) -> dict:
        return {
            "output_folder": {"type": "string"},
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

        serial_number = camera.serial_number
        frames_queue = camera.frames_queue
        folder = self._storage_folders[serial_number]

        self._stream_signals.run.wait()

        while not self._stream_signals.stop.is_set():
            if frames_queue.empty():
                self._stream_signals.run.wait()

            try:
                frames = frames_queue.get(timeout=5)

                for frame in frames:
                    threading.Thread(target=self._storage_target, args=(frame, folder)).start()

                self._stored_frames[serial_number] += 1
            except Exception:
                continue

        while not frames_queue.empty():
            try:
                frames = frames_queue.get(timeout=5)

                for frame in frames:
                    threading.Thread(target=self._storage_target, args=(frame, folder)).start()

                self._stored_frames[serial_number] += 1
            except Exception:
                continue

    def _op_time_handler_target(self) -> None:
        """
        Target function of the operation time handler thread.
        """

        def get_start_hour(now: datetime) -> datetime:
            # current operation time
            if now.hour < self._args.op_times[now.weekday()][1]:
                ref_weekday = now.weekday()
            # next operation time
            else:
                ref_weekday = now.weekday() + 1 if now.weekday() < 6 else 0
                now += timedelta(days=1)

            return now.replace(
                hour=self._args.op_times[ref_weekday][0],
                minute=0,
                second=0,
            )

        def get_finish_hour(now: datetime) -> datetime:
            # current operation time
            if now.hour < self._args.op_times[now.weekday()][1]:
                ref_weekday = now.weekday()
            # next operation time
            else:
                ref_weekday = now.weekday() + 1 if now.weekday() < 6 else 0
                now += timedelta(days=1)

            return now.replace(
                hour=self._args.op_times[ref_weekday][1] - 1,
                minute=59,
                second=59,
            )

        while not self._stream_signals.stop.is_set():
            now = datetime.now()
            start = get_start_hour(datetime.now())
            finish = get_finish_hour(datetime.now())

            # idle stream until next op_time
            if not start <= now < finish:
                idle_time = (start - now).total_seconds()

                self._logger.info("Pausing stream for %s seconds.", str(idle_time / 60))

                self._stream_signals.run.clear()

                self._op_time_signal.wait(idle_time)

                self._stream_signals.run.set()

                self._logger.info("Restarting stream.")

            # idle op time check until end of current op time
            else:
                idle_time = (finish - now).total_seconds()

                self._op_time_signal.wait(idle_time)

    # main function of the class

    def run(self) -> None:
        """
        Runs the acquire mode (in a blocking way).
        """

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

        try:
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
