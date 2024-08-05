"""
Init file for the API module.
"""

from flask import Blueprint

from .. import app as _app

from . import datasets as _datasets
from . import nodes as _nodes

blueprint = Blueprint("api", __name__, url_prefix="/api")

blueprint.register_blueprint(_datasets.blueprint)
blueprint.register_blueprint(_nodes.blueprint)

_app.register_blueprint(blueprint)
