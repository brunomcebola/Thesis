"""
This module contains utility functions.

Functions:
- parse_yaml(file_path): Validates a YAML file at the given file path.
"""

import json
import sys
import yaml

from colorama import Fore, Style

sys.tracebacklimit = None


def parse_yaml(file_path):
    """
    Parses a YAML file and returns its contents as a dictionary.

    Args:
        file_path (str): The path to the YAML file to be parsed.

    Returns:
        dict: The contents of the YAML file as a dictionary.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            args = yaml.safe_load(f)
            print(json.dumps(args, indent=4))
            return args
    except FileNotFoundError:
        print(
            f"\n{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} " \
            + "Specified YAML file not found.\n"
        )
        exit(1)
    except yaml.YAMLError as e:
        if hasattr(e, 'problem_mark'):
            print(
                f"\n{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} " \
                + f"Wrong syntax on line {e.problem_mark.line + 1} of the YAML file.\n"
            )
        else:
            print(
                f"\n{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} " \
                + "Unknown problem on the YAML file\n"
            )
        exit(1)
        