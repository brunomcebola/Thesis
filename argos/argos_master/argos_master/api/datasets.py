"""
This module contains the routes to interact with the datasets.
"""

import os
from http import HTTPStatus
from flask import Blueprint, jsonify, send_file, request, send_from_directory


blueprint = Blueprint("datasets", __name__, url_prefix="/datasets")

DATASETS_DIR_NAME = "datasets"
DATASET_DESCRIPTION_FILE_NAME = "desc.txt"
DATASET_TRAIN_IMAGES_DIR_NAME = "images/train"
DATASET_VAL_IMAGES_DIR_NAME = "images/val"
DATASET_TEST_IMAGES_DIR_NAME = "images/test"


def _ensure_filesystem():
    """
    Ensure the integrity of the filesystem
    """

    # Create base folder
    datasets_dir = os.path.join(os.environ["BASE_DIR"], DATASETS_DIR_NAME)
    os.makedirs(datasets_dir, exist_ok=True)

    # Create desc_file and images folders
    for dataset_dir in os.listdir(datasets_dir):
        dataset_path = os.path.join(datasets_dir, dataset_dir)

        desc_file = os.path.join(dataset_path, DATASET_DESCRIPTION_FILE_NAME)
        with open(desc_file, "a", encoding="utf-8"):
            pass

        train_images_dir = os.path.join(dataset_path, DATASET_TRAIN_IMAGES_DIR_NAME)
        os.makedirs(train_images_dir, exist_ok=True)

        val_images_dir = os.path.join(dataset_path, DATASET_VAL_IMAGES_DIR_NAME)
        os.makedirs(val_images_dir, exist_ok=True)

        test_images_dir = os.path.join(dataset_path, DATASET_TEST_IMAGES_DIR_NAME)
        os.makedirs(test_images_dir, exist_ok=True)


@blueprint.before_request
def before_request():
    """
    Ensure the filesystem
    """

    _ensure_filesystem()


@blueprint.route("/")
@blueprint.route("/<path:subpath>/")
def navigate(subpath=""):
    """
    # TODO
    """

    full_path = os.path.join(os.environ["BASE_DIR"], "datasets", subpath)

    if os.path.exists(full_path) and os.path.isdir(full_path):
        files = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            files.append(
                {
                    "name": item,
                    "is_dir": os.path.isdir(item_path),
                }
            )
        return jsonify(files), HTTPStatus.OK
    else:
        return jsonify({"error": "Path does not exist"}), 404
