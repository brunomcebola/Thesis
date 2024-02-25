"""
This module defines the CmdParser class, which provides a command line interface for Argos.
It defines the available modes and their arguments, and parses the cmd line args into a dict.

Classes:
    - CmdParser: Object for parsing command line arguments into Python objects.
"""

import argparse
import sys

from colorama import Style

from . import utils


class Parser:
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

            if self.description:
                formatter.add_text(
                    Style.BRIGHT
                    + self.description
                    + (
                        (" - " + self.usage.split(" ")[1].strip().capitalize() + " mode")  # type: ignore # pylint: disable=line-too-long
                        if self.prog != "argos.py"
                        else ""
                    )
                    + Style.RESET_ALL
                )

            # usage
            formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

            # positionals, optionals and user-defined groups
            for action_group in self._action_groups[::-1]:
                formatter.start_section(
                    Style.BRIGHT + action_group.title + Style.RESET_ALL
                    if action_group.title is not None
                    else None
                )
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
            utils.print_error(message)
            print()

            if not self._subparsers:
                self.print_help()
            else:
                actions = self._subparsers._group_actions  # pylint: disable=protected-access
                keys = actions[0].choices.keys()  # type: ignore

                if len(sys.argv) > 1 and sys.argv[1] in keys:
                    self.parse_args([sys.argv[1], "-h"])
                else:
                    self.print_help()

            exit(2)

    class _HelpFormatter(argparse.HelpFormatter):
        def add_usage(self, usage, actions, groups, prefix=None):
            if prefix is None:
                prefix = Style.BRIGHT + "Usage:\n  " + Style.RESET_ALL
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

    class _HelpFormatterModes(_HelpFormatter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._max_help_position = 100

    def __init__(self):
        self._parser = self._ArgumentParser(
            description="Argos, Real-time Image Analysis for Fraud Detection",
            formatter_class=self._HelpFormatter,
            usage="1. argos.py <mode> [<args>]\n" + "  2. argos.py [-h | --help]",
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

    def _add_subparsers(self):
        self._add_acquire_mode_subparser()
        self._add_realtime_mode_subparser()
        self._add_train_mode_subparser()
        self._add_online_mode_subparser()

    # subparsers

    def _add_acquire_mode_subparser(self):
        parser = self._subparsers.add_parser(
            "acquire",
            aliases="a",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to capture and store video.",
            allow_abbrev=False,
            formatter_class=self._HelpFormatterModes,
            usage="1. argos.py acquire \n"
            + "  2. argos.py acquire [(-l | --logs) [<dest>]] \n"
            + "  3. argos.py acquire [-h | --help]",
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
            "-l",
            "--logs",
            nargs="?",
            const="",
            help="Access the logs of the acquire mode.",
            metavar="dest",
            dest="logs_dest",
        )

        subparsers = parser.add_subparsers(
            title="Mode",
            dest="sub_mode",
            required=True,
        )

        # create cmd subparser

        cmd = subparsers.add_parser(
            "cmd",
            aliases="c",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Define the arguments in the command line.",
            allow_abbrev=False,
            formatter_class=self._HelpFormatterModes,
            usage="argos.py acquire cmd (-o | --output) <path> [(-c | --camera) <sn>]\n"
            + "                       [-h | --help]",
            add_help=False,
        )

        cmd.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        cmd.add_argument(
            "-c",
            "--camera",
            nargs=1,
            help="Specify the camera to use by passing its serial number.",
            metavar="sn",
            dest="serial_numbers",
            type=_non_empty_string_type,
        )

        cmd_required = cmd.add_argument_group("Required arguments")

        cmd_required.add_argument(
            "-o",
            "--output-folder",
            required=True,
            help="Folder where sub folders for each camera will be created to store the images.",
            metavar="path",
            type=_non_empty_string_type,
        )

        # create yaml subparser

        yaml = subparsers.add_parser(
            "yaml",
            aliases="y",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Define the arguments in a yaml file.",
            allow_abbrev=False,
            formatter_class=self._HelpFormatterModes,
            usage="argos.py acquire yaml (-f | --file) <path> [-h | --help]",
            add_help=False,
        )

        yaml.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        yaml_required = yaml.add_argument_group("Required arguments")

        yaml_required.add_argument(
            "-f",
            "--file",
            required=True,
            help="Path to the yaml file containing the configuration.",
            metavar="path",
            type=_non_empty_string_type,
        )

    def _add_realtime_mode_subparser(self):
        parser = self._subparsers.add_parser(
            "realtime",
            aliases="r",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to stream the cameras in real-time.",
            allow_abbrev=False,
            formatter_class=self._HelpFormatterModes,
            usage="argos.py realtime [-h | --help]",
            add_help=False,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

    # TODO
    def _add_train_mode_subparser(self):
        parser = self._subparsers.add_parser(
            "train",
            aliases="t",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to train a model.",
            allow_abbrev=False,
            formatter_class=self._HelpFormatterModes,
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

    # TODO
    def _add_online_mode_subparser(self):
        parser = self._subparsers.add_parser(
            "online",
            aliases="o",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to run the model online.",
            allow_abbrev=False,
            formatter_class=self._HelpFormatterModes,
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

    # methods

    def get_args(self):
        """
        Parses the command line arguments and returns them as a dictionary.

        Returns:
            dict: The command line arguments as a dictionary.
        """
        return self._parser.parse_args()


# type checkers
def _non_empty_string_type(value: str):
    """
    Checks if value is not an empty string.
    """
    value = value.strip()
    if len(value) == 0:
        raise argparse.ArgumentTypeError("Empty string")
    return value
