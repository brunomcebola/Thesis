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

from .namespace import NodeNamespace
from .controllers import cameras


import threading
import cv2


class DisplayThread(threading.Thread):
    """Display thread"""

    def __init__(self, namespace):
        super().__init__()
        self.namespace: NodeNamespace = namespace
        self.running = True

    def run(self):
        while self.running:
            frame = self.namespace.camera_interaction(
                self.namespace.cameras_sn[0], self.namespace.CameraInteraction.GET_NEXT_FRAME
            )

            if frame is None or frame.color is None:
                continue

            # Process frame here
            cv2.imshow("Color", frame.color)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.stop()

    def stop(self):
        """Stop"""
        self.running = False
        cv2.destroyAllWindows()


# Cleanup function with parameters
def cleanup_before_exit(namespace: NodeNamespace, display_thread: DisplayThread):
    """
    Cleanup function to be called before exiting the program
    """
    print("Cleanup!")
    # Perform any necessary cleanup

    if display_thread.is_alive():
        display_thread.stop()
        display_thread.join()

    for sn in namespace.cameras_sn:
        namespace.remove_camera(sn)

    sys.exit(0)


# Wrapper function to pass parameters
def signal_handler_wrapper(namespace: NodeNamespace, display_thread: DisplayThread):
    """
    Wrapper function to pass parameters to the cleanup function
    """

    def handler(signum, frame):
        cleanup_before_exit(namespace, display_thread)

    return handler


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

    node_namespace.camera_interaction(
        node_namespace.cameras_sn[0], node_namespace.CameraInteraction.START_STREAMING
    )

    display_thread = DisplayThread(node_namespace)
    display_thread.daemon = True
    display_thread.start()

    signal.signal(signal.SIGINT, signal_handler_wrapper(node_namespace, display_thread))

    app = Flask(__name__)

    app.config["namespace"] = node_namespace

    app.register_blueprint(cameras.handler)

    port = int(os.getenv("ARGOS_PORT", "5000"))

    ac.Printer.print_info(f"Launched server on port {port}!")

    app.run(port=port, load_dotenv=False)


if __name__ == "__main__":
    main()
