"""
Module for testing
"""

class Test(Exception):
    """Base class for exceptions in this module."""


try:
    raise Test("This is a test exception.", "ola")
except Test as e:
    print(e)