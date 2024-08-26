"""
This module is the entry point of ARGOS - master.
"""

from __future__ import annotations

import os
import sys

from . import app as _app
from . import socketio as _socketio


def main():
    """
    Main function of the program
    """

    from . import handlers  # pylint: disable=import-outside-toplevel, unused-import
    from . import routes  # pylint: disable=import-outside-toplevel, unused-import

    # @_socketio.on('connect', namespace='/gui')
    # def on_disconnect():
    #     print('Client disconnected from /gui namespace')

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
        __package__ = str("argos_master")  # pylint: disable=redefined-builtin

    main()
