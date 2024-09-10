"""
This module contains the routes to interact with the datasets.
"""

import os
from http import HTTPStatus
from flask import Blueprint, jsonify, send_file, request, send_from_directory


from .. import logger as _logger
from ..handlers.datasets import datasets_handler

blueprint = Blueprint("datasets", __name__, url_prefix="/datasets")


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
def get_datasets():
    """
    Returns the nodes
    """

    return (
        jsonify(datasets_handler.get_datasets()),
        HTTPStatus.OK,
    )


# @blueprint.route("/")
# @blueprint.route("/<path:subpath>/")
# def navigate(subpath=""):
#     """
#     # TODO
#     """

#     full_path = os.path.join(os.environ["BASE_DIR"], "datasets", subpath)

#     if os.path.exists(full_path) and os.path.isdir(full_path):
#         files = []
#         for item in os.listdir(full_path):
#             item_path = os.path.join(full_path, item)
#             files.append(
#                 {
#                     "name": item,
#                     "is_dir": os.path.isdir(item_path),
#                 }
#             )
#         return jsonify(files), HTTPStatus.OK
#     else:
#         return jsonify({"error": "Path does not exist"}), 404
