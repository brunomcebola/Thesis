"""
This module is the entry point of ARGOS - master.
"""

from __future__ import annotations

import os
import sys
import signal
import atexit
import logging
from flask import Flask
from appdirs import AppDirs
from flask_socketio import SocketIO
from dotenv import find_dotenv, load_dotenv


def _global_exception_hook(logger: logging.Logger):
    """
    Global exception handler
    """

    def _callback(exc_type, exc_value, exc_traceback):  # pylint: disable=unused-argument
        logger.error(f"{exc_type.__name__}: {exc_value}")

    return _callback


def _exit_callback(logger: logging.Logger):
    """
    Cleanup function to be called when the program is interrupted
    """

    if os.getenv("WERKZEUG_RUN_MAIN") == "true" or signal.SIGINT:
        logger.info("ARGOS master stopped!")


def _set_environment_variables() -> None:
    """
    Load the environment variables from the nearest .env.argos file
    """

    # Find the .env file
    env_path = find_dotenv(filename=".env.argos_master")

    # Load the .env file
    if env_path:
        load_dotenv(dotenv_path=env_path)

    # BASE_DIR validation
    if not os.getenv("BASE_DIR"):
        os.environ["BASE_DIR"] = AppDirs(__package__).user_data_dir

    # Create BASE_DIR if it does not exist
    os.makedirs(os.environ["BASE_DIR"], exist_ok=True)

    # HOST validation
    if not os.getenv("HOST"):
        os.environ["HOST"] = "0.0.0.0"

    # PORT validation
    if not os.getenv("PORT"):
        os.environ["PORT"] = "9876"


def _get_logger() -> logging.Logger:
    """
    Get the logger
    """

    logger = logging.getLogger(__package__)
    logger.setLevel(logging.INFO)

    log_file_path = os.path.join(os.environ["BASE_DIR"], f"{__package__}.log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    file_handler = logging.FileHandler(log_file_path)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


def _launch_master(logger: logging.Logger) -> None:
    """
    Launch the GUI
    """

    if os.getenv("WERKZEUG_RUN_MAIN") == "true":
        logger.info("ARGOS master started!")

    from . import gui  # pylint: disable=import-outside-toplevel
    from . import api  # pylint: disable=import-outside-toplevel

    # Create the Flask app
    app = Flask(__name__)

    # Create the SocketIO app
    socketio = SocketIO(app)

    # Add app configs
    app.config["logger"] = logger
    app.config["WEBASSETS_CACHE"] = False

    # Register the API
    api.register(app, socketio)

    # Register the GUI
    gui.register(app)

    socketio.run(
        app,
        host=os.environ["HOST"],
        port=int(os.environ["PORT"]),
        debug=False,
        use_reloader=True,
        log_output=False,
    )


def main():
    """
    Main function of the program
    """

    # Set the environment variables
    _set_environment_variables()

    # Get the logger
    logger = _get_logger()

    # Register the exit callback
    atexit.register(_exit_callback, logger)

    # Register the global exception handler
    sys.excepthook = _global_exception_hook(logger)

    # Register the signal handler
    signal.signal(signal.SIGINT, lambda signum, frame: exit(0))

    # Launch the master
    _launch_master(logger)


if __name__ == "__main__":
    main()
