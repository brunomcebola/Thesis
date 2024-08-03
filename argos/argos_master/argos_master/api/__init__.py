"""
Init file for the API module.
"""

from http import HTTPStatus
from flask import Flask, Blueprint
from flask_socketio import SocketIO

from . import datasets
from . import nodes
from . import cameras


def register(app: Flask, socketio: SocketIO):
    """
    Register the GUI views
    """

    # Register the routes

    nodes.init()
    # cameras.init()

    blueprint = Blueprint("api", __name__, url_prefix="/api")

    blueprint.register_blueprint(datasets.blueprint)
    blueprint.register_blueprint(nodes.blueprint)
    blueprint.register_blueprint(cameras.blueprint)

    app.register_blueprint(blueprint)
