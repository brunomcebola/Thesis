"""
This module contains the routes to interact with the nodes.
"""

import os
from http import HTTPStatus
import yaml
import jsonschema
from flask import Blueprint, jsonify, send_file


blueprint = Blueprint("nodes", __name__, url_prefix="/nodes")

NODES_DIR = "nodes"
NODES_FILE = "nodes.yaml"
IMAGES_DIR = "images"

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
    nodes_dir = os.path.join(os.environ["BASE_DIR"], NODES_DIR)
    os.makedirs(nodes_dir, exist_ok=True)

    # Create images folder
    images_dir = os.path.join(nodes_dir, IMAGES_DIR)
    os.makedirs(images_dir, exist_ok=True)

    # Create nodes file
    nodes_file = os.path.join(nodes_dir, NODES_FILE)
    with open(nodes_file, "a", encoding="utf-8"):
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
        # Get the nodes directory
        nodes_dir = os.path.join(os.environ["BASE_DIR"], NODES_DIR)

        with open(os.path.join(nodes_dir, NODES_FILE), "r", encoding="utf-8") as f:
            nodes_list: list[dict] = yaml.safe_load(f) or []

            _validate_nodes_list(nodes_list)

        return (
            jsonify(nodes_list),
            HTTPStatus.OK,
        )

    except Exception as e:  # pylint: disable=broad-except
        print(e)
        return (
            jsonify({"error": "Internal error."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@blueprint.route("/<node_id>/image")
def image(node_id: int):
    """
    Returns the image of the node
    """

    print("OLA")

    # Get the nodes directory
    nodes_dir = os.path.join(os.environ["BASE_DIR"], NODES_DIR)

    # Get the images dir
    images_dir = os.path.join(nodes_dir, IMAGES_DIR)

    # Get the node image
    for file in os.listdir(images_dir):
        print(file)
        if file.startswith(f"{node_id}."):
            return send_file(os.path.join(images_dir, file))

    return (
        jsonify({"error": "Image not found."}),
        HTTPStatus.NOT_FOUND,
    )
