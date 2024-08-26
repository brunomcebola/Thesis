"""
Init file for the routes module.
"""

from .. import app as _app


from . import socket
from . import ui as _ui
from . import api as _api

_app.register_blueprint(_api.blueprint)
_app.register_blueprint(_ui.blueprint)
