"""
Init file for the routes module.
"""

import os

from .. import app as _app

from . import cameras as _cameras
from . import logs as _logs

_app.register_blueprint(_cameras.blueprint)
_app.register_blueprint(_logs.blueprint)
