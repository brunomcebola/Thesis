"""
This module contains utility functions.

Classes:
--------
- ArgSource: An enumeration of the different sources of the arguments.
- BaseNamespace: The base class for the different modes specific namespaces.

Functions:
----------
- parse_yaml(file_path): Validates a YAML file at the given file path.
- print_info(message): Prints an info message.
- print_success(message): Prints a success message.
- print_warning(message): Prints a warning message.
- print_error(message): Prints an error message.
"""

from enum import IntEnum
from types import SimpleNamespace
import yaml
from colorama import Fore, Style


class ArgSource(IntEnum):
    """
    An enumeration of the different sources of the arguments.

    Attributes:
    -----------
        - CMD (0): The arguments come from the command line.
        - YAML (1): The arguments come from a YAML file.
    """

    CMD = 0
    YAML = 1


class BaseNamespace(SimpleNamespace):
    """
    This class serves as the base for the different modes specific namesapces.

    It is not inteded to be instantiated directly, but rather to be inherited from.

    Attributes:
    -----------
        - source:
            Indicates wheter the args come from the command line of from a YAML file.
    """

    def __init__(self, source: ArgSource):
        self.source = ArgSource(source)


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
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            args = yaml.safe_load(f)
            return dict(args)
    except FileNotFoundError:
        print_error(f"Specified YAML file not found ({file_path}).")
        exit(1)
    except yaml.YAMLError as e:
        if hasattr(e, "problem_mark"):
            print_error(f"Wrong syntax on line {e.problem_mark.line + 1} of the YAML file.")
        else:
            print_error("Unknown problem on the specified YAML file.")
        exit(1)


def print_info(message: str) -> None:
    """
    Prints an info message.

    Args:
    -----
        - message: The info message to be printed.
    """
    print(f"{Fore.BLUE + Style.BRIGHT}Info:{Style.RESET_ALL} {message}")


def print_success(message: str) -> None:
    """
    Prints a success message.

    Args:
    -----
        - message: The success message to be printed.
    """
    print(f"{Fore.GREEN + Style.BRIGHT}Success:{Style.RESET_ALL} {message}")


def print_warning(message: str) -> None:
    """
    Prints a warning message.

    Args:
    -----
        - message: The warning message to be printed.
    """
    print(f"{Fore.YELLOW + Style.BRIGHT}Warning:{Style.RESET_ALL} {message}")


def print_error(message: str) -> None:
    """
    Prints an error message.

    Args:
    -----
        - message: The error message to be printed.
    """
    print(f"{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} {message}")
