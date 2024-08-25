"""
This module is the entry point of ARGOS - node.
"""

from __future__ import annotations


import os
import sys

from . import app as _app
from . import socketio as _socketio


def main() -> None:
    """
    Launch the API
    """

    from . import routes  # pylint: disable=import-outside-toplevel, unused-import

    # Lauch server
    _socketio.run(
        _app,
        host=os.environ["HOST"],
        port=int(os.environ["PORT"]),
        debug=False,
        use_reloader=False,
        log_output=False,
    )


if __name__ == "__main__":
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        __package__ = str("argos_node")  # pylint: disable=redefined-builtin

    main()
