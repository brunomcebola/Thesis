"""
This module contains the routes to interact with the nodes.
"""

import os
from http import HTTPStatus
import threading
import pickle
import yaml
import jsonschema
from flask import Blueprint, jsonify, send_file
import socketio
import socketio.exceptions
import requests

from .. import logger as _logger
from .. import socketio as _socketio

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


def _node_handler_target(node: dict):
    """
    Target function for the node handler thread
    """

    def _callback(data):
        frame = pickle.loads(data)
        print([f_type.shape if f_type is not None else None for f_type in frame])

    # Creat socketio connection for node
    sio = socketio.Client()

    for camera in node["cameras"]:
        sio.on(camera, _callback)

    try:
        sio.connect(f"http://{node['address']}")

        if os.getenv("WERKZEUG_RUN_MAIN") == "true" or os.getenv("HOT_RELOAD") == "false":
            _logger.info("Connected to node %s at %s.", node["id"], node["address"])

    except socketio.exceptions.ConnectionError:
        return


def _init():
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
        nodes_list = yaml.safe_load(f) or []

    if nodes_list:
        try:
            jsonschema.validate(instance=nodes_list, schema=NODES_CONFIG_SCHEMA)
        except jsonschema.ValidationError as e:
            raise NodeConfigurationException(
                f"Invalid nodes configuration ({e.message} on instance {e.path[0]}: {e.instance})."
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

        # Get the cameras of each node
        for node in nodes_list:
            try:
                response = requests.get(f"http://{node['address']}/cameras", timeout=5)
                node["cameras"] = response.json() if response.status_code == HTTPStatus.OK else []
            except Exception:  # pylint: disable=broad-except
                node["cameras"] = []

        # Launch thread for each node
        for node in nodes_list:
            node["thread"] = threading.Thread(
                target=_node_handler_target,
                args=(node,),
                daemon=True,
            )
            node["thread"].start()


#
# Initialization
#

_init()

#
# Routes
#


@blueprint.errorhandler(Exception)
def handle_exception(e):
    """
    Handles exceptions
    """

    print(e)

    return (
        jsonify({"error": "Internal error."}),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@blueprint.route("/")
def nodes():
    """
    Returns the nodes in BASE_DIR/nodes
    """

    keys_to_keep = ["id", "name", "address", "has_image"]
    sanitized_nodes = []
    for node in nodes_list:
        sanitized_nodes.append({key: value for key, value in node.items() if key in keys_to_keep})

    return (
        jsonify(sanitized_nodes),
        HTTPStatus.OK,
    )


@blueprint.route("/<node_id>/image")
def image(node_id: int):
    """
    Returns the image of the node
    """

    if not any(node["id"] == node_id for node in nodes_list):
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

    # Make a GET request to retrieve the list of cameras
    response = requests.get(f"http://{node['address']}/cameras", timeout=5)

    return (
        jsonify(response.json() if response.status_code == HTTPStatus.OK else []),
        HTTPStatus.OK,
    )
