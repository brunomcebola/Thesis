"""
This module contains the controller for the datasets endpoint.
"""

from __future__ import annotations

import os

from http import HTTPStatus
from flask import Blueprint, request, jsonify, Response


from ..models.datasets import Dataset

blueprint = Blueprint("datasets", __name__)


@blueprint.route("/datasets", methods=["GET"])
def get_all_datasets() -> tuple[Response, int]:
    """
    Get list with all datasets
    """

    datasets_path = os.getenv("ARGOS_DATASETS_PATH")

    dir_content = os.listdir(datasets_path)

    datasets = [
        {"id": i, "name": dataset, "path": f"{datasets_path}/{dataset}"}
        for i, dataset in enumerate(dir_content)
    ]

    return jsonify(datasets), HTTPStatus.OK


@blueprint.route("/raw", methods=["GET"])
def get_all_raw_data() -> tuple[Response, int]:
    """
    Get list with all raw data
    """
    raw_path = os.getenv("ARGOS_RAW_PATH")

    dir_content = os.listdir(raw_path)

    raw = [{"id": i, "name": raw, "path": f"{raw_path}/{raw}"} for i, raw in enumerate(dir_content)]

    return jsonify(raw), HTTPStatus.OK
