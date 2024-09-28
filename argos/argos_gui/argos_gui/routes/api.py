"""
This module contains the routes to interact with the logs.
"""

import os
from http import HTTPStatus
import requests
from flask import jsonify, request, Response
from flask import Blueprint as _Blueprint

from .. import logger as _logger

from .socket import master_sio as _master_sio


class Blueprint(_Blueprint):
    """
    Custom Blueprint class to keep track of defined routes
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._routes = set()

    def add_url_rule(self, endpoint, *args, **kwargs):
        if endpoint:
            self._routes.add(endpoint)
        super().add_url_rule(endpoint, *args, **kwargs)

    def route_defined(self, endpoint):
        """
        Checks if a route is defined in the blueprint
        """

        return endpoint in self._routes


blueprint = Blueprint("api", __name__, url_prefix="/api")


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


@blueprint.route("/logs")
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

    return jsonify(content)


@blueprint.route("/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def redirect_to_master(subpath: str):
    """
    Intercept requests that do not match any defined routes in the blueprint
    and forward them to another server.
    """

    if not _master_sio.connected:
        return (
            jsonify("Unable to reach master. Please try again later."),
            HTTPStatus.SERVICE_UNAVAILABLE,
        )

    # Construct the URL for the target server
    target_url = f"http://{os.getenv('MASTER_ADDRESS')}/{subpath}"

    # Forward the request to the argos_master
    response = requests.request(
        method=request.method,
        url=target_url,
        headers={key: value for key, value in request.headers if key != "Host"},
        params=request.args.to_dict(flat=False) if request.args else None,
        data=request.get_data(),
        cookies=request.cookies,
        timeout=30,
    )

    headers = [(name, value) for name, value in response.raw.headers.items()]

    # Create a Flask response object with the original status code and headers
    flask_response = Response(response.content, status=response.status_code, headers=headers)

    # Set cookies in the Flask response if present
    for cookie in response.cookies:
        if cookie.value is not None:
            flask_response.set_cookie(cookie.name, cookie.value)

    return flask_response
