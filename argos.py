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

import src.parser as parser
import src.utils as utils

import src.modes as modes

if __name__ == "__main__":
    try:
        parser = parser.Parser()
        cmd_line_args = parser.get_args()

        print()

        # Set up the mode

        if cmd_line_args.mode in ["acquire", "a"]:
            if cmd_line_args.sub_mode in ["log", "l"]:
                modes.acquire.Acquire.logs(cmd_line_args.export_path)

                exit(0)

            else:
                if cmd_line_args.sub_mode in ["yaml", "y"]:
                    args = modes.acquire.AcquireNamespace.from_yaml(cmd_line_args.file)

                else:
                    args = cmd_line_args.__dict__
                    del args["mode"]
                    del args["sub_mode"]
                    args = modes.acquire.AcquireNamespace(**args)

            mode = modes.acquire.Acquire(args)

        elif cmd_line_args.mode in ["realtime", "r"]:
            args = cmd_line_args.__dict__
            del args["mode"]
            args = modes.realtime.RealtimeNamespace(**args)

            mode = modes.realtime.Realtime(args)

        # Run the mode

        print()
        utils.print_info("Mode settings:\n")
        print(args)
        print()

        user_confirm = utils.get_user_confirmation("Do you wish to start the data acquisition?")
        print()

        if user_confirm:
            mode.run()

    except Exception as e:
        utils.print_error(str(e) + "\n")

        utils.print_warning("Terminating program!\n")

        exit(1)

    except KeyboardInterrupt as e:
        print()
        print()

        utils.print_warning("Terminating program!\n")

        exit(1)

    exit(0)
