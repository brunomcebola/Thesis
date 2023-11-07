"""
This module defines the CmdParser class, which provides a command line interface for Argos.
It defines the available modes and their arguments, and parses the cmd line args into a dict.

Classes:
    - CmdParser: Object for parsing command line arguments into Python objects.
"""
import argparse
import sys

from colorama import Style
from utils import print_error
from intel import StreamType


# TODO: add option in parser to access thread output
class ArgParser:
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
                        (" - " + self.prog.strip().capitalize() + " mode")
                        if self.prog != "argos.py"
                        else ""
                    )
                    + Style.RESET_ALL
                )

            # usage
            formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

            # positionals, optionals and user-defined groups
            for action_group in self._action_groups[::-1]:
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
            print_error(message)
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
                prefix = Style.BRIGHT + "Usage\n  " + Style.RESET_ALL
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
            usage="argos.py <mode> [<args>]",
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

    def _add_acquire_mode_subparser(self):
        def _camera_type(value: str):
            """
            Checks if a non-empty string was assigned to the camera argument.
            """
            value = value.strip()
            if len(value) == 0:
                raise argparse.ArgumentTypeError("Empty string")
            return value

        def _stream_type_type(value: str):
            """
            Checks if the stream type is either a key or a value of the StreamType enum.
            """
            value = value.strip().upper()

            if value in [type.name for type in StreamType]:
                return StreamType[value]
            elif value.isdigit() and int(value) in [type.value for type in StreamType]:
                return StreamType(int(value))
            else:
                options = ", ".join([f"'{type.name}' ({type.value})" for type in StreamType])
                raise argparse.ArgumentTypeError(
                    f"invalid choice: '{value}' (choose from {options})"
                )

        def _output_folder_type(value: str):
            """
            Checks if a non-empty string was assigned to the output folder argument.
            """
            value = value.strip()
            if len(value) == 0:
                raise argparse.ArgumentTypeError("Empty string")
            return value

        parser = self._subparsers.add_parser(
            "acquire",
            aliases="a",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to capture and store video.",
            allow_abbrev=False,
            formatter_class=self._HelpFormatterModes,
            usage="argos.py acquire (-o | --output) <path> [(-c | --camera) <sn>]\n"
            + "                  [(-s | --stream-type) <stream>]",
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
            "--camera",
            nargs="?",
            help="Specify the camera to use by passing its serial number.",
            metavar="sn",
            dest="serial_numbers",
            type=_camera_type,
            action="append",
        )

        options = ", ".join([f"{type.name}" for type in StreamType])
        parser.add_argument(
            "-s",
            "--stream-type",
            nargs="?",
            help=f"Specify the stream type to use ({options}).",
            dest="stream_types",
            metavar="stream",
            type=_stream_type_type,
            action="append",
        )

        parser_required = parser.add_argument_group("Required arguments")

        parser_required.add_argument(
            "-o",
            "--output-folder",
            required=True,
            help="Folder where sub folders for each camera will be created to store the images.",
            metavar="path",
            type=_output_folder_type,
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

    # TODO
    def _add_yaml_mode_subparser(self):
        def _config_file(value: str):
            """
            Checks if a non-empty string was assigned to the output folder argument.
            """
            value = value.strip()
            if len(value) == 0:
                raise argparse.ArgumentTypeError("Empty string")
            return value

        parser = self._subparsers.add_parser(
            "yaml",
            aliases="y",
            description="Argos, Real-time Image Analysis for Fraud Detection",
            help="Mode to run the model based on a yaml file.",
            allow_abbrev=False,
            formatter_class=self._HelpFormatterModes,
            usage="argos.py yaml (-f | --config-file) <path>",
            add_help=False,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        parser_required = parser.add_argument_group("Required arguments")

        parser_required.add_argument(
            "-f",
            "--config-file",
            required=True,
            help="Path to the yaml file containing the camera's configuration.",
            metavar="path",
            type=_config_file,
        )

    def _add_subparsers(self):
        self._add_acquire_mode_subparser()
        self._add_train_mode_subparser()
        self._add_online_mode_subparser()
        self._add_yaml_mode_subparser()

    def get_args(self):
        """
        Parses the command line arguments and returns them as a dictionary.

        Returns:
            dict: The command line arguments as a dictionary.
        """
        return self._parser.parse_args()
