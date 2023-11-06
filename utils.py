"""
This module contains utility functions.

Functions:
----------
- parse_yaml(file_path) -> dict: Validates a YAML file at the given file path.
- print_info(message): Prints an info message.
- print_success(message): Prints a success message.
- print_warning(message): Prints a warning message.
- print_error(message): Prints an error message.
- get_user_confirmation(message) -> bool: Asks the user for confirmation.
"""

import yaml
from colorama import Fore, Style
from jsonschema import validate

import intel


class ModeError(Exception):
    """
    Raised when an invalid mode is specified.
    """


def parse_yaml(file_path: str) -> dict:
    """
    Parses a YAML file and returns its contents as a dictionary.

    Args:
    -----
        - file_path: The path to the YAML file to be parsed.

    Returns:
    --------
        The contents of the YAML file as a dictionary.
    """

    aquire_schema = {
        "type": "object",
        "properties": {
            "output_folder": {"type": "string"},
            "op_time": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "uniqueItems": True,
                "prefixItems": [
                    {"type": "integer", "minimum": 0, "maximum": 23},
                    {"type": "integer", "minimum": 1, "maximum": 24},
                ],
            },
            "op_times": {
                "type": "array",
                "minItems": 7,
                "maxItems": 7,
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "uniqueItems": True,
                    "prefixItems": [
                        {"type": "integer", "minimum": 0, "maximum": 23},
                        {"type": "integer", "minimum": 1, "maximum": 24},
                    ],
                },
            },
            "camera": {
                "anyOf": [{"type": "string"}, {"type": "number", "minimum": 0}]
            },
            "stream_type": {"enum": [type.name.lower() for type in intel.StreamType]},
            "cameras": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "sn": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "number", "minimum": 0},
                            ]
                        },
                        "name": {"type": "string", "minLength": 1},
                        "stream_type": {"enum": [type.name.lower() for type in intel.StreamType]},
                        "stream_config": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "width": {"type": "integer", "minimum": 0},
                                    "height": {"type": "integer", "minimum": 0},
                                    "format": {"type": "string"},
                                    "fps": {"type": "number", "minimum": 0},
                                },
                                "required": ["width", "height", "format", "fps"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["sn"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["output_folder"],
        "allOf": [
            {"not": {"required": ["op_time", "op_times"]}},
            {"not": {"required": ["camera", "cameras"]}},
            {"not": {"required": ["stream_type", "cameras"]}},
        ],
        "additionalProperties": False,
    }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            args = yaml.safe_load(f)

            mode = args["mode"]
            del args["mode"]

            if mode == "aquire":
                try:
                    validate(args, aquire_schema)

                    return {}
                except Exception as e:
                    raise e

            elif mode == "train":
                pass
            elif mode == "online":
                pass
            else:
                raise ModeError("Invalid mode.")

            return dict(args)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Specified YAML file not found ({file_path}).") from e
    except yaml.YAMLError as e:
        if hasattr(e, "problem_mark"):
            line = e.problem_mark.line + 1  # type: ignore
            raise SyntaxError(f"Wrong syntax on line {line} of the YAML file.") from e
        else:
            raise RuntimeError("Unknown problem on the specified YAML file.") from e


def print_info(message: str) -> None:
    """
    Prints an info message.

    Args:
    -----
        - message: The info message to be printed.
    """
    print(f"{Fore.LIGHTCYAN_EX + Style.BRIGHT}Info:{Style.RESET_ALL} {message}")


def print_success(message: str) -> None:
    """
    Prints a success message.

    Args:
    -----
        - message: The success message to be printed.
    """
    print(f"{Fore.LIGHTGREEN_EX + Style.BRIGHT}Success:{Style.RESET_ALL} {message}")


def print_warning(message: str) -> None:
    """
    Prints a warning message.

    Args:
    -----
        - message: The warning message to be printed.
    """
    print(f"{Fore.LIGHTYELLOW_EX + Style.BRIGHT}Warning:{Style.RESET_ALL} {message}")


def print_error(message: str) -> None:
    """
    Prints an error message.

    Args:
    -----
        - message: The error message to be printed.
    """
    print(f"{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} {message}")


def get_user_confirmation(message: str) -> bool:
    """
    Asks the user for confirmation.
    """
    while True:
        response = input(f"{message} (y/n): ")
        if response in ["y", "Y", "yes", "Yes", "YES"]:
            return True
        elif response in ["n", "N", "no", "No", "NO"]:
            return False
        else:
            print_warning("Invalid response. Please enter y or n.")
