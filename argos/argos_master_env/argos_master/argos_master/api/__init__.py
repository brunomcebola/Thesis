"""
Init file for the API module.
"""

from flask import Flask

from . import routes


def register(app: Flask):
    """
    Register the GUI views
    """

    # Register the routes

    app.register_blueprint(routes.blueprint)
