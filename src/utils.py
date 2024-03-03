"""
This module contains utility functions.

Functions:
----------
- parse_yaml(file) -> dict: Validates a YAML file at the given file path.
- print_info(message): Prints an info message.
- print_success(message): Prints a success message.
- print_warning(message): Prints a warning message.
- print_error(message): Prints an error message.
- get_user_confirmation(message) -> bool: Asks the user for confirmation.
"""

# pylint: disable=pointless-string-statement

from __future__ import annotations

import os
import logging
import copy
from typing import Type, TypeVar
from types import SimpleNamespace
from abc import ABC, abstractmethod
import yaml
from colorama import Fore, Style
import jsonschema

from . import intel


# Exceptions
"""
███████╗██╗  ██╗ ██████╗███████╗██████╗ ████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
█████╗   ╚███╔╝ ██║     █████╗  ██████╔╝   ██║   ██║██║   ██║██╔██╗ ██║███████╗
██╔══╝   ██╔██╗ ██║     ██╔══╝  ██╔═══╝    ██║   ██║██║   ██║██║╚██╗██║╚════██║
███████╗██╔╝ ██╗╚██████╗███████╗██║        ██║   ██║╚██████╔╝██║ ╚████║███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
"""


class ModeNamespaceError(Exception):
    """
    Exception raised when errors related to the serial number occur.
    """


# Classes
"""
 ██████╗██╗      █████╗ ███████╗███████╗███████╗███████╗
██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██╔════╝██╔════╝
██║     ██║     ███████║███████╗███████╗█████╗  ███████╗
██║     ██║     ██╔══██║╚════██║╚════██║██╔══╝  ╚════██║
╚██████╗███████╗██║  ██║███████║███████║███████╗███████║
 ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝
"""

MN = TypeVar("MN", bound="ModeNamespace")


class ModeNamespace(SimpleNamespace, ABC):
    """
    This class is intended to be used as a namespace for the modes.

    Class Attributes:
    -----------------
        - _EXCEPTION_CLS (Type[ModeNamespaceError]):
            The exception class to be raised if any of the arguments is invalid.
            It must be overridden by the subclasses.

    Attributes:
    -----------
        - cameras (list[intel.RealSenseCamera]):
            The list with the cameras to be used.
            It only exists if the _init_cameras method is called.

    Instance methods:
    -----------------
        - _init_cameras(
            serial_numbers: list[str] | None = None,
            stream_configs: list[list[intel.StreamConfig]] | None = None
        ) -> None:
            Initializes the cameras attribute.
            It must be overridden by the subclasses.
        - _str_cameras() -> str:
            Returns a string representation of the cameras attribute.

    Class methods:
    --------------
        - _get_cameras_yaml_schema() -> dict:
            Returns the schema of the cameras attribute.
        - _format_cameras_yaml_args(args: dict) -> dict:
            Formats the arguments parsed from the YAML file related to the cameras.
        - from_yaml(file: str) -> MN:
            Loads the mode from a YAML file and returns an instance of the subclass.

    Abstract class methods:
    -----------------------
        - _get_yaml_schema() -> dict:
            Returns the schema of the mode.
        - _format_yaml_args(args: dict) -> dict:
            Formats the arguments parsed from the YAML file.
    """

    # Class attributes

    _EXCEPTION_CLS: Type[ModeNamespaceError] = ModeNamespaceError

    # Instance attributes

    cameras: list[intel.RealSenseCamera]

    # Instance methods

    def _init_cameras(
        self,
        serial_numbers: list[str] | None = None,
        stream_configs: list[list[intel.StreamConfig]] | None = None,
        align_to: list[intel.StreamType | None] | None = None,
    ) -> None:
        """
        AcquireNamespace constructor.

        Args:
        -----
            - serial_numbers: The serial numbers of the cameras to be used.
            - stream_configs: The stream configs of the cameras to be used.
            - exception: The exception class to be raised if any of the arguments is invalid.

            Note: The number of stream configs must match the number of cameras.

        Raises:
        -------
            - Type[ModeNamespaceError]: If any of the arguments is invalid.

        """

        # serial_numbers validations
        if serial_numbers is None:
            print_warning("No cameras specified. Using all available cameras.")

            serial_numbers = intel.RealSenseCamera.get_available_cameras_serial_numbers()

            if len(serial_numbers) == 0:
                raise type(self)._EXCEPTION_CLS("No cameras available.")

        elif len(serial_numbers) == 0:
            raise type(self)._EXCEPTION_CLS("At least one serial number must be specified.")

        elif len(set(serial_numbers)) != len(serial_numbers):
            raise type(self)._EXCEPTION_CLS("There are repeated serial numbers.")

        # stream configs validations
        if stream_configs is None or len(stream_configs) == 0:
            print_warning("No stream configurations specified. Using default configurations.")

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

        elif len(stream_configs) != len(serial_numbers):
            raise type(self)._EXCEPTION_CLS(
                "The number of stream configs must match the number of cameras."
            )

        for camera_stream_configs in stream_configs:
            if len(camera_stream_configs) == 0:
                raise type(self)._EXCEPTION_CLS(
                    "At least one stream config must be specified for each camera."
                )

            if len(camera_stream_configs) != len(
                set(
                    camera_stream_config.type.name for camera_stream_config in camera_stream_configs
                )
            ):
                raise type(self)._EXCEPTION_CLS(
                    "There are repeated stream configs for the same camera."
                )

        # align_to validations
        if align_to is None or len(align_to) == 0:
            print_warning("No align to specified. Not aligning any stream.")

            align_to = [None for _ in range(len(serial_numbers))]

        elif len(align_to) != len(serial_numbers):
            raise type(self)._EXCEPTION_CLS(
                "The number of align to must match the number of cameras."
            )

        # create list of camera instances
        self.cameras = [
            intel.RealSenseCamera(sn.strip(), sc, al)
            for sn, sc, al in zip(serial_numbers, stream_configs, align_to)
        ]

    def _str_cameras(self) -> str:
        string = ""

        string += "\tCameras:"
        for camera in self.cameras:
            string += "\n"
            string += f"\t\tSerial number: {camera.serial_number}\n"
            string += "\t\tStream configs:\n"
            for stream_config in camera.stream_configs:
                string += f"\t\t\t{stream_config}\n"
            string += f"\t\tAlign to: {camera.align_to if camera.align_to is not None else 'Not aligned'}\n"

        return (string).rstrip()

    # Class methods

    @classmethod
    def _get_cameras_yaml_schema(cls) -> dict:
        """
        Return the schema of the cameras attribute.
        """

        return {
            "cameras": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "serial_number": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "number", "minimum": 0},
                                {"type": "null"},
                            ]
                        },
                        "stream_configs": {
                            "anyOf": [
                                {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "enum": [
                                                    s_type.name.lower()
                                                    for s_type in intel.StreamType
                                                ]
                                            },
                                            "format": {
                                                "enum": [
                                                    s_format.name.lower()
                                                    for s_format in intel.StreamFormat
                                                ]
                                            },
                                            "resolution": {
                                                "enum": [
                                                    s_resolution.name.lower()
                                                    for s_resolution in intel.StreamResolution
                                                ]
                                            },
                                            "fps": {
                                                "enum": [
                                                    s_fps.name.lower() for s_fps in intel.StreamFPS
                                                ]
                                            },
                                        },
                                        "required": ["type", "format", "resolution", "fps"],
                                        "additionalProperties": False,
                                    },
                                },
                                {"type": "null"},
                            ],
                        },
                        "align_to": {
                            "anyOf": [
                                {
                                    "type": "string",
                                    "enum": [s_type.name.lower() for s_type in intel.StreamType],
                                },
                                {"type": "null"},
                            ]
                        },
                    },
                    "required": ["serial_number", "stream_configs", "align_to"],
                    "additionalProperties": False,
                },
            },
        }

    @classmethod
    def _format_cameras_yaml_args(cls, args: dict) -> dict:
        """
        Formats the arguments parsed from the YAML file related to the cameras.
        """

        args = copy.deepcopy(args)

        if "cameras" not in args:
            return args

        args["serial_numbers"] = [str(camera["serial_number"]) for camera in args["cameras"]]

        if "None" in args["serial_numbers"]:
            args["serial_numbers"] = None

        args["stream_configs"] = [
            (
                [
                    intel.StreamConfig(
                        intel.StreamType[stream_config["type"].upper()],
                        intel.StreamFormat[stream_config["format"].upper()],
                        intel.StreamResolution[stream_config["resolution"].upper()],
                        intel.StreamFPS[stream_config["fps"].upper()],
                    )
                    for stream_config in camera["stream_configs"]
                ]
                if camera["stream_configs"] is not None
                else None
            )
            for camera in args["cameras"]
        ]

        if None in args["stream_configs"]:
            args["stream_configs"] = None

        args["align_to"] = [
            intel.StreamType[align_to.upper()] if align_to is not None else None
            for align_to in [camera["align_to"] for camera in args["cameras"]]
        ]

        del args["cameras"]

        return args

    @classmethod
    def from_yaml(cls: Type[MN], file: str) -> MN:
        """
        Loads the mode from a YAML file.

        Args:
        -----
            - file: The YAML file to be loaded.
        """

        try:
            with open(file, "r", encoding="utf-8") as f:
                args = yaml.safe_load(f)

                jsonschema.validate(args, cls._get_yaml_schema())

                args = cls._format_yaml_args(args)

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Specified YAML file not found ({file}).") from e
        except yaml.YAMLError as e:
            if hasattr(e, "problem_mark"):
                line = e.problem_mark.line + 1  # type: ignore
                raise SyntaxError(f"Wrong syntax on line {line} of the YAML file.") from e
            else:
                raise RuntimeError("Unknown problem on the specified YAML file.") from e
        except jsonschema.ValidationError as e:
            raise cls._EXCEPTION_CLS(str(e).split("\n", maxsplit=1)[0]) from e

        try:
            return cls(**args)
        except Exception as e:
            raise cls._EXCEPTION_CLS(e) from e

    # Abstract class methods

    @classmethod
    @abstractmethod
    def _get_yaml_schema(cls) -> dict:
        """
        Return the schema of the mode.
        """

    @classmethod
    @abstractmethod
    def _format_yaml_args(cls, args: dict) -> dict:
        """
        Formats the arguments parsed from the YAML file.
        """


class Mode(ABC):
    """
    Abstract class for modes.

    Subclasses must implement the following methods:
        - run(): Runs the mode.
        - stop(): Stops the mode.
    """

    _LOG_FILE: str

    @abstractmethod
    def run(self) -> None:
        """
        Runs the mode.
        """

    @classmethod
    def logs(cls, file: str) -> None:
        """
        Prints or exports the logs of the mode.

        Args:
        -----
            - file: The file to print the logs to. If None, the logs are printed to the console.
        """

        # print to console
        if file:
            print_info(f"Exporting logs to {file}...")
            print()

            with open(
                cls._LOG_FILE,
                "r",
                encoding="utf-8",
            ) as origin, open(
                file,
                "w",
                encoding="utf-8",
            ) as destination:
                destination.write("".join(origin.readlines()))

            print_success("Logs exported!")
            print()

        # export to file
        else:
            with open(
                cls._LOG_FILE,
                "r",
                encoding="utf-8",
            ) as f:
                file_lines = f.readlines()

                for line in file_lines:
                    if line[0].isdigit():
                        line = line.split(" - ", 3)
                        print(
                            Fore.GREEN
                            + line[0]
                            + " - "
                            + Fore.LIGHTMAGENTA_EX
                            + line[1]
                            + Style.RESET_ALL
                            + " - "
                            + line[2],
                            end="",
                        )
                    else:
                        print(line, end="")

                # session_logs = file.split("\n\n")

                # for session_log in session_logs:
                #     if session_log == "":
                #         continue

                #     lines = re.split(r"\n(?=\d{4}-\d{2}-\d{2})", session_log)

                #     utils.print_log(f"Session {lines[0].split('(')[1][:-2]}")

                #     for line in lines:
                #         date, level, source, message = line.split(" - ", 3)
                #         utils.print_log(message, date, source, level)


class Logger(logging.Logger):
    """
    Logger class.
    """

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    level = logging.INFO

    def __init__(self, name: str, file: str) -> None:
        super().__init__(name, Logger.level)

        os.makedirs(os.path.dirname(file), exist_ok=True)

        file_handler = logging.FileHandler(file)
        file_handler.setLevel(Logger.level)
        file_handler.setFormatter(Logger.formatter)

        self.addHandler(file_handler)


# Methods
"""
███╗   ███╗███████╗████████╗██╗  ██╗ ██████╗ ██████╗ ███████╗
████╗ ████║██╔════╝╚══██╔══╝██║  ██║██╔═══██╗██╔══██╗██╔════╝
██╔████╔██║█████╗     ██║   ███████║██║   ██║██║  ██║███████╗
██║╚██╔╝██║██╔══╝     ██║   ██╔══██║██║   ██║██║  ██║╚════██║
██║ ╚═╝ ██║███████╗   ██║   ██║  ██║╚██████╔╝██████╔╝███████║
╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
"""


def print_info(message: str) -> None:
    """
    Prints an info message.

    Args:
    -----
        - message: The info message to be printed.
    """
    print(f"{Fore.LIGHTCYAN_EX + Style.BRIGHT}Info:{Style.RESET_ALL} {message}")


def print_success(message: str) -> None:
    """
    Prints a success message.

    Args:
    -----
        - message: The success message to be printed.
    """
    print(f"{Fore.LIGHTGREEN_EX + Style.BRIGHT}Success:{Style.RESET_ALL} {message}")


def print_warning(message: str) -> None:
    """
    Prints a warning message.

    Args:
    -----
        - message: The warning message to be printed.
    """
    print(f"{Fore.LIGHTYELLOW_EX + Style.BRIGHT}Warning:{Style.RESET_ALL} {message}")


def print_error(message: str) -> None:
    """
    Prints an error message.

    Args:
    -----
        - message: The error message to be printed.
    """
    print(f"{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} {message}")


def get_user_confirmation(message: str) -> bool:
    """
    Asks the user for confirmation.
    """
    while True:
        response = input(f"{message} (y/n): ")
        if response in ["y", "Y", "yes", "Yes", "YES"]:
            return True
        elif response in ["n", "N", "no", "No", "NO"]:
            return False
        else:
            print_warning("Invalid response. Please enter y or n.")
            print()
