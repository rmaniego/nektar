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
from .exceptions import NektarException

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
        self.account = self.appbase.api("condenser").get_accounts([[self.username]])

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

    def communities(self, last=None, limit=100, sorting="rank", query=None):
        """
            List all communities.
            
            :last: last known community name `hive-*`, paging mechanism (optional)
            :limit: maximum limit of communities to list.
            :sorting: sort by `rank`, `new`, or `subs`
            :query: additional filter keywords for search
        """

        params = {}
        params["observer"] = self.username
        params["sort"] = "rank"
        if sorting in ("new", "sub"):
            params["sort"] = sorting
        if isinstance(last, str):
            params["query"] = query
        
        # custom limits by nektar, hive api limit: 100
        custom_limit = within_range(limit, 1, 10000, 100)
        crawls = custom_limit // 100
        params["limit"] = custom_limit
        if crawls > 0:
            params["limit"] = 100

        if isinstance(last, str):
            match = re.findall(r"\bhive-[\d]{1,6}\b", last)
            if len(match):
                params["last"] = last

        results = []
        for _ in range(crawls):
            result = self.appbase.api("bridge").list_communities(params)
            if len(result) < 100:
                break
            results.extend(result)
            if len(results) >= custom_limit:
                break
            params["last"] = results[-1]["name"]
        return results[:custom_limit]

    def subscribers(self, community, last=None, limit=100):
        """
            Gets a list of subscribers for a given community.
            
            :community: community name `hive-*`
            :last: last known subscriber username, paging mechanism (optional)
            :limit: maximum limit of subscribers to list.
        """

        params = {}

        params["community"] = community
        if isinstance(community, str):
            match = re.findall(r"\bhive-[\d]{1,6}\b", community)
            if not len(match):
                raise NektarException(f"Community name '{community}' format is unsupported.")
        
        # custom limits by nektar, hive api limit: 100
        custom_limit = within_range(limit, 1, 10000, 100)
        crawls = custom_limit // 100
        params["limit"] = custom_limit
        if crawls > 0:
            params["limit"] = 100

        if isinstance(last, str):
            match = re.findall(r"\bhive-[\d]{1,6}\b", last)
            if len(match):
                params["last"] = last

        results = []
        for _ in range(crawls):
            result = self.appbase.api("bridge").list_subscribers(params)
            if len(result) < 100:
                break
            results.extend(result)
            if len(results) >= custom_limit:
                break
            params["last"] = results[-1][0]
        return results[:custom_limit]

    def accounts(self, start=None, limit=100):
        """
            Looks up accounts starting with name.
            
            :start: starting part of username to search
            :limit: maximum limit of accounts to list.
        """

        params = ["", 1]
        
        # custom limits by nektar, hive api limit: 1000
        custom_limit = within_range(limit, 1, 10000, 100)
        crawls = custom_limit // 100
        params[1] = custom_limit
        if crawls > 0:
            params[1] = 1000

        params[0] = start
        if not isinstance(start, str):
            params[0] = ""
            start = ""

        results = []
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        for letter in alphabet:
            if not len(start):
                params[0] = letter
            for _ in range(crawls):
                result = self.appbase.api("condenser").lookup_accounts(params)
                if len(result) < 1000:
                    break
                results.extend(result)
                if len(results) >= custom_limit:
                    results[:custom_limit]
            if not len(start):
                break
        return results[:custom_limit]

    def vote(self, author, permlink, weight, expire=30, synchronous=False, truncated=True, strict=True):
        """
            Looks up accounts starting with name.
            
            :start: starting part of username to search
            :limit: maximum limit of accounts to list.
        """
        if not isinstance(author, str):
            raise NektarException("author must be a string.")

        pattern = r"[\w][\w\d\.\-]{2,15}"
        match = re.findall(pattern, author)
        if not len(match):
            raise raise NektarException("author must be a string of length 3 - 16.")
            
        pattern = r"[\w][\w\d\-\%]{0,255}"
        match = re.findall(pattern, permlink)
        if not len(match):
            raise raise NektarException("permlink must be a valid url-escaped string.")
        
        weight = within_range(weight, -10000, 10000)
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
        return self._broadcast(transaction, synchronous, truncated, strict)
    
    def _broadcast(self, transaction, synchronous=True, truncated=True, strict=True):
        method = "condenser_api.broadcast_transaction"
        if synchronous:
            method = "condenser_api.broadcast_transaction_synchronous"
            result = self.appbase.broadcast(method, transaction, truncated, strict)
            if result:
                return result
        return self.appbase.broadcast(method, transaction, truncated, strict)

##############################
# utils                      #
##############################

def _make_expiration(secs=30):
    timestamp = time.time() + int(secs)
    return datetime.utcfromtimestamp(timestamp).strftime(DATETIME_FORMAT)

def within_range(value, minimum, maximum, fallback=None):
    if not isinstance(value, int) and not isinstance(fallback, (None, int)):
        raise NektarException(f"Input values must be integers.")
    if not (1 <= value <= 10000):
        if fallback is None:
            raise NektarException(f"Integer value must be within {minimum} to {maximum} only.")
        return fallback
    return value

def true_or_false(value, fallback):
    if isinstance(value, bool):
        return value
    return fallback