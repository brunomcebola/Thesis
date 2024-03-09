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
from datetime import datetime
import numpy as np
import cv2
from tqdm import tqdm

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
    threshold: tuple[int, int] | None

    def __init__(
        self,
        origin_folder: str,
        destination_folder: str,
        threshold: tuple[int, int] | None = None,
        **kwargs,
    ) -> None:
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

        if not os.path.exists(origin_folder):
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

        if len(os.listdir(origin_folder)) % 2 != 0:
            raise PreprocessNamespaceError(
                "The origin folder must contain an even number of files (color and depth)."
            )

        self.origin_folder = os.path.abspath(origin_folder)

        # destination_folder validations
        if destination_folder is None:
            raise PreprocessNamespaceError("The destination folder must be specified.")

        destination_folder = destination_folder.strip()

        if destination_folder == "":
            raise PreprocessNamespaceError("The destination folder cannot be a empty string.")

        if os.path.exists(destination_folder):
            raise PreprocessNamespaceError("The destination folder already exists.")

        self.destination_folder = os.path.abspath(destination_folder)

        # threshold validations
        if threshold is not None:
            if len(threshold) != 2:
                raise PreprocessNamespaceError("The threshold must be a tuple with two integers.")

            if not all(isinstance(i, int) for i in threshold):
                raise PreprocessNamespaceError("The threshold min and max must be integers.")

            if threshold[0] < 0 or threshold[1] < 0:
                raise PreprocessNamespaceError(
                    "The threshold min and max must be non-negative integers."
                )

            if threshold[0] > threshold[1]:
                raise PreprocessNamespaceError("The threshold min must be less than the max.")

        self.threshold = threshold

    def __str__(self) -> str:
        string = ""

        string += f"\tOrigin folder: {self.origin_folder}\n"

        string += f"\tDestination folder: {self.destination_folder}\n"

        string += f"\tThreshold: {str(self.threshold[0]) + ' mm to ' + str(self.threshold[1]) + ' mm' if self.threshold is not None else '-'}\n"  # pylint: disable=line-too-long

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
                "threshold": {
                    "anyOf": [
                        {
                            "type": "array",
                            "prefixItems": [
                                {"type": "integer", "minimum": 0},
                                {"type": "integer", "minimum": 0},
                            ],
                            "minItems": 2,
                            "maxItems": 2,
                            "additionalItems": False,
                        },
                        {"type": "null"},
                    ]
                },
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

    def _create_destination_folders(self) -> None:
        """
        Creates the destination folder for the processed data, along with any needed subfolder.

        Returns:
        --------
        A string with the paths to the output folders.
        """

        if not os.path.exists(self._args.destination_folder):
            os.makedirs(self._args.destination_folder)

        if not os.path.exists(self._args.destination_folder + "/raw"):
            os.makedirs(self._args.destination_folder + "/raw")

        if not os.path.exists(self._args.destination_folder + "/labels"):
            os.makedirs(self._args.destination_folder + "/labels")

        if not os.path.exists(self._args.destination_folder + "/images/depth"):
            os.makedirs(self._args.destination_folder + "/images/depth")

        if not os.path.exists(self._args.destination_folder + "/images/color"):
            os.makedirs(self._args.destination_folder + "/images/color")

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

        self._create_destination_folders()

        # loop trough the files in the origin folder

        for filename in sorted(os.listdir(self._args.origin_folder)):

            file = np.load(self._args.origin_folder + "/" + filename)

            if "color" in filename:
                file = cv2.cvtColor(file, cv2.COLOR_BGR2RGB)

                cv2.imwrite(
                    self._args.destination_folder
                    + "/images/color/"
                    + "_".join(os.path.splitext(filename)[0].split("_")[:-1])
                    + ".jpg",
                    file,
                )

            if "depth" in filename:
                # Trim the values outside the threshold
                if self._args.threshold is not None:
                    min_threshold = self._args.threshold[0]
                    max_threshold = self._args.threshold[1]

                    file[file >= max_threshold] = max_threshold
                    file[file <= min_threshold] = max_threshold

                    file = file - min_threshold

                # Normalize the values to the range [0, 1]
                file = file / np.max(file)

                file = (file * 255).astype(np.uint8)

                file = cv2.applyColorMap(file, cv2.COLORMAP_JET)

                cv2.imwrite(
                    self._args.destination_folder
                    + "/images/depth/"
                    + "_".join(os.path.splitext(filename)[0].split("_")[:-1])
                    + ".jpg",
                    file,
                )

            os.rename(
                self._args.origin_folder + "/" + filename,
                self._args.destination_folder + "/raw/" + filename,
            )

        self._logger.info("Preprocessing session finished.\n")

        utils.print_info("Preprocess mode terminated!\n")
