# -*- coding: utf-8 -*-
"""
    nektar.exceptions
    ~~~~~~~~~

    Custom Nektar Exceptions

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""


class NektarException(Exception):
    """ """

    def __init__(self, message):
        super().__init__(message)
