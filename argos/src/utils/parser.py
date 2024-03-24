"""
This module defines the Parser class, which provides a command line interface for Argos.
"""

from __future__ import annotations

import argparse
import sys

from colorama import Style

from . import utils

__all__ = ["Parser"]


class _ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._optionals.title = "Optional arguments"
        self._positionals.title = "Positional arguments"

    def format_help(self):
        formatter = self._get_formatter()

        if self.description:
            formatter.add_text(Style.BRIGHT + self.description + Style.RESET_ALL)

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

            formatter.add_arguments(action_group._group_actions)  # pylint: disable=protected-access

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


class Parser:
    """
    A class for parsing command line arguments into Python objects.
    """

    # class _HelpFormatterModes(_HelpFormatter):
    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)
    #         self._max_help_position = 100

    def __init__(self):
        self._parser = _ArgumentParser(
            description="Argos, Real-time Image Analysis for Fraud Detection",
            formatter_class=_HelpFormatter,
            usage="1. argos.py <resource> [<args>]\n" + "  2. argos.py (-h | --help)",
            add_help=False,
        )

        self._parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        resources_subparsers = self._parser.add_subparsers(
            title="Resources",
            dest="resource",
            required=True,
        )

        # client

        interface_parser = self._add_middle_subparser(
            resources_subparsers,
            {
                "description": "Interface launcher",
                "name": "interface",
                "help": "Mode to start the Argos Interface.",
            },
        )

        # services

        services_parser = self._add_middle_subparser(
            resources_subparsers,
            {
                "description": "Services launcher",
                "name": "service",
                "help": "Mode to launch an Argos service.",
            },
            "service",
        )

        services_subparsers = services_parser.add_subparsers(
            title="Services",
            dest="service",
            required=True,
        )

        self._add_final_subparser(
            services_subparsers,
            {
                "name": "acquire",
                "help": "Mode to capture and store video.",
            },
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

        self._add_final_subparser(
            services_subparsers,
            {
                "name": "preprocess",
                "help": "Mode to preprocess the acquired data.",
            },
            [
                (
                    ["-o", "--origin-folder"],
                    {
                        "help": "Folder where the images to be preprocessed are stored.",
                        "metavar": "path",
                        "type": _non_empty_string_type,
                    },
                ),
                (
                    ["-d", "--destination-folder"],
                    {
                        "help": "Folder where the generated datasets will be stored.",
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

    def _add_middle_subparser(
        self,
        subparser_dest: argparse._SubParsersAction,
        configs: dict,
        child_subparsers_name: str | None = None,
    ) -> _ArgumentParser:
        configs["description"] = (
            f"Argos, Real-time Image Analysis for Fraud Detection {'- ' + str(configs['description']) if 'description' in list(configs.keys()) else ''}"  # pylint: disable=line-too-long
        )

        count = 1
        usage = ""
        if child_subparsers_name is not None:
            usage += f"{count}. argos.py {configs['name']} <{child_subparsers_name}> [<args>]\n  "
            count += 1
        usage += f"{count}. argos.py {configs['name']} (-h | --help)"

        parser: _ArgumentParser = subparser_dest.add_parser(
            allow_abbrev=False,
            formatter_class=_HelpFormatter,
            add_help=False,
            **configs,
            usage=usage,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        return parser

    def _add_final_subparser(
        self,
        subparser_dest: argparse._SubParsersAction,
        subparser_configs: dict,
        subparser_args: list[tuple[list, dict]],
    ):
        description = f"Argos, Real-time Image Analysis for Fraud Detection - {subparser_configs['name'].capitalize()} mode"  # pylint: disable=line-too-long

        usage = f"1. argos.py {subparser_configs['name']} <command> [<args>]"
        usage += f"\n  2. argos.py {subparser_configs['name']} (-h | --help)"

        parser: _ArgumentParser = subparser_dest.add_parser(
            description=description,
            allow_abbrev=False,
            formatter_class=_HelpFormatter,
            add_help=False,
            **subparser_configs,
            usage=usage,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        subparsers = parser.add_subparsers(
            title="Commands",
            dest="command",
            required=True,
        )

        # run command

        usage = []

        run_args = []
        for args in subparser_args:
            required = "required" in args[1].keys() and args[1]["required"]
            run_args.append(
                (
                    (
                        ("[" if not required else "")
                        + ("(" if len(args[0]) > 1 else "")
                        + " | ".join(args[0])
                        + (")" if len(args[0]) > 1 else "")
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

        usage = f"1. argos.py {subparser_configs['name']} run {run_args}"
        usage += f"\n  2. argos.py {subparser_configs['name']} run (-h | --help)"

        run_cmd = subparsers.add_parser(
            name="run",
            description=description + " (run)",
            formatter_class=_HelpFormatter,
            add_help=False,
            usage=usage,
            help=f"Run the {subparser_configs['name'] if 'name' in subparser_configs.keys() else ''} mode.",  # pylint: disable=line-too-long
        )

        for args in subparser_args:
            run_cmd.add_argument(*args[0], **args[1])

        run_cmd.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        # logs command

        usage = f"1. argos.py {subparser_configs['name']} logs [(-d | --dest) <path>]"
        usage += f"\n  2. argos.py {subparser_configs['name']} logs (-h | --help)"

        logs_cmd = subparsers.add_parser(
            name="logs",
            description=description + " (logs)",
            allow_abbrev=False,
            formatter_class=_HelpFormatter,
            add_help=False,
            usage=usage,
            help=f"Access the logs of the {subparser_configs['name'] if 'name' in subparser_configs.keys() else ''} mode.",  # pylint: disable=line-too-long
        )

        logs_cmd.add_argument(
            "-d",
            "--dest",
            help="Specify where to exports the logs to. If not specified the logs will be printed to the console.",  # pylint: disable=line-too-long
            metavar="path",
            dest="logs_dest",
            type=_non_empty_string_type,
        )

        logs_cmd.add_argument(
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
