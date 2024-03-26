"""
This module is the entry point of Argos, a real-time image analysis tool for fraud detection.
"""

from __future__ import annotations

import os

from typing import Type
from dotenv import load_dotenv

from .src import utils
from .src.core import services
from .src.interface import run_interface

MAP_TO_SERVICE_CLASS: dict[str, Type[services.base.Service]] = {
    "acquire": services.acquire.AcquireService,
    "preprocess": services.preprocess.PreprocessService,
}

MAP_TO_SERVICE_NAMESPACE_CLASS: dict[str, Type[services.base.ServiceNamespace]] = {
    "acquire": services.acquire.AcquireServiceNamespace,
    "preprocess": services.preprocess.PreprocessServiceNamespace,
}


def main():
    """
    Main function of the program
    """

    load_dotenv()

    try:
        parser = utils.parser.Parser()

        cmd_line_args = parser.get_args()

        print()
        utils.print_header()
        print()

        if cmd_line_args.resource == "interface":
            run_interface()

        elif cmd_line_args.resource == "service":
            service = cmd_line_args.service
            command = cmd_line_args.command

            cmd_line_args = cmd_line_args.__dict__

            del cmd_line_args["resource"]
            del cmd_line_args["service"]
            del cmd_line_args["command"]

            if command == "run":
                if "yaml" in cmd_line_args and cmd_line_args["yaml"] is not None:
                    args = MAP_TO_SERVICE_NAMESPACE_CLASS[service].from_yaml(cmd_line_args["yaml"])
                else:
                    args = MAP_TO_SERVICE_NAMESPACE_CLASS[service](**cmd_line_args)

                # Run the service

                utils.print_info(f"{MAP_TO_SERVICE_CLASS[service].__name__} settings")
                print(args)
                print()

                user_confirm = utils.get_user_confirmation(
                    "Do you wish to start the data acquisition?"
                )
                print()

                if user_confirm:
                    MAP_TO_SERVICE_CLASS[service](args).run()

            elif command == "logs":
                MAP_TO_SERVICE_CLASS[service].logs(cmd_line_args["logs_dest"])

            else:
                utils.print_error("Invalid command!\n")

    except Exception as e:  # pylint: disable=broad-except
        utils.print_error(str(e) + "\n")

        utils.print_warning("Terminating program!\n")

        exit(1)

    except KeyboardInterrupt as e:  # pylint: disable=unused-variable
        print()
        print()

        utils.print_warning("Terminating program!\n")

        exit(1)

    print()
    print()

    utils.print_warning("Terminating program!\n")

    exit(0)


if __name__ == "__main__":
    main()
