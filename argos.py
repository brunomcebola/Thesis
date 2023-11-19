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

import os
import sys

# import threading

import utils
import acquire
from arg_parser import ArgParser

if __name__ == "__main__":
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    sys.tracebacklimit = -1

    parser = ArgParser()
    cmd_args = parser.get_args()

    if cmd_args.mode in ["acquire", "a"]:
        mode = acquire.Acquire(**cmd_args.__dict__)

        mode.run()

        # mode.stop()

    elif cmd_args.mode in ["train", "t"]:
        utils.print_info("Entering train mode...\n")
    elif cmd_args.mode in ["online", "o"]:
        utils.print_info("Entering online mode...\n")
    elif cmd_args.mode in ["yaml", "y"]:
        utils.print_info("Entered YAML mode!\n")

        try:
            args = utils.parse_yaml(cmd_args.config_file)
        except Exception as e:
            utils.print_error(str(e))
            exit(1)

        if args["mode"] == "acquire":
            utils.print_info("Switched to acquire mode!\n")

            try:
                acquire_args = acquire.AcquireNamespace(**args)
                print()
                utils.print_info("Aquire mode settings:\n")
                print(acquire_args)
                print()
            except Exception as e:
                print(e)
                exit(1)

            mode = acquire.Acquire(acquire_args)

            user_prompt = utils.get_user_confirmation(  # pylint: disable=invalid-name
                "Do you wish to start the data acquisition?"
            )
            print()

            if user_prompt is True:
                mode.run()

            exit(0)

    else:
        exit(0)
