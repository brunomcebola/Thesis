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

    cameras = realsense.connected_cameras()

    return jsonify(cameras), HTTPStatus.OK


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


@handler.route("/cameras/<serial_number>/stream/start", methods=["GET"])
def start_stream(serial_number: str):
    """
    Start the streaming of a camera.
    """

    cameras: dict[str, realsense.Camera] = current_app.config["cameras"]

    # check if camera exists
    if serial_number not in cameras:
        return jsonify("Camera not connected."), HTTPStatus.NOT_FOUND

    # check if camera is operational
    if cameras[serial_number].is_stopped:
        return jsonify("Camera not operational."), HTTPStatus.SERVICE_UNAVAILABLE

    # check if camera is already streaming
    if cameras[serial_number].is_streaming:
        return jsonify("Camera already streaming."), HTTPStatus.OK

    cameras[serial_number].start_streaming()

    current_app.config["logger"].info(f"Camera {serial_number} streaming started.")

    return jsonify("Camera streaming started."), HTTPStatus.OK


@handler.route("/cameras/<serial_number>/stream/pause", methods=["GET"])
def pause_stream(serial_number: str):
    """
    Pause the streaming of a camera.
    """

    cameras: dict[str, realsense.Camera] = current_app.config["cameras"]

    # check if camera exists
    if serial_number not in cameras:
        return jsonify("Camera not connected."), HTTPStatus.NOT_FOUND

    # check if camera is operational
    if cameras[serial_number].is_stopped:
        return jsonify("Camera not operational."), HTTPStatus.SERVICE_UNAVAILABLE

    # check if camera is already paused
    if not cameras[serial_number].is_streaming:
        return jsonify("Camera already paused."), HTTPStatus.OK

    cameras[serial_number].pause_streaming()

    current_app.config["logger"].info(f"Camera {serial_number} streaming paused.")

    return jsonify("Camera streaming paused."), HTTPStatus.OK
