"""
This module is the entry point of ARGOS - node.
"""

from __future__ import annotations


import os
import sys
import signal

from . import app as _app
from . import socketio as _socketio


def main() -> None:
    """
    Launch the API
    """

    from . import routes  # pylint: disable=import-outside-toplevel, unused-import

    def _cleanup_callback(signum, frame):  # pylint: disable=unused-argument
        """
        Cleanup function to be called when the program is interrupted
        """

        # Perform any necessary cleanup
        routes.cleanup_cameras()

        sys.exit(0)

    signal.signal(signal.SIGINT, _cleanup_callback)

    # Lauch server
    _socketio.run(
        _app,
        host=os.environ["HOST"],
        port=int(os.environ["PORT"]),
        debug=False,
        use_reloader=os.getenv("HOT_RELOAD") == "true",
        log_output=False,
    )


if __name__ == "__main__":
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        __package__ = str("argos_node")  # pylint: disable=redefined-builtin

    main()
