"""
# TODO
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any
import threading
import jsonschema


from . import intel
from .rabbit import RabbitMQ

_CAMERA_SCHEMA = {
    "type": "object",
    "properties": {
        "serial_number": {
            "type": "string",
        },
        "stream_configs": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {
                "type": "object",
                "properties": {
                    "type": {"enum": [s_type.name.lower() for s_type in intel.StreamType]},
                    "format": {"enum": [s_format.name.lower() for s_format in intel.StreamFormat]},
                    "resolution": {
                        "enum": [
                            s_resolution.name.lower() for s_resolution in intel.StreamResolution
                        ]
                    },
                    "fps": {"enum": [s_fps.name.lower() for s_fps in intel.StreamFPS]},
                },
                "required": ["type", "format", "resolution", "fps"],
                "additionalProperties": False,
            },
        },
        "alignment": {
            "anyOf": [
                {
                    "type": "string",
                    "enum": [s_type.name.lower() for s_type in intel.StreamType],
                },
                {"type": "null"},
            ]
        },
    },
    "required": ["serial_number", "stream_configs"],
    "additionalProperties": False,
}


class NodeNamespace:
    """
    # TODO
    """

    # Class attributes

    class CameraInteraction(Enum):
        """
        Enumerates the possible interactions with the cameras.
        """

        PAUSE_STREAMING = 0
        START_STREAMING = 1

    # Instance attributes

    _cameras: dict[str, intel.RealSenseCamera]
    _rabbitmq: RabbitMQ

    # Instance methods

    def __init__(self, cameras: list[dict] | None) -> None:
        # RabbitMQ
        rabbitmq_server = os.getenv("RABBITMQ_SERVER")
        rabbitmq_user = os.getenv("RABBITMQ_USER")
        rabbitmq_pwd = os.getenv("RABBITMQ_PWD")

        try:
            self._rabbitmq = RabbitMQ(rabbitmq_server, rabbitmq_user, rabbitmq_pwd)  # type: ignore
        except Exception as e:  # pylint: disable=broad-except
            raise RuntimeError("RabbitMQ connection failed!") from e

        # cameras
        self._cameras = {}
        if cameras:
            for camera in cameras:
                self.add_camera(camera)

    # Instance properties

    @property
    def cameras_sn(self) -> list[str]:
        """
        Returns the list of cameras
        """
        return list(self._cameras.keys())

    # Instance methods

    def add_camera(self, camera: dict) -> None:
        """
        Adds a camera to the list of cameras.

        Parameters
        - camera: The camera configuration.

        Notes:
        - The camera configuration must follow the _CAMERA_SCHEMA.
        - During the addition of a camera, exceptions from the `intel` module may be raised.
        """

        # Gets the signal and condition from the first camera
        if self.cameras_sn:
            signal, condition = self._cameras[self.cameras_sn[0]].control_mechanisms
        # Or creates new ones if there are no cameras
        else:
            signal = threading.Event()
            condition = threading.Condition()

        # Validates the camera configuration
        try:
            jsonschema.validate(instance=camera, schema=_CAMERA_SCHEMA)
        except jsonschema.ValidationError as e:
            error_detail = str(e).split("\n", maxsplit=1)[0]
            raise ValueError(f"YAML file - {error_detail[0].lower() + error_detail[1:]}!") from e

        # Transforms the YAML data into the needed arguments
        serial_number = camera["serial_number"]
        stream_configs = [
            intel.StreamConfig(
                intel.StreamType[stream_config["type"].upper()],
                intel.StreamFormat[stream_config["format"].upper()],
                intel.StreamResolution[stream_config["resolution"].upper()],
                intel.StreamFPS[stream_config["fps"].upper()],
            )
            for stream_config in camera["stream_configs"]
        ]
        alignment = intel.StreamType[camera["alignment"].upper()] if "alignment" in camera else None

        # Generates RabbitMQ publisher
        publisher = self._rabbitmq.generate_publisher(serial_number)

        # Creates the camera instance
        try:
            self._cameras[serial_number] = intel.RealSenseCamera(
                serial_number, stream_configs, alignment, signal, condition, publisher
            )
        except intel.ConfigurationError as e:
            raise intel.ConfigurationError(f"[Camera {serial_number}] {e}") from e

    def remove_camera(self, serial_number: str) -> None:
        """
        Removes a camera from the list of cameras.

        Parameters
        - serial_number: The serial number of the camera.
        """

        if serial_number not in self._cameras:
            raise ValueError(f"Camera {serial_number} not found!")

        self._cameras[serial_number].cleanup()
        del self._cameras[serial_number]

    def camera_interaction(self, serial_number: str, selector: CameraInteraction) -> Any:
        """
        Returns the information of a camera.

        Parameters
        - serial_number: The serial number of the camera.
        - selector: The data to be returned.
        """

        if serial_number not in self._cameras:
            raise ValueError(f"Camera {serial_number} not found!")

        if selector == self.CameraInteraction.PAUSE_STREAMING:
            self._cameras[serial_number].pause_streaming()
            return None

        if selector == self.CameraInteraction.START_STREAMING:
            self._cameras[serial_number].start_streaming()
            return None
