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
    parser = parser.Parser()
    parsed_args = parser.get_args()

    print()

    try:
        # acquire mode
        if parsed_args.mode in ["acquire", "a"]:
            if parsed_args.sub_mode in ["log", "l"]:
                if parsed_args.export_path is None:
                    modes.acquire.Acquire.print_logs()
                else:
                    modes.acquire.Acquire.export_logs(parsed_args.export_path)

            else:
                args = None  # pylint: disable=invalid-name

                if parsed_args.sub_mode in ["yaml", "y"]:
                    args = modes.acquire.parse_acquire_yaml(parsed_args.file)
                else:
                    args = parsed_args.__dict__
                    del args["mode"]
                    del args["sub_mode"]

                try:
                    acquire_args = modes.acquire.AcquireNamespace(**args)
                    print()
                    utils.print_info("Aquire mode settings:\n")
                    print(acquire_args)
                    print()
                except Exception as e:
                    utils.print_error(str(e) + "\n")
                    exit(1)

                acquire_handler = modes.acquire.Acquire(acquire_args)

                user_prompt = utils.get_user_confirmation(  # pylint: disable=invalid-name
                    "Do you wish to start the data acquisition?"
                )
                print()

                if user_prompt is True:
                    acquire_handler.run()

        # realtime mode
        elif parsed_args.mode in ["realtime", "r"]:
            args = parsed_args.__dict__
            del args["mode"]

            try:
                realtime_args = modes.realtime.RealtimeNamespace(**args)
                print()
                utils.print_info("Realtime mode settings:\n")
                print(realtime_args)
                print()
            except Exception as e:
                utils.print_error(str(e) + "\n")
                exit(1)

            realtime_handler = modes.realtime.Realtime(realtime_args)

            user_prompt = utils.get_user_confirmation(  # pylint: disable=invalid-name
                "Do you wish to start the data acquisition?"
            )
            print()

            if user_prompt is True:
                realtime_handler.run()

        # calibration mode
        elif parsed_args.mode in ["calibrate", "cal"]:
            pass

        # train mode
        elif parsed_args.mode in ["train", "t"]:
            utils.print_warning("This mode is not yet implemented!\n")

        # online mode
        elif parsed_args.mode in ["online", "o"]:
            utils.print_warning("This mode is not yet implemented!\n")

    except Exception as e:
        utils.print_error(str(e) + "\n")

        utils.print_warning("Terminating program!\n")

        exit(1)

    exit(0)
