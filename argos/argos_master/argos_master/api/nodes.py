"""
This module contains the routes to interact with the nodes.
"""

import os
import pickle
import io
from http import HTTPStatus
import base64
from functools import wraps
import yaml
import requests
import jsonschema
import socketio
import socketio.exceptions
from PIL import Image
from flask import Blueprint, jsonify, send_file, request, Response

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


def _camera_callback(data, node, camera):
    frame = pickle.loads(data)

    # TODO: ensure sequential order of frames

    if frame["color"] is not None:
        # Convert BGR to RGB
        rgb_image = frame["color"][:, :, ::-1]

        pil_image = Image.fromarray(rgb_image)

        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG")

        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        _socketio.emit(f"{node}_{camera}", img_base64)


def _connect_node(node: dict) -> None:
    """
    Connects to a node and sets the callbacks of the cameras
    """

    def _disconnect_callback():
        _logger.info("Disconnected from node %s at %s.", node["id"], node["address"])
        node["sio"] = None

    # Create socketio connection for node
    try:
        node["sio"] = socketio.Client()

        node["sio"].connect(f"http://{node['address']}")

        _logger.info("Connected to node %s at %s.", node["id"], node["address"])

        node["sio"].on("disconnect", _disconnect_callback)

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


def _verify_node_existance(f):
    """
    Decorator to verify if a node exists
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Find the node in the global nodes_list
        node = next((node for node in nodes_list if node["id"] == kwargs["node_id"]), None)

        # If the node is not found, return a 404 error
        if node is None:
            return (
                jsonify({"error": "Node not found."}),
                HTTPStatus.NOT_FOUND,
            )

        # If the node is found, pass it to the route function
        return f(node=node, *args, **kwargs)

    return decorated_function


def _redirect_request_to_node(f):
    """
    Decorator to redirect the request to the node
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Construct the target URL for proxying

        if "node" not in kwargs:
            return (
                jsonify({"error": "Internal error."}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        route = request.path.split(f"/api/nodes/{kwargs['node']['id']}/")[1]
        target_url = f"http://{kwargs['node']['address']}/{route}"

        try:

            # Forward the request to the target URL using requests
            response = requests.request(
                method=request.method,
                url=target_url,
                params=request.args.to_dict(flat=False) if request.args else None,
                json=request.json if "Content-Type" in dict(request.headers) else None,
                timeout=5,
            )
            # Convert the proxied response to a Flask Response object
            response = (
                jsonify(response.json()),
                response.status_code,
            )

            # Pass the response object to the wrapped function
            return f(response, *args, **kwargs)

        except requests.exceptions.RequestException:
            return (
                jsonify({"error": "Unable to connect to node."}),
                HTTPStatus.SERVICE_UNAVAILABLE,
            )

    return decorated_function


@blueprint.errorhandler(Exception)
def handle_exception(e):
    """
    Handles exceptions
    """

    _logger.warning(e)

    return (
        jsonify({"error": "Internal error."}),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@blueprint.route("/")
def nodes(*args, **kwargs):  # pylint: disable=unused-argument
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
def create_node(*args, **kwargs):  # pylint: disable=unused-argument
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
            jsonify({"error": "Invalid data"}),
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

    # Log creation
    _logger.info(
        "Added node %s (%s @ %s)", node_data["id"], node_data["name"], node_data["address"]
    )

    # Connect to node
    _connect_node(node_data)

    # Return a success message with the newly created node
    return (
        jsonify({"message": "Node created successfully"}),
        HTTPStatus.CREATED,
    )


@blueprint.route("/<int:node_id>", methods=["PUT"])
@_verify_node_existance
def edit_node(node: dict, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Edits node
    """

    # Get the textual data
    node_data: dict = {"name": request.form.get("name"), "address": request.form.get("address")}

    if not node_data:
        return (
            jsonify({"error": "No data provided"}),
            HTTPStatus.BAD_REQUEST,
        )

    node_data["id"] = node["id"]
    node_data["has_image"] = node["has_image"]

    # Validate provided data structure
    try:
        jsonschema.validate(instance=[node_data], schema=NODES_CONFIG_SCHEMA)
    except jsonschema.ValidationError:
        return (
            jsonify({"error": "Invalid data"}),
            HTTPStatus.BAD_REQUEST,
        )

    # Ensure name is not taken
    names = [node["name"] for node in nodes_list]
    if node_data["name"] in names and node_data["name"] != node["name"]:
        return (
            jsonify({"error": "Name already in use."}),
            HTTPStatus.BAD_REQUEST,
        )

    # Ensure unique addresses
    addresses = [node["address"] for node in nodes_list]
    if node_data["address"] in addresses and node_data["address"] != node["address"]:
        return (
            jsonify({"error": "Address already in use."}),
            HTTPStatus.BAD_REQUEST,
        )

    # Disconnect from node
    if node["sio"]:
        node["sio"].disconnect()

    # Update node
    node["name"] = node_data["name"]
    node["address"] = node_data["address"]

    # Edit nodes.yaml
    with open(NODES_FILE, "w", encoding="utf-8") as f:
        keys_to_keep = ["id", "name", "address", "has_image"]
        sanitized_nodes_list = [
            {key: value for key, value in node.items() if key in keys_to_keep}
            for node in nodes_list
        ]

        yaml.safe_dump(sanitized_nodes_list, f, sort_keys=False)

    # Log creation
    _logger.info(
        "Edited node %s (%s @ %s)", node_data["id"], node_data["name"], node_data["address"]
    )

    # Connect to node
    _connect_node(node_data)

    # Return a success message with the newly created node
    return (
        jsonify({"message": "Node edited successfully"}),
        HTTPStatus.CREATED,
    )


@blueprint.route("/<int:node_id>", methods=["DELETE"])
@_verify_node_existance
def delete_node(node: dict, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Deletes a node
    """

    node_id = node["id"]
    node_name = node["name"]
    node_address = node["address"]

    # Remove the node from the nodes_list
    if node["sio"]:
        node["sio"].disconnect()
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
        if file.startswith(str(node_id)):
            os.remove(os.path.join(IMAGES_DIR, file))

    _logger.info("Removed node %s (%s @ %s)", node_id, node_name, node_address)

    # Return a success message
    return (
        jsonify({"message": "Node deleted successfully."}),
        HTTPStatus.OK,
    )


@blueprint.route("/<int:node_id>/image")
@_verify_node_existance
def image(node: dict, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Returns the image of the node
    """

    # Get the node image
    for file in os.listdir(IMAGES_DIR):
        if file.startswith(str(node["id"])):
            return send_file(os.path.join(IMAGES_DIR, file))

    return (
        jsonify({"error": "Image not found."}),
        HTTPStatus.NOT_FOUND,
    )


@blueprint.route("/<int:node_id>/logs")
@_verify_node_existance
@_redirect_request_to_node
def logs(response: tuple[Response, int], *args, **kwargs):  # pylint: disable=unused-argument
    """
    Returns a list with the cameras of the node
    """

    return response


#
# Camera related route
#


@blueprint.route("/<int:node_id>/cameras")
@_verify_node_existance
@_redirect_request_to_node
def cameras(response: tuple[Response, int], *args, **kwargs):  # pylint: disable=unused-argument
    """
    Returns a list with the cameras of a node
    """

    return response


@blueprint.route("/<int:node_id>/cameras/<string:camera_id>/config")
@_verify_node_existance
@_redirect_request_to_node
def get_camera_config(
    response: tuple[Response, int], *args, **kwargs
):  # pylint: disable=unused-argument
    """
    Returns the configuration of a camera
    """

    return response


@blueprint.route("/<int:node_id>/cameras/<string:camera_id>/config", methods=["PUT"])
@_verify_node_existance
@_redirect_request_to_node
def edit_camera_config(
    response: tuple[Response, int], *args, **kwargs
):  # pylint: disable=unused-argument
    """
    Edits the configuration of a camera
    """

    return response


@blueprint.route("/<int:node_id>/cameras/<string:camera_id>/status")
@_verify_node_existance
@_redirect_request_to_node
def get_camera_stream_status(
    response: tuple[Response, int], *args, **kwargs
):  # pylint: disable=unused-argument
    """
    Returns the status of a camera
    """

    return response


@blueprint.route("/<int:node_id>/cameras/<string:camera_id>/restart", methods=["PUT"])
@_verify_node_existance
@_redirect_request_to_node
def set_camera_stream_status(
    response: tuple[Response, int], *args, **kwargs
):  # pylint: disable=unused-argument
    """
    Restarts a camera
    """

    return response
