"""
Init file for the routes module.
"""

from .. import app as _app

from . import cameras as _cameras

_app.register_blueprint(_cameras.blueprint)

cleanup_cameras = _cameras.cleanup
