"""
Cameras controller module.
"""

from __future__ import annotations

import os
import pickle
import threading
from http import HTTPStatus
from typing import NamedTuple
import yaml
import jsonschema
from flask import Blueprint, jsonify, request

from .. import realsense as _realsense
from .. import logger as _logger
from .. import socketio as _socketio

blueprint = Blueprint("cameras_handlers", __name__, url_prefix="/cameras")

CAMERAS_DIR = os.path.join(os.environ["BASE_DIR"], "cameras")
GROUPS_FILE = os.path.join(CAMERAS_DIR, "groups.yaml")

GROUPS_CONFIG_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 1,
        "uniqueItems": True,
    },
}

CAMERA_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "stream_configs": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {
                "type": "object",
                "properties": {
                    "type": {"enum": [s_type.name.lower() for s_type in _realsense.StreamType]},
                    "format": {
                        "enum": [s_format.name.lower() for s_format in _realsense.StreamFormat]
                    },
                    "resolution": {
                        "enum": [
                            s_resolution.name.lower()
                            for s_resolution in _realsense.StreamResolution
                        ]
                    },
                    "fps": {"enum": [s_fps.name.lower() for s_fps in _realsense.StreamFPS]},
                },
                "required": ["type", "format", "resolution", "fps"],
                "additionalProperties": False,
            },
        },
        "alignment": {
            "anyOf": [
                {
                    "type": "string",
                    "enum": [s_type.name.lower() for s_type in _realsense.StreamType],
                },
                {"type": "null"},
            ]
        },
    },
    "required": ["stream_configs", "alignment"],
    "additionalProperties": False,
}


class _GroupTuple(NamedTuple):
    controls: tuple[threading.Event, threading.Condition]
    cameras: list[str]


groups: dict[str, _GroupTuple] = {}
cameras: dict[str, _realsense.Camera | None] = {}


def cleanup() -> None:
    """
    Cleanup function to be called when the program is interrupted
    """

    for camera_sn, camera in cameras.items():
        if camera is not None:
            camera.cleanup()
        del cameras[camera_sn]


def _get_groups() -> None:
    try:
        with open(GROUPS_FILE, "a", encoding="utf-8") as f:
            pass

        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            groups_yaml: dict = yaml.safe_load(f)

            if not groups_yaml:
                _logger.warning("Camera groups not defined (empty config file).")

            else:
                # Validates the groups configuration
                try:
                    jsonschema.validate(instance=groups_yaml, schema=GROUPS_CONFIG_SCHEMA)

                    # Generate the control mechanisms for each group
                    groups_str = []
                    for group_name, group_cameras in groups_yaml.items():
                        groups[group_name] = _GroupTuple(
                            (threading.Event(), threading.Condition()),
                            group_cameras,
                        )
                        groups_str.append(f"{group_name}: {', '.join(group_cameras)}")
                    groups_str = " / ".join(groups_str)

                    _logger.info("Camera groups set: %s.", groups_str)

                except jsonschema.ValidationError as e:
                    error = str(e).split("\n", maxsplit=1)[0]
                    _logger.warning("Camera groups not set - config error: %s.", error)

    except PermissionError:
        _logger.warning("Camera groups not set - unable to open config file.")

    except yaml.YAMLError as e:
        if hasattr(e, "problem_mark"):
            line = e.problem_mark.line + 1  # type: ignore
            _logger.warning("Camera groups not set - config file error on line %s.", line)
        else:
            _logger.warning("Camera groups not set - unknown error on config file.")

    except Exception as e:  # pylint: disable=broad-except
        _logger.warning("Camera groups not set - unknown error.")


def _launch_camera(camera_sn: str, config_file: str) -> _realsense.Camera | None:
    """
    Launches a camera instance.

    Args:
        - camera_sn: The serial number of the camera.
        - config_file: The path to the camera configuration file.
        - camera_controls: The dictionary of camera controls.

    Returns:
        - The camera instance if it was successfully launched, otherwise None.

    """

    def _camera_callback(camera_sn: str, frame: tuple):
        """
        Callback function to send the camera frames to the socket connection
        """
        try:
            _socketio.emit(camera_sn, pickle.dumps(frame))
        except Exception:  # pylint: disable=broad-except
            pass

    _logger.info("Launching camera %s...", camera_sn)

    controls = next(
        (group.controls for group in groups.values() if camera_sn in group.cameras), (None, None)
    )

    try:
        with open(config_file, "a", encoding="utf-8") as f:
            pass

        with open(config_file, "r", encoding="utf-8") as f:
            configs: dict = yaml.safe_load(f)

            if not configs:
                _logger.warning("Camera %s not launched - empty config file.", camera_sn)

            else:
                # Validates the camera_sn configuration
                try:
                    jsonschema.validate(instance=configs, schema=CAMERA_CONFIG_SCHEMA)

                    # Structures the camera_sn arguments
                    stream_configs = [
                        _realsense.StreamConfig(
                            _realsense.StreamType[stream_config["type"].upper()],
                            _realsense.StreamFormat[stream_config["format"].upper()],
                            _realsense.StreamResolution[stream_config["resolution"].upper()],
                            _realsense.StreamFPS[stream_config["fps"].upper()],
                        )
                        for stream_config in configs["stream_configs"]
                    ]

                    alignment = (
                        _realsense.StreamType[configs["alignment"].upper()]
                        if configs["alignment"]
                        else None
                    )

                    control_signal, control_condition = controls

                    # Creates the camera_sn instance
                    try:
                        camera = _realsense.Camera(
                            camera_sn,
                            stream_configs,
                            alignment,
                            control_signal,
                            control_condition,
                            lambda x: _camera_callback(camera_sn, x),
                        )

                        _logger.info("Camera %s launched.", camera_sn)

                        return camera
                    except _realsense.ConfigurationError as e:
                        _logger.warning("Camera %s not launched - invalid config: %s", camera_sn, e)

                except jsonschema.ValidationError as e:
                    error = str(e).split("\n", maxsplit=1)[0]
                    _logger.warning("Camera %s not launched - config error: %s.", camera_sn, error)

    except PermissionError:
        _logger.warning("Camera %s not launched - unable to open config file.", camera_sn)

    except yaml.YAMLError as e:
        if hasattr(e, "problem_mark"):
            line = e.problem_mark.line + 1  # type: ignore
            _logger.warning(
                "Camera %s not launched - config file error on line %s.", camera_sn, line
            )
        else:
            _logger.warning("Camera %s not launched - unknown error on config file.", camera_sn)

    except Exception:  # pylint: disable=broad-except
        _logger.warning("Camera %s not launched - unknown error.", camera_sn)

    return None


def _init() -> None:
    """
    Initializes the nodes modul
    """

    _get_groups()

    for camera in _realsense.connected_cameras():
        cameras[camera] = None

    if not cameras:
        _logger.warning("No cameras connected.")
        exit(0)

    for camera in cameras:
        cameras[camera] = _launch_camera(camera, os.path.join(CAMERAS_DIR, f"{camera}.yaml"))


#
# Initialization
#

_init()

#
# Routes
#


@blueprint.route("/", methods=["GET"])
def get_cameras():
    """
    Get the list of connected cameras.
    """

    return jsonify(list(cameras.keys())), HTTPStatus.OK


@blueprint.route("/<string:serial_number>/status", methods=["GET"])
def get_camera(serial_number: str):
    """
    Get the details of a camera.
    """

    # check if camera exists
    if serial_number not in cameras:
        return jsonify("Camera not connected."), HTTPStatus.NOT_FOUND

    # check if camera is operational
    if cameras[serial_number] is None or cameras[serial_number].is_stopped:  # type: ignore
        return jsonify("Camera not operational."), HTTPStatus.SERVICE_UNAVAILABLE

    return jsonify("Camera operational."), HTTPStatus.OK


@blueprint.route("/<string:serial_number>/config", methods=["PUT"])
def update_camera(serial_number: str):
    """
    Update the configuration of a camera.
    """

    # check if camera exists
    if serial_number not in cameras:
        return (
            jsonify("Camera not connected."),
            HTTPStatus.NOT_FOUND,
        )

    new_config: dict = request.get_json()

    if not new_config:
        return (
            jsonify("Invalid configuration: empty configuration."),
            HTTPStatus.BAD_REQUEST,
        )

    # Validate new configuration
    try:
        jsonschema.validate(instance=new_config, schema=CAMERA_CONFIG_SCHEMA)
    except jsonschema.ValidationError as e:
        return (
            jsonify("Invalid configuration: %s.", str(e).split("\n", maxsplit=1)[0]),
            HTTPStatus.BAD_REQUEST,
        )

    _logger.info("Updating camera %s configuration...", serial_number)

    # Stop camera if exists
    if cameras[serial_number] is not None:
        cameras[serial_number].cleanup()  # type: ignore
        _logger.info("Camera %s stopped.", serial_number)
    del cameras[serial_number]

    with open(os.path.join(CAMERAS_DIR, f"{serial_number}.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(new_config, f)

    cameras[serial_number] = _launch_camera(
        serial_number, os.path.join(CAMERAS_DIR, f"{serial_number}.yaml")
    )

    return jsonify("Camera updated."), HTTPStatus.OK


@blueprint.route("/<string:serial_number>/launch", methods=["POST"])
def launch_camera(serial_number: str):
    """
    Launch a camera.
    """

    if serial_number not in cameras:
        return (
            jsonify("Camera not connected."),
            HTTPStatus.NOT_FOUND,
        )

    if cameras[serial_number] is not None and not cameras[serial_number].is_stopped:  # type: ignore
        return (
            jsonify("Camera already launched."),
            HTTPStatus.OK,
        )

    if cameras[serial_number] is not None and cameras[serial_number].is_stopped:  # type: ignore
        cameras[serial_number].cleanup()  # type: ignore
        del cameras[serial_number]

    cameras[serial_number] = _launch_camera(
        serial_number, os.path.join(CAMERAS_DIR, f"{serial_number}.yaml")
    )

    if cameras[serial_number] is None:
        return jsonify("Camera not launched."), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify("Camera launched."), HTTPStatus.OK


@blueprint.route("/<string:serial_number>/stream/<string:action>", methods=["POST"])
def start_stream(serial_number: str, action: str):
    """
    Start the streaming of a camera.
    """

    if action not in ["start", "stop"]:
        return jsonify("Invalid action."), HTTPStatus.BAD_REQUEST

    # check if camera exists
    if serial_number not in cameras:
        return jsonify("Camera not connected."), HTTPStatus.NOT_FOUND

    # check if camera is operational
    if cameras[serial_number] is None or cameras[serial_number].is_stopped:  # type: ignore
        return jsonify("Camera not operational."), HTTPStatus.SERVICE_UNAVAILABLE

    # check if camera is already streaming
    if action == "start" and cameras[serial_number].is_streaming:  # type: ignore
        return jsonify("Camera stream already started."), HTTPStatus.OK
    elif action == "stop" and not cameras[serial_number].is_streaming:  # type: ignore
        return jsonify("Camera stream already stopped."), HTTPStatus.OK

    getattr(cameras[serial_number], f"{action}_stream")()

    _logger.info(
        "Camera %s stream %s.", serial_number, "started" if action == "start" else "stopped"
    )
    return jsonify("Camera stream started."), HTTPStatus.OK
