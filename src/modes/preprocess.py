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
import re
from ultralytics import YOLO

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

        if len(os.listdir(origin_folder)) % 2 != 0 or len(os.listdir(origin_folder)) == 0:
            raise PreprocessNamespaceError(
                "The origin folder must contain an even number of files."
            )

        if len(
            [f for f in os.listdir(origin_folder) if os.path.isfile(os.path.join(origin_folder, f))]
        ) != len(os.listdir(origin_folder)):
            raise PreprocessNamespaceError(
                "The origin folder must contain only files (no subfolders)."
            )

        for filename in os.listdir(origin_folder):
            if not re.match(r".*_(color|depth)\.npy", filename):
                raise PreprocessNamespaceError(
                    "The origin folder must contain only files ending in _color.npy or _depth.npy."
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

        self._yolo_model = os.path.abspath(
            os.path.dirname(os.path.abspath(__file__)) + "/../YOLO_models/yolov8n.pt"
        )

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

        # get the filenames

        filenames = sorted(os.listdir(self._args.origin_folder))

        # ensure filenames are in pairs (same initial part)
        # ensure files have shape (X, Y, 3) for color and (X, Y) for depth
        for i in tqdm(range(0, len(filenames), 2), desc="    Checking files", unit_scale=2):
            if filenames[i].split("_")[:-1] != filenames[i + 1].split("_")[:-1]:
                raise PreprocessError(
                    "The origin folder must contain pairs of files with the same initial part."
                )

            color_file = np.load(self._args.origin_folder + "/" + filenames[i])
            depth_file = np.load(self._args.origin_folder + "/" + filenames[i + 1])

            if len(color_file.shape) != 3 or color_file.shape[2] != 3:
                raise PreprocessError(
                    f"The color files must have shape (X, Y, 3). (file: {filenames[i]})"
                )

            if len(depth_file.shape) != 2 or len(depth_file.shape) != 2:
                raise PreprocessError(
                    f"The depth files must have shape (X, Y). (file: {filenames[i + 1]})"
                )

            if (
                color_file.shape[0] != depth_file.shape[0]
                or color_file.shape[1] != depth_file.shape[1]
            ):
                raise PreprocessError(
                    f"The color and depth files must have the same shape. (files: {filenames[i]} and {filenames[i + 1]})"  # pylint: disable=line-too-long
                )

        print()

        # generating dataset
        model = YOLO(self._yolo_model)

        counter = 0

        for i in tqdm(range(0, len(filenames), 2), desc="Generating dataset"):
            # get numpy files and move them to the raw folder

            color_file = np.load(self._args.origin_folder + "/" + filenames[i])
            depth_file = np.load(self._args.origin_folder + "/" + filenames[i + 1])

            os.rename(
                f"{self._args.origin_folder}/{filenames[i]}",
                f"{self._args.destination_folder}/raw/{filenames[i]}",
            )

            os.rename(
                f"{self._args.origin_folder}/{filenames[i + 1]}",
                f"{self._args.destination_folder}/raw/{filenames[i + 1]}",
            )

            # generate label file

            predictions = model.predict(source=color_file, classes=[0], verbose=False)

            # if no detections, skip to next image
            if len(predictions[0].boxes) == 0:
                continue

            counter += 1

            labels_dest = (
                self._args.destination_folder
                + "/labels/"
                + "_".join(os.path.splitext(filenames[i])[0].split("_")[:-1])
                + ".txt"
            )

            with open(labels_dest, "w", encoding="utf-8") as f:
                for box in predictions[0].boxes:
                    f.write("0 " + " ".join([f"{x:.6f}" for x in box.xywhn[0].tolist()]) + "\n")

            # generate color image

            color_file = cv2.cvtColor(color_file, cv2.COLOR_BGR2RGB)

            color_dest = (
                self._args.destination_folder
                + "/images/color/"
                + "_".join(os.path.splitext(filenames[i])[0].split("_")[:-1])
                + ".jpg"
            )

            for box in predictions[0].boxes:
                x = box.xywhn[0][0] * color_file.shape[1]
                y = box.xywhn[0][1] * color_file.shape[0]
                w = box.xywhn[0][2] * color_file.shape[1]
                h = box.xywhn[0][3] * color_file.shape[0]

                color_file = cv2.rectangle(
                    color_file,
                    (int(x - w / 2), int(y - h / 2)),
                    (int(x + w / 2), int(y + h / 2)),
                    (0, 0, 255),
                    2,
                )

            cv2.imwrite(color_dest, color_file)

            # generate depth image

            # Trim the values outside the threshold
            if self._args.threshold is not None:
                min_threshold = self._args.threshold[0]
                max_threshold = self._args.threshold[1]

                depth_file[depth_file >= max_threshold] = max_threshold
                depth_file[depth_file <= min_threshold] = max_threshold

                depth_file = depth_file - min_threshold

            # Normalize the values to the range [0, 1]
            depth_file = depth_file / np.max(depth_file)

            depth_file = (depth_file * 255).astype(np.uint8)

            depth_file = cv2.applyColorMap(depth_file, cv2.COLORMAP_JET)

            depth_dest = (
                self._args.destination_folder
                + "/images/depth/"
                + "_".join(os.path.splitext(filenames[i + 1])[0].split("_")[:-1])
                + ".jpg"
            )

            cv2.imwrite(depth_dest, depth_file)

        print()

        print(f"Dataset has {counter} images.")

        print()

        self._logger.info("Preprocessing session finished.\n")

        utils.print_info("Preprocess mode terminated!\n")
