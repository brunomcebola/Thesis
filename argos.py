"""
This module is the entry point of Argos, a real-time image analysis tool for fraud detection.
It includes a command-line interface with four modes:
    - `acquire` mode captures and stores video
    - `train` mode trains a model
    - `online` mode runs the model online
    - `yaml` mode runs the model based on a yaml file.

Usage:
    $ python argos.py [-h] {acquire,train,online,yaml} ...
"""

import colorama

import src.parser as parser
import src.utils as utils

import src.modes as modes

MAP_TO_MODE_CLASS = {
    "acquire": modes.acquire.Acquire,
    "a": modes.acquire.Acquire,
}

MAP_TO_MODE_NAMESPACE_CLASS = {
    "acquire": modes.acquire.AcquireNamespace,
    "a": modes.acquire.AcquireNamespace,
}

if __name__ == "__main__":
    try:
        print()
        print(
            colorama.Style.BRIGHT
            + colorama.Fore.CYAN
            + "Welcome to Argos, Real-time Image Analysis for Fraud Detection!"
            + colorama.Style.RESET_ALL
        )
        print()

        parser = parser.Parser()

        cmd_line_args = parser.get_args()

        mode = cmd_line_args.mode

        if cmd_line_args.run and cmd_line_args.logs:
            raise ValueError("Cannot run and log at the same time.")

        elif cmd_line_args.run:
            if cmd_line_args.yaml:
                args = MAP_TO_MODE_NAMESPACE_CLASS[mode].from_yaml(cmd_line_args.yaml)
            else:
                cmd_line_args = cmd_line_args.__dict__

                del cmd_line_args["mode"]
                del cmd_line_args["run"]
                del cmd_line_args["logs"]
                del cmd_line_args["logs_dest"]
                args = MAP_TO_MODE_NAMESPACE_CLASS[mode](**cmd_line_args)

            # Run the mode

            print()
            utils.print_info(
                colorama.Style.BRIGHT
                + f"{MAP_TO_MODE_CLASS[mode].__name__} settings"
                + colorama.Style.RESET_ALL
            )
            print(args)
            print()

            USER_CONFIRM = utils.get_user_confirmation("Do you wish to start the data acquisition?")
            print()

            if USER_CONFIRM:
                MAP_TO_MODE_CLASS[mode](args).run()

        elif cmd_line_args.logs:
            MAP_TO_MODE_CLASS[mode].logs(cmd_line_args.logs_dest)

        else:
            raise ValueError("No mode selected.")

    except Exception as e:  # pylint: disable=broad-except
        utils.print_error(str(e) + "\n")

        utils.print_warning("Terminating program!\n")

        exit(1)

    except KeyboardInterrupt as e:
        print()
        print()

        utils.print_warning("Terminating program!\n")

        exit(1)

    exit(0)
