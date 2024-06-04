"""
Init file for the GUI module.
"""

import os
from flask import Flask
from flask_assets import Environment, Bundle

from . import routes


def register(app: Flask):
    """
    Register the GUI views
    """

    # Register the assets

    base_dir = os.path.dirname(os.path.abspath(__file__))
    scss_path = os.path.join(base_dir, "static", "scss", "main.scss")
    css_output_path = os.path.join(base_dir, "static", "css", "main.css")  # Absolute output path

    assets = Environment(app)
    assets.register(
        {
            "main_style": Bundle(
                scss_path,  # Absolute path to the SCSS file
                filters="pyscss",
                output=css_output_path,  # Absolute output path
            )
        }
    )

    # Register the routes

    app.register_blueprint(routes.blueprint)
