"""
This module contains the ArgosPrinter class.
"""

from __future__ import annotations

from enum import Enum
from colorama import Fore, Style


class ArgosPrinter:
    """
    A class that contains static methods for printing messages to the console.
    """

    class Space(Enum):
        """
        An enumeration that defines the space options for the print methods.
        """

        NONE = 0
        BEFORE = 1
        AFTER = 2
        BOTH = 3

    @classmethod
    def _base_print(cls, message: str, space: Space = Space.NONE) -> None:
        """
        Prints a base message.
        """

        if space == cls.Space.BEFORE or space == cls.Space.BOTH:
            print()

        print(message)

        if space == cls.Space.AFTER or space == cls.Space.BOTH:
            print()

    @classmethod
    def print_header(cls, space: Space = Space.NONE) -> None:
        """
        Prints the program header.
        """

        cls._base_print(
            f"{Style.BRIGHT + Fore.LIGHTBLUE_EX}Welcome to Argos, Real-time Image Analysis for Fraud Detection!{Style.RESET_ALL}",  # pylint: disable=line-too-long
            space,
        )

    @classmethod
    def print_info(cls, message: str, space: Space = Space.NONE) -> None:
        """
        Prints an info message.

        Args:
        -----
            - message: The info message to be printed.
        """
        cls._base_print(
            f"{Fore.LIGHTCYAN_EX + Style.BRIGHT}Info:{Style.RESET_ALL} {message}",
            space,
        )

    @classmethod
    def print_success(cls, message: str, space: Space = Space.NONE) -> None:
        """
        Prints a success message.

        Args:
        -----
            - message: The success message to be printed.
        """
        cls._base_print(
            f"{Fore.LIGHTGREEN_EX + Style.BRIGHT}Success:{Style.RESET_ALL} {message}",
            space,
        )

    @classmethod
    def print_warning(cls, message: str, space: Space = Space.NONE) -> None:
        """
        Prints a warning message.

        Args:
        -----
            - message: The warning message to be printed.
        """
        cls._base_print(
            f"{Fore.LIGHTYELLOW_EX + Style.BRIGHT}Warning:{Style.RESET_ALL} {message}",
            space,
        )

    @classmethod
    def print_error(cls, message: str, space: Space = Space.NONE) -> None:
        """
        Prints an error message.

        Args:
        -----
            - message: The error message to be printed.
        """
        cls._base_print(
            f"{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} {message}",
            space,
        )
