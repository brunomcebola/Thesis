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


def create_filesystem():
    """
    Create the filesystem
    """

    #  Create base folder
    nodes_dir = os.path.join(os.environ["BASE_DIR"], NODES_DIR)
    os.makedirs(nodes_dir, exist_ok=True)

    # Create images folder
    images_dir = os.path.join(nodes_dir, IMAGES_DIR)
    os.makedirs(images_dir, exist_ok=True)

    # Create nodes file
    nodes_file = os.path.join(nodes_dir, NODES_FILE)
    with open(nodes_file, "a", encoding="utf-8") as f:
        pass


@blueprint.route("/")
def nodes():
    """
    Returns the nodes in BASE_DIR/nodes
    """

    nodes_config_schema = {
        "type": "object",
        "patternProperties": {
            "^[a-zA-Z0-9]{1,15}$": {
                "type": "string",
                "pattern": "^((25[0-5]|(2[0-4]|1\\d|[1-9]|)\\d)\\.\\b){4}:(6553[0-5]|655[0-2][0-9]|65[0-4][0-9]{2}|6[0-4][0-9]{3}|[1-5][0-9]{4}|[1-9][0-9]{0,3}|0)$",  # pylint: disable=line-too-long
            }
        },
        "additionalProperties": False,
    }

    try:

        # Get the nodes directory
        nodes_dir = os.path.join(os.environ["BASE_DIR"], NODES_DIR)

        nodes_list = []

        with open(os.path.join(nodes_dir, NODES_FILE), "r", encoding="utf-8") as f:
            nodes_dict: dict = yaml.safe_load(f)

            if nodes_dict:
                jsonschema.validate(instance=nodes_dict, schema=nodes_config_schema)

                nodes_images_dir = os.path.join(nodes_dir, "images")
                images = [os.path.splitext(image)[0] for image in os.listdir(nodes_images_dir)]

                for node_name, node_address in nodes_dict.items():
                    nodes_list.append(
                        {
                            "name": node_name,
                            "address": node_address,
                            "has_image": node_name in images,
                        }
                    )

        return (
            jsonify(nodes_list),
            HTTPStatus.OK,
        )

    except Exception:
        return (
            jsonify({"error": "Internal error."}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@blueprint.route("/nodes/<node_name>/image")
def image(node_name: str):
    """
    Returns the image of the node
    """

    try:

        # Get the nodes directory
        nodes_dir = os.path.join(os.environ["BASE_DIR"], "nodes")

        # Check if the node exists
        with open(os.path.join(nodes_dir, "nodes.yaml"), "r", encoding="utf-8") as f:
            nodes_dict: dict = yaml.safe_load(f)

            if not nodes_dict or node_name not in nodes_dict:
                return (
                    jsonify({"error": "Node not found."}),
                    HTTPStatus.NOT_FOUND,
                )

        nodes_images_dir = os.path.join(nodes_dir, "images")
        os.makedirs(nodes_images_dir, exist_ok=True)

        image_path = os.path.join(nodes_images_dir, f"{node_name}.png")

        if not os.path.exists(image_path):
            return (
                jsonify({"error": "Image not found."}),
                HTTPStatus.NOT_FOUND,
            )

        return send_file(image_path, mimetype="image/png")

    except Exception:
        return (
            jsonify(),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
