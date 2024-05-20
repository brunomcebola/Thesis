"""
Cameras controller module.
"""

from __future__ import annotations

from http import HTTPStatus
from flask import Blueprint, current_app, jsonify

from .. import intel

handler = Blueprint("cameras_handlers", __name__, url_prefix="/cameras")


@handler.route("/<camera_index>/stream/start", methods=["GET"])
def stream(camera_index: int):
    """
    # TODO
    """

    # check if index is valid
    if camera_index < 0 or camera_index >= len(current_app.config["cameras"]):
        return jsonify("Invalid camera."), HTTPStatus.BAD_REQUEST

    camera: intel.RealSenseCamera = current_app.config["cameras"][camera_index]

    # check if camera is stopped
    if camera.is_stopped:
        return jsonify("Camera is not working."), HTTPStatus.BAD_REQUEST

    # check if camera is already streaming
    if camera.is_streaming:
        return jsonify("Camera is already streaming."), HTTPStatus.BAD_REQUEST

    # start streaming
    camera.start_streaming()

    return jsonify("Camera streaming started."), HTTPStatus.OK


@handler.route("/<camera_index>/stream/pause", methods=["GET"])
def stop_stream(camera_index: int):
    """
    # TODO
    """

    # check if index is valid
    if camera_index < 0 or camera_index >= len(current_app.config["cameras"]):
        return jsonify("Invalid camera."), HTTPStatus.BAD_REQUEST

    camera: intel.RealSenseCamera = current_app.config["cameras"][camera_index]

    # check if camera is stopped
    if camera.is_stopped:
        return jsonify("Camera is not working."), HTTPStatus.BAD_REQUEST

    # check if camera is already streaming
    if not camera.is_streaming:
        return jsonify("Camera is already paused."), HTTPStatus.BAD_REQUEST

    # stop streaming
    camera.pause_streaming()

    return jsonify("Camera streaming paused."), HTTPStatus.OK
