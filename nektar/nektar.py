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
from .constants import NEKTAR_VERSION, ASSETS, ROLES, DATETIME_FORMAT
from .exceptions import NektarException

class Waggle:
    def __init__(self, username, wif=None, role=None, wifs=None, app=None, version=None):
        self.set_username(username)
        
        self.appbase = AppBase()
        
        if isinstance(role, str) and isinstance(wif, str):
            self.appbase.append_wif(role, wif)
        if isinstance(wifs, dict):
            self.appbase.append_wif(wifs)
        self.roles = list(self.appbase.wifs.keys())

        self.account = None
        self.refresh()
        
        self.app = "nektar"
        if isinstance(app, str):
            self.app = app
        
        self.version = NEKTAR_VERSION
        if isinstance(version, str):
            self.version = version

    def set_username(self, username):
        if not isinstance(username, str):
            raise NektarException("Username must be a valid Hive account username.")
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

    def communities(self, last=None, sort="rank", limit=100, query=None):
        """
            List all communities.
            
            :last: last known community name `hive-*`, paging mechanism (optional)
            :limit: maximum limit of communities to list.
            :sort: sort by `rank`, `new`, or `subs`
            :query: additional filter keywords for search
        """

        params = {}
        params["observer"] = self.username
        params["sort"] = "rank"
        if sort in ("new", "subs"):
            params["sort"] = sort
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
            results.extend(result)
            if len(result) < 100:
                break
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
            results.extend(result)
            if len(result) < 100:
                break
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
                results.extend(result)
                if len(result) < 1000:
                    break
                if len(results) >= custom_limit:
                    return results[:custom_limit]
            if not len(start):
                break
        return results[:custom_limit]

    def followers(self, account=None, start=None, ignore=False, limit=1000):
        """
            Looks up accounts starting with name.
            
            :account: get followers of an account, default = username (optional)
            :start: account to start from, paging mechanism (optional)
            :ignore: show all muted accounts if True, default = False (optional)
            :limit: maximum limit of accounts to list. (optional)
        """

        params = ["", "", "", 1000]

        params[0] = self.username
        if isinstance(start, str):
            params[0] = account

        params[1] = ""
        if isinstance(start, str):
            params[1] = start

        params[2] = "blog"
        if not isinstance(ignore, bool):
            if ignore:
                params[2] = "ignore"
        
        # custom limits by nektar, hive api limit: 1000
        custom_limit = within_range(limit, 1, 10000, 100)
        crawls = custom_limit // 100
        params[3] = custom_limit
        if crawls > 0:
            params[3] = 1000

        results = []
        for _ in range(crawls):
            result = self.appbase.api("condenser").get_followers(params)
            for item in result:
                results.append(item["follower"])
            if len(result) < 1000:
                break
            if len(results) >= custom_limit:
                break
            params[1] = results[-1]["follower"]
        return results[:custom_limit]

    def posts(self, community=None, sort="created", paidout=None, limit=100):
        """
            Get ranked posts based on tag.
            
            :tag: community name `hive-*` (optional)
            :sort: sort by `created`, `trending`, `hot`, `promoted`, `payout`, `payout_comments`, or `muted`
            :paidout: return new (False), paidout (True), all (None)
            :limit: maximum limit of blogs
        """

        params = {}
        params["tag"] = ""
        if isinstance(community, str):
            match = re.findall(r"\bhive-[\d]{1,6}\b", community)
            if len(match):
                params["tag"] = community
        params["sort"] = "created"
        if sort in ("trending", "hot", "promoted", "payout", "payout_comments", "muted"):
            params["sort"] = sort
        params["observer"] = self.username

        # custom limits by nektar, hive api limit: 100?
        limit = within_range(limit, 1, 1000, 100)
        params["limit"] = limit

        results = []
        filter = [True, False]
        if isinstance(paidout, bool):
            filter = [paidout]
        result = self.appbase.api("bridge").get_ranked_posts(params)
        for post in result:
            if not post["depth"] and post["is_paidout"] in filter:
                results.append(post)
        return results

    def blogs(self, account=None, sort="posts", paidout=None, limit=20):
        """
            Lists posts related to a given account.
            
            :acount: any valid account, default = set username (optional)
            :sort: sort by `blog`, `feed`, `post`, `replies`, or `payout`
            :limit: maximum limit of posts
        """

        params = {}
        params["account"] = self.username
        if isinstance(account, str):
            params["account"] = account
        params["sort"] = "posts"
        if sort in ("blog", "feed", "replies", "payout"):
            params["sort"] = sort
        params["observer"] = self.username

        # custom limits by nektar, hive api limit: 100?
        limit = within_range(limit, 1, 100, 100)
        params["limit"] = limit

        results = []
        filter = [True, False]
        if isinstance(paidout, bool):
            filter = [paidout]
        result = self.appbase.api("bridge").get_account_posts(params)
        for post in result:
            if not post["depth"] and post["is_paidout"] in filter:
                results.append(post)
        return results

    def new_post(self, title, body, description=None, tags=None, community=None, expire=30, synchronous=False):
        """
            Create a new post.
            
            :title: a human readable title of the post being submitted
            :body: body of the post being submitted
            :description: the very short summary of the post
            :tags: a space separated list of tags
            :community: the community to post e.g. `hive-*` (optional)
            :format: usually `markdown`
        """
        
        if not _check_wifs(self.roles, "comment"):
            raise NektarException("The `comment` operation requires" \
                                    "one of the following private keys:" + ", ".join(ROLES["comment"]))
    
        data = {}
        data["author"] = self.username
        
        if not isinstance(title, str):
            raise NektarException("Title must be a UTF-8 string.")
        title = re.sub(r"[\r\n]", "", title)
        if not (1 <= len(title.encode("utf-8")) <= 256):
            raise NektarException("Title must be within 1 to 256 bytes.")
        data["title"] = title
        
        if not isinstance(body, str):
            raise NektarException("Body must be a UTF-8 string.")
        if not len(body.encode("utf-8")):
            raise NektarException("Body must be at least 1 byte.")
        # body = body.replace("\r\n", "\\\n")
        # body = body.replace("\n", "\\\n")
        # body = body.replace("\"", "\\\"")
        data["body"] = body
        
        permlink = re.sub(r"[^\w\ ]", "", title.lower())
        permlink = permlink.replace(" ", "-")
        data["permlink"] = permlink
        data["parent_author"] = ""

        ## set parent permlink as empty, or the community being posted to
        data["parent_permlink"] = ""
        if isinstance(community, str):
            if not len(re.findall(r"hive-[\d]{1,}", community)):
                raise NektarException("Community name must follow `hive-*` format.")
            data["parent_permlink"] = community
        
        ## create blog metadata
        json_metadata = {}
        json_metadata["description"] = ""
        if isinstance(description, str):
            description = re.sub(r"[\r\n]", "", description)
            json_metadata["description"] = description
        ## make sure tags are valid
        ## accept more than 5, but only looks for the first five
        json_metadata["tags"] = []
        if isinstance(tags, str):
            json_metadata["tags"] = list(re.sub(r"[^\w\ ]", "", tags).split(" "))
        json_metadata["format"] = "markdown"
        json_metadata["app"] = self.app + "/" + self.version
        pattern_images = r"[!]\[[\w\ \-._~!$&'()*+,;=:@#\/?]*\]\([\w\-._~!$&'()*+,;=:@#\/?]+\)"
        json_metadata["image"] = list(re.findall(pattern_images, body))
        data["json_metadata"] = json.dumps(json_metadata).replace("'", "\\\"")
        
        ## initialize transaction data
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expiration = _make_expiration(expire)
        expire = within_range(expire, 5, 120, 30)
        synchronous = true_or_false(synchronous, False)

        operations = [[ "comment", data ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous)

    def reply(self, author, permlink, body, expire=30, synchronous=False):
        """
            Create a new comment to a post.
            
            :author: username of author of the blog post being replied to
            :permlink: permlink to the blog post being replied to
            :body: body of the comment being submitted
        """
        
        if not _check_wifs(self.roles, "comment"):
            raise NektarException("The `comment` operation requires" \
                                    "one of the following private keys:" + ", ".join(ROLES["comment"]))
    
        data = {}
        data["author"] = self.username
        data["title"] = ""
        
        data["parent_author"] = author
        data["parent_permlink"] = permlink
        
        if not isinstance(body, str):
            raise NektarException("Body must be a UTF-8 string.")
        if not len(body.encode("utf-8")):
            raise NektarException("Body must be at least 1 byte.")
        data["body"] = body
       
        data["permlink"] = ("re-" + permlink)[:255]
        
        ## create comment metadata
        json_metadata = {}
        json_metadata["description"] = ""
        json_metadata["format"] = "markdown"
        json_metadata["app"] = self.app + "/" + self.version
        pattern_images = r"[!]\[[\w\ \-._~!$&'()*+,;=:@#\/?]*\]\([\w\-._~!$&'()*+,;=:@#\/?]+\)"
        json_metadata["image"] = list(re.findall(pattern_images, body))
        data["json_metadata"] = json.dumps(json_metadata).replace("'", "\\\"")
        
        ## initialize transaction data
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expiration = _make_expiration(expire)
        expire = within_range(expire, 5, 120, 30)
        synchronous = true_or_false(synchronous, False)

        operations = [[ "comment", data ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous)

    def vote(self, author, permlink, weight, expire=30, synchronous=False, strict=True):
        """
            Looks up accounts starting with name.
            
            :start: starting part of username to search
            :limit: maximum limit of accounts to list.
        """
        
        
        if not _check_wifs(self.roles, "vote"):
            raise NektarException("The `comment` operation requires" \
                                    "one of the following private keys:" + ", ".join(ROLES["vote"]))
        
        if not isinstance(author, str):
            raise NektarException("author must be a string.")

        pattern = r"[\w][\w\d\.\-]{2,15}"
        match = re.findall(pattern, author)
        if not len(match):
            raise NektarException("author must be a string of length 3 - 16.")
            
        pattern = r"[\w][\w\d\-\%]{0,255}"
        match = re.findall(pattern, permlink)
        if not len(match):
            raise NektarException("permlink must be a valid url-escaped string.")
        
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        weight = within_range(weight, -10000, 10000, 10000)
        expire = within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = true_or_false(synchronous, False)

        operations = [[ "vote", { "voter": self.username, "author": author, "permlink": permlink, "weight": weight } ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous, strict)

    def memo(self, receiver, amount, asset, message, expire=30, synchronous=False):
        """
            Transfers asset from one account to another.
            
            :receiver: a valid hive account username
            :amount: any positive value
            :asset: asset type to send, `HBD` or `HIVE` only
            :message: any UTF-8 string up to 2048 bytes only
        """
        
        if not _check_wifs(self.roles, "transfer"):
            raise NektarException("The `comment` operation requires" \
                                    "one of the following private keys:" + ", ".join(ROLES["transfer"]))
    
        data = {}
        data["from"] = self.username
        if not isinstance(receiver, str):
            raise NektarException("Receiver must be a valid Hive account user.")
        if self.username == receiver:
            raise NektarException("Receiver must be unique from the sender.")
        data["to"] = receiver
        
        if not isinstance(amount, (int, float)):
            raise NektarException("Amount must be a positive numeric value.")
        if amount <= 0:
            raise NektarException("Amount must be a positive numeric value.")
        if asset not in ("HBD", "HIVE"):
            raise NektarException("Memo only accepts transfer of HBD and HIVE assets.")
        
        amount = round(amount, ASSETS[asset]["precision"])
        data["amount"] = str(amount) + " " + asset
        
        if not isinstance(message, str):
            raise NektarException("Memo message must be a UTF-8 string.")
        if not (len(message.encode("utf-8")) <= 256):
            raise NektarException("Memo message must be not more than 2048 bytes.")
        data["memo"] = message
        
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = true_or_false(synchronous, False)

        operations = [[ "transfer", data ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous)

    def custom_json(self, protocol_id, json_data, required_auths, required_posting_auths, expire=30, synchronous=False):
        """
            Provides a generic way to add higher level protocols.
            
            :protocol_id: a valid string in a lowercase snake case form
            :json_data: any valid JSON data
            :required_auths: account usernames required to sign with private keys
            :required_posting_auths: account usernames required to sign with a `posting` private key
        """
    
        data = {}    
        roles = "posting" # initial required role
        
        if not isinstance(required_auths, list):
            raise NektarException("The `required_auths` requires a list of valid usernames.")
        data["required_auths"] = required_auths
        
        # if required auths is not empty, include owner,
        # active and posting roles
        if len(required_auths):
            roles = "custom_json"
        if not _check_wifs(self.roles, roles):
            raise NektarException("The `custom_json` operation requires" \
                                    "one of the following private keys:" + ", ".join(ROLES[roles]))

        if not isinstance(required_posting_auths, list):
            raise NektarException("The `required_posting_auths` requires a list of valid usernames.")
        data["required_posting_auths"] = required_posting_auths
        
        if len(re.findall(r"[^\w]+", protocol_id)):
            raise NektarException("Custom JSON id must be a valid string preferrably in lowercase and snake case format.")
        data["id"] = protocol_id
        
        if not isinstance(json_data, dict):
            raise NektarException("Custom JSON must be in dictionary format.")
        data["json"] = json.dumps(json_data).replace("'", "\\\"")
        
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = true_or_false(synchronous, False)

        operations = [[ "custom_json", data ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous)

    def _custom_json(self, custom_json_id, json_data, required_posting_auths, expire=30, synchronous=False):
        """
            Provides a generic way to add higher level protocols.
            
            :custom_json_id: a valid string in a lowercase snake case form
            :json_data: any valid JSON data
            :required_auths: account usernames required to sign with a private key
            :required_posting_auths: account usernames required to sign with a `posting` private key
            :roles: account usernames required to sign with a `posting` private key
        """
        
        pass
    
    def _broadcast(self, transaction, synchronous, strict=True):
        method = "condenser_api.broadcast_transaction"
        if synchronous:
            method = "condenser_api.broadcast_transaction_synchronous"
            result = self.appbase.broadcast(method, transaction, strict)
            if result:
                return result
        return self.appbase.broadcast(method, transaction, strict)

##############################
# utils                      #
##############################

def _check_wifs(roles, operation):
    return len([role for role in ROLES[operation]
        if role in roles])

def _make_expiration(secs=30):
    timestamp = time.time() + int(secs)
    return datetime.utcfromtimestamp(timestamp).strftime(DATETIME_FORMAT)

def within_range(value, minimum, maximum, fallback=None):
    if not isinstance(value, int) and not isinstance(fallback, int):
        raise NektarException(f"Input values must be integers.")
    if not (minimum <= value <= maximum):
        if fallback is not None:
            raise NektarException(f"Integer value must be within {minimum} to {maximum} only.")
        return fallback
    return value

def true_or_false(value, fallback):
    if isinstance(value, bool):
        return value
    return fallback