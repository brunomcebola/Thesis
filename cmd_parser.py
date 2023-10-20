"""
This module defines the CmdParser class, which provides a command line interface for Argos.
It defines the available modes and their arguments, and parses the cmd line args into a dict.

Classes:
    - CmdParser: Object for parsing command line arguments into Python objects.
"""
import argparse
import sys

from colorama import Fore, Style


class CmdParser:
    """
    A class for parsing command line arguments into Python objects.

    Methods:
        get_args(): Parses the command line arguments and returns them as a dictionary.
    """

    class _ArgumentParser(argparse.ArgumentParser):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._optionals.title = "Optional arguments"
            self._positionals.title = "Positional arguments"

        def format_help(self):
            formatter = self._get_formatter()

            # description
            if self.description:
                formatter.add_text(Style.BRIGHT + self.description + Style.RESET_ALL)

            # usage
            formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

            # positionals, optionals and user-defined groups
            for action_group in self._action_groups:
                formatter.start_section(action_group.title)
                formatter.add_text(action_group.description)
                formatter.add_arguments(
                    action_group._group_actions  # pylint: disable=protected-access
                )
                formatter.end_section()

            # epilog
            formatter.add_text(self.epilog)

            # determine help from format above
            return formatter.format_help()

        def error(self, message):
            print(f"{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} {message}\n")

            if len({"a", "aquire"}.intersection(sys.argv[1:])):
                self.parse_args(["a", "-h"])
            elif len({"t", "train"}.intersection(sys.argv[1:])):
                # self.parse_args(["t", "-h"])
                pass
            elif len({"o", "online"}.intersection(sys.argv[1:])):
                # self.parse_args(["o", "-h"])
                pass
            elif len({"y", "yaml"}.intersection(sys.argv[1:])):
                self.parse_args(["y", "-h"])
            else:
                self.print_help()

            self.exit(2)

    class _SubcommandHelpFormatter(argparse.HelpFormatter):
        def add_usage(self, usage, actions, groups, prefix=None):
            if prefix is None:
                prefix = "Usage: "
                return super().add_usage(usage, actions, groups, prefix)

        def _format_action(self, action):
            parts = super()._format_action(action)

            if action.nargs == argparse.PARSER:
                parts = parts.split("\n")[1:]
                parts = list(map(lambda p: ")  ".join(p.split(")")), parts))
                parts = list(map(lambda p: "  " + p.strip(), parts))
                parts = "\n".join(parts)
                parts = parts.rstrip()

            return parts

    class _SubcommandHelpFormatterModes(_SubcommandHelpFormatter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._max_help_position = 100

    def __init__(self):
        self._parser = self._ArgumentParser(
            description="Argos, Real-time Image Analysis for Fraud Detection",
            formatter_class=self._SubcommandHelpFormatter,
            usage="argos.py [-h | --help]\n" + "       argos.py <mode> [<args>]",
            add_help=False,
        )

        self._parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        self._subparsers = self._parser.add_subparsers(
            title="Modes",
            dest="mode",
            required=True,
        )

        self._add_subparsers()

    def _add_aquire_mode_subparser(self):
        parser = self._subparsers.add_parser(
            "aquire",
            aliases="a",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to capture and store video.",
            allow_abbrev=False,
            formatter_class=self._SubcommandHelpFormatterModes,
            usage="argos.py aquire [-h | --help]\n"
            + "       argos.py aquire {-o | --output <path>} [-c | --cameras <sn> ...]",
            add_help=False,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        parser.add_argument(
            "-c",
            "--cameras",
            nargs="+",
            help="List with the serial numbers of the cameras to be used.",
            metavar="sn",
        )

        parser_required = parser.add_argument_group("Required arguments")

        parser_required.add_argument(
            "-o",
            "--output",
            required=True,
            help="Folder where will be created folders for each camera to store the images.",
            metavar="path",
        )

    def _add_train_mode_subparser(self):
        parser = self._subparsers.add_parser(
            "train",
            aliases="t",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to train a model.",
            allow_abbrev=False,
            formatter_class=self._SubcommandHelpFormatterModes,
            usage="argos.py train [-h | --help]",
            add_help=False,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

    def _add_online_mode_subparser(self):
        parser = self._subparsers.add_parser(
            "online",
            aliases="o",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to run the model online.",
            allow_abbrev=False,
            formatter_class=self._SubcommandHelpFormatterModes,
            usage="argos.py online [-h | --help]",
            add_help=False,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

    def _add_yaml_mode_subparser(self):
        # create the parser for the "yaml" mode
        parser = self._subparsers.add_parser(
            "yaml",
            aliases="y",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to run the model based on a yaml file.",
            allow_abbrev=False,
            formatter_class=self._SubcommandHelpFormatterModes,
            usage="argos.py yaml [-h | --help]\n" + "       argos.py yaml <file>",
            add_help=False,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        parser.add_argument("file", help="Path to yaml file.")

    def _add_subparsers(self):
        self._add_aquire_mode_subparser()
        self._add_train_mode_subparser()
        self._add_online_mode_subparser()
        self._add_yaml_mode_subparser()

    def get_args(self):
        """
        Parses the command line arguments and returns them as a dictionary.

        Returns:
            dict: The command line arguments as a dictionary.
        """
        return vars(self._parser.parse_args())
