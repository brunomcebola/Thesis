"""
Main file for the Flask app.
"""

import os
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="client")


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

    app.run()


if __name__ == "__main__":
    run()


# from waitress import serve
# serve(app, host="0.0.0.0", port=5000)
