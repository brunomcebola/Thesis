"""
This module holds the tools to preprocess the data  preprocessd from the realsense cameras.

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
import math
from datetime import datetime
import re
import numpy as np
import cv2
from tqdm import tqdm
from ultralytics import YOLO
from sklearn.model_selection import train_test_split

from .. import base
from .... import utils

__all__ = [
    "PreprocessServiceNamespace",
    "PreprocessService",
    "PreprocessServiceNamespaceError",
    "PreprocessServiceError",
]

# Exceptions
"""
███████╗██╗  ██╗ ██████╗███████╗██████╗ ████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
█████╗   ╚███╔╝ ██║     █████╗  ██████╔╝   ██║   ██║██║   ██║██╔██╗ ██║███████╗
██╔══╝   ██╔██╗ ██║     ██╔══╝  ██╔═══╝    ██║   ██║██║   ██║██║╚██╗██║╚════██║
███████╗██╔╝ ██╗╚██████╗███████╗██║        ██║   ██║╚██████╔╝██║ ╚████║███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
"""


class PreprocessServiceNamespaceError(base.ServiceNamespaceError):
    """
    Exception raised when errors related to the preprocess service namespace occur.
    """


class PreprocessServiceError(Exception):
    """
    Exception raised when errors related to the preprocess service occur.
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


class PreprocessServiceNamespace(base.ServiceNamespace):
    """
    This class holds the arguments for the preprocess  service.

    Attributes:
    -----------
        - TODO
    """

    _EXCEPTION_CLS = PreprocessServiceNamespaceError

    # type hints
    origin_folder: str
    destination_folder: str
    threshold: tuple[int, int] | None
    val_size: float

    def __init__(
        self,
        origin_folder: str,
        destination_folder: str,
        threshold: tuple[int, int] | None = None,
        val_size: float | None = None,
        **kwargs,
    ) -> None:
        """
        TODO
        """

        del kwargs

        # origin_folder validations
        if origin_folder is None:
            raise PreprocessServiceNamespaceError("The origin folder must be specified.")

        origin_folder = origin_folder.strip()

        if origin_folder == "":
            raise PreprocessServiceNamespaceError("The origin folder cannot be a empty string.")

        if not os.path.exists(origin_folder):
            raise PreprocessServiceNamespaceError("The origin folder does not exist.")

        if len(os.listdir(origin_folder)) % 2 != 0 or len(os.listdir(origin_folder)) == 0:
            raise PreprocessServiceNamespaceError(
                "The origin folder must contain an even number of files."
            )

        if len(
            [f for f in os.listdir(origin_folder) if os.path.isfile(os.path.join(origin_folder, f))]
        ) != len(os.listdir(origin_folder)):
            raise PreprocessServiceNamespaceError(
                "The origin folder must contain only files (no subfolders)."
            )

        for filename in os.listdir(origin_folder):
            if not re.match(r".*_(color|depth)\.npy", filename):
                raise PreprocessServiceNamespaceError(
                    "The origin folder must contain only files ending in _color.npy or _depth.npy."
                )

        self.origin_folder = os.path.abspath(origin_folder)

        # destination_folder validations
        if destination_folder is None:
            raise PreprocessServiceNamespaceError("The destination folder must be specified.")

        destination_folder = destination_folder.strip()

        if destination_folder == "":
            raise PreprocessServiceNamespaceError(
                "The destination folder cannot be a empty string."
            )

        if os.path.exists(destination_folder):
            raise PreprocessServiceNamespaceError("The destination folder already exists.")

        self.destination_folder = os.path.abspath(destination_folder)

        # threshold validations
        if threshold is not None:
            if len(threshold) != 2:
                raise PreprocessServiceNamespaceError(
                    "The threshold must be a tuple with two integers."
                )

            if not all(isinstance(i, int) for i in threshold):
                raise PreprocessServiceNamespaceError("The threshold min and max must be integers.")

            if threshold[0] < 0 or threshold[1] < 0:
                raise PreprocessServiceNamespaceError(
                    "The threshold min and max must be non-negative integers."
                )

            if threshold[0] > threshold[1]:
                raise PreprocessServiceNamespaceError(
                    "The threshold min must be less than the max."
                )

        self.threshold = threshold

        # val_size validations
        if val_size is None:
            utils.print_warning(
                "The validation size was not specified. The validation folder will be empty."
            )

            self.val_size = 0

        else:
            val_size = float(val_size)

            if math.isnan(val_size):
                raise PreprocessServiceNamespaceError("The validation size must be a number.")

            if not 0 <= val_size <= 1:
                raise PreprocessServiceNamespaceError(
                    "The validation size must be a number between 0 and 1."
                )

            self.val_size = val_size

    def __str__(self) -> str:
        string = ""

        string += f"\tOrigin folder: {self.origin_folder}\n"

        string += f"\tDestination folder: {self.destination_folder}\n"

        string += f"\tThreshold: {str(self.threshold[0]) + ' mm to ' + str(self.threshold[1]) + ' mm' if self.threshold is not None else '-'}\n"  # pylint: disable=line-too-long

        string += (
            f"\tTrain/Val split: {(1 - self.val_size) * 100:.0f}%/{self.val_size * 100:.0f}%\n"
        )

        return string.rstrip()

    @classmethod
    def _get_yaml_schema(cls) -> dict:
        """
        Returns the schema of the  service.
        """

        schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["create_dataset", "edit_dataset"]},
            },
            "required": ["action"],
            "if": {"properties": {"action": {"const": "create_dataset"}}},
            "then": {
                "properties": {
                    "action": {"const": "create_dataset"},
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
                    "val_size": {
                        "anyOf": [
                            {"type": "number", "minimum": 0, "maximum": 1},
                            {"type": "null"},
                            {"type": "string"},
                        ]
                    },
                },
                "required": [
                    "origin_folder",
                    "destination_folder",
                    "threshold",
                    "val_size",
                ],
                "additionalProperties": False,
            },
            "else": {
                "if": {"properties": {"action": {"const": "edit_dataset"}}},
                "then": {
                    "properties": {
                        "action": {"const": "join_dataset"},
                        "origin_folders": {"type": "array", "items": {"type": "string"}},
                        "destination_folder": {"type": "string"},
                    },
                    "required": [
                        "action",
                    ],
                    "additionalProperties": False,
                },
            },
        }

        # schema["required"] = list(schema["properties"].keys())

        return schema

    @classmethod
    def _format_yaml_args(cls, args: dict) -> dict:
        return args


class PreprocessService(base.Service):
    """
    This class holds the tools to preprocess data from the realsense cameras.

    Methods:
    --------
        - run: Runs the preprocess service (in a blocking way).

    """

    _LOG_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../../logs/preprocess.log"
    )

    # type hints

    _args: PreprocessServiceNamespace

    # logger

    _logger: base.Logger = base.Logger("", _LOG_FILE)

    def __init__(self, args: PreprocessServiceNamespace) -> None:
        """
        Acquire constructor.

        Args:
        -----
            - args: The arguments for the preprocess service (matching the constructor of
                    AcquireNamespace).

        """

        self._args = args

        self._yolo_model = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../YOLO_models/yolov8n.pt"
        )

    def run(self) -> None:
        """
        Runs the preprocessing service (in a blocking way).
        """

        # TODO: add a way to cancel if an error or ctrl+c occurs
        # TODO: generate train yaml file for ultralytics

        self._logger.info(
            "New preprocessing session (%s) started\n%s",
            datetime.now().strftime("%Y%m%d_%H%M%S"),
            self._args,
        )

        utils.print_info("New preprocessing session started!\n")

        # create destination folders

        os.makedirs(self._args.destination_folder)

        os.makedirs(os.path.join(self._args.destination_folder, "raw"))

        os.makedirs(os.path.join(self._args.destination_folder, "images"))
        os.makedirs(os.path.join(self._args.destination_folder, "images/box"))
        os.makedirs(os.path.join(self._args.destination_folder, "images/train"))
        os.makedirs(os.path.join(self._args.destination_folder, "images/val"))

        os.makedirs(os.path.join(self._args.destination_folder, "labels"))
        os.makedirs(os.path.join(self._args.destination_folder, "labels/train"))
        os.makedirs(os.path.join(self._args.destination_folder, "labels/val"))

        # get the filenames

        filenames = sorted(os.listdir(self._args.origin_folder))

        # ensure filenames are in pairs (same initial part)
        # ensure files have shape (X, Y, 3) for color and (X, Y) for depth
        for i in tqdm(range(0, len(filenames), 2), desc="    Checking files", unit_scale=2):
            if filenames[i].split("_")[:-1] != filenames[i + 1].split("_")[:-1]:
                raise PreprocessServiceError(
                    "The origin folder must contain pairs of files with the same initial part."
                )

            color_file = np.load(os.path.join(self._args.origin_folder, filenames[i]))
            depth_file = np.load(os.path.join(self._args.origin_folder, filenames[i + 1]))

            if len(color_file.shape) != 3 or color_file.shape[2] != 3:
                raise PreprocessServiceError(
                    f"The color files must have shape (X, Y, 3). (file: {filenames[i]})"
                )

            if len(depth_file.shape) != 2 or len(depth_file.shape) != 2:
                raise PreprocessServiceError(
                    f"The depth files must have shape (X, Y). (file: {filenames[i + 1]})"
                )

            if (
                color_file.shape[0] != depth_file.shape[0]
                or color_file.shape[1] != depth_file.shape[1]
            ):
                raise PreprocessServiceError(
                    f"The color and depth files must have the same shape. (files: {filenames[i]} and {filenames[i + 1]})"  # pylint: disable=line-too-long
                )

        print()

        # generate dataset
        model = YOLO(self._yolo_model)

        counter = 0

        for i in tqdm(range(0, len(filenames), 2), desc="Generating dataset"):
            # get numpy files and move them to the raw folder

            color_file = np.load(os.path.join(self._args.origin_folder, filenames[i]))
            depth_file = np.load(os.path.join(self._args.origin_folder, filenames[i + 1]))

            filename = "_".join(os.path.splitext(filenames[i])[0].split("_")[:-1])

            # generate label file

            predictions = model.predict(source=color_file, classes=[0], verbose=False)

            # if no detections, skip to next image
            if len(predictions[0].boxes) == 0:
                continue

            counter += 1

            labels_dest = os.path.join(self._args.destination_folder, "labels", filename + ".txt")

            with open(labels_dest, "w", encoding="utf-8") as f:
                for box in predictions[0].boxes:
                    f.write("0 " + " ".join([f"{x:.6f}" for x in box.xywhn[0].tolist()]) + "\n")

            # generate color image

            color_file = cv2.cvtColor(color_file, cv2.COLOR_BGR2RGB)

            color_dest = os.path.join(
                self._args.destination_folder, "images/box", filename + ".jpg"
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

            depth_dest = os.path.join(
                self._args.destination_folder, "images/depth", filename + ".jpg"
            )

            cv2.imwrite(depth_dest, depth_file)

        print()

        # move raw files to the raw folder

        for i in tqdm(range(0, len(filenames), 2), desc="  Moving raw files"):
            os.rename(
                os.path.join(self._args.origin_folder, filenames[i]),
                os.path.join(self._args.destination_folder, "raw", filenames[i]),
            )

            os.rename(
                os.path.join(self._args.origin_folder, filenames[i + 1]),
                os.path.join(self._args.destination_folder, "raw", filenames[i + 1]),
            )

        print()

        os.rmdir(self._args.origin_folder)

        msg = f"Generated dataset has {counter} out of the initial {len(filenames) // 2} images ({(counter * 100) / (len(filenames) // 2):.2f}%)."  # pylint: disable=line-too-long

        self._logger.info(msg)
        utils.print_info(msg + "\n")

        # split in train and val

        # get filenames

        filenames = sorted(os.listdir(self._args.destination_folder + "/labels"))

        # split dataset

        train_filenames, _ = train_test_split(
            filenames, test_size=self._args.val_size, random_state=42, shuffle=True
        )

        for i in tqdm(range(len(filenames)), desc=" Splitting dataset"):
            dest_folder = "train" if filenames[i] in train_filenames else "val"

            os.rename(
                os.path.join(
                    self._args.destination_folder,
                    "images/depth",
                    os.path.splitext(filenames[i])[0] + ".jpg",
                ),
                os.path.join(
                    self._args.destination_folder,
                    "images",
                    dest_folder,
                    "depth",
                    os.path.splitext(filenames[i])[0] + ".jpg",
                ),
            )

            os.rename(
                os.path.join(self._args.destination_folder, "labels", filenames[i]),
                os.path.join(self._args.destination_folder, "labels", dest_folder, filenames[i]),
            )

        print()

        # remove empty folders

        os.rmdir(os.path.join(self._args.destination_folder, "images/depth"))

        msg = f"Train folder has {len(filenames) - len(train_filenames)} images and validation folder has {len(train_filenames)} images."  # pylint: disable=line-too-long

        self._logger.info(msg)
        utils.print_info(msg + "\n")

        self._logger.info("Preprocessing session finished.\n")

        utils.print_info("Preprocess service terminated!\n")
