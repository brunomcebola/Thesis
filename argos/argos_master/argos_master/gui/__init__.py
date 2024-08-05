"""
Init file for the GUI module.
"""

import os
from flask_assets import Environment, Bundle

from .. import app as _app
from . import routes as _routes


# Register the assets

assets = Environment(_app)

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

for scss_file in os.listdir(os.path.join(base_dir, "scss")):
    if not scss_file.endswith(".scss"):
        continue

    name = scss_file.replace(".scss", "")
    scss_path = os.path.join(base_dir, "scss", scss_file)
    css_output_path = os.path.join(base_dir, "css", scss_file.replace(".scss", ".css"))

    assets.register(
        {
            name: Bundle(
                scss_path,  # Absolute path to the SCSS file
                filters="pyscss",
                output=css_output_path,  # Absolute output path
            )
        }
    )

# Register the routes

_app.register_blueprint(_routes.blueprint)
