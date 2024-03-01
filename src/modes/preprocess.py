"""
This module holds the tools to preprocess the data acquired from the realsense cameras.

Methods:
--------
- TODO

Classes:
--------
- TODO

Exceptions:
-----------
- TODO

"""

# pylint: disable=pointless-string-statement

from __future__ import annotations

import os
import calendar
import threading
from datetime import datetime

from .. import intel
from .. import utils

# Exceptions
"""
███████╗██╗  ██╗ ██████╗███████╗██████╗ ████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
█████╗   ╚███╔╝ ██║     █████╗  ██████╔╝   ██║   ██║██║   ██║██╔██╗ ██║███████╗
██╔══╝   ██╔██╗ ██║     ██╔══╝  ██╔═══╝    ██║   ██║██║   ██║██║╚██╗██║╚════██║
███████╗██╔╝ ██╗╚██████╗███████╗██║        ██║   ██║╚██████╔╝██║ ╚████║███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
"""


class PreprocessNamespaceError(utils.ModeNamespaceError):
    """
    Exception raised when errors related to the acquire namespace occur.
    """


class PreprocessError(Exception):
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


class PreprocessNamespace(utils.ModeNamespace):
    """
    This class holds the arguments for the preprocess mode.

    Attributes:
    -----------
        - TODO
    """

    _EXCEPTION_CLS = PreprocessNamespaceError

    # type hints
    origin_folder: str
    destination_folder: str

    def __init__(self, origin_folder: str, destination_folder: str, **kwargs) -> None:
        """
        TODO
        """

        del kwargs

        # origin_folder validations
        if origin_folder is None:
            raise PreprocessNamespaceError("The origin folder must be specified.")

        origin_folder = origin_folder.strip()

        if origin_folder == "":
            raise PreprocessNamespaceError("The origin folder cannot be a empty string.")

        if not os.path.isdir(origin_folder):
            raise PreprocessNamespaceError("The origin folder does not exist.")

        if len(os.listdir(origin_folder)) == 0:
            raise PreprocessNamespaceError("The origin folder is empty.")

        if len(
            [f for f in os.listdir(origin_folder) if os.path.isfile(os.path.join(origin_folder, f))]
        ) != len(os.listdir(origin_folder)):
            raise PreprocessNamespaceError(
                "The origin folder must contain only files (no subfolders)."
            )

        if len([f for f in os.listdir(origin_folder) if f.endswith(".npy")]) != len(
            os.listdir(origin_folder)
        ):
            raise PreprocessNamespaceError("The origin folder must contain only .npy files.")

        self.origin_folder = os.path.abspath(origin_folder)

        # destination_folder validations
        if destination_folder is None:
            raise PreprocessNamespaceError("The destination folder must be specified.")

        destination_folder = destination_folder.strip()

        if destination_folder == "":
            raise PreprocessNamespaceError("The destination folder cannot be a empty string.")

        self.destination_folder = os.path.abspath(destination_folder)

    def __str__(self) -> str:
        string = ""

        string += f"\tOrigin folder: {self.origin_folder}\n"

        string += f"\tDestination folder: {self.destination_folder}\n"

        return string.rstrip()

    @classmethod
    def _get_yaml_schema(cls) -> dict:
        """
        Returns the schema of the mode.
        """

        schema = {
            "type": "object",
            "properties": {
                "origin_folder": {"type": "string"},
                "destination_folder": {"type": "string"},
            },
            "additionalProperties": False,
        }

        schema["required"] = list(schema["properties"].keys())

        return schema

    @classmethod
    def _format_yaml_args(cls, args: dict) -> dict:
        return args


class Preprocess(utils.Mode):
    """
    This class holds the tools to acquire data from the realsense cameras.

    Methods:
    --------
        - run: Runs the acquire mode (in a blocking way).

    """

    _LOG_FILE = os.path.abspath(
        os.path.dirname(os.path.abspath(__file__)) + "/../../logs/preprocess.log"
    )

    # type hints

    _args: PreprocessNamespace

    # logger

    _logger: utils.Logger = utils.Logger("", _LOG_FILE)

    def __init__(self, args: PreprocessNamespace) -> None:
        """
        Acquire constructor.

        Args:
        -----
            - args: The arguments for the acquire mode (matching the constructor of
                    AcquireNamespace).

        """

        self._args = args

    def _create_destination_folder(self) -> None:
        """
        Creates the destination folder for the processed datas.

        Returns:
        --------
        A string with the paths to the output folders.
        """

        if not os.path.exists(self._args.destination_folder):
            os.makedirs(self._args.destination_folder)

    def run(self) -> None:
        """
        Runs the preprocessing mode (in a blocking way).
        """

        self._logger.info(
            "New preprocessing session (%s) started\n%s",
            datetime.now().strftime("%Y%m%d_%H%M%S"),
            self._args,
        )

        utils.print_info("New preprocessing session started!\n")

        # create destination folders

        self._create_destination_folder()

        self._logger.info("Preprocessing session finished.\n")

        utils.print_info("Preprocess mode terminated!\n")
