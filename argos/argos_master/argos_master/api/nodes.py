"""
This module contains the routes to interact with the nodes.
"""

import os
import pickle
import io
from http import HTTPStatus
import base64
import yaml
import requests
import jsonschema
import socketio
import socketio.exceptions
from PIL import Image
from flask import Blueprint, jsonify, send_file, request

from .. import logger as _logger
from .. import socketio as _socketio  # pylint: disable=reimported

blueprint = Blueprint("nodes", __name__, url_prefix="/nodes")

NODES_DIR = os.path.join(os.environ["BASE_DIR"], "nodes")
NODES_FILE = os.path.join(NODES_DIR, "nodes.yaml")
IMAGES_DIR = os.path.join(NODES_DIR, "images")

NODES_CONFIG_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "minimum": 1,
            },
            "name": {
                "type": "string",
                "pattern": "^[A-Za-zÀ-ÖØ-öø-ÿ0-9-_ ]+$",
            },
            "address": {
                "type": "string",
                "pattern": "^((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]).){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9]):(6553[0-5]|655[0-2][0-9]|65[0-4][0-9]|6[0-4][0-9]{3}|[1-5][0-9]{4}|[1-9][0-9]{0,3}|0)$",  # pylint: disable=line-too-long
            },
            "has_image": {
                "type": "boolean",
            },
        },
        "required": ["id", "name", "address", "has_image"],
        "additionalProperties": False,
    },
    "uniqueItems": True,
}


nodes_list: list[dict] = []


class NodeConfigurationException(Exception):
    """
    Custom exception class for nodes
    """


def _connect_node(node: dict) -> None:
    """
    Connects to a node and sets the callbacks of the cameras
    """

    def _camera_callback(data, node, camera):
        frame = pickle.loads(data)

        # TODO: ensure sequential order of frames

        if frame[0] is not None:
            # Convert BGR to RGB
            rgb_image = frame[0][:, :, ::-1]
            # rgb_image = frame[0]

            pil_image = Image.fromarray(rgb_image)

            buffer = io.BytesIO()
            pil_image.save(buffer, format="JPEG")

            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            _socketio.emit(f"{node}_{camera}", img_base64)

    def _disconnect_callback():
        _logger.info("Disconnected from node %s at %s.", node["id"], node["address"])
        node["sio"] = None

    # Create socketio connection for node
    try:
        node["sio"] = socketio.Client()

        node["sio"].connect(f"http://{node['address']}")

        node["sio"].on("disconnect", _disconnect_callback)

        _logger.info("Connected to node %s at %s.", node["id"], node["address"])

    except socketio.exceptions.ConnectionError:
        _logger.info("Failed to connected to node %s at %s.", node["id"], node["address"])

        node["sio"] = None

    # Get cameras and set callbacks
    if node["sio"] is not None:
        try:
            response = requests.get(f"http://{node['address']}/cameras", timeout=5)
            node["cameras"] = response.json() if response.status_code == HTTPStatus.OK else []
            for camera in node["cameras"]:
                node["sio"].on(
                    camera,
                    lambda data: _camera_callback(
                        data, node["id"], camera  # pylint: disable=cell-var-from-loop
                    ),
                )
        except Exception:  # pylint: disable=broad-except
            node["cameras"] = []
    else:
        node["cameras"] = []


def _init() -> None:
    """
    Initializes the nodes module
    """
    global nodes_list  # pylint: disable=global-statement

    #  Create base folder if it doesn't exist
    os.makedirs(NODES_DIR, exist_ok=True)

    # Create images folde if it doesn't exist
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Create nodes file if it doesn't exist
    with open(NODES_FILE, "a", encoding="utf-8"):
        pass

    # Get nodes from file
    with open(NODES_FILE, "r", encoding="utf-8") as f:
        try:
            nodes_list = yaml.safe_load(f) or []
        except Exception as e:  # pylint: disable=broad-except
            raise NodeConfigurationException("Invalid nodes configuration file") from e

    if nodes_list:
        try:
            jsonschema.validate(instance=nodes_list, schema=NODES_CONFIG_SCHEMA)
        except jsonschema.ValidationError as e:
            if not e.path:
                raise NodeConfigurationException(f"Invalid configuration ({e.message}).") from e
            else:
                raise NodeConfigurationException(
                    f"Invalid configuration ({e.message} for instance {e.path[0]}: {e.instance})."
                ) from e

        # Ensure unique ids
        ids = [node["id"] for node in nodes_list]
        if len(ids) != len(set(ids)):
            duplicate_id = next(id_ for id_ in ids if ids.count(id_) > 1)
            raise NodeConfigurationException(f"Duplicated ids ({duplicate_id}).")

        # Ensure unique names
        names = [node["name"] for node in nodes_list]
        if len(names) != len(set(names)):
            duplicate_name = next(name for name in names if names.count(name) > 1)
            raise NodeConfigurationException(f"Duplicated names ({duplicate_name}).")

        # Ensure unique addresses
        addresses = [node["address"] for node in nodes_list]
        if len(addresses) != len(set(addresses)):
            duplicate_address = next(
                address for address in addresses if addresses.count(address) > 1
            )
            raise NodeConfigurationException(f"Duplicated addresses ({duplicate_address}).")

        # Connect to nodes
        for node in nodes_list:
            _connect_node(node)


#
# Initialization
#

_init()

#
# Routes
#


@blueprint.errorhandler(Exception)
def handle_exception(_):
    """
    Handles exceptions
    """

    return (
        jsonify({"error": "Internal error."}),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@blueprint.route("/")
def nodes():
    """
    Returns the nodes
    """

    keys_to_keep = ["id", "name", "address", "has_image"]
    sanitized_nodes = []
    for node in nodes_list:
        sanitized_nodes.append({key: value for key, value in node.items() if key in keys_to_keep})

    return (
        jsonify(sanitized_nodes),
        HTTPStatus.OK,
    )


@blueprint.route("/", methods=["POST"])
def create_node():
    """
    Creates new node
    """

    # Get the textual data
    node_data: dict = {"name": request.form.get("name"), "address": request.form.get("address")}

    if not node_data:
        return (
            jsonify({"error": "No data provided"}),
            HTTPStatus.BAD_REQUEST,
        )

    # Get the image
    node_image = request.files["image"]
    node_data["has_image"] = True if node_image.filename else False

    # Attribute id to node
    ids = [node["id"] for node in nodes_list]
    node_data["id"] = max(ids) + 1 if len(ids) else 1

    # Validate provided data structure
    try:
        jsonschema.validate(instance=[node_data], schema=NODES_CONFIG_SCHEMA)
    except jsonschema.ValidationError:
        return (
            jsonify({"error": "Invalid data format"}),
            HTTPStatus.BAD_REQUEST,
        )

    # Ensure name is not taken
    names = [node["name"] for node in nodes_list]
    if node_data["name"] in names:
        return (
            jsonify({"error": "Name already in use."}),
            HTTPStatus.BAD_REQUEST,
        )

    # Ensure unique addresses
    addresses = [node["address"] for node in nodes_list]
    if node_data["address"] in addresses:
        return (
            jsonify({"error": "Address already in use."}),
            HTTPStatus.BAD_REQUEST,
        )

    # Add to nodes.yaml
    with open(NODES_FILE, "a", encoding="utf-8") as f:
        yaml.safe_dump([node_data], f, sort_keys=False)

    # Save image
    if node_data["has_image"]:
        extension = node_image.filename.split(".")[-1].lower()  # type: ignore
        node_image.save(f"{IMAGES_DIR}/{node_data['id']}.{extension}")

    # Add the new node to the nodes_list
    nodes_list.append(node_data)

    # Connect to node
    _connect_node(node_data)

    # Return a success message with the newly created node
    return (
        jsonify({"message": "Node created successfully"}),
        HTTPStatus.CREATED,
    )


@blueprint.route("/<int:node_id>", methods=["DELETE"])
def delete_node(node_id: int):
    """
    Deletes a node
    """

    # Get the node
    node = next((node for node in nodes_list if node["id"] == node_id), None)
    if node is None:
        return (
            jsonify({"error": "Node not found."}),
            HTTPStatus.NOT_FOUND,
        )

    # Remove the node from the nodes_list
    nodes_list.remove(node)

    # Remove the node from the nodes.yaml
    with open(NODES_FILE, "w", encoding="utf-8") as f:
        keys_to_keep = ["id", "name", "address", "has_image"]
        sanitized_nodes_list = [
            {key: value for key, value in node.items() if key in keys_to_keep}
            for node in nodes_list
        ]

        if not sanitized_nodes_list:
            f.write("")
        else:
            yaml.safe_dump(sanitized_nodes_list, f, sort_keys=False)

    # Remove the image
    for file in os.listdir(IMAGES_DIR):
        if file.startswith(f"{node_id}."):
            os.remove(os.path.join(IMAGES_DIR, file))

    # Return a success message
    return (
        jsonify({"message": "Node deleted successfully."}),
        HTTPStatus.OK,
    )


@blueprint.route("/<int:node_id>/image")
def image(node_id: int):
    """
    Returns the image of the node
    """

    if node_id not in [node["id"] for node in nodes_list]:
        return (
            jsonify({"error": "Node not found."}),
            HTTPStatus.NOT_FOUND,
        )

    # Get the node image
    for file in os.listdir(IMAGES_DIR):
        if file.startswith(f"{node_id}."):
            return send_file(os.path.join(IMAGES_DIR, file))

    return (
        jsonify({"error": "Image not found."}),
        HTTPStatus.NOT_FOUND,
    )


@blueprint.route("/<int:node_id>/cameras")
def cameras(node_id: int):
    """
    Returns a list with the cameras of the node
    """

    # Get the node
    node = next((node for node in nodes_list if node["id"] == node_id), None)
    if node is None:
        return (
            jsonify({"error": "Node not found."}),
            HTTPStatus.NOT_FOUND,
        )

    # Try to connect node if it's not connected
    if node["sio"] is None:
        _connect_node(node)

    if node["sio"] is None:
        raise RuntimeError("Failed to connect to node.")

    # Make a GET request to retrieve the list of cameras
    response = requests.get(f"http://{node['address']}/cameras", timeout=5)

    return (
        jsonify(response.json() if response.status_code == HTTPStatus.OK else []),
        HTTPStatus.OK,
    )


@blueprint.route("/<int:node_id>/cameras/<string:camera_id>/stream")
def get_camera_stream_status(node_id: int, camera_id: str):
    """
    Returns the status of the camera stream for a specific node and camera
    """

    # Get the node
    node = next((node for node in nodes_list if node["id"] == node_id), None)
    if node is None:
        return (
            jsonify({"error": "Node not found."}),
            HTTPStatus.NOT_FOUND,
        )

    # Try to connect node if it's not connected
    if node["sio"] is None:
        _connect_node(node)

    if node["sio"] is None:
        raise RuntimeError("Failed to connect to node.")

    # Check if camera exists
    if camera_id not in node["cameras"]:
        return (
            jsonify({"error": "Camera not found."}),
            HTTPStatus.NOT_FOUND,
        )

    # Make a GET request to retrieve the status of the camera stream
    response = requests.get(f"http://{node['address']}/cameras/{camera_id}/stream", timeout=5)

    if response.status_code != HTTPStatus.OK:
        return (
            jsonify({"error": "Failed to retrieve camera stream status."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    return (
        jsonify(response.json()),
        HTTPStatus.OK,
    )


@blueprint.route(
    "/<int:node_id>/cameras/<string:camera_id>/stream/<string:action>",
    methods=["POST"],
)
def set_camera_stream(node_id: int, camera_id: str, action: str):
    """
    Starts the camera stream for a specific node and camera
    """

    # Check if valid action
    if action not in ["start", "stop"]:
        return (
            jsonify({"error": "Invalid action."}),
            HTTPStatus.BAD_REQUEST,
        )

    # Get the node
    node = next((node for node in nodes_list if node["id"] == node_id), None)
    if node is None:
        return (
            jsonify({"error": "Node not found."}),
            HTTPStatus.NOT_FOUND,
        )

    # Try to connect node if it's not connected
    if node["sio"] is None:
        _connect_node(node)

    if node["sio"] is None:
        raise RuntimeError("Failed to connect to node.")

    # Check if camera exists
    if camera_id not in node["cameras"]:
        return (
            jsonify({"error": "Camera not found."}),
            HTTPStatus.NOT_FOUND,
        )

    # Make a GET request to start the camera stream
    response = requests.post(
        f"http://{node['address']}/cameras/{camera_id}/stream/{action}", timeout=5
    )

    if response.status_code != HTTPStatus.OK:
        return (
            jsonify({"error": f"Failed to {action} camera stream."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    return (
        jsonify({"message": f"Camera stream {'started' if action == 'start' else 'stopped'}."}),
        HTTPStatus.OK,
    )
