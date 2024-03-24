"""
This module contains the controller for the datasets endpoint.
"""

from __future__ import annotations

from http import HTTPStatus
from flask import Blueprint, request, jsonify, Response


from ..models.datasets import Dataset

blueprint = Blueprint("datasets", __name__)


@blueprint.route("/datasets", methods=["GET"])
def get_all() -> tuple[Response, int]:
    """
    Get all datasets
    """
    datasets = Dataset.query.all()
    print(datasets)

    return jsonify("ola"), HTTPStatus.OK
