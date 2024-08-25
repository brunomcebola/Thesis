"""
This module contains the handlers for the nodes
"""

from __future__ import annotations


import os
import io
import time
import pickle
import base64
import threading
import yaml
import requests
import socketio
import jsonschema
from PIL import Image
from flask import Request, Response, jsonify
from werkzeug.datastructures import FileStorage

from .. import socketio as _socketio  # pylint: disable=reimported
from .. import logger as _logger

NODES_DIR = os.path.join(os.environ["BASE_DIR"], "nodes")
NODES_FILE = os.path.join(NODES_DIR, "nodes.yaml")
IMAGES_DIR = os.path.join(NODES_DIR, "images")

NODE_CONFIG_SCHEMA = {
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
}


class Node:
    """
    Class representing a node
    """

    _id: int
    _name: str
    _address: str
    _image: str | None
    _sio: socketio.Client | None
    _cameras: list[str]

    def __init__(
        self,
        node_config: dict,
    ) -> None:
        """
        Initializes the node

        Args:
            node_config (dict): The configuration of the node. Must follow NODE_CONFIG_SCHEMA
        """

        jsonschema.validate(instance=node_config, schema=NODE_CONFIG_SCHEMA)

        self._id = node_config["id"]
        self._name = node_config["name"]
        self._address = node_config["address"]
        self._image = (
            next(
                (
                    os.path.join(IMAGES_DIR, file)
                    for file in os.listdir(IMAGES_DIR)
                    if file.startswith(str(self._id))
                ),
                None,
            )
            if node_config["has_image"]
            else None
        )
        self._sio = None
        self._cameras = []

    # Instance properties

    @property
    def id(self) -> int:
        """
        Returns the id of the node
        """
        return self._id

    @property
    def name(self) -> str:
        """
        Returns the name of the node
        """
        return self._name

    @property
    def address(self) -> str:
        """
        Returns the address of the node
        """
        return self._address

    @property
    def image(self) -> str | None:
        """
        Returns the image of the node
        """

        return self._image

    @property
    def has_image(self) -> bool:
        """
        Returns if the node has an image
        """
        return bool(self._image)

    # Instance private methods

    def _retry_connect(self):
        while self._sio and not self._sio.connected:
            try:
                self._sio.connect(f"http://{self._address}")
                break
            except Exception:  # pylint: disable=broad-except
                time.sleep(1)

    @staticmethod
    def _camera_callback(data, node, camera):
        frame = pickle.loads(data)

        if frame["color"] is not None:
            # Convert BGR to RGB
            rgb_image = frame["color"][:, :, ::-1]

            pil_image = Image.fromarray(rgb_image)

            buffer = io.BytesIO()
            pil_image.save(buffer, format="JPEG")

            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            _socketio.emit(f"{node}_{camera}", img_base64)

    # Instance public methods

    def connect(self) -> None:
        """
        Connects to the node
        """

        _logger.info("Connecting to node %s at %s...", self._id, self._address)

        # Create socketio client
        sio = socketio.Client(reconnection=True)

        @sio.event
        def connect():
            _logger.info("Connected to node %s at %s.", self._id, self._address)

            # Get cameras
            response = requests.get(f"http://{self._address}/cameras", timeout=5)
            cameras = response.json()

            # Set callback of each camera
            for camera in cameras:
                sio.on(
                    camera,
                    lambda data: self._camera_callback(
                        data, self._id, camera  # pylint: disable=cell-var-from-loop
                    ),
                )

            self._cameras = cameras

            # print(sio.handlers)

        @sio.event
        def disconnect():
            _logger.warning("Disconnected from node %s at %s.", self._id, self._address)

            # # Remove callbacks of each camera
            # for camera in self._cameras:
            #     sio.handlers['/'].pop['handler_name_to_remove']
            # sio.handlers

        self._sio = sio

        # Connect to the node
        try:
            self._sio.connect(f"http://{self._address}")
        except Exception:  # pylint: disable=broad-except
            _logger.warning(
                "Unable to connect to node %s at %s. Retrying in background...",
                self._id,
                self._address,
            )

            threading.Thread(target=self._retry_connect, daemon=True).start()

        # print(sio.handlers)

    def disconnect(self) -> None:
        """
        Disconnects from the node
        """

        if self._sio:
            self._sio.disconnect()

        self._sio = None


class NodesHandler:
    """
    Class used to handle the nodes
    """

    _nodes: list[Node]

    def __init__(self) -> None:
        self._nodes = []

        _logger.info("Initializing nodes...")

        with open(NODES_FILE, "r", encoding="utf-8") as f:
            try:
                nodes_configs = yaml.safe_load(f) or []
            except Exception as e:  # pylint: disable=broad-except
                raise type(e)("Unable to initialize node - ") from e

        success = 0
        fail = 0
        for node_config in nodes_configs:
            fail += 1

            try:
                self.__add_node(node_config)
            except Exception as e:  # pylint: disable=broad-except
                _logger.warning("Unable to initialize node - %s.", e)
                continue

            fail -= 1
            success += 1

        _logger.info(
            "Nodes initialized - Total: %s, Success: %s, Fail: %s.", success + fail, success, fail
        )

    # Instance private methods

    def __add_node(
        self,
        node_config: dict,
        node_image: FileStorage | None = None,
        save_to_file: bool = False,
    ) -> Node:
        """
        Adds a new node to the list and connects to it

        Args:
            node_config (dict): The configuration of the node. Must follow NODE_CONFIG_SCHEMA

        Returns:
            Node: The created node

        Raises:
            ValueError: If the configuration is invalid
        """

        try:
            node = Node(node_config)
        except jsonschema.ValidationError as e:
            if not e.path:
                raise ValueError(f"Invalid configuration ({e.message}).") from e
            else:
                raise ValueError(
                    f"Invalid configuration ({e.message} for {e.path[0]}: {e.instance})."
                ) from e

        # Ensure unique ids
        if node.id in [node.id for node in self._nodes]:
            raise ValueError(f"Id '{node.id}' already registered.")

        # Ensure unique names
        if node.name in [node.name for node in self._nodes]:
            raise ValueError(f"Name '{node.name}' already registered.")

        # Ensure unique addresses
        if node.address in [node.address for node in self._nodes]:
            raise ValueError(f"Address '{node.address}' already registered.")

        node.connect()

        self._nodes.append(node)

        # Save node
        if save_to_file:
            with open(NODES_FILE, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.get_nodes(), f, sort_keys=False)

        # Save image
        if node_image and node_image.filename:
            extension = node_image.filename.split(".")[-1].lower()
            node_image.save(f"{IMAGES_DIR}/{node.id}.{extension}")

        return node

    def __delete_node(
        self,
        node_id: int,
        delete_image: bool = True,
    ) -> Node:
        """
        Removes a node from the list

        Args:
            node_id (int): The id of the node to remove
            delete_image (bool): If the image of the node should be deleted

        Returns:
            Node: The removed node

        Raises:
            ValueError: If the node is not found
        """

        node = next((node for node in self._nodes if node.id == node_id), None)
        if not node:
            raise ValueError(f"Node '{node_id}' not found.")

        node.disconnect()

        self._nodes.remove(node)

        with open(NODES_FILE, "w", encoding="utf-8") as f:
            nodes = self.get_nodes()
            if nodes:
                yaml.safe_dump(nodes, f, sort_keys=False)

        if delete_image:
            for file in os.listdir(IMAGES_DIR):
                if file.startswith(str(node_id)):
                    os.remove(os.path.join(IMAGES_DIR, file))

        return node

    # Instance public methods

    def get_nodes(self) -> list[dict]:
        """
        Returns the list of nodes
        """

        return [
            {
                "id": node.id,
                "name": node.name,
                "address": node.address,
                "has_image": node.has_image,
            }
            for node in self._nodes
        ]

    def create_node(
        self,
        node_name: str,
        node_address: str,
        node_image: FileStorage | None,
    ) -> None:
        """
        Creates a new node

        Args:
            node_name (str): The name of the node
            node_address (str): The address of the node
            node_image (FileStorage | None): The image of the node

        Raises:
            ValueError: If no name or address is provided
        """

        if not node_name:
            raise ValueError("No name provided.")

        if not node_address:
            raise ValueError("No address provided.")

        _logger.info("Creating new node...")

        node_config = {
            "id": max([0] + [node.id for node in self._nodes]) + 1,
            "name": node_name,
            "address": node_address,
            "has_image": bool(node_image and node_image.filename),
        }

        try:
            node = self.__add_node(node_config, node_image, save_to_file=True)
        except Exception as e:  # pylint: disable=broad-except
            _logger.warning("Unable to create node - %s.", e)
            raise

        _logger.info("Created new node %s (%s @ %s)", node.id, node.name, node.address)

    def edit_node(
        self,
        node_id: int,
        node_name: str | None = None,
        node_address: str | None = None,
    ) -> None:
        """
        Edits a node

        Args:
            node_name (str): The new name of the node
            node_address (str): The new address of the node
        """

        if not node_name and not node_address:
            raise ValueError("No data provided.")

        _logger.info("Editing node...")

        node = self.__delete_node(node_id, delete_image=False)

        old_node_config = {
            "id": node.id,
            "name": node.name,
            "address": node.address,
            "has_image": node.has_image,
        }

        new_node_config = {
            "id": node.id,
            "name": node_name or node.name,
            "address": node_address or node.address,
            "has_image": node.has_image,
        }

        try:
            self.__add_node(new_node_config, save_to_file=True)
        except Exception as e:  # pylint: disable=broad-except
            _logger.warning("Unable to edit node - %s.", e)
            self.__add_node(old_node_config)
            raise e

        _logger.info("Edited node %s (%s @ %s)", node.id, node.name, node.address)

    def delete_node(self, node_id: int) -> None:
        """
        Deletes a node

        Args:
            node_id (int): The id of the node to delete
        """

        _logger.info("Deleting node...")

        node = self.__delete_node(node_id)

        _logger.info("Deleted node %s (%s @ %s)", node.id, node.name, node.address)

    def get_node_image(self, node_id: int) -> str | None:
        """
        Returns the path to the image of a node

        Args:
            node_id (int): The id of the node

        Returns:
            str | None: The path to the image of the node
        """

        node = next((node for node in self._nodes if node.id == node_id), None)
        if not node:
            raise ValueError(f"Node '{node_id}' not found.")

        return node.image

    def redirect_request_to_node(
        self, node_id: int, route: str, request: Request
    ) -> tuple[Response, int]:
        """
        Redirects a request to a node

        Args:
            node_id (int): The id of the node
            endpoint (str): The endpoint to redirect the request to

        Returns:
            requests.Response: The response of the request

        Raises:
            ValueError: If the node is not found
            ConnectionError: If the node is not reachable
        """

        node = next((node for node in self._nodes if node.id == node_id), None)
        if not node:
            raise ValueError(f"Node '{node_id}' not found.")

        target_url = f"http://{node.address}/{route}"

        try:
            response = requests.request(
                method=request.method,
                url=target_url,
                params=request.args.to_dict(flat=False) if request.args else None,
                json=request.json if "Content-Type" in dict(request.headers) else None,
                timeout=5,
            )
        except Exception as e:
            raise ConnectionError(f"Unable to connect to node '{node_id}' at {node.address}") from e

        return (
            jsonify(response.json()),
            response.status_code,
        )


#  Create base folder if it doesn't exist
os.makedirs(NODES_DIR, exist_ok=True)

# Create images folde if it doesn't exist
os.makedirs(IMAGES_DIR, exist_ok=True)

# Create nodes file if it doesn't exist
with open(NODES_FILE, "a", encoding="utf-8"):
    pass


# Create nodes handler
nodes_handler = NodesHandler()
