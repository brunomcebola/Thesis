"""
This module holds the tools to stream in realtime from the cameras.

Classes:
--------
- AcquireNamespace: Holds the arguments for the acquire mode.
- Acquire: Holds the tools to acquire data from the realsense cameras.

Exceptions:
-----------
- AcquireNamespaceError: Exception raised when errors related to the acquire namespace occur.
- AcquireError: Exception raised when errors related to the acquire mode occur.

"""

# pylint: disable=pointless-string-statement
from __future__ import annotations

from .. import intel
from .. import utils

# Exceptions
"""
███████╗██╗  ██╗ ██████╗███████╗██████╗ ████████╗██╗ ██████╗ ███╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║██╔════╝
█████╗   ╚███╔╝ ██║     █████╗  ██████╔╝   ██║   ██║██║   ██║██╔██╗ ██║███████╗
██╔══╝   ██╔██╗ ██║     ██╔══╝  ██╔═══╝    ██║   ██║██║   ██║██║╚██╗██║╚════██║
███████╗██╔╝ ██╗╚██████╗███████╗██║        ██║   ██║╚██████╔╝██║ ╚████║███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝        ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
"""


class RealtimeNamespaceError(utils.ModeNamespaceError):
    """
    Exception raised when errors related to the acquire namespace occur.
    """


# Main content
"""
███╗   ███╗ █████╗ ██╗███╗   ██╗     ██████╗ ██████╗ ███╗   ██╗████████╗███████╗███╗   ██╗████████╗
████╗ ████║██╔══██╗██║████╗  ██║    ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║╚══██╔══╝
██╔████╔██║███████║██║██╔██╗ ██║    ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║   ██║
██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║   ██║
██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗██║ ╚████║   ██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝   ╚═╝
"""


class RealtimeNamespace(utils.ModeNamespace):
    """
    This class holds the arguments for the realtime mode.

    Attributes:
    -----------
        - cameras (list[intel.RealSenseCamera]):
            The list with the cameras to be used.
    """

    @classmethod
    def from_yaml(cls, file: str) -> RealtimeNamespace:
        return cls.from_yaml(file)

    @classmethod
    def _get_specific_yaml_schema(cls) -> dict:
        return {}


class Realtime(utils.Mode):
    """
    This class holds the tools to stream data from the realsense cameras.

    Methods:
    --------
        - run: Runs the realtime mode (in a blocking way).

    """

    # type hints

    __args: RealtimeNamespace

    def __init__(self, args: RealtimeNamespace) -> None:
        """
        Acquire constructor.

        Args:
        -----
            - args: The arguments for the acquire mode (matching the constructor of
                    AcquireNamespace).

        """

        self.__args = args

    def run(self) -> None:
        """
        Runs the realtime mode (in a blocking way).
        """

        print(self.__args)
