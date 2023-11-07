"""
Module for testing
"""

import acquire
import utils

try:
    aq = acquire.AcquireNamespace("./")

    print(aq)
except Exception as e:
    utils.print_error(str(e))
