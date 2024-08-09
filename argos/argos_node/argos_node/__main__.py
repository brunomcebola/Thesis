"""
This module is the entry point of ARGOS - node.
"""

from __future__ import annotations


import os
import sys
import signal
import threading
import pickle
import yaml
import jsonschema
from flask import Flask
from flask_socketio import SocketIO

from . import logger as _logger
from . import realsense as _realsense
from . import routes as _routes


def launch_cameras() -> dict[str, _realsense.Camera | None]:
    """
    Launch the cameras that have a .yaml file in the BASE_DIR/cameras directory
    """

    groups_config_schema = {
        "type": "object",
        "additionalProperties": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "uniqueItems": True,
        },
    }

    camera_config_schema = {
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

    _logger.info("Launching cameras...")

    # Get the cameras directory
    cameras_dir = os.path.join(os.environ["BASE_DIR"], "cameras")
    os.makedirs(cameras_dir, exist_ok=True)

    # Get the control mechinisms for each camera based on the groups configuration
    cameras_controls = {}

    try:
        with open(os.path.join(cameras_dir, "groups.yaml"), "a", encoding="utf-8") as f:
            pass

        with open(os.path.join(cameras_dir, "groups.yaml"), "r", encoding="utf-8") as f:
            groups: dict = yaml.safe_load(f)

            if not groups:
                _logger.warning("Camera groups not set - empty config file.")

            else:
                # Validates the groups configuration
                try:
                    jsonschema.validate(instance=groups, schema=groups_config_schema)

                    # Generate the control mechanisms for each group
                    for group, cameras in groups.items():
                        control_signal = threading.Event()
                        control_condition = threading.Condition()

                        for camera in cameras:
                            cameras_controls[camera] = (control_signal, control_condition)

                    # generate string with group and cameras
                    groups_str = " / ".join(
                        f"{group}: {', '.join(cameras)}" for group, cameras in groups.items()
                    )

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

    # Launch each camera from its configuration .yaml file
    cameras: dict[str, _realsense.Camera | None] = {
        camera: None for camera in _realsense.connected_cameras()
    }

    if not cameras:
        _logger.warning("No cameras connected.")
        exit(0)

    for camera in cameras:
        try:
            with open(os.path.join(cameras_dir, f"{camera}.yaml"), "a", encoding="utf-8") as f:
                pass

            with open(os.path.join(cameras_dir, f"{camera}.yaml"), "r", encoding="utf-8") as f:
                configs: dict = yaml.safe_load(f)

                if not configs:
                    _logger.warning("Camera %s not launched - empty config file.", camera)

                else:
                    # Validates the camera configuration
                    try:
                        jsonschema.validate(instance=configs, schema=camera_config_schema)

                        # Structures the camera arguments
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

                        control_signal, control_condition = cameras_controls.get(
                            camera, (None, None)
                        )

                        # Creates the camera instance
                        try:
                            cameras[camera] = _realsense.Camera(
                                camera,
                                stream_configs,
                                alignment,
                                control_signal,
                                control_condition,
                            )

                            _logger.info("Camera %s launched.", camera)
                        except _realsense.ConfigurationError as e:
                            _logger.warning(
                                "Camera %s not launched - invalid config: %s", camera, e
                            )

                    except jsonschema.ValidationError as e:
                        error = str(e).split("\n", maxsplit=1)[0]
                        _logger.warning("Camera %s not launched - config error: %s.", camera, error)

        except PermissionError:
            _logger.warning("Camera %s not launched - unable to open config file.", camera)

        except yaml.YAMLError as e:
            if hasattr(e, "problem_mark"):
                line = e.problem_mark.line + 1  # type: ignore
                _logger.warning(
                    "Camera %s not launched - config file error on line %s.", camera, line
                )
            else:
                _logger.warning("Camera %s not launched - unknown error on config file.", camera)

        except Exception:  # pylint: disable=broad-except
            _logger.warning("Camera %s not launched - unknown error.", camera)

        finally:
            continue

    return cameras


def launch_node(cameras: dict[str, _realsense.Camera | None]) -> None:
    """
    Launch the API
    """

    def _cleanup_callback(signum, frame):  # pylint: disable=unused-argument
        """
        Cleanup function to be called when the program is interrupted
        """

        # Perform any necessary cleanup
        for camera in cameras.values():
            if camera is not None:
                camera.cleanup()
            del camera

        sys.exit(0)

    def _camera_callback(camera_sn: str, frame: tuple):
        """
        Callback function to send the camera frames to the socket connection
        """
        try:
            socketio.emit(camera_sn, pickle.dumps(frame))
        except Exception:  # pylint: disable=broad-except
            pass

    signal.signal(signal.SIGINT, _cleanup_callback)

    app = Flask(__name__)
    socketio = SocketIO(app)

    for sn, camera in cameras.items():
        if camera is None:
            continue

        camera.set_stream_callback(
            lambda x: _camera_callback(sn, x)  # pylint: disable=cell-var-from-loop
        )
        _logger.info("Camera %s set stream callback for socket connection.", sn)

    app.config["cameras"] = cameras

    app.register_blueprint(_routes.handler)

    socketio.run(
        app,
        host=os.environ["HOST"],
        port=int(os.environ["PORT"]),
        debug=False,
        use_reloader=os.getenv("HOT_RELOAD") == "true",
        log_output=False,
    )


def main():
    """
    Main function of the program
    """

    cameras = launch_cameras()

    launch_node(cameras)


if __name__ == "__main__":
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        __package__ = str("argos_node")  # pylint: disable=redefined-builtin

    main()
