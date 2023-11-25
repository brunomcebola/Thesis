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

import arg_parser
import utils
import acquire

if __name__ == "__main__":
    parser = arg_parser.ArgParser()
    parsed_args = parser.get_args()

    try:
        print()
        if parsed_args.mode in ["acquire", "a"]:
            utils.print_info("Entered acquire mode!\n")

            if parsed_args.source in ["yaml", "y"]:
                try:
                    args = utils.parse_acquire_yaml(parsed_args.file)
                except Exception as e:
                    utils.print_error(str(e))
                    exit(1)
            else:
                args = parsed_args.__dict__
                del args["mode"]
                del args["source"]

            try:
                acquire_args = acquire.AcquireNamespace(**args)
                print()
                utils.print_info("Aquire mode settings:\n")
                print(acquire_args)
                print()
            except Exception as e:
                utils.print_error(str(e) + "\n")
                exit(1)

            mode = acquire.Acquire(acquire_args)

            user_prompt = utils.get_user_confirmation(  # pylint: disable=invalid-name
                "Do you wish to start the data acquisition?"
            )
            print()

            if user_prompt is True:
                mode.run()

        elif parsed_args.mode in ["train", "t"]:
            utils.print_info("Entering train mode...\n")
        elif parsed_args.mode in ["online", "o"]:
            utils.print_info("Entering online mode...\n")

    except Exception as e:
        print(e)

        exit(1)

    exit(0)
