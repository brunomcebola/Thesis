"""
This module contains the routes to interact with the datasets.
"""

from http import HTTPStatus
from flask import Blueprint, jsonify, request


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
    Returns the datasets
    """

    return (
        jsonify(datasets_handler.get_datasets()),
        HTTPStatus.OK,
    )


@blueprint.route("/", methods=["POST"])
def create_dataset():
    """
    Creates a new dataset
    """

    # Create the dataset
    try:
        datasets_handler.create_dataset(
            request.form.get("name", ""),
        )
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    # Return a success message
    return (
        jsonify("Dataset created successfully"),
        HTTPStatus.CREATED,
    )


@blueprint.route("/<string:dataset_name>", methods=["PUT"])
def edit_dataset(dataset_name: str):
    """
    Edits dataset
    """

    # Edit the dataset
    try:
        datasets_handler.edit_dataset(
            dataset_name,
            request.form.get("name", ""),
        )
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    # Return a success message with the newly created dataset
    return (
        jsonify("dataset edited successfully"),
        HTTPStatus.CREATED,
    )


@blueprint.route("/<string:dataset_name>", methods=["DELETE"])
def delete_dataset(dataset_name: str):
    """
    Deletes a dataset
    """

    # Delete the dataset
    try:
        datasets_handler.delete_dataset(dataset_name)
    except Exception as e:  # pylint: disable=broad-except
        return (
            jsonify(str(e)),
            HTTPStatus.BAD_REQUEST,
        )

    # Return a success message
    return (
        jsonify("dataset deleted successfully."),
        HTTPStatus.OK,
    )
