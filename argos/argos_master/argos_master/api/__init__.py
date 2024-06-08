"""
Init file for the API module.
"""

from http import HTTPStatus
from flask import Flask, Blueprint

from . import datasets
from . import nodes


def register(app: Flask):
    """
    Register the GUI views
    """

    # Register the routes

    blueprint = Blueprint("api", __name__, url_prefix="/api")

    blueprint.register_blueprint(datasets.blueprint)
    blueprint.register_blueprint(nodes.blueprint)

    app.register_blueprint(blueprint)
