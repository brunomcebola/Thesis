"""
This module contains the routes to interact with the nodes.
"""

import os
from http import HTTPStatus
import yaml
import jsonschema
from flask import Blueprint, jsonify, send_file
import requests


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
                "minimum": 0,
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


def _ensure_filesystem():
    """
    Ensures the integrity of the filesystem
    """

    #  Create base folder
    os.makedirs(NODES_DIR, exist_ok=True)

    # Create images folder
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Create nodes file
    with open(NODES_FILE, "a", encoding="utf-8"):
        pass


def _validate_nodes_list(nodes_list: list[dict]):
    """
    Validates the nodes list
    """

    if nodes_list:
        # Ensure the schema
        jsonschema.validate(instance=nodes_list, schema=NODES_CONFIG_SCHEMA)

        # Ensure unique ids
        ids = [node["id"] for node in nodes_list]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicated ids.")

        # Ensure unique names
        names = [node["name"] for node in nodes_list]
        if len(names) != len(set(names)):
            raise ValueError("Duplicated names.")

        # Ensure unique addresses
        addresses = [node["address"] for node in nodes_list]
        if len(addresses) != len(set(addresses)):
            raise ValueError("Duplicated addresses.")


@blueprint.before_request
def before_request():
    """
    Ensure the filesystem
    """

    _ensure_filesystem()


@blueprint.route("/")
def nodes():
    """
    Returns the nodes in BASE_DIR/nodes
    """

    try:
        with open(NODES_FILE, "r", encoding="utf-8") as f:
            nodes_list: list[dict] = yaml.safe_load(f) or []

            _validate_nodes_list(nodes_list)

        return (
            jsonify(nodes_list),
            HTTPStatus.OK,
        )

    except Exception:  # pylint: disable=broad-except
        return (
            jsonify({"error": "Internal error."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@blueprint.route("/<node_id>/image")
def image(node_id: int):
    """
    Returns the image of the node
    """

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

    # BUG: node_id=0 breaks access to rout

    try:
        with open(NODES_FILE, "r", encoding="utf-8") as f:
            nodes_list: list[dict] = yaml.safe_load(f) or []

            _validate_nodes_list(nodes_list)

        # Get the node
        node = next((node for node in nodes_list if node["id"] == node_id), None)

        if node is None:
            return (
                jsonify({"error": "Node not found."}),
                HTTPStatus.NOT_FOUND,
            )

        # Make a GET request to retrieve the list of cameras
        response = requests.get(f"http://{node['address']}/cameras")

        return (
            jsonify(response.json() if response.status_code == HTTPStatus.OK else []),
            HTTPStatus.OK,
        )

    except Exception as e:  # pylint: disable=broad-except
        print(e)
        return (
            jsonify({"error": "Internal error."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
