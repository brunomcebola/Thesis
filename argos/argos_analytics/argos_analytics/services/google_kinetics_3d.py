"""
This service ...
"""

from __future__ import annotations

import os
import time
import pickle
import threading
from queue import Queue
import cv2
import requests
import numpy as np
from socketio import Client as SocketIO_Client
from flask_socketio.namespace import Namespace

from .. import logger as _logger
from .. import socketio as _socketio


service_name = os.path.basename(__file__).split(".")[0]
service_sio = SocketIO_Client(reconnection=True)

raw_data_queues: dict[str, Queue[dict[str, np.ndarray | None]]] = {}

_socketio.on_namespace(Namespace(f"/{service_name}"))

current_frame = None


def _connect_service():
    while not service_sio.connected:
        try:
            service_sio.connect(
                f"http://{os.getenv('HOST')}:{os.getenv('PORT')}", namespaces=f"/{service_name}"
            )
            break
        except Exception:  # pylint: disable=broad-except
            time.sleep(1)

    _logger.info("Service '%s' launched", service_name)


def _display_image():
    global current_frame

    while True:
        print(current_frame)
        if current_frame is not None:
            cv2.imshow("Received Image", current_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


def _camera_callback(event, data) -> None:
    global current_frame

    frame = pickle.loads(data)

    if frame["color"] is not None:
        current_frame = frame["color"]


@service_sio.event(namespace=f"/{service_name}")
def connect():
    """
    Handler for the connection event
    """

    try:
        requests.put(
            f"http://{os.getenv('MASTER_ADDRESS')}/nodes/emit_update_events_list_events",
            timeout=5,
        )
    except Exception as e:  # pylint
        raise RuntimeError(
            f"Unable to set set handlers for socket communication with master in service '{service_name}'."  # pylint: disable=line-too-long
        ) from e


@service_sio.on("update_events_list", namespace=f"/{service_name}")  # type: ignore
def update_events_list(data):
    """
    Sends the list of events to the client
    """

    # Remove unnecessary handlers
    handlers_to_keep = [f"{data['node_id']}_{camera}" for camera in data["cameras"]]

    service_sio.handlers[f"/{service_name}"] = {
        k: v for k, v in service_sio.handlers[f"/{service_name}"].items() if k in handlers_to_keep
    }

    # Add missing handlers
    for camera in data["cameras"]:
        if f"{data['node_id']}_{camera}" not in service_sio.handlers[f"/{service_name}"]:
            service_sio.on(
                f"{data['node_id']}_{camera}",
                lambda x: _camera_callback(
                    f"{data['node_id']}_{camera}", x  # pylint: disable=cell-var-from-loop
                ),
                namespace=f"/{service_name}",
            )


threading.Thread(target=_connect_service, daemon=True).start()

threading.Thread(target=_display_image, daemon=True).start()
