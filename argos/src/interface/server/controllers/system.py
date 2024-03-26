"""
This module contains the controller for the datasets endpoint.
"""

from __future__ import annotations

import os
from http import HTTPStatus
from flask import Blueprint, request, jsonify, Response

blueprint = Blueprint("system", __name__)


@blueprint.route("working_dir", methods=["GET"])
def get_working_dir() -> tuple[Response, int]:
    """
    Get the working directory
    """

    return jsonify(os.getcwd().split("/")[1:]), HTTPStatus.OK


@blueprint.route("dir_co", methods=["GET"])
def get_sub_dirs() -> tuple[Response, int]:
    """
    Get the sub directories of a given directory
    """

    directory = request.args.get("dir")
    if directory is None:
        return jsonify("Directory not provided"), HTTPStatus.BAD_REQUEST

    if not os.path.isdir(directory):
        return jsonify("Directory not found"), HTTPStatus.NOT_FOUND

    return jsonify(os.listdir(directory)), HTTPStatus.OK
