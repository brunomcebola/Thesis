"""
This module is the entry point of Argos, a real-time image analysis tool for fraud detection.
It includes a command-line interface with four modes:
    - `aquire` mode captures and stores video
    - `train` mode trains a model
    - `online` mode runs the model online
    - `yaml` mode runs the model based on a yaml file.

Usage:
    $ python argos.py [-h] {aquire,train,online,yaml} ...
"""

import os
import sys

# import threading

import utils
import aquire
from arg_parser import ArgParser

if __name__ == "__main__":
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    sys.tracebacklimit = -1

    parser = ArgParser()
    cmd_args = parser.get_args()

    if cmd_args.mode in ["aquire", "a"]:
        utils.print_info("Entering aquire mode...")
        print()

        try:
            aquireNamespace = aquire.AquireNamespace(utils.ArgSource.CMD, **cmd_args.__dict__)
        except Exception as e:
            utils.print_error(str(e))
            exit(1)

        print()
        utils.print_info("Aquire mode settings:")
        print(aquireNamespace)
        print()

        prompt = utils.get_user_confirmation(  # pylint: disable=invalid-name
            "Do you wish to continue?"
        )
        print()

        if prompt:
            pass
            # t1 = threading.Thread(target=aquire.aquire)
            # t1.start()

            # if not get_user_confirmation("Do you wish to continue?"):
            #     aquire.STOP_FLAG = True
            #     t1.join()
            #     exit(0)
        else:
            utils.print_info("Exiting aquire mode...")
            exit(0)

    elif cmd_args.mode in ["train", "t"]:
        utils.print_info("Entering train mode...")
        print()
    elif cmd_args.mode in ["online", "o"]:
        utils.print_info("Entering online mode...")
        print()
    elif cmd_args.mode in ["yaml", "y"]:
        utils.print_info("Entering yaml mode...")
        print()

        args = utils.parse_yaml(cmd_args.config_file)
        # print(args)

        try:
            aquireNamespace = aquire.AquireNamespace(utils.ArgSource.YAML, **args)
        except Exception as e:
            utils.print_error(str(e))
            exit(1)

        print()
        utils.print_info("Aquire mode settings:")
        print(aquireNamespace)
        print()
    else:
        exit(0)
