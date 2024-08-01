"""
This module is the entry point of ARGOS - master.
"""

from __future__ import annotations

import os
import sys
import signal
import logging
from flask import Flask
from flask_socketio import SocketIO
from dotenv import find_dotenv, load_dotenv


def set_environment_variables() -> None:
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
        os.environ["BASE_DIR"] = os.path.join(os.path.dirname(__file__), "..", "data")

    # Create BASE_DIR if it does not exist
    os.makedirs(os.environ["BASE_DIR"], exist_ok=True)

    # HOST validation
    if not os.getenv("HOST"):
        os.environ["HOST"] = "0.0.0.0"

    # PORT validation
    if not os.getenv("PORT"):
        os.environ["PORT"] = "9876"


def get_logger() -> logging.Logger:
    """
    Get the logger
    """

    logger = logging.getLogger("argos_master")
    logger.setLevel(logging.INFO)

    log_file_path = os.path.join(os.environ["BASE_DIR"], "argos_master.log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    file_handler = logging.FileHandler(log_file_path)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.info("ARGOS master started!")

    return logger


def launch_master(logger: logging.Logger) -> None:
    """
    Launch the GUI
    """

    from . import gui # pylint: disable=import-outside-toplevel
    from . import api # pylint: disable=import-outside-toplevel

    def _cleanup_callback(signum, frame):  # pylint: disable=unused-argument
        """
        Cleanup function to be called when the program is interrupted
        """
        logger.info("ARGOS master stopped!")

        sys.exit(0)

    signal.signal(signal.SIGINT, _cleanup_callback)

    # Create the Flask app
    app = Flask(__name__)

    # Add app configs
    app.config["logger"] = logger
    app.config["WEBASSETS_CACHE"] = False

    # Register the API
    api.register(app)

    # Register the GUI
    gui.register(app)

    # Create the SocketIO app
    socketio = SocketIO(app)

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

    set_environment_variables()

    logger = get_logger()

    launch_master(logger)


if __name__ == "__main__":
    main()
