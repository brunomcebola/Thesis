"""
This module contains the routes to interact with the nodes.
"""

from http import HTTPStatus
from flask import Blueprint, jsonify, send_file, request


from .. import logger as _logger
from ..handlers.nodes import nodes_handler


blueprint = Blueprint("nodes", __name__, url_prefix="/nodes")


@blueprint.errorhandler(Exception)
def handle_exception(e):
    """
    Handles exceptions
    """

    _logger.warning(e)

    return (
        jsonify("Internal error."),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@blueprint.route("/")
def get_nodes():
    """
    Returns the nodes
    """

    return (
        jsonify(nodes_handler.get_nodes()),
        HTTPStatus.OK,
    )


@blueprint.route("/", methods=["POST"])
def create_node():
    """
    Creates new node
    """

    # Create the node
    try:
        nodes_handler.create_node(
            request.form.get("name", ""),
            request.form.get("address", ""),
            request.files["image"],
        )
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    # Return a success message with the newly created node
    return (
        jsonify("Node created successfully"),
        HTTPStatus.CREATED,
    )


@blueprint.route("/emit_update_events_list_events", methods=["PUT"])
def force_update_events_list():
    """
    Force update events list
    """

    nodes_handler.emit_update_events_list_events()

    return (
        jsonify("Emitted update events list events for all nodes"),
        HTTPStatus.OK,
    )


@blueprint.route("/<int:node_id>", methods=["PUT"])
def edit_node(node_id: int):
    """
    Edits node
    """

    # Edit the node
    try:
        nodes_handler.edit_node(
            node_id,
            request.form.get("name"),
            request.form.get("address"),
        )
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    # Return a success message with the newly created node
    return (
        jsonify("Node edited successfully"),
        HTTPStatus.CREATED,
    )


@blueprint.route("/<int:node_id>", methods=["DELETE"])
def delete_node(node_id: int):
    """
    Deletes a node
    """

    # Delete the node
    try:
        nodes_handler.delete_node(node_id)
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    # Return a success message
    return (
        jsonify("Node deleted successfully."),
        HTTPStatus.OK,
    )


@blueprint.route("/<int:node_id>/image")
def get_node_image(node_id: int):
    """
    Returns the image of the node
    """

    # Get the node image
    try:
        image_path = nodes_handler.get_node_image(node_id)
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    if image_path:
        return send_file(image_path)

    return (
        jsonify("Image not found."),
        HTTPStatus.NOT_FOUND,
    )


@blueprint.route("/<int:node_id>/cameras")
def get_node_cameras(node_id: int):
    """
    Returns the image of the node
    """

    # Get the node image
    try:
        cameras = nodes_handler.get_node_cameras(node_id)
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    return (
        jsonify(cameras),
        HTTPStatus.OK,
    )


@blueprint.route("/<int:node_id>/cameras/<int:camera_id>/recording")
def get_camera_recording(node_id: int, camera_id: int):
    """
    Returns the camera recording
    """

    # Get the camera recording
    try:
        recording = nodes_handler.get_node_camera_recording(node_id, str(camera_id))
    except Exception as e: # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    return (
        jsonify(recording),
        HTTPStatus.OK,
    )


@blueprint.route("/<int:node_id>/cameras/<int:camera_id>/recording", methods=["PUT"])
def toggle_camera_recording(node_id: int, camera_id: int):
    """
    Toggles the camera recording
    """

    # Toggle the camera recording
    try:
        nodes_handler.toggle_node_camera_recording(node_id, str(camera_id))
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    return (
        jsonify("Camera recording toggled successfully."),
        HTTPStatus.OK,
    )


@blueprint.route("/<int:node_id>/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def redirect_to_node(node_id: int, subpath: str):
    """
    Redirects the request to the node
    """
    try:
        return nodes_handler.redirect_request_to_node(node_id, subpath, request)
    except ValueError as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )
    except ConnectionError as e:
        return (
            jsonify(str(e)),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )
