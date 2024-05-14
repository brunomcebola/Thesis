"""
This module is the entry point of Argos, a real-time image analysis tool for fraud detection.
"""

from __future__ import annotations

import os
from typing import Type
from dotenv import find_dotenv, load_dotenv

import argos_common as ac


# from ..src.core import services

# MAP_TO_SERVICE_CLASS: dict[str, Type[services.base.Service]] = {
# "acquire": services.acquire.AcquireService,
# "preprocess": services.preprocess.PreprocessService,
# }
#
# MAP_TO_SERVICE_NAMESPACE_CLASS: dict[str, Type[services.base.ServiceNamespace]] = {
# "acquire": services.acquire.AcquireServiceNamespace,
# "preprocess": services.preprocess.PreprocessServiceNamespace,
# }


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

    # parser.add_parser(
    #     "terminal",
    #     "start",
    #     {
    #         "description": "Services launcher",
    #         "help": "Mode to launch an Argos service.",
    #     },
    # )

    # parser.add_parser(
    #     "terminal",
    #     "service",
    #     {
    #         "description": "Services launcher",
    #         "help": "Mode to launch an Argos service.",
    #     },
    # )

    # parser.add_parser(
    #     "service",
    #     "acquire",
    #     {
    #         "description": "Services launcher",
    #         "help": "Mode to launch an Argos service.",
    #     },
    # )

    # parser.add_arguments_to_parser(
    #     "acquire",
    #     [
    #         (
    #             ["-c", "--camera"],
    #             {
    #                 "nargs": 1,
    #                 "help": "Specify the camera to be used by serial number.",
    #                 "metavar": "sn",
    #                 "dest": "serial_numbers",
    #                 "type": ac.Parser.non_empty_string_type,
    #             },
    #         ),
    #         (
    #             ["-o", "--output-folder"],
    #             {
    #                 "help": "Folder where the acquired images will be stored.",
    #                 "metavar": "path",
    #                 "type": ac.Parser.non_empty_string_type,
    #             },
    #         ),
    #         (
    #             ["-y", "--yaml"],
    #             {
    #                 "help": "Path to the yaml configuration file.",
    #                 "metavar": "path",
    #                 "type": ac.Parser.non_empty_string_type,
    #             },
    #         ),
    #     ],
    # )

    return parser


def main():
    """
    Main function of the program
    """

    ac.Printer.print_header(ac.Printer.Space.BOTH)

    # Generate the parser
    parser = _generate_parser()

    # Parse the command line arguments
    cmd_line_args = parser.get_args()

    # Build the .env file name based on the ARGOS_ENV environment variable
    # Defaults to '.env.production' if ARGOS_ENV not set
    env_type = os.getenv("ARGOS_ENV", "production")
    env_file = f".env.{env_type}"

    ac.Printer.print_info(f"Setting {env_type.upper()} environment!")

    # Find the .env file
    try:
        env_path = find_dotenv(filename=env_file, raise_error_if_not_found=True)
    except IOError as e:
        ac.Printer.print_error(str(e), ac.Printer.Space.AFTER)
        exit(1)

    # Load the environment variables from the corresponding file
    load_dotenv(dotenv_path=env_path)
    ac.Printer.print_success(
        f"Environment variables loaded from {env_path}!", ac.Printer.Space.AFTER
    )

    try:

        pass

        # if cmd_line_args.resource == "interface":
        #     run_interface()

        # elif cmd_line_args.resource == "service":
        #     service = cmd_line_args.service
        #     command = cmd_line_args.command

        #     cmd_line_args = cmd_line_args.__dict__

        #     del cmd_line_args["resource"]
        #     del cmd_line_args["service"]
        #     del cmd_line_args["command"]

        #     if command == "run":
        #         if "yaml" in cmd_line_args and cmd_line_args["yaml"] is not None:
        #             args = MAP_TO_SERVICE_NAMESPACE_CLASS[service].from_yaml(cmd_line_args["yaml"])
        #         else:
        #             args = MAP_TO_SERVICE_NAMESPACE_CLASS[service](**cmd_line_args)

        #         # Run the service

        #         utils.print_info(f"{MAP_TO_SERVICE_CLASS[service].__name__} settings")
        #         print(args)
        #         print()

        #         user_confirm = utils.get_user_confirmation(
        #             "Do you wish to start the data acquisition?"
        #         )
        #         print()

        #         if user_confirm:
        #             MAP_TO_SERVICE_CLASS[service](args).run()

        #     elif command == "logs":
        #         MAP_TO_SERVICE_CLASS[service].logs(cmd_line_args["logs_dest"])

        #     else:
        #         utils.print_error("Invalid command!\n")

    except Exception as e:  # pylint: disable=broad-except
        ac.Printer.print_error(str(e) + "\n")

        ac.Printer.print_warning("Terminating program!\n")

        exit(1)

    except KeyboardInterrupt as e:  # pylint: disable=unused-variable
        print()
        print()

        ac.Printer.print_warning("Terminating program!\n")

        exit(1)

    ac.Printer.print_warning("Terminating program!\n")

    exit(0)


if __name__ == "__main__":
    main()
