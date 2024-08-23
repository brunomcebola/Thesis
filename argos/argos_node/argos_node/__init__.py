"""
Init file for the argos_node
"""

import os
import re
import sys
import atexit
import signal
import logging

from flask import Flask
from appdirs import AppDirs
from flask_socketio import SocketIO
from dotenv import find_dotenv, load_dotenv

from . import realsense as _realsense

logger: logging.Logger
app: Flask
socketio: SocketIO


def _set_environment_variables() -> None:
    """
    Load the environment variables from the nearest .env.argos_node file
    """

    # Find the .env file
    env_path = find_dotenv(filename=".env.argos_node")

    # Load the .env file
    if env_path:
        load_dotenv(dotenv_path=env_path)

    # BASE_DIR validation
    if not os.getenv("BASE_DIR"):
        os.environ["BASE_DIR"] = AppDirs(__package__).user_data_dir

    # Create BASE_DIR if it does not exist
    os.makedirs(os.environ["BASE_DIR"], exist_ok=True)

    # HOST validation
    address_regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]).){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$"  # pylint: disable=line-too-long
    if not os.getenv("HOST") or not re.match(address_regex, os.environ["HOST"]):
        os.environ["HOST"] = "0.0.0.0"

    # PORT validation
    if (
        not os.getenv("PORT")
        or not os.environ["PORT"].isdigit()
        or int(os.environ["PORT"]) > 65535
        or int(os.environ["PORT"]) < 1024
    ):
        os.environ["PORT"] = "5000"

    # HOT_RELOAD validation
    if not os.getenv("HOT_RELOAD") or os.getenv("HOT_RELOAD") not in ["true", "false"]:
        os.environ["HOT_RELOAD"] = "false"


def _set_logger() -> None:
    """
    Set up the logging for the application
    """

    class _LogFilter(logging.Filter):
        def filter(self, record):
            # Custom validation logic here
            # Return True to allow the log message, False to block it
            if os.getenv("WERKZEUG_RUN_MAIN") == "true" or os.getenv("HOT_RELOAD") == "false":
                return True
            return False

    global logger  # pylint: disable=global-statement

    # Create logger
    logger = logging.getLogger(__package__)
    logger.setLevel(logging.INFO)

    # Create file handler
    log_file_path = os.path.join(os.environ["BASE_DIR"], f"{__package__}.log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    file_handler = logging.FileHandler(log_file_path)

    # Create filter
    log_filter = _LogFilter()
    file_handler.addFilter(log_filter)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Add file handler to logger
    logger.addHandler(file_handler)

    logger.info("ARGOS node started!")


def _set_atexit_handler() -> None:
    """
    Cleanup function to be called when the program is interrupted
    """

    def _callback():
        os.environ["WERKZEUG_RUN_MAIN"] = "true"
        logger.info("ARGOS node stopped!")

    atexit.register(_callback)


def _set_global_exception_hook() -> None:
    """
    Global exception handler
    """

    def _callback(exc_type, exc_value, exc_traceback):  # pylint: disable=unused-argument
        logger.error("%s: %s", exc_type.__name__, exc_value)

    sys.excepthook = _callback


def _set_server() -> None:
    """
    Set up the Flask and SocketIO server
    """

    global app  # pylint: disable=global-statement
    global socketio  # pylint: disable=global-statement

    # Create the Flask app
    app = Flask(__name__)

    # Create the SocketIO app
    socketio = SocketIO(app)

    # Add app configs
    app.config["WEBASSETS_CACHE"] = False

    # Register the signal handler
    signal.signal(
        signal.SIGINT,
        lambda signum, frame: (logger.warning("Terminate signal received, exiting..."), exit(0)),
    )


# Initialization code

if "--realsense-types" in sys.argv:
    print([s_type.name.lower() for s_type in _realsense.StreamType])
    exit(0)
elif "--realsense-formats" in sys.argv:
    print([s_format.name.lower() for s_format in _realsense.StreamFormat])
    exit(0)
elif "--realsense-resolutions" in sys.argv:
    print([s_res.name.lower() for s_res in _realsense.StreamResolution])
    exit(0)
elif "--realsense-fps" in sys.argv:
    print([s_rate.name.lower() for s_rate in _realsense.StreamFPS])
    exit(0)


_set_environment_variables()

_set_logger()

_set_atexit_handler()

_set_global_exception_hook()

_set_server()
