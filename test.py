"""
Module for testing
"""

import aquire
import utils

try:
    aq = aquire.AquireNamespace("./")

    print(aq)
except Exception as e:
    utils.print_error(str(e))
