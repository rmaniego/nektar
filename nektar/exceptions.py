# -*- coding: utf-8 -*-
"""
    nektar.exceptions
    ~~~~~~~~~

    Custom Nektar Exceptions

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

class RPCNodeException(Exception):
    def __init__(self, message, code=None, raw_body=None):
        super().__init__(message)
        self.code = code
        self.raw_body = raw_body

class NodeException(Exception):
    def __init__(self, message):
        super().__init__(message)

class APIException(Exception):
    def __init__(self, message):
        super().__init__(message)

class APIMethodException(Exception):
    def __init__(self, message):
        super().__init__(message)

class OperationException(Exception):
    def __init__(self, message):
        super().__init__(message)

class WIFException(Exception):
    def __init__(self, message):
        super().__init__(message)

class IntRangeException(Exception):
    def __init__(self, message):
        super().__init__(message)