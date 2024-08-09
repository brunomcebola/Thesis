"""
Init file for the routes module.
"""

import os

from .. import app as _app

if os.getenv("WERKZEUG_RUN_MAIN") == "true" or os.getenv("HOT_RELOAD") == "false":
    from . import cameras as _cameras

    _app.register_blueprint(_cameras.blueprint)
