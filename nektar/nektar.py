# -*- coding: utf-8 -*-
"""
    nektar.nektar
    ~~~~~~~~~

    Interact with Hive API in Python.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import re
import json
import time
import struct
from datetime import datetime, timezone
from binascii import hexlify, unhexlify

from .appbase import AppBase
from .constants import DATETIME_FORMAT

class Waggle:
    def __init__(self, username, wifs=None):
        self.set_username(username)
        
        self.appbase = AppBase()
        self.appbase.append_wif(wifs)

        self.account = None
        self.refresh()

    def set_username(self, username):
        if not isinstance(username, str):
            raise
        self.username = username.replace("@", "")

    def refresh(self):
        params = [[self.username]]
        self.account = self.appbase.api("condenser").get_accounts(params)

    def get_dynamic_global_properties(self, api="condenser"):
        ## use database_api
        return self.appbase.api(api).get_dynamic_global_properties({})

    def get_previous_block(self, head_block_number):
        block_number = head_block_number - 2
        blocks = self.appbase.api("block").get_block({"block_num": block_number})
        return blocks["block"]["previous"]

    def get_reference_block_data(self):
        ## beembase / ledgertransactions
        properties = self.get_dynamic_global_properties("database")
        ref_block_num = properties["head_block_number"] - 3 & 0xFFFF
        previous = self.get_previous_block(properties["head_block_number"])
        ref_block_prefix = struct.unpack_from("<I", unhexlify(previous), 4)[0]
        return ref_block_num, ref_block_prefix

    def vote(self, author, permlink, weight, expire=30, synchronous=True, truncated=True):

        pattern = r"[\w][\w\d]+[\.]{0,1}[\w\d]+"
        match = re.findall(pattern, author)
        if not len(match):
            raise
        
        pattern = r"[\w][\w\d\-\%]+"
        match = re.findall(pattern, permlink)
        if not len(match):
            raise
        
        weight = within_range(weight, 1, 10000)
        expire = within_range(expire, 5, 120)
        synchronous = true_or_false(synchronous, True)
        truncated = true_or_false(truncated, True)
        
        expiration = _make_expiration(expire)
        ref_block_num, ref_block_prefix = self.get_reference_block_data()

        operations = [[ "vote", { "voter": self.username, "author": author, "permlink": permlink, "weight": weight } ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous, truncated)
    
    def _broadcast(self, transaction, synchronous=True, truncated=True):
        method = "condenser_api.broadcast_transaction"
        if synchronous:
            method = "condenser_api.broadcast_transaction_synchronous"
            return self.appbase.broadcast(method, transaction, truncated)
        return self.appbase.broadcast(method, transaction, truncated)

def _make_expiration(secs=30):
    timestamp = time.time() + int(secs)
    return datetime.utcfromtimestamp(timestamp).strftime(DATETIME_FORMAT)

def within_range(value, minimum, maximum):
    if not isinstance(value, int):
        raise IntRangeException(f"Integer value must be within f{minimum} to f{maximum} only.")
    if not (1 <= value <= 10000):
        raise IntRangeException(f"Integer value must be within f{minimum} to f{maximum} only.")
    return value

def true_or_false(value, fallback):
    if isinstance(value, bool):
        return value
    return fallback