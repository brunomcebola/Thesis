"""
Init file for the argos_gui
"""

import os
import re
import sys
import time
import atexit
import signal
import logging
import threading

from flask import Flask
from appdirs import AppDirs
from socketio import Client
from flask_socketio import SocketIO
from dotenv import find_dotenv, load_dotenv

logger: logging.Logger
app: Flask
socketio: SocketIO
master_sio: Client


def _set_environment_variables() -> None:
    """
    Load the environment variables from the nearest .env.argos_gui file
    """

    # Find the .env file
    env_path = find_dotenv(filename=f".env.{__package__}")

    # Load the .env file
    if env_path:
        load_dotenv(dotenv_path=env_path)

    # BASE_DIR validation
    if not os.getenv("BASE_DIR"):
        os.environ["BASE_DIR"] = AppDirs(__package__).user_data_dir

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
        os.environ["PORT"] = "8080"

    # MASTER_ADDRESS validation
    address_regex = r"^(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]).(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]).(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]).(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]):\d{4}$"  # pylint: disable=line-too-long
    if not os.getenv("MASTER_ADDRESS") or not re.match(address_regex, os.environ["MASTER_ADDRESS"]):
        os.environ["MASTER_ADDRESS"] = "localhost:3000"


def _set_logger() -> None:
    """
    Set up the logging for the application
    """

    global logger  # pylint: disable=global-statement

    # Create logger
    logger = logging.getLogger(__package__)
    logger.setLevel(logging.INFO)

    # Create file handler
    log_file_path = os.path.join(os.environ["BASE_DIR"], f"{__package__}.log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    file_handler = logging.FileHandler(log_file_path)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Add file handler to logger
    logger.addHandler(file_handler)

    logger.info("ARGOS gui started!")


def _set_atexit_handler() -> None:
    """
    Cleanup function to be called when the program is interrupted
    """

    def _callback():
        logger.info("ARGOS gui stopped!")

    atexit.register(_callback)


def _set_global_exception_hook() -> None:
    """
    Global exception handler
    """

    def _callback(exc_type, exc_value, _):
        logger.error("%s: %s", exc_type.__name__, exc_value)

    sys.excepthook = _callback


def _connect_to_master() -> None:
    """
    Connect to the master server
    """

    def _retry_connect():
        while master_sio and not master_sio.connected:
            try:
                master_sio.connect(f"http://{os.getenv('MASTER_ADDRESS')}", namespaces=["/gui"])
                break
            except Exception:  # pylint: disable=broad-except
                time.sleep(1)

    global master_sio  # pylint: disable=global-statement

    sio = Client(reconnection=True)

    @sio.event(namespace="/gui")
    def connect():
        logger.info("Connected to master")

    @sio.event(namespace="/gui")
    def disconnect():
        logger.warning("Disconnected from master")

    master_sio = sio

    # Connect to the node
    try:
        master_sio.connect(f"http://{os.getenv('MASTER_ADDRESS')}", namespaces="/gui")
    except Exception as e:  # pylint: disable=broad-except
        logger.warning("Unable to connect to master. Retrying in background...")

    threading.Thread(target=_retry_connect, daemon=True).start()


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

_set_environment_variables()

_set_logger()

_set_atexit_handler()

_set_global_exception_hook()

_set_server()

_connect_to_master()
