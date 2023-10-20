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
from cmd_parser import CmdParser
from utils import parse_yaml

if __name__ == "__main__":
    parser = CmdParser()
    cmd_args = parser.get_args()

    if cmd_args["mode"] in ["aquire", "a"]:
        print("aquire")
    elif cmd_args["mode"] in ["train", "t"]:
        print("train")
    elif cmd_args["mode"] in ["online", "o"]:
        print("online")
    elif cmd_args["mode"] in ["yaml", "y"]:
        parse_yaml(cmd_args["file"])
    else:
        exit(0)
