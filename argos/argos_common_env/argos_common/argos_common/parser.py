"""
This module contains the Parser class.
"""

from __future__ import annotations

import argparse
import sys

from typing import Any

from colorama import Style, Fore


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
        print(f"{Fore.RED + Style.BRIGHT}Error:{Style.RESET_ALL} {message}\n")

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_help_position = 100

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


class _ParserTree:
    """
    The ParserTree class represents the parser tree.
    """

    class Node:
        """
        The Node class represents a node in the parser tree.
        """

        name: str
        parser: _ArgumentParser
        subparsers_wrapper: argparse._SubParsersAction | None
        child_nodes: list[_ParserTree.Node]

        def __init__(
            self,
            name: str,
            parser: _ArgumentParser,
        ):
            self.name = name
            self.parser = parser
            self.subparsers_wrapper = None
            self.child_nodes: list[_ParserTree.Node] = []

    def __init__(self, root: _ParserTree.Node):
        self.root = root
        self.node_names: list[str] = ["root"]

    def get_node(
        self,
        name: str,
        curr_node: _ParserTree.Node | None = None,
    ) -> _ParserTree.Node | None:
        """
        Gets a node by its name.

        Args:
            name (str): The name of the node.
            curr_node (_ParserTree.Node): The current node to start the search from. If None, starts from the root. # pylint: disable=line-too-long

        Returns:
            _ParserTree.Node | None: The node if it exists, otherwise None.
        """

        if name not in self.node_names:
            return None

        if curr_node is None:
            curr_node = self.root

        if curr_node.name == name:
            return curr_node

        for child_node in curr_node.child_nodes:
            result = self.get_node(name, child_node)

            if result is not None:
                return result

        return None

    def add_node(self, new_node: _ParserTree.Node, parent_node: _ParserTree.Node):
        """
        Adds a new node to the parser tree.

        Args:
            new_node (_ParserTree.Node): The new node to add.
            parent_node (_ParserTree.Node): The parent node of the new node.
        """

        if new_node.name in self.node_names:
            raise ValueError(f"A parser named '{new_node.name}' already exists.")

        parent_node.child_nodes.append(new_node)
        self.node_names.append(new_node.name)


class Parser:
    """
    The Parser class is responsible for parsing the command line arguments.
    """

    def __init__(self):

        parser = _ArgumentParser(
            formatter_class=_HelpFormatter,
            add_help=False,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        self._parser_tree = _ParserTree(_ParserTree.Node("root", parser))

    def add_parser(  # pylint: disable=dangerous-default-value
        self,
        nest_under: str,
        name: str,
        configs: dict[str, Any] = {},
    ) -> None:
        """
        Adds a new parser to the Parser.

        Initially, only the "root" parser exists.

        Args:
            nest_under (str): The name of the parser to nest the new parser under.
            name (str): The name of the new parser.
            dest (str): The group to which the new parser belongs.
        """

        # gets the parser where the new parser will be nested under
        nest_under_parser_node = self._parser_tree.get_node(nest_under)
        # if the parser does not exist, raises an error
        if nest_under_parser_node is None:
            raise ValueError(f"The parser '{nest_under}' to nest under does not exist.")

        dest = nest_under + "_command"

        # if the parser to nest under does not have a subparsers_wrapper, creates one
        if nest_under_parser_node.subparsers_wrapper is None:
            nest_under_parser_node.subparsers_wrapper = (
                nest_under_parser_node.parser.add_subparsers(
                    title=nest_under.capitalize() + " Commands",
                    dest=dest,
                    required=True,
                )
            )
        # if the parser to nest under has a subparsers_wrapper, checks if the group is the same
        elif nest_under_parser_node.subparsers_wrapper.dest != dest:
            raise ValueError(
                f"The parser '{nest_under}' to nest under already has a group '{nest_under_parser_node.subparsers_wrapper.dest}'."  # pylint: disable=line-too-long
            )

        # creates the new parser

        parser = nest_under_parser_node.subparsers_wrapper.add_parser(
            allow_abbrev=False,
            formatter_class=_HelpFormatter,
            add_help=False,
            name=name,
            **configs,
        )

        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )

        # add parser to tree
        self._parser_tree.add_node(_ParserTree.Node(name, parser), nest_under_parser_node)

    def add_arguments_to_parser(self, name: str, parser_args: list[tuple[list, dict]]) -> None:
        """
        Adds arguments to a parser in the Parser.

        Args:
            name (str): The name of the parser to add the arguments to.
            parser_args (list[tuple[list, dict]]): The arguments to add to the parser.
        """

        # get the parser node
        parser_node = self._parser_tree.get_node(name)
        # if the parser does not exist, raises an error
        if parser_node is None:
            raise ValueError(f"The parser '{name}' does not exist.")

        for args in parser_args:
            parser_node.parser.add_argument(*args[0], **args[1])

    # methods

    def get_args(self):
        """
        Parses the command line arguments and returns them as a dictionary.

        Returns:
            dict: The command line arguments as a dictionary.
        """

        return self._parser_tree.root.parser.parse_args()

    # type checkers
    @classmethod
    def non_empty_string_type(cls, value: str):
        """
        Checks if value is not an empty string.
        """
        value = value.strip()
        if len(value) == 0:
            raise argparse.ArgumentTypeError("Empty string")
        return value
