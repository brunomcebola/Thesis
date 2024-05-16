"""
Main file for the Flask app.
"""

import os
from flask import Flask
from waitress import serve

import argos_common as ac

app = Flask(__name__)


# hello world route
@app.route("/")
def hello_world():
    """
    Hello world route
    """
    return "Hello, World!"


def run_network():
    """
    Run the Flask app
    """

    port = int(os.getenv("ARGOS_PORT", "5000"))

    if os.environ["ARGOS_ENV"] == "production":
        ac.Printer.print_info(f"Launched server on port {port}!")
        serve(app, port=port)
    else:
        app.run(port=port)


if __name__ == "__main__":

    run_network()
