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
    Create the filesystem
    """

    # Create base folder
    datasets_dir = os.path.join(os.environ["BASE_DIR"], DATASETS_DIR_NAME)
    os.makedirs(datasets_dir, exist_ok=True)

    # Create desc_file and images folders
    for dataset_dir in os.listdir(datasets_dir):
        dataset_path = os.path.join(datasets_dir, dataset_dir)

        desc_file = os.path.join(dataset_path, DATASET_DESCRIPTION_FILE_NAME)
        with open(desc_file, "a", encoding="utf-8") as f:
            pass

        train_images_dir = os.path.join(dataset_path, DATASET_TRAIN_IMAGES_DIR_NAME)
        os.makedirs(train_images_dir, exist_ok=True)

        val_images_dir = os.path.join(dataset_path, DATASET_VAL_IMAGES_DIR_NAME)
        os.makedirs(val_images_dir, exist_ok=True)

        test_images_dir = os.path.join(dataset_path, DATASET_TEST_IMAGES_DIR_NAME)
        os.makedirs(test_images_dir, exist_ok=True)


def _get_dataset_description(dataset_path: str) -> str:
    """
    Get the dataset description
    """

    desc_file = os.path.join(dataset_path, DATASET_DESCRIPTION_FILE_NAME)

    with open(desc_file, "a", encoding="utf-8") as f:
        pass

    with open(desc_file, "r", encoding="utf-8") as f:
        description = f.read().strip()

    return description


def _get_dataset_images(dataset_path: str) -> tuple[list[str], list[str], list[str]]:
    """
    Get the dataset images
    """

    train_images_dir = os.path.join(dataset_path, DATASET_TRAIN_IMAGES_DIR_NAME)
    val_images_dir = os.path.join(dataset_path, DATASET_VAL_IMAGES_DIR_NAME)
    test_images_dir = os.path.join(dataset_path, DATASET_TEST_IMAGES_DIR_NAME)

    train_images = os.listdir(train_images_dir)
    val_images = os.listdir(val_images_dir)
    test_images = os.listdir(test_images_dir)

    return train_images, val_images, test_images


@blueprint.before_request
def before_request():
    """
    Ensure the filesystem
    """

    _ensure_filesystem()


# @blueprint.errorhandler(500)
# def handle_500_error(_):
#     return (
#         jsonify({"error": "Internal error."}),
#         HTTPStatus.INTERNAL_SERVER_ERROR,
#     )


# @blueprint.route("/")
# def get_datasets():
#     """
#     Returns the datasets
#     """

#     # Get the datasets directory
#     datasets_dir = os.path.join(os.environ["BASE_DIR"], DATASETS_DIR_NAME)

#     # Get the datasets
#     datasets_list = []
#     for dataset in os.listdir(datasets_dir):
#         dataset_path = os.path.join(datasets_dir, dataset)

#         datasets_list.append(
#             {
#                 "name": dataset,
#                 "description": _get_dataset_description(dataset_path),
#             }
#         )

#     return (
#         jsonify(datasets_list),
#         HTTPStatus.OK,
#     )


# @blueprint.route("/<dataset_name>/")
# def get_dataset(dataset_name: str):
#     """
#     Returns dataset information (including images)
#     """

#     dataset_path = os.path.join(os.environ["BASE_DIR"], DATASETS_DIR_NAME, dataset_name)

#     return (
#         jsonify(
#             {
#                 "name": dataset_name,
#                 "description": _get_dataset_description(dataset_path),
#                 "images": _get_dataset_images(dataset_path),
#             }
#         ),
#         HTTPStatus.OK,
#     )


# @blueprint.route("/<dataset_name>/images/<image_name>")
# def get_dataset_image(dataset_name: str, image_name: str):
#     """
#     Returns the image
#     """

#     # Check if the dataset exists
#     if not os.path.isdir(os.path.join(datasets_dir, dataset_name)):
#         return (
#             jsonify({"error": "Dataset not found."}),
#             HTTPStatus.NOT_FOUND,
#         )

#     dataset_path = os.path.join(datasets_dir, dataset_name)

#     # Get the images
#     images_dir = os.path.join(dataset_path, "images")
#     os.makedirs(images_dir, exist_ok=True)

#     # Check if the image exists
#     if not os.path.isfile(os.path.join(images_dir, image_name)):
#         return (
#             jsonify({"error": "Image not found."}),
#             HTTPStatus.NOT_FOUND,
#         )

#     return send_file(os.path.join(images_dir, image_name), mimetype="image/png")

@blueprint.route("/")
@blueprint.route("/<path:subpath>/")
def navigate(subpath = ""):
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