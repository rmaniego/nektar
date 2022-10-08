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
from .constants import NEKTAR_VERSION, BLOCKCHAIN_OPERATIONS, ASSETS, ROLES, DATETIME_FORMAT
from .exceptions import NektarException


class Nektar:
    """
        Nektar Class
        ~~~~~~~~~

        Base Class to access access AppBase/Condenser API methods.
    """
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
        
        # lazy mode
        self.config = None

    def set_username(self, username):
        if not isinstance(username, str):
            raise NektarException("Username must be a valid Hive account username.")
        self.username = username.replace("@", "")

    def refresh(self):
        self.account = self.appbase.api("condenser").get_accounts([[self.username]])[0]

    def resource_credits(self, account=None):
        """
            Get the current resource credits of an account.
            
            :account: get followers of an account, default = username (optional)
        """
        
        params = {}
        if account is None:
            account = self.username
        if not isinstance(account, str):
            raise NektarException("Account must be a string.")
        pattern = r"[\w][\w\d\.\-]{2,15}"
        if not len(re.findall(pattern, account)):
            raise NektarException("Account must be a string of length 3 - 16.")
        params["accounts"] = [ account ]
        
        data = self.appbase.api("rc").find_rc_accounts(params)["rc_accounts"]
        if not data:
            return {}
        return data[0]

    def manabar(self, account=None):
        """
            Returns the current manabar precentage.
            
            :account: get followers of an account, default = username (optional)
        """
        
        data = self.resource_credits(account)
        return (int(data["rc_manabar"]["current_mana"]) / int(data["max_rc"])) * 100
        

    def get_config(self, field=None, fallback=None):
        """
            Get low-level blockchain constants.
            
            :field: configuration field to get (optional)
            :fallback: a fallback value if field is not found (optional)
        """
        # Hive Developer Portal > Understanding Configuration Values
        # https://developers.hive.io/tutorials-recipes/understanding-configuration-values.html
        if self.config is None:
            self.config = self.appbase.api("database").get_config({})
        if isinstance(field, str):
            return self.config.get(field, fallback)
        return self.config

    def get_dynamic_global_properties(self, api="condenser"):
        ## use database_api
        return self.appbase.api(api).get_dynamic_global_properties({})

    def get_previous_block(self, head_block_number):
        block_number = head_block_number - 2
        blocks = self.appbase.api("block").get_block({"block_num": block_number})
        return blocks["block"]["previous"]

    def get_reference_block_data(self):
        properties = self.get_dynamic_global_properties("database")
        ref_block_num = properties["head_block_number"] - 3 & 0xFFFF
        previous = self.get_previous_block(properties["head_block_number"])
        ref_block_prefix = struct.unpack_from("<I", unhexlify(previous), 4)[0]
        return ref_block_num, ref_block_prefix

    def custom_json(self, json_id, json_data, required_auths, required_posting_auths, expire=30, synchronous=False, strict=True, verify_only=False):
        """
            Provides a generic way to add higher level protocols.
            
            :json_id: a valid string in a lowercase snake case form
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
        
        if len(re.findall(r"[^\w]+", json_id)):
            raise NektarException("Custom JSON id must be a valid string preferrably in lowercase and snake case format.")
        data["id"] = json_id
        
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
    

class Waggle(Nektar):
    """
        Waggle Class
        ~~~~~~~~~

        Methods to interact with the Hive Blockchain.
    """
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
        
        self.app = "nektar.waggle"
        if isinstance(app, str):
            self.app = app
        
        self.version = NEKTAR_VERSION
        if isinstance(version, str):
            self.version = version
        
        # lazy mode
        self.config = None
        
        # most recent transactions
        self.transaction = None

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

    def history(self, account=None, start=-1, limit=1000, low=None, high=None):
        """
            Get all account delegators and other related information.
            
            :account: any valid Hive account username, default = initialized username (optional)
            :start: upperbound range, or -1 for reverse history (optional)
            :limit: upperbound range, or -1 for reverse history (optional)
        """
        
        params = [self.username]
        if isinstance(account, str):
            params[0] = account

        if not isinstance(start, int):
            raise NektarException("Start must be an integer.")
        if not (start == -1 or start > 999):
            raise NektarException("Start be `-1` or an upperbound of value 1000 or higher.")
        params.append(start)

        limit = within_range(limit, 1, 1000, 1000)
        params.append(limit)
        
        operations = list(range(len(BLOCKCHAIN_OPERATIONS)))
        if isinstance(low, int):
            ## for the first 64 blockchain operation
            if low not in operations:
                raise NektarException("Operation Filter `low` is not a valid blockchain operation ID.")
            params.append(int("1".ljust(low+1, "0"), 2))

        if isinstance(high, int):
            ## for the next 64 blockchain operation
            if high not in operations:
                raise NektarException("Operation Filter `high` is not a valid blockchain operation ID.")
            params.append(0) # set to `operation_filter_low` zero
            params.append(int("1".ljust(high+1, "0"), 2))
        
        return self.appbase.api("condenser").get_account_history(params)

    def delegators(self, account=None, active=False):
        """
            Get all account delegators and other related information.
            
            :account: any valid Hive account username, default = initialized username (optional)
            :active: include all changes in delegations if false (optional)
        """

        params = ["", -1, 1000, 0]

        params[0] = self.username
        if isinstance(account, str):
            params[0] = account
        
        operation_id = 40  # delegate_vesting_shares_operation
        params[3] = int("1".ljust(operation_id+1, "0"), 2)
        
        results = {}
        while True:
            try:
                result = self.appbase.api("condenser").get_account_history(params)
            except:
                if params[1] == -1:
                    break
                params[1] -= 1000
            for item in result:
                if params[1] == -1:
                    params[1] = ((item[0] // 1000) * 1000) - 2000
                if item[0] < params[1]:
                    params[1] = ((item[0] // 1000) * 1000) - 1000
                delegator = item[1]["op"][1]["delegator"]
                if delegator == self.username:
                    continue
                if delegator not in results:
                    results[delegator] = {}
                timestamp = item[1]["timestamp"]
                results[delegator][timestamp] = float(item[1]["op"][1]["vesting_shares"].split(" ")[0])
            if params[1] < 1000:
                break
        if active:
            active_delegations = {}
            for d, data in results.items():
                recent = max(list(data.keys()))
                vesting = data[recent]
                if vesting:
                    active_delegations[d] = vesting
            return active_delegations
        return results

    def delegatees(self, account=None, active=False):
        """
            Get all account delegatees and other related information.
            
            :account: any valid Hive account username, default = initialized username (optional)
            :active: include all changes in delegations if false (optional)
        """

        params = ["", -1, 1000, 0]

        params[0] = self.username
        if isinstance(account, str):
            params[0] = account
        
        operation_id = 40  # delegate_vesting_shares_operation
        params[3] = int("1".ljust(operation_id+1, "0"), 2)
        
        results = {}
        while True:
            try:
                result = self.appbase.api("condenser").get_account_history(params)
            except:
                if params[1] == -1:
                    break
                params[1] -= 1000
            for item in result:
                if params[1] == -1:
                    params[1] = ((item[0] // 1000) * 1000) - 2000
                if item[0] < params[1]:
                    params[1] = ((item[0] // 1000) * 1000) - 1000
                delegatee = item[1]["op"][1]["delegatee"]
                if delegatee == self.username:
                    continue
                if delegatee not in results:
                    results[delegatee] = {}
                timestamp = item[1]["timestamp"]
                results[delegatee][timestamp] = float(item[1]["op"][1]["vesting_shares"].split(" ")[0])
            if params[1] < 1000:
                break
        if active:
            active_delegations = {}
            for d, data in results.items():
                recent = max(list(data.keys()))
                vesting = data[recent]
                if vesting:
                    active_delegations[d] = vesting
            return active_delegations
        return results

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
            
            :account: any valid account, default = set username (optional)
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

    def get_post(self, author, permlink, retries=1):
        """
            Get the current data of a post, if not found returns empty dictionary.
            
            :author: username of author of the blog post being accessed
            :permlink: permlink to the blog post being accessed
            :retries: number of times to check the existence of the post, must be between 1-5 (Optional)
        """

        params = {}
        if not isinstance(author, str):
            raise NektarException("Author must be a string.")
        pattern = r"[\w][\w\d\.\-]{2,15}"
        if not len(re.findall(pattern, author)):
            raise NektarException("author must be a string of length 3 - 16.")
        params["author"] = author
        pattern = r"[\w][\w\d\-\%]{0,255}"
        if not len(re.findall(pattern, permlink)):
            raise NektarException("permlink must be a valid url-escaped string.")
        params["permlink"] = permlink
        params["observer"] = self.username
        
        if not isinstance(retries, int):
            raise NektarException("Retries must be an integer.")
        if not (1 <= retries <= 5):
            raise NektarException("Retries must be between 1 to 5 times.")
        
        for _ in range(retries):
            try:
                data = self.appbase.api("bridge").get_post(params)
                if len(data):
                    return data
            except:
                pass
        return {}

    def new_post(self, title, body, description=None, tags=None, community=None, expire=30, synchronous=False, strict=True, verify_only=False):
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
        strict = true_or_false(strict, True)
        verify_only = true_or_false(verify_only, False)

        operations = [[ "comment", data ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def reply(self, author, permlink, body, expire=30, synchronous=False, strict=True, verify_only=False):
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
        strict = true_or_false(strict, True)
        verify_only = true_or_false(verify_only, False)

        operations = [[ "comment", data ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def vote(self, author, permlink, weight=10000, percent=None, expire=30, synchronous=False, strict=True, verify_only=False):
        """
            Looks up accounts starting with name.
            
            :author: author of the post or comment being voted
            :permlink: permlink of the post or comment being voted
            :weight: vote value between -10000 to 10000 (Optional)
            :percent: override weight with precentage (Optional)
            :expire: transaction expiration in seconds (Optional)
            :synchronous: broadcast transaction synchronously (Optional)
            :strict: verify authority and raise exception on errors (Optional)
        """
        
        
        if not _check_wifs(self.roles, "vote"):
            raise NektarException("The `comment` operation requires" \
                                    "one of the following private keys:" + ", ".join(ROLES["vote"]))
        
        if not isinstance(author, str):
            raise NektarException("Author must be a string.")

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
        strict = true_or_false(strict, True)
        verify_only = true_or_false(verify_only, False)

        operations = [[ "vote", { "voter": self.username, "author": author, "permlink": permlink, "weight": weight } ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def memo(self, receiver, amount, asset, message, expire=30, synchronous=False, strict=True, verify_only=False):
        """
            Transfers asset from one account to another.
            
            :receiver: a valid hive account username
            :amount: any positive value
            :asset: asset type to send, `HBD` or `HIVE` only
            :message: any UTF-8 string up to 2048 bytes only
        """
        
        if not _check_wifs(self.roles, "transfer"):
            raise NektarException("The `transfer` operation requires" \
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
        
        precision = ASSETS[asset]["precision"]
        whole, fraction = str(float(amount)).split(".")
        fraction = fraction.ljust(precision, "0")[:precision]
        data["amount"] = whole + "." + fraction + " " + asset
        
        if not isinstance(message, str):
            raise NektarException("Memo message must be a UTF-8 string.")
        if not (len(message.encode("utf-8")) <= 256):
            raise NektarException("Memo message must be not more than 2048 bytes.")
        data["memo"] = message
        
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = true_or_false(synchronous, False)
        strict = true_or_false(strict, True)
        verify_only = true_or_false(verify_only, False)

        operations = [[ "transfer", data ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }

        return self._broadcast(transaction, synchronous, strict, verify_only)
    
    def _broadcast(self, transaction, synchronous, strict=True, verify_only=False):
        method = "condenser_api.broadcast_transaction"
        if synchronous:
            method = "condenser_api.broadcast_transaction_synchronous"
            result = self.appbase.broadcast(method, transaction, strict, verify_only)
            if result:
                return result
        return self.appbase.broadcast(method, transaction, strict, verify_only)
    
    def verify_authority(self, transaction):
        """
            Returns true if the transaction has all of the required signatures.
            
            :transaction: a valid transaction data
        """
        return self.appbase.api("condenser").verify_authority(transaction, strict=False)


class Swarm(Nektar):
    """
        Swarm Class
        ~~~~~~~~~

        Wrapped methods for admins and moderators to manage communities.
    """
    def __init__(self, community, username, wif=None, role=None, wifs=None, app=None, version=None):
        self.set_username(username)
        
        self.appbase = AppBase()
        
        if isinstance(role, str) and isinstance(wif, str):
            self.appbase.append_wif(role, wif)
        if isinstance(wifs, dict):
            self.appbase.append_wif(wifs)
        self.roles = list(self.appbase.wifs.keys())

        self.account = None
        self.refresh()
        
        self.app = "nektar.swarm"
        if isinstance(app, str):
            self.app = app
        
        self.version = NEKTAR_VERSION
        if isinstance(version, str):
            self.version = version

        self._community = community
        if not len(re.findall(r"\bhive-[\d]{1,6}\b", community)):
            raise NektarException("Community must be a valid community name in `hive-*` format.")

        self._required_posting_auths = [self.username]

    def mute(self, author, permlink, notes):
        """
            Mute posts or comments with a designated note.

            :author: username of author of the blog post being replied to.
            :permlink: permlink to the blog post being muted.
            :notes: reason for muting.
        """

        if not isinstance(author, str):
            raise NektarException("Username must be a valid Hive account username.")
        author = author.replace("@", "")
        
        pattern = r"[\w][\w\d\-\%]{0,255}"
        if not len(re.findall(pattern, permlink)):
            raise NektarException("The permlink must be a valid url-escaped string.")

        if not isinstance(notes, str):
            raise NektarException("Notes must be in string format.")
        
        data = {}
        data["required_auths"] = []
        data["required_posting_auths"] = [self.username]
        data["id"] = "community"
        
        json_data = {}
        json_data["community"] = self._community
        json_data["account"] = author
        json_data["permlink"] = permlink
        json_data["notes"] = notes
        operation = [ "mutePost", json_data ]
        data["json"] = json.dumps(operation).replace("'", "\\\"")
        
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = true_or_false(synchronous, False)
        strict = true_or_false(strict, True)
        verify_only = true_or_false(verify_only, False)

        operations = [[ "custom_json", data ]]
        transaction = { "ref_block_num": ref_block_num,
                     "ref_block_prefix": ref_block_prefix,
                     "expiration": expiration,
                     "operations": operations,
                     "extensions": [] }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def mark_spam(self, author, permlink):
        """
            Muting post but noted as `spam` as standardized label for spams.
        """
        self.mute(author, permlink, "spam")
        
    

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