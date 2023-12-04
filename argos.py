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

import helpers.arg_parser as arg_parser
import helpers.utils as utils
import modes.acquire as acquire

if __name__ == "__main__":
    parser = arg_parser.ArgParser()
    parsed_args = parser.get_args()

    print()

    try:
        # acquire mode
        if parsed_args.mode in ["acquire", "a"]:
            if parsed_args.sub_mode in ["log", "l"]:
                if parsed_args.export_path is None:
                    acquire.Acquire.print_logs()
                else:
                    acquire.Acquire.export_logs(parsed_args.export_path)

            if parsed_args.sub_mode in ["yaml", "y"] or parsed_args.sub_mode in ["cmd", "c"]:
                args = None  # pylint: disable=invalid-name

                if parsed_args.sub_mode in ["yaml", "y"]:
                    args = utils.parse_acquire_yaml(parsed_args.file)
                else:
                    args = parsed_args.__dict__
                    del args["mode"]
                    del args["sub_mode"]

                try:
                    acquire_args = acquire.AcquireNamespace(**args)
                    print()
                    utils.print_info("Aquire mode settings:\n")
                    print(acquire_args)
                    print()
                except Exception as e:
                    utils.print_error(str(e) + "\n")
                    exit(1)

                acquire_handler = acquire.Acquire(acquire_args)

                user_prompt = utils.get_user_confirmation(  # pylint: disable=invalid-name
                    "Do you wish to start the data acquisition?"
                )
                print()

                if user_prompt is True:
                    acquire_handler.run()
        # train mode
        elif parsed_args.mode in ["train", "t"]:
            utils.print_warning("This mode is not yet implemented!\n")

        # online mode
        elif parsed_args.mode in ["online", "o"]:
            utils.print_warning("This mode is not yet implemented!\n")

        # calibration mode
        elif parsed_args.mode in ["calibrate", "cal"]:
            pass

    except Exception as e:
        utils.print_error(str(e) + "\n")

        utils.print_warning("Terminating program!\n")

        exit(1)

    exit(0)
