"""
This module is the entry point of Argos, a real-time image analysis tool for fraud detection.
"""

from __future__ import annotations

import os
from flask import Flask
from dotenv import find_dotenv, load_dotenv

import argos_common as ac

from .namespace import NodeNamespace


def main():
    """
    Main function of the program
    """

    ac.Printer.print_header(ac.Printer.Space.BOTH)

    # Find the .env file
    ac.Printer.print_info("Setting environment variables!")
    try:
        env_path = find_dotenv(filename=".env.argos", raise_error_if_not_found=True)
    except IOError:
        ac.Printer.print_error(
            "Unable to setup environment varibales. No '.env.argos' file found!",
            ac.Printer.Space.AFTER,
        )
        exit(1)

    # Load the environment variables from the corresponding file
    load_dotenv(dotenv_path=env_path)
    ac.Printer.print_success("Environment variables set!", ac.Printer.Space.AFTER)

    # Get YAML path from environment variables. If not found, print error and exit
    yaml_path = os.getenv("ARGOS_YAML")
    if yaml_path is None:
        ac.Printer.print_error(
            "No ARGOS_YAML found in environment variables! Exiting...",
            ac.Printer.Space.AFTER,
        )
        exit(1)

    try:
        node_namespace: NodeNamespace = ac.YAMLParser(NodeNamespace).parse(yaml_path)
    except Exception as e:  # pylint: disable=broad-except
        ac.Printer.print_error(str(e), ac.Printer.Space.AFTER)
        exit(1)

    app = Flask(__name__)

    app.config["namespace"] = node_namespace

    port = int(os.getenv("ARGOS_PORT", "5000"))

    ac.Printer.print_info(f"Launched server on port {port}!")
    app.run(port=port)


if __name__ == "__main__":
    main()
