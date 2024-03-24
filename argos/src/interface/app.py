"""
Main file for the Flask app.
"""

import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__, static_folder="client", static_url_path="")

# define the db
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "argos.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

from .server import models  # pylint: disable=unused-import disable=wrong-import-position

# define the api endpoints
from .server import controllers  # pylint: disable=wrong-import-position

app.register_blueprint(controllers.datasets.blueprint, url_prefix="/api")


# serve the Vue app
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_vue_app(path):
    """
    Serve the Vue app
    """
    if path != "" and os.path.exists(app.static_folder + "/" + path):  # type: ignore
        return send_from_directory(app.static_folder, path)  # type: ignore
    else:
        return send_from_directory(app.static_folder, "index.html")  # type: ignore


def run():
    """
    Run the Flask app
    """

    with app.app_context():
        db.create_all()

    app.run()


if __name__ == "__main__":
    run()


# from waitress import serve
# serve(app, host="0.0.0.0", port=5000)
