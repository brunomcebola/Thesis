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
                        (" - " + self.prog.split(" ")[1].strip().capitalize() + " mode")  # type: ignore # pylint: disable=line-too-long
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
            usage="1. argos.py <mode> [<args>]\n" + "  2. argos.py (-h | --help)",
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

        # acquire mode
        self._add_subparser(
            {"name": "acquire", "aliases": "a", "help": "Mode to capture and store video."},
            [
                (
                    ["-c", "--camera"],
                    {
                        "nargs": 1,
                        "help": "Specify the camera to be used by serial number.",
                        "metavar": "sn",
                        "dest": "serial_numbers",
                        "type": _non_empty_string_type,
                    },
                ),
                (
                    ["-o", "--output-folder"],
                    {
                        "help": "Folder where the acquired images will be stored.",
                        "metavar": "path",
                        "type": _non_empty_string_type,
                    },
                ),
                (
                    ["-y", "--yaml"],
                    {
                        "help": "Path to the yaml configuration file.",
                        "metavar": "path",
                        "type": _non_empty_string_type,
                    },
                ),
            ],
        )

        # self._add_subparser(
        #     {
        #         "name": "preprocess",
        #         "aliases": "p",
        #         "help": "Mode to preprocess the acquired data.",
        #     },
        #     [],
        # )

        # self._add_subparser(
        #     {
        #         "name": "train",
        #         "aliases": "t",
        #         "help": "Mode to train a model.",
        #     },
        #     [],
        # )

        self._add_subparser(
            {
                "name": "online",
                "aliases": "o",
                "help": "Mode to run the model in real-time.",
            },
            [],
        )

    # subparsers

    def _add_subparser(self, subparser_configs: dict, subparser_args: list[tuple[list, dict]]):
        usage = []

        run_args = []
        for args in subparser_args:
            required = "required" in args[1].keys() and args[1]["required"]
            run_args.append(
                (
                    (
                        ("[" if not required else "")
                        + ("(" if not required and len(args[0]) > 1 else "")
                        + " | ".join(args[0])
                        + (")" if not required and len(args[0]) > 1 else "")
                        + " <"
                        + args[1]["metavar"]
                        + ">"
                        + ("]" if not required else "")
                    ),
                    args[1]["required"] if "required" in args[1].keys() else False,
                )
            )  # pylint: disable=line-too-long
        # sort run_args so that the required arguments are shown first
        run_args.sort(key=lambda x: x[1], reverse=True)
        run_args = " ".join([arg[0] for arg in run_args])

        usage.append(
            f"{str(len(usage) + 1)}. argos.py {subparser_configs['name']} (-r | --run) {run_args}"
        )

        usage.append(
            f"{str(len(usage) + 1)}. argos.py {subparser_configs['name']} (-l | --logs) [(-d | --dest) <path>]"  # pylint: disable=line-too-long
        )

        usage.append(f"{str(len(usage) + 1)}. argos.py {subparser_configs['name']} (-h | --help)")

        usage = "\n  ".join(usage)

        parser = self._subparsers.add_parser(
            description="Argos, Real-time Image Analysis for Fraud Detection",
            allow_abbrev=False,
            formatter_class=self._HelpFormatterModes,
            add_help=False,
            **subparser_configs,
            usage=usage,
        )

        help_cmd = parser.add_argument_group("Help mode arguments")

        help_cmd.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        logs_cmd = parser.add_argument_group("Logs mode arguments")

        logs_cmd.add_argument(
            "-l",
            "--logs",
            action="store_true",
            help=f"Access the logs of the {subparser_configs['name'] if 'name' in subparser_configs.keys() else ''} mode.",  # pylint: disable=line-too-long
        )

        logs_cmd.add_argument(
            "-d",
            "--dest",
            help="Specify where to exports the logs to. If not specified the logs will be printed to the console.",  # pylint: disable=line-too-long
            metavar="path",
            dest="logs_dest",
        )

        run_cmd = parser.add_argument_group("Run mode arguments")

        run_cmd.add_argument(
            "-r",
            "--run",
            action="store_true",
            help=f"Run the {subparser_configs['name'] if 'name' in subparser_configs.keys() else ''} mode.",  # pylint: disable=line-too-long
        )

        for args in subparser_args:
            run_cmd.add_argument(*args[0], **args[1])

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
