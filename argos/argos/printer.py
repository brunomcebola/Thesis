"""
This module contains the ArgosPrinter class.
"""

from colorama import Fore, Style


class ArgosPrinter:
    """
    A class that contains static methods for printing messages to the console.
    """

    @classmethod
    def print_header(cls) -> None:
        """
        Prints the program header.
        """
        print(
            Style.BRIGHT
            + Fore.LIGHTBLUE_EX
            + "Welcome to Argos, Real-time Image Analysis for Fraud Detection!"
            + Style.RESET_ALL
        )

    @classmethod
    def print_info(cls, message: str) -> None:
        """
        Prints an info message.

        Args:
        -----
            - message: The info message to be printed.
        """
        print(f"{Fore.LIGHTCYAN_EX + Style.BRIGHT}Info:{Style.RESET_ALL} {message}")

    @classmethod
    def print_success(cls, message: str) -> None:
        """
        Prints a success message.

        Args:
        -----
            - message: The success message to be printed.
        """
        print(f"{Fore.LIGHTGREEN_EX + Style.BRIGHT}Success:{Style.RESET_ALL} {message}")

    @classmethod
    def print_warning(cls, message: str) -> None:
        """
        Prints a warning message.

        Args:
        -----
            - message: The warning message to be printed.
        """
        print(f"{Fore.LIGHTYELLOW_EX + Style.BRIGHT}Warning:{Style.RESET_ALL} {message}")

    @classmethod
    def print_error(cls, message: str) -> None:
        """
        Prints an error message.

        Args:
        -----
            - message: The error message to be printed.
        """
        print(f"{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} {message}")
