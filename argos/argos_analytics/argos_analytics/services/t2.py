"""
This service ...
"""

import os
import time
import threading

from socketio import Client as SocketIO_Client
from flask_socketio.namespace import Namespace

from .. import logger as _logger
from .. import socketio as _socketio


service_name = os.path.basename(__file__).split(".")[0]
service_sio = SocketIO_Client(reconnection=True)

_socketio.on_namespace(Namespace(f"/{service_name}"))


def _connect_service():
    while not service_sio.connected:
        try:
            service_sio.connect(
                f"http://{os.getenv('HOST')}:{os.getenv('PORT')}", namespaces=f"/{service_name}"
            )
            break
        except Exception:  # pylint: disable=broad-except
            time.sleep(1)

    _logger.info("Service '%s' running", service_name)


threading.Thread(target=_connect_service, daemon=True).start()


@service_sio.on("*", namespace=f"/{service_name}")  # type: ignore
def test(event, *args, **kwargs):
    print(event)
