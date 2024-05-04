"""
This module contains the Logger class.
"""

import os
import logging


class Logger(logging.Logger):
    """
    Custom logger for Argos.
    """

    def __init__(
        self,
        name: str,
        file: str,
    ) -> None:
        super().__init__(name)

        os.makedirs(os.path.dirname(file), exist_ok=True)

        file_handler = logging.FileHandler(file)
        file_handler.setLevel(logging.NOTSET)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

        self.addHandler(file_handler)
