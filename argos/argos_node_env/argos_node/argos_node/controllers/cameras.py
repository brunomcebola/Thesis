"""
Cameras controller module.
"""

from __future__ import annotations

from http import HTTPStatus
from flask import Blueprint, current_app, jsonify

from ..namespace import NodeNamespace

handler = Blueprint("cameras_handlers", __name__, url_prefix="/cameras")


@handler.route("/", methods=["GET"])
def get_cameras():
    """
    Get the list of cameras.
    """

    node_namespace: NodeNamespace = current_app.config["namespace"]

    return jsonify(node_namespace.cameras_sn), HTTPStatus.OK


@handler.route("/<serial_number>/stream/start", methods=["GET"])
def start_stream(serial_number: str):
    """
    Start the streaming of a camera.
    """

    node_namespace: NodeNamespace = current_app.config["namespace"]

    # check if camera exists
    if serial_number not in node_namespace.cameras_sn:
        return jsonify("Camera not found."), HTTPStatus.NOT_FOUND

    node_namespace.camera_interaction(
        serial_number, node_namespace.CameraInteraction.START_STREAMING
    )

    return jsonify(""), HTTPStatus.OK


@handler.route("/<serial_number>/stream/pause", methods=["GET"])
def stop_stream(serial_number: str):
    """
    Pause the streaming of a camera.
    """

    node_namespace: NodeNamespace = current_app.config["namespace"]

    # check if camera exists
    if serial_number not in node_namespace.cameras_sn:
        return jsonify("Camera not found."), HTTPStatus.NOT_FOUND

    node_namespace.camera_interaction(
        serial_number, node_namespace.CameraInteraction.PAUSE_STREAMING
    )

    return jsonify(""), HTTPStatus.OK
