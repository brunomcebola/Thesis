"""
This module is the entry point of Argos, a real-time image analysis tool for fraud detection.
"""

from __future__ import annotations

import os
from dotenv import find_dotenv, load_dotenv

import argos_common as ac

from .network import run_network


def _generate_parser() -> ac.Parser:
    """
    Generates the ArgosParser object.

    Returns:
    --------
        - ArgosParser: The generated ArgosParser object.
    """

    parser = ac.Parser()

    parser.add_parser(
        "root",
        "network",
        {
            "description": "Network interface",
            "help": "Launches the network interface.",
        },
    )

    parser.add_parser(
        "root",
        "terminal",
        {
            "description": "Terminal interface",
            "help": "Launches the terminal interface.",
        },
    )

    return parser


def main():
    """
    Main function of the program
    """

    # Checks if ARGOS_ENV environment variable is set
    # If not, defaults to 'production'
    if "ARGOS_ENV" not in os.environ:
        os.environ["ARGOS_ENV"] = "production"

    ac.Printer.print_header(ac.Printer.Space.BOTH)

    # Find the .env file
    ac.Printer.print_info(f"Setting {os.environ['ARGOS_ENV'].upper()} environment!")
    try:
        env_path = find_dotenv(
            filename=f".env.{os.environ['ARGOS_ENV']}", raise_error_if_not_found=True
        )
    except IOError:
        ac.Printer.print_error(
            f"Unable to set {os.environ['ARGOS_ENV'].upper()} environment!", ac.Printer.Space.AFTER
        )
        exit(1)

    # Load the environment variables from the corresponding file
    load_dotenv(dotenv_path=env_path)
    ac.Printer.print_success(
        f"{os.environ['ARGOS_ENV'].upper()} environment set!", ac.Printer.Space.AFTER
    )

    # Generate the parser
    parser = _generate_parser()

    # Parse the command line arguments
    cmd_line_args = parser.get_args()

    if cmd_line_args.root_command == "network":
        run_network()
        
        ac.Printer.print_goodbye(ac.Printer.Space.AFTER)
        exit(0)

    if cmd_line_args.root_command == "terminal":
        print("Terminal\n")

        ac.Printer.print_goodbye(ac.Printer.Space.AFTER)
        exit(0)


if __name__ == "__main__":
    main()
