"""
Web controller module.
"""

from __future__ import annotations

import os

from http import HTTPStatus
from flask import Blueprint, current_app, jsonify

handler = Blueprint("web_handlers", __name__)

# serve the Vue app
@handler.route("/", defaults={"path": ""})
@handler.route("/<path:path>")
def serve_vue_app(path):
    """
    Serve the Vue app
    """
    if path != "" and os.path.exists(app.static_folder + "/" + path):  # type: ignore
        return send_from_directory(app.static_folder, path)  # type: ignore
    else:
        return send_from_directory(app.static_folder, "index.html")  # type: ignore
