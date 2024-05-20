"""
This module is the entry point of Argos, a real-time image analysis tool for fraud detection.
"""

from __future__ import annotations


import os
import sys
import signal
from flask import Flask
from dotenv import find_dotenv, load_dotenv

import argos_common as ac

from . import controllers
from .namespace import NodeNamespace


def load_argos_env():
    """
    Load the environment variables from the nearest .env.argos file
    """
    # Find the .env file
    ac.Printer.print_info("Setting up environment variables...")
    try:
        env_path = find_dotenv(filename=".env.argos", raise_error_if_not_found=True)
    except IOError:
        ac.Printer.print_error(
            "Unable to setup environment variables. No '.env.argos' file found!",
            ac.Printer.Space.AFTER,
        )
        exit(1)

    # Load the environment variables from the corresponding file
    load_dotenv(dotenv_path=env_path)

    # Ensures the CONFIG_YAML environment variable is set
    if not os.getenv("CONFIG_YAML"):
        ac.Printer.print_error(
            "No ARGOS_YAML found in environment variables!",
            ac.Printer.Space.AFTER,
        )
        exit(1)

    # Ensures the FLASK_SERVER environment variable is set
    if not os.getenv("FLASK_SERVER"):
        ac.Printer.print_error(
            "No FLASK_SERVER found in environment variables!",
            ac.Printer.Space.AFTER,
        )
        exit(1)
    if len(os.getenv("FLASK_SERVER").split(":")) != 2:  # type: ignore
        ac.Printer.print_error(
            "FLASK_SERVER must be in the format 'host:port'!",
            ac.Printer.Space.AFTER,
        )
        exit(1)

    # Ensures the RABBITMQ_* environment variables are set
    if not os.getenv("RABBITMQ_SERVER"):
        ac.Printer.print_error(
            "No RABBITMQ_SERVER found in environment variables!",
            ac.Printer.Space.AFTER,
        )
        exit(1)
    elif not os.getenv("RABBITMQ_USER"):
        ac.Printer.print_error(
            "No RABBITMQ_USER found in environment variables!",
            ac.Printer.Space.AFTER,
        )
        exit(1)
    elif not os.getenv("RABBITMQ_PWD"):
        ac.Printer.print_error(
            "No RABBITMQ_PWD found in environment variables!",
            ac.Printer.Space.AFTER,
        )
        exit(1)

    if len(os.getenv("RABBITMQ_SERVER").split(":")) != 2:  # type: ignore
        ac.Printer.print_error(
            "FLASK_SERVER must be in the format 'host:port'!",
            ac.Printer.Space.AFTER,
        )
        exit(1)

    ac.Printer.print_success("Environment variables setup complete!", ac.Printer.Space.AFTER)


def generate_namespace() -> NodeNamespace:
    """
    Generate the namespace from the YAML file
    """
    # Get YAML path from environment variables. If not found, print error and exit
    yaml_path = os.getenv("CONFIG_YAML")

    ac.Printer.print_info("Setting up namespace...")
    try:
        namespace = ac.YAMLParser(NodeNamespace).parse(yaml_path)
    except Exception as e:  # pylint: disable=broad-except
        ac.Printer.print_error(str(e), ac.Printer.Space.AFTER)
        exit(1)
    ac.Printer.print_success("Namespace setup complete!", ac.Printer.Space.AFTER)

    return namespace


def launch_server(namespace: NodeNamespace):
    """
    Launch the server
    """

    flask_server = os.getenv("FLASK_SERVER")

    flask_host = flask_server.split(":")[0] if flask_server else None
    flask_port = int(flask_server.split(":")[1]) if flask_server else None

    app = Flask(__name__)

    app.config["namespace"] = namespace

    app.register_blueprint(controllers.cameras.handler)

    ac.Printer.print_info("")

    app.run(host=flask_host, port=flask_port, load_dotenv=False)


def cleanup(namespace: NodeNamespace):
    """
    Cleanup function to be called when the program is interrupted
    """

    def _callback():
        # Perform any necessary cleanup
        for sn in namespace.cameras_sn:
            namespace.remove_camera(sn)

        print("\r  ", end="", flush=True)
        ac.Printer.print_goodbye(ac.Printer.Space.BOTH)

        sys.exit(0)

    def handler(signum, frame):  # pylint: disable=unused-argument
        _callback()

    return handler


def main():
    """
    Main function of the program
    """

    ac.Printer.print_header(ac.Printer.Space.BOTH)

    load_argos_env()

    namespace = generate_namespace()

    signal.signal(signal.SIGINT, cleanup(namespace))

    launch_server(namespace)


if __name__ == "__main__":
    main()
