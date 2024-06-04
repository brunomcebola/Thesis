"""
This module is the entry point of ARGOS - node.
"""

from __future__ import annotations


import os
import sys
import signal
import logging
import threading
import pickle
import yaml
import jsonschema
from flask import Flask
from flask_socketio import SocketIO
from dotenv import find_dotenv, load_dotenv

from . import realsense
from . import routes


def set_environment_variables() -> None:
    """
    Load the environment variables from the nearest .env.argos file
    """

    # Find the .env file
    env_path = find_dotenv(filename=".env.argos_node")

    # Load the .env file
    if env_path:
        load_dotenv(dotenv_path=env_path)

    # BASE_DIR validation
    if not os.getenv("BASE_DIR"):
        os.environ["BASE_DIR"] = os.path.join(os.path.dirname(__file__), "..", "data")

    # Create BASE_DIR if it does not exist
    os.makedirs(os.environ["BASE_DIR"], exist_ok=True)

    # HOST validation
    if not os.getenv("HOST"):
        os.environ["HOST"] = "0.0.0.0"

    # PORT validation
    if not os.getenv("PORT"):
        os.environ["PORT"] = "19876"


def get_logger() -> logging.Logger:
    """
    Get the logger
    """

    logger = logging.getLogger("argos_node")
    logger.setLevel(logging.INFO)

    log_file_path = os.path.join(os.environ["BASE_DIR"], "argos_node.log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    file_handler = logging.FileHandler(log_file_path)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.info("ARGOS node started!")

    return logger


def launch_cameras(logger: logging.Logger) -> dict[str, realsense.Camera]:
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
                        "type": {"enum": [s_type.name.lower() for s_type in realsense.StreamType]},
                        "format": {
                            "enum": [s_format.name.lower() for s_format in realsense.StreamFormat]
                        },
                        "resolution": {
                            "enum": [
                                s_resolution.name.lower()
                                for s_resolution in realsense.StreamResolution
                            ]
                        },
                        "fps": {"enum": [s_fps.name.lower() for s_fps in realsense.StreamFPS]},
                    },
                    "required": ["type", "format", "resolution", "fps"],
                    "additionalProperties": False,
                },
            },
            "alignment": {
                "anyOf": [
                    {
                        "type": "string",
                        "enum": [s_type.name.lower() for s_type in realsense.StreamType],
                    },
                    {"type": "null"},
                ]
            },
        },
        "required": ["stream_configs", "alignment"],
        "additionalProperties": False,
    }

    logger.info("Launching cameras...")

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
                logger.warning("Camera groups not set - empty config file.")

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

                    logger.info(f"Camera groups set: {groups_str}")

                except jsonschema.ValidationError as e:
                    error = str(e).split("\n", maxsplit=1)[0]
                    logger.warning(f"Camera groups not set - config error: {error}.")

    except PermissionError:
        logger.warning("Camera groups not set - unable to open config file.")

    except yaml.YAMLError as e:
        if hasattr(e, "problem_mark"):
            line = e.problem_mark.line + 1  # type: ignore
            logger.warning(f"Camera groups not set - config file error on line {line}.")
        else:
            logger.warning("Camera groups not set - unknown error on config file.")

    except Exception as e:  # pylint: disable=broad-except
        logger.warning("Camera groups not set - unknown error.")

    # Launch each camera from its configuration .yaml file
    cameras = {}

    if not realsense.connected_cameras():
        logger.warning("No cameras connected.")
        return cameras

    for camera in realsense.connected_cameras():
        try:
            with open(os.path.join(cameras_dir, f"{camera}.yaml"), "a", encoding="utf-8") as f:
                pass

            with open(os.path.join(cameras_dir, f"{camera}.yaml"), "r", encoding="utf-8") as f:
                configs: dict = yaml.safe_load(f)

                if not configs:
                    logger.warning(f"Camera {camera} not launched - empty config file.")

                else:
                    # Validates the camera configuration
                    try:
                        jsonschema.validate(instance=configs, schema=camera_config_schema)

                        # Structures the camera arguments
                        stream_configs = [
                            realsense.StreamConfig(
                                realsense.StreamType[stream_config["type"].upper()],
                                realsense.StreamFormat[stream_config["format"].upper()],
                                realsense.StreamResolution[stream_config["resolution"].upper()],
                                realsense.StreamFPS[stream_config["fps"].upper()],
                            )
                            for stream_config in configs["stream_configs"]
                        ]

                        alignment = (
                            realsense.StreamType[configs["alignment"].upper()]
                            if configs["alignment"]
                            else None
                        )

                        control_signal, control_condition = cameras_controls.get(
                            camera, (None, None)
                        )

                        # Creates the camera instance
                        try:
                            cameras[camera] = realsense.Camera(
                                camera,
                                stream_configs,
                                alignment,
                                control_signal,
                                control_condition,
                            )

                            logger.info(f"Camera {camera} launched.")
                        except realsense.ConfigurationError as e:
                            logger.warning(f"Camera {camera} not launched - invalid config: {e}")

                    except jsonschema.ValidationError as e:
                        error = str(e).split("\n", maxsplit=1)[0]
                        logger.warning(f"Camera {camera} not launched - config error: {error}.")

        except PermissionError:
            logger.warning(f"Camera {camera} not launched - unable to open config file.")

        except yaml.YAMLError as e:
            if hasattr(e, "problem_mark"):
                line = e.problem_mark.line + 1  # type: ignore
                logger.warning(f"Camera {camera} not launched - config file error on line {line}.")
            else:
                logger.warning(f"Camera {camera} not launched - unknown error on config file.")

        except Exception:  # pylint: disable=broad-except
            logger.warning(f"Camera {camera} not launched - unknown error.")

        finally:
            continue

    return cameras


def launch_node(logger: logging.Logger, cameras: dict[str, realsense.Camera]) -> None:
    """
    Launch the API
    """

    def _cleanup_callback(signum, frame):  # pylint: disable=unused-argument
        """
        Cleanup function to be called when the program is interrupted
        """

        # Perform any necessary cleanup
        for camera in cameras.values():
            camera.cleanup()
            del camera

        logger.info("ARGOS node stopped!")

        sys.exit(0)

    signal.signal(signal.SIGINT, _cleanup_callback)

    app = Flask(__name__)
    socketio = SocketIO(app)

    for sn, camera in cameras.items():
        camera.set_stream_callback(lambda x, sn=sn: socketio.emit(sn, pickle.dumps(x)))
        logger.info(f"Camera {sn} set stream callback for socket connection.")

    app.config["cameras"] = cameras
    app.config["logger"] = logger

    app.register_blueprint(routes.handler)

    socketio.run(
        app,
        host=os.environ["HOST"],
        port=int(os.environ["PORT"]),
        debug=False,
        use_reloader=False,
        log_output=False,
    )


def main():
    """
    Main function of the program
    """

    set_environment_variables()

    logger = get_logger()

    cameras = launch_cameras(logger)

    launch_node(logger, cameras)


if __name__ == "__main__":
    main()
