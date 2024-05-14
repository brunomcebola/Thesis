"""
Main file for the Flask app.
"""

import os
from flask import Flask
from waitress import serve

from .. import utils

app = Flask(__name__, static_folder="client", static_url_path="")


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


def run_interface():
    """
    Run the Flask app
    """

    utils.print_success("Argos interface is running at http://localhost:5000/\n")

    # TODO: change this comments
    # serve(app, host="0.0.0.0", port=5000)
    app.run(debug=True)


if __name__ == "__main__":

    app.run(debug=True)
