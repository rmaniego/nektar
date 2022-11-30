# -*- coding: utf-8 -*-
"""
    nektar.utils
    ~~~~~~~~~

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import re
import time
from datetime import datetime, timezone
from .constants import (
    ROLES,
    DATETIME_FORMAT
)

class NektarException(Exception):
    """ """

    def __init__(self, message):
        super().__init__(message)


def check_wifs(roles, operation):
    """Check if supplied WIF is in the required authority for the specific operation.

    Parameters
    ----------
    roles : list
        list of key authority
    operation : str
        operation name

    Returns
    -------
        Boolean value.
    """
    return bool(len([r for r in ROLES[operation] if r in roles]))

def make_expiration(seconds=30, formatting=None):
    """Return a UTC datetime formatted for the blockchain.

    Parameters
    ----------
    seconds : int
        seconds to add to the current timestamp (Default is 30)
    formatting : str, None
        format of the date-time string

    Returns
    -------
    str:
        Formatted date and time string.
    """
    timestamp = time.time() + int(seconds)
    if formatting is None:
        formatting = DATETIME_FORMAT
    valid_string(formatting)
    return datetime.utcfromtimestamp(timestamp).strftime(formatting)

def valid_string(value, pattern=None, fallback=None):
    """Check if the value is a valid string.

    Parameters
    ----------
    value : str
        value to be tested
    pattern : str
        regex pattern
    fallback : str, None
        value if failing

    Returns
    -------
    str:
        The value or the fallback.
    """
    if not isinstance(value, str):
        if fallback is None:
            raise NektarException("The value must be a string.")
        return fallback
    if pattern is None:
        return value
    if not bool(len(re.findall(pattern, value))):
        raise NektarException("The value is unsupported.")
    return value

def greater_than(value, minimum, fallback=None):
    """Check if input is greater than, otherwise return fallback.

    Parameters
    ----------
    value :
        value to be tested
    minimum :
        value to be tested against
    fallback :
        Default is None

    Returns
    -------
        The value or the fallback.

    """
    if not (isinstance(value, int) or rid > minimum):
        if fallback is None:
            raise NektarException(f"Value must be an integer greater than {minimum}.")
        return fallback
    return value


def within_range(value, minimum, maximum, fallback=None):
    """Check if input is within the range, otherwise return fallback.

    Parameters
    ----------
    value :
        value to be tested
    minimum :
        minimum value of the range
    maximum :
        maximum value of the range
    fallback : integer, None
        fallback value

    Returns
    -------

    """
    if not (isinstance(value, int) and (minimum <= int(value) <= maximum)):
        if fallback is None:
            raise NektarException(f"Value must be within {minimum} to {maximum} only.")
        return fallback
    return value

def is_boolean(value, fallback=None):
    """Check if input is boolean, otherwise return fallback.

    Parameters
    ----------
    value :
        value to be tested
    fallback : bool, None
        fallback value

    Returns
    -------
        The value or the fallback.

    """
    if not isinstance(value, bool):
        if fallback is None:
            raise NektarException("The value must be `True` or `False` only.")
        return fallback
    return value
