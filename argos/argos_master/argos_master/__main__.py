"""
This module is the entry point of ARGOS - master.
"""

from __future__ import annotations

import os
import sys
import signal
from flask import Flask
from flask_socketio import SocketIO


def main():
    """
    Main function of the program
    """

    from . import gui  # pylint: disable=import-outside-toplevel
    from . import api  # pylint: disable=import-outside-toplevel

    # Create the Flask app
    app = Flask(__name__)

    # Create the SocketIO app
    socketio = SocketIO(app)

    # Add app configs
    app.config["WEBASSETS_CACHE"] = False

    # Register the API
    api.register(app)

    # Register the GUI
    gui.register(app)

    # Register the signal handler
    signal.signal(signal.SIGINT, lambda signum, frame: exit(0))

    socketio.run(
        app,
        host=os.environ["HOST"],
        port=int(os.environ["PORT"]),
        debug=False,
        use_reloader=os.getenv("HOT_RELOAD") == "true",
        log_output=False,
    )


if __name__ == "__main__":
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        __package__ = str("argos_master")  # pylint: disable=redefined-builtin

    main()
