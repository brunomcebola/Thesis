"""
Ĩnit file for the services module
"""

import os
import time
import pkgutil
import threading
import importlib
import requests

from socketio import Client

from .. import logger as _logger
from .. import socketio as _socketio


master_sio: Client = Client(reconnection=True)

services = [
    file.split(".")[0] for file in os.listdir(os.path.dirname(__file__)) if "__" not in file
]


def _retry_connect():
    while master_sio and not master_sio.connected:
        try:
            master_sio.connect(
                f"http://{os.getenv('MASTER_ADDRESS')}", namespaces=["/", "/analytics"]
            )
            break
        except Exception:  # pylint: disable=broad-except
            time.sleep(1)


@master_sio.event(namespace="/analytics")
def connect():
    """
    Handler for the connection event
    """

    _logger.info("Connected to master")

    try:
        requests.put(
            f"http://{os.getenv('MASTER_ADDRESS')}/nodes/emit_update_events_list_events",
            timeout=30,
        )
    except Exception as e:  # pylint
        raise RuntimeError(
            "Unable to set set handlers for socket communication with master."
        ) from e


@master_sio.event(namespace="/analytics")
def disconnect():
    """
    Handler for the disconnection event
    """

    _logger.warning("Disconnected from master")


@master_sio.on("update_events_list")  # type: ignore
def update_events_list(data):
    """
    Sends the list of events to the client
    """

    for service in services:
        _socketio.emit("update_events_list", data, namespace=f"/{service}")


@master_sio.on("*", namespace="/analytics")  # type: ignore
def redirect_event(event, *args, **kwargs):
    """
    Redirects all events to the client
    """

    for service in services:
        _socketio.emit(event, *args, **kwargs, namespace=f"/{service}")


# Connect to the master
try:
    master_sio.connect(f"http://{os.getenv('MASTER_ADDRESS')}", namespaces=["/", "/analytics"])
except Exception:  # pylint: disable=broad-except
    _logger.warning("Unable to connect to master. Retrying in background...")
    threading.Thread(target=_retry_connect, daemon=True).start()


# Import all services
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    if not is_pkg:  # Ignore sub-packages, if any
        module = importlib.import_module(f".{module_name}", package=__name__)
        globals()[module_name] = module
