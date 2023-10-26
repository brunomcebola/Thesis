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

import aquire
from arg_parser import ArgParser
from utils import parse_yaml, ArgSource, print_info, get_user_confirmation

from camera import StreamConfig

s = StreamConfig(1,1,1,1)
print(s)

if __name__ == "__main__":
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    sys.tracebacklimit = -1

    parser = ArgParser()
    cmd_args = parser.get_args()
    print(cmd_args)

    if cmd_args.mode in ["aquire", "a"]:
        print_info("Entering aquire mode...")
        print()

        aquireNamespace = aquire.AquireNamespace(ArgSource.CMD, **cmd_args.__dict__)

        print()
        print_info("Aquire mode settings:")
        print(aquireNamespace)
        print()

        if get_user_confirmation("Do you wish to continue?"):
            pass
            # t1 = threading.Thread(target=aquire.aquire)
            # t1.start()

            # if not get_user_confirmation("Do you wish to continue?"):
            #     aquire.STOP_FLAG = True
            #     t1.join()
            #     exit(0)
        else:
            exit(0)

    elif cmd_args.mode in ["train", "t"]:
        print("train")
    elif cmd_args.mode in ["online", "o"]:
        print("online")
    elif cmd_args.mode in ["yaml", "y"]:
        print(cmd_args)
        args = parse_yaml(cmd_args.file)
        print(args["mode"])
    else:
        exit(0)
