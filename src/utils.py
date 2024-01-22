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

from __future__ import annotations

import os
import logging

from typing import Type
from types import SimpleNamespace
from abc import ABC, abstractmethod
from colorama import Fore, Style

from . import intel


class ModeNamespaceError(Exception):
    """
    Exception raised when errors related to the serial number occur.
    """


class ModeNamespace(SimpleNamespace):
    """
    This class is intended to be used as a namespace for the modes.

    Attributes:
    -----------
        - cameras (list[intel.RealSenseCamera]):
            The list with the cameras to be used.
    """

    def __init__(
        self,
        serial_numbers: list[str] | None = None,
        stream_types: list[intel.StreamType] | None = None,
        stream_configs: list[dict[intel.StreamType, intel.StreamConfig]] | None = None,
        exception: Type[ModeNamespaceError] = ModeNamespaceError,
    ) -> None:
        """
        AcquireNamespace constructor.

        Args:
        -----
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
            - ModeNamespaceError: If any of the arguments is invalid.

        """

        # type definitions
        self.cameras: list[intel.RealSenseCamera] = []

        # serial_numbers validations
        if serial_numbers is None:
            print_warning("No camera specified. Using all connected cameras.")

            serial_numbers = intel.RealSenseCamera.get_available_cameras_sn()

            if len(serial_numbers) == 0:
                raise intel.CameraUnavailableError("No available cameras.")

        elif len(set(serial_numbers)) == len(serial_numbers):
            serial_numbers = [str(serial_number).strip() for serial_number in serial_numbers]

        else:
            raise exception("Serial numbers.")

        # stream_types validations
        if stream_types is None:
            print_warning("No stream type specified. Setting depth as stream type of all cameras.")

            stream_types = [intel.StreamType.DEPTH] * len(serial_numbers)

        elif len(stream_types) == 1:
            print_warning("Using the specified stream type for all cameras.")

            stream_types = stream_types * len(serial_numbers)

        elif len(stream_types) == len(serial_numbers):
            pass

        else:
            raise exception("Stream types.")

        # stream configs validations
        if stream_configs is None:
            print_warning(
                "No stream configs specified. Using default stream configs for each camera model."
            )

            stream_configs = [
                intel.RealSenseCamera.get_default_config(
                    intel.RealSenseCamera.get_camera_model(serial_number)
                )
                for serial_number in serial_numbers
            ]

        elif len(stream_configs) == 1:
            print_warning("Using the specified stream config for all cameras.")

            stream_configs = stream_configs * len(serial_numbers)

        elif len(stream_configs) == len(serial_numbers):
            pass

        else:
            raise exception("Stream configs.")

        # create list of camera instances
        self.cameras = [
            intel.RealSenseCamera(sn, st, sc)
            for sn, st, sc in zip(serial_numbers, stream_types, stream_configs)
        ]

    def __str__(self) -> str:
        string = ""

        string += "\tCameras:"
        for camera in self.cameras:
            string += "\n"
            string += f"\t\tName:{camera.name}\n"
            string += f"\t\tSerial number:{camera.serial_number}\n"
            string += f"\t\tStream type:{camera.stream_type}\n"
            for key, value in camera.stream_configs.items():
                string += f"\t\t{key.name.capitalize()} stream config:{str(value)}\n"

        # align elements
        string = string.split("Cameras:")
        lines = string[1].split("\t\t")

        max_title = max([len(line.split(":")[0]) for line in lines])

        lines = [
            f":  {' ' * (max_title - len(line.split(':')[0]))}".join(line.split(":"))
            for line in lines
        ]

        lines = "\t\t".join(lines)

        return (string[0] + "Cameras:" + lines).rstrip()


class Mode(ABC):
    """
    Abstract class for modes.

    Subclasses must implement the following methods:
        - run(): Runs the mode.
        - stop(): Stops the mode.
    """

    @abstractmethod
    def run(self) -> None:
        """
        Runs the mode.
        """


class Logger(logging.Logger):
    """
    Logger class.
    """

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    level = logging.INFO

    def __init__(self, name: str, file: str) -> None:
        super().__init__(name, Logger.level)

        os.makedirs(os.path.dirname(file), exist_ok=True)

        file_handler = logging.FileHandler(file)
        file_handler.setLevel(Logger.level)
        file_handler.setFormatter(Logger.formatter)

        self.addHandler(file_handler)


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
