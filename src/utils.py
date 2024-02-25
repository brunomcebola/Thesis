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
from typing import Type
from types import SimpleNamespace
from abc import ABC, abstractmethod
import yaml
from colorama import Fore, Style
from jsonschema import validate

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


class ModeNamespace(SimpleNamespace, ABC):
    """
    This class is intended to be used as a namespace for the modes.

    Attributes:
    -----------
        - cameras (list[intel.RealSenseCamera]):
            The list with the cameras to be used.

    Class methods:
    --------------
        - from_yaml(file: str):
            Loads the namespace from a YAML file.
    """

    # type hints
    cameras: list[intel.RealSenseCamera]

    # Instance constructor

    def __init__(
        self,
        serial_numbers: list[str],
        stream_configs: list[list[intel.StreamConfig]],
        exception: Type[ModeNamespaceError] = ModeNamespaceError,
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
        if len(serial_numbers) == 0:
            raise exception("At least one serial number must be specified.")

        if len(set(serial_numbers)) != len(serial_numbers):
            raise exception("There are repeated serial numbers.")

        # stream configs validations
        if len(stream_configs) != len(serial_numbers):
            raise exception("The number of stream configs must match the number of cameras.")

        for camera_stream_configs in stream_configs:
            if len(camera_stream_configs) == 0:
                raise exception("At least one stream config must be specified for each camera.")

            if len(camera_stream_configs) != len(
                set(
                    camera_stream_config.type.name for camera_stream_config in camera_stream_configs
                )
            ):
                raise exception("There are repeated stream configs for the same camera.")

        # create list of camera instances
        self.cameras = [
            intel.RealSenseCamera(sn.strip(), sc) for sn, sc in zip(serial_numbers, stream_configs)
        ]

    # Instance special methods

    def __str__(self) -> str:
        string = ""

        string += "\tCameras:"
        for camera in self.cameras:
            string += "\n"
            string += f"\t\tSerial number: {camera.serial_number}\n"
            string += "\t\tStream configs:\n"
            for stream_config in camera.stream_configs:
                string += f"\t\t\t{stream_config}\n"

        return (string).rstrip()

    # Class methods

    @classmethod
    def _get_yaml_args(cls, file: str) -> dict:
        """
        Loads the mode from a YAML file.

        Args:
        -----
            - file: The YAML file to be loaded.
        """
        try:
            with open(file, "r", encoding="utf-8") as f:
                args = yaml.safe_load(f)

                validate(args, cls._get_full_yaml_schema())

                args["serial_numbers"] = [
                    str(camera["serial_number"]) for camera in args["cameras"]
                ]

                args["stream_configs"] = [
                    [
                        intel.StreamConfig(
                            intel.StreamType[stream_config["type"].upper()],
                            intel.StreamFormat[stream_config["format"].upper()],
                            intel.StreamResolution[stream_config["resolution"].upper()],
                            intel.StreamFPS[stream_config["fps"].upper()],
                        )
                        for stream_config in camera["stream_configs"]
                    ]
                    for camera in args["cameras"]
                ]

                del args["cameras"]

                return args

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Specified YAML file not found ({file}).") from e
        except yaml.YAMLError as e:
            if hasattr(e, "problem_mark"):
                line = e.problem_mark.line + 1  # type: ignore
                raise SyntaxError(f"Wrong syntax on line {line} of the YAML file.") from e
            else:
                raise RuntimeError("Unknown problem on the specified YAML file.") from e

    @classmethod
    def _get_full_yaml_schema(cls) -> dict:
        """
        Returns the schema of the mode.
        """
        schema = {
            "type": "object",
            "properties": cls._get_specific_yaml_schema()
            | {
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
                                ]
                            },
                            "stream_configs": {
                                "type": "array",
                                "minItems": 1,
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "enum": [
                                                s_type.name.lower() for s_type in intel.StreamType
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
                        },
                        "required": ["serial_number", "stream_configs"],
                        "additionalProperties": False,
                    },
                },
            },
            "additionalProperties": False,
        }

        schema["required"] = list(schema["properties"].keys())

        return schema

    @classmethod
    @abstractmethod
    def _get_specific_yaml_schema(cls) -> dict:
        """
        Returns the schema of the mode.
        """

    @classmethod
    @abstractmethod
    def from_yaml(cls, file: str) -> ModeNamespace:
        """
        Loads the mode from a YAML file.

        Args:
        -----
            - file: The YAML file to be loaded.
        """


class Mode(ABC):
    """
    Abstract class for modes.

    Subclasses must implement the following methods:
        - run(): Runs the mode.
        - stop(): Stops the mode.
    """

    _LOG_FILE: str | None = None

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

        if cls._LOG_FILE is None:
            raise ValueError("The mode has no logs to print.")

        # print to console
        if file == "":
            with open(
                cls._LOG_FILE,
                "r",
                encoding="utf-8",
            ) as f:
                file_lines = f.readlines()

                for line in file_lines[1:]:
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

        # export to file
        else:
            with open(
                cls._LOG_FILE,
                "r",
                encoding="utf-8",
            ) as origin, open(
                file,
                "w",
                encoding="utf-8",
            ) as destination:
                destination.write("".join(origin.readlines()[1:]))


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


def print_log(
    message: str, date: str | None = None, source: str | None = None, level: str | None = None
) -> None:
    """
    Prints a log message.

    Args:
    -----
        - message: The log message to be printed.
    """

    if date is None:
        print(f"{Fore.LIGHTGREEN_EX + Style.BRIGHT}{message}{Style.RESET_ALL}")
        print()

    else:
        text = Fore.GREEN + date + Style.RESET_ALL + " - "
        text += (
            (Fore.LIGHTRED_EX if level == "ERROR" else Fore.LIGHTCYAN_EX)
            + Style.BRIGHT
            + str(level)
            + Style.RESET_ALL
            + " - "
        )
        text += str(source) + " - "
        text += message

        print(text)


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
