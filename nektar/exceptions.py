# -*- coding: utf-8 -*-
"""
    nektar.exceptions
    ~~~~~~~~~

    Custom Nektar Exceptions

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

class RPCNektarException(Exception):
    def __init__(self, message, code=None, raw_body=None):
        super().__init__(message)
        self.code = code
        self.raw_body = raw_body

class NektarException(Exception):
    def __init__(self, message):
        super().__init__(message)