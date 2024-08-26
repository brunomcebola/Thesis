"""
Ĩnit file for the services module
"""

import os

from .. import logger as _logger
from .. import socketio as _socketio
from .. import master_sio as _master_sio

from . import t1
from . import t2

services = [
    file.split(".")[0] for file in os.listdir(os.path.dirname(__file__)) if "__" not in file
]


@_master_sio.on("*", namespace="/analytics")  # type: ignore
def redirect_event(event, *args, **kwargs):
    """
    Redirects all events to the client
    """

    for service in services:
        _socketio.emit(event, *args, **kwargs, namespace=f"/{service}")
