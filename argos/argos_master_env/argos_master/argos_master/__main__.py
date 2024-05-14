"""
This module is the entry point of Argos master.
"""

from __future__ import annotations

from dotenv import load_dotenv

from ..printer import ArgosPrinter
from ..parser import ArgosParser


# from .web import run_interface


def _generate_parser() -> ArgosParser:
    """
    Generates the ArgosParser object.

    Returns:
    --------
        - ArgosParser: The generated ArgosParser object.
    """

    parser = ArgosParser("(master)")

    parser.add_parser(
        "root",
        "command",
        "interface",
        True,
        {
            "description": "Interface launcher",
            "help": "Mode to start the Argos Interface.",
        },
    )

    return parser


def main():
    """
    Main function of the program
    """

    load_dotenv()

    try:
        parser = _generate_parser()

        cmd_line_args = parser.get_args()

        ArgosPrinter.print_header(ArgosPrinter.Space.BOTH)

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

        #         ArgosPrinter.print_info(f"{MAP_TO_SERVICE_CLASS[service].__name__} settings")
        #         print(args)
        #         print()

        #         while True:
        #             response = input("Do you wish to start the data acquisition? (y/n): ")

        #             if response in ["y", "Y", "yes", "Yes", "YES"]:
        #                 MAP_TO_SERVICE_CLASS[service](args).run()

        #             elif response in ["n", "N", "no", "No", "NO"]:
        #                 return False

        #             else:
        #                 Printer.print_warning("Invalid response. Please enter y or n.")
        #                 print()

        #     elif command == "logs":
        #         MAP_TO_SERVICE_CLASS[service].logs(cmd_line_args["logs_dest"])

        #     else:
        #         Printer.print_error("Invalid command!\n")

    except Exception as e:  # pylint: disable=broad-except
        ArgosPrinter.print_error(str(e) + "\n")

        ArgosPrinter.print_warning("Terminating program!\n")

        exit(1)

    except KeyboardInterrupt as e:  # pylint: disable=unused-variable
        print()
        print()

        ArgosPrinter.print_warning("Terminating program!\n")

        exit(1)

    ArgosPrinter.print_warning("Terminating program!\n")

    exit(0)


if __name__ == "__main__":
    main()