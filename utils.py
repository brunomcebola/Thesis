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
