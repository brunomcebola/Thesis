"""
This module contains the routes for the API.
"""

import os
from http import HTTPStatus
from flask import Blueprint, jsonify, send_file


blueprint = Blueprint("api", __name__, url_prefix="/api")


@blueprint.route("/datasets")
def datasets():
    """
    Returns the datasets in BASE_DIR/datasets
    """

    # Get the datasets directory
    datasets_dir = os.path.join(os.environ["BASE_DIR"], "datasets")
    os.makedirs(datasets_dir, exist_ok=True)

    # Get the datasets
    datasets_list = []
    for dataset in os.listdir(datasets_dir):  # pylint: disable=redefined-outer-name
        # Get only directories
        if not os.path.isdir(os.path.join(datasets_dir, dataset)):
            continue

        # Get description
        desc_file = os.path.join(datasets_dir, dataset, "desc.txt")
        with open(desc_file, "a", encoding="utf-8") as f:
            pass

        with open(desc_file, "r", encoding="utf-8") as f:
            description = f.read().strip()

            if not description:
                description = "No description available."

        # Append the dataset to the list
        datasets_list.append(
            {
                "name": dataset,
                "description": description,
            }
        )

    return (
        jsonify(datasets_list),
        HTTPStatus.OK,
    )


@blueprint.route("/datasets/<dataset_name>")
def dataset(dataset_name: str):
    """
    Returns dataset information (including images)
    """

    # Get the datasets directory
    datasets_dir = os.path.join(os.environ["BASE_DIR"], "datasets")
    os.makedirs(datasets_dir, exist_ok=True)

    # Check if the dataset exists
    if not os.path.isdir(os.path.join(datasets_dir, dataset_name)):
        return (
            jsonify({"error": "Dataset not found."}),
            HTTPStatus.NOT_FOUND,
        )

    dataset_path = os.path.join(datasets_dir, dataset_name)

    # Get description
    desc_file = os.path.join(dataset_path, "desc.txt")
    with open(desc_file, "a", encoding="utf-8") as f:
        pass

    with open(desc_file, "r", encoding="utf-8") as f:
        description = f.read().strip()

        if not description:
            description = "No description available."

    # Get the images
    images_dir = os.path.join(dataset_path, "images")
    os.makedirs(images_dir, exist_ok=True)

    images_names = []
    for image_name in os.listdir(images_dir):
        # Get only files
        if not os.path.isfile(os.path.join(images_dir, image_name)):
            continue
        
        images_names.append(f"/api/datasets/{ dataset_name }/images/{ image_name }")

    return (
        jsonify(
            {
                "name": dataset_name,
                "description": description,
                "images": images_names,
            }
        ),
        HTTPStatus.OK,
    )


@blueprint.route("/datasets/<dataset_name>/images/<image_name>")
def image(dataset_name: str, image_name: str):
    """
    Returns the image
    """

    # Get the datasets directory
    datasets_dir = os.path.join(os.environ["BASE_DIR"], "datasets")
    os.makedirs(datasets_dir, exist_ok=True)

    # Check if the dataset exists
    if not os.path.isdir(os.path.join(datasets_dir, dataset_name)):
        return (
            jsonify({"error": "Dataset not found."}),
            HTTPStatus.NOT_FOUND,
        )

    dataset_path = os.path.join(datasets_dir, dataset_name)

    # Get the images
    images_dir = os.path.join(dataset_path, "images")
    os.makedirs(images_dir, exist_ok=True)

    # Check if the image exists
    if not os.path.isfile(os.path.join(images_dir, image_name)):
        return (
            jsonify({"error": "Image not found."}),
            HTTPStatus.NOT_FOUND,
        )

    return send_file(os.path.join(images_dir, image_name), mimetype="image/png")
