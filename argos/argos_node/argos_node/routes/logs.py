"""
This module contains the routes to interact with the logs.
"""

from http import HTTPStatus
from flask import Blueprint, jsonify, request

from .. import logger as _logger

blueprint = Blueprint("logs", __name__, url_prefix="/logs")


@blueprint.errorhandler(Exception)
def handle_exception(_):
    """
    Handles exceptions
    """

    return (
        jsonify({"error": "Internal error."}),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@blueprint.route("/")
def logs():
    """
    Returns the logs.

    Request must contain the following parameters:
        - start_line: the line to start from
        - nb_lines: the number of lines
    """

    start_line = request.args.get("start_line", type=int)
    nb_lines = request.args.get("nb_lines", type=int)

    if start_line is None or nb_lines is None:
        return (
            jsonify({"error": "start_line and nb_lines are required."}),
            HTTPStatus.BAD_REQUEST,
        )
    if start_line <= 0 or nb_lines <= 0:
        return (
            jsonify({"error": "start_line and nb_lines must be positive integers."}),
            HTTPStatus.BAD_REQUEST,
        )

    # Your code to retrieve logs using start_line and nb_lines goes here

    with open(_logger.handlers[0].baseFilename, "r", encoding="utf-8") as file:  # type: ignore
        content = file.readlines() or []

    if start_line == 1:
        content = content[-nb_lines:]
    else:
        content = content[-nb_lines - start_line : -start_line + 1]
    content.reverse()

    return (
        jsonify(content),
        HTTPStatus.OK,
    )
