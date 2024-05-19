"""
This module contains the YAMLParser class.
"""

from __future__ import annotations

from typing import Type, TypeVar

import inspect
import yaml

T = TypeVar("T")


class YAMLParser:
    """
    This class is responsible for parsing YAML files and creating instances of the target class.

    Attributes
    - cls: The target class to create instances of.

    Methods
    - parse(file_path): Parses a YAML file and creates an instance of the target class.
    """

    def __init__(self, cls: Type) -> None:
        """
        Initializes the YAMLParser object.

        Parameters
        - cls: The target class to create instances of.
        """

        self.cls = cls

    def parse(self, file_path) -> T:  # type: ignore
        """
        Parses a YAML file and creates an instance of the target class.

        Parameters
        - file_path: The path to the YAML file.

        Returns
        - An instance of the target class.

        Raises
        - FileNotFoundError: If the YAML file is not found.
        - PermissionError: If the YAML file cannot be read.
        - UnicodeDecodeError: If the YAML file has the wrong encoding.
        - SyntaxError: If the YAML file has the wrong syntax.
        - ValueError: If the YAML file is missing required parameters or has unexpected parameters.
        - RuntimeError: If the YAML file has an unknown problem.

        Notes:
        - Since this method is used to create instances of a target class, it can also raise any
          exceptions that the target class constructor raises.
        """

        # Load the YAML file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"YAML file not found ({file_path}).") from e
        except PermissionError as e:
            raise PermissionError(f"YAML file permission denied ({file_path}).") from e
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(
                e.encoding, e.object, e.start, e.end, f"YAML file wrong encoding ({file_path})."
            ) from e
        except yaml.YAMLError as e:
            if hasattr(e, "problem_mark"):
                line = e.problem_mark.line + 1  # type: ignore
                raise SyntaxError(f"YAML file wrong syntax on line {line}.") from e
            else:
                raise RuntimeError("YAML file unknown problem.") from e

        # Get lists of mandatory and optional parameters of cls constructor
        signature = inspect.signature(self.cls.__init__)

        mandatory_params = [
            param.name
            for param in signature.parameters.values()
            if param.default == inspect.Parameter.empty and param.name != "self"
        ]
        optional_params = [
            param.name
            for param in signature.parameters.values()
            if param.default != inspect.Parameter.empty and param.name != "self"
        ]

        # Check if all required parameters are in the YAML data
        for param in mandatory_params:
            if param not in data:
                raise ValueError(f"YAML file missing required parameter ({param}).")

        # Check if there are any unexpected parameters in the YAML data
        expected_params = mandatory_params + optional_params
        for param in data:
            if param not in expected_params:
                raise ValueError(f"YAML file unexpected parameter ({param}).")

        # Create an instance of the target class with the parsed data
        return self.cls(**data)
