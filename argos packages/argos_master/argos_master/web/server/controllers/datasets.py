"""
This module contains the controller for the datasets endpoint.
"""

from __future__ import annotations

import os

from pathlib import Path
from http import HTTPStatus
from flask import Blueprint, request, jsonify, Response, send_from_directory


from ..models.datasets import Dataset

blueprint = Blueprint("datasets", __name__)


@blueprint.route("/datasets", methods=["GET"])
def get_datasets_list() -> tuple[Response, int]:
    """
    Get list with all datasets
    """

    datasets_path = os.getenv("ARGOS_DATASETS_PATH")

    dir_content = os.listdir(datasets_path)

    datasets = [{"name": dataset, "path": f"{datasets_path}/{dataset}"} for dataset in dir_content]

    return jsonify(datasets), HTTPStatus.OK


@blueprint.route("/datasets/<dataset>/images", methods=["GET"])
def get_dataset_images_list(dataset: str) -> tuple[Response, int]:
    """
    Get list with all images in a dataset
    """

    base_path = os.getenv("ARGOS_DATASETS_PATH")

    if base_path is None:
        return jsonify(""), HTTPStatus.INTERNAL_SERVER_ERROR

    dataset_path = Path(os.path.join(base_path, dataset)).resolve()

    # Check if path is a descendant of basedir
    try:
        dataset_path.relative_to(base_path)
    except ValueError:
        return jsonify(""), HTTPStatus.BAD_REQUEST

    images = os.listdir(os.path.join(dataset_path, "images/train/color"))

    return jsonify(images), HTTPStatus.OK


@blueprint.route("/datasets/<dataset>/images/<image>", methods=["GET"])
def get_dataset_image(dataset, image):
    """
    Get an image from a dataset
    """

    base_path = os.getenv("ARGOS_DATASETS_PATH")

    if base_path is None:
        return jsonify(""), HTTPStatus.INTERNAL_SERVER_ERROR

    dataset_path = Path(os.path.join(base_path, dataset)).resolve()

    # Check if path is a descendant of basedir
    try:
        dataset_path.relative_to(base_path)
    except ValueError:
        return jsonify(""), HTTPStatus.BAD_REQUEST

    return send_from_directory(dataset_path, f"images/train/color/{image}")


@blueprint.route("/raw", methods=["GET"])
def get_raw_data_list() -> tuple[Response, int]:
    """
    Get list with all raw data
    """
    raw_path = os.getenv("ARGOS_RAW_PATH")

    dir_content = os.listdir(raw_path)

    raw = [{"name": raw, "path": f"{raw_path}/{raw}"} for raw in dir_content]

    return jsonify(raw), HTTPStatus.OK
