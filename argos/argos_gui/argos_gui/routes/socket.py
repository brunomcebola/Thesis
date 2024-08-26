"""
This file contains the socket handlers for the connection with master
"""

import os
import io
import time
import threading
import pickle
import base64
import requests
from PIL import Image
from socketio import Client

from .. import socketio as _socketio
from .. import logger as _logger

master_sio: Client = Client(reconnection=True)


def _retry_connect():
    while master_sio and not master_sio.connected:
        try:
            master_sio.connect(f"http://{os.getenv('MASTER_ADDRESS')}", namespaces=["/", "/gui"])
            break
        except Exception:  # pylint: disable=broad-except
            time.sleep(1)


def _camera_callback(event, data) -> None:
    frame = pickle.loads(data)

    # Send image to GUI
    if frame["color"] is not None:
        # Convert BGR to RGB
        rgb_image = frame["color"][..., ::-1]

        pil_image = Image.fromarray(rgb_image)

        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG")

        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        _socketio.emit(event, img_base64)


@master_sio.event(namespace="/gui")
def connect():
    """
    Handler for the connection event
    """

    _logger.info("Connected to master")

    try:
        requests.put(
            f"http://{os.getenv('MASTER_ADDRESS')}/nodes/emit_update_events_list_events",
            timeout=5,
        )
    except Exception as e:  # pylint
        raise RuntimeError(
            "Unable to set set handlers for socket communication with master."
        ) from e


@master_sio.event(namespace="/gui")
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

    # Remove unnecessary handlers
    handlers_to_keep = ["connect", "disconnect"] + [
        f"{data['node_id']}_{camera}" for camera in data["cameras"]
    ]

    master_sio.handlers["/gui"] = {
        k: v for k, v in master_sio.handlers["/gui"].items() if k in handlers_to_keep
    }

    # Add missing handlers
    for camera in data["cameras"]:
        if f"{data['node_id']}_{camera}" not in master_sio.handlers["/gui"]:
            master_sio.on(
                f"{data['node_id']}_{camera}",
                lambda x: _camera_callback(
                    f"{data['node_id']}_{camera}", x  # pylint: disable=cell-var-from-loop
                ),
                namespace="/gui",
            )


# Connect to the master
try:
    master_sio.connect(f"http://{os.getenv('MASTER_ADDRESS')}", namespaces=["/", "/gui"])
except Exception:  # pylint: disable=broad-except
    _logger.warning("Unable to connect to master. Retrying in background...")
    threading.Thread(target=_retry_connect, daemon=True).start()
