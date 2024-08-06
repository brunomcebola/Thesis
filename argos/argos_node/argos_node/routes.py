"""
Cameras controller module.
"""

from __future__ import annotations

from http import HTTPStatus
from flask import Blueprint, current_app, jsonify

from . import realsense

handler = Blueprint("cameras_handlers", __name__)


@handler.route("/cameras", methods=["GET"])
def get_cameras():
    """
    Get the list of connected cameras.
    """

    cameras: dict[str, realsense.Camera] = current_app.config["cameras"]

    return jsonify(list(cameras.keys())), HTTPStatus.OK


@handler.route("/cameras/<serial_number>/status", methods=["GET"])
def get_camera(serial_number: str):
    """
    Get the details of a camera.
    """

    cameras: dict[str, realsense.Camera] = current_app.config["cameras"]

    # check if camera exists
    if serial_number not in cameras:
        return jsonify("Camera not connected."), HTTPStatus.NOT_FOUND

    # check if camera is operational
    if cameras[serial_number].is_stopped:
        return jsonify("Camera not operational."), HTTPStatus.SERVICE_UNAVAILABLE

    return jsonify("Camera operational."), HTTPStatus.OK


@handler.route("/cameras/<string:serial_number>/stream/<string:action>", methods=["GET"])
def start_stream(serial_number: str, action: str):
    """
    Start the streaming of a camera.
    """

    if action not in ["start", "stop"]:
        return jsonify("Invalid action."), HTTPStatus.BAD_REQUEST

    cameras: dict[str, realsense.Camera] = current_app.config["cameras"]

    # check if camera exists
    if serial_number not in cameras:
        return jsonify("Camera not connected."), HTTPStatus.NOT_FOUND

    # check if camera is operational
    if cameras[serial_number].is_stopped:
        return jsonify("Camera not operational."), HTTPStatus.SERVICE_UNAVAILABLE

    # check if camera is already streaming
    if action == "start" and cameras[serial_number].is_streaming:
        return jsonify("Camera stream already started."), HTTPStatus.OK
    elif action == "stop" and not cameras[serial_number].is_streaming:
        return jsonify("Camera stream already stopped."), HTTPStatus.OK

    getattr(cameras[serial_number], f"{action}_stream")()

    if action == "play":
        current_app.config["logger"].info(f"Camera {serial_number} stream started.")
        return jsonify("Camera stream started."), HTTPStatus.OK
    else:
        current_app.config["logger"].info(f"Camera {serial_number} stream stopped.")
        return jsonify("Camera stream started."), HTTPStatus.OK
