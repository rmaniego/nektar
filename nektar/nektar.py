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
import math
import time
import struct
from datetime import datetime, timezone
from binascii import hexlify, unhexlify

from .appbase import AppBase
from .constants import (
    NEKTAR_VERSION,
    BLOCKCHAIN_OPERATIONS,
    ASSETS,
    ROLES,
    DATETIME_FORMAT,
)
from .exceptions import NektarException


class Nektar:
    """Nektar base class.
    ~~~~~~~~~

    :param username: a valid Hive account username
    :param wif: the WIF or private key (Default value = None)
    :param role: the equivalent authority of the WIF (Default value = None)
    :param wifs: a dictionary of roles and their equivalent WIFs (Default value = None)
    :param app: the name of the app built with nektar (Default value = None)
    :param version: the version `x.y.x` of the app built with nektar (Default value = None)
    :param timeout: seconds before the request is dropped (Default value = 10)
    :param retries: times the request retries if errors are encountered (Default value = 3)
    :param warning: display warning messages (Default value = False)

    """

    def __init__(
        self,
        username,
        wif=None,
        role=None,
        wifs=None,
        app=None,
        version=None,
        timeout=10,
        retries=3,
        warning=False,
    ):
        self.appbase = AppBase(timeout=timeout, retries=retries, warning=warning)
        self.set_username(username, wif, role, wifs)

        self.account = None
        self.refresh()

        # lazy mode
        self.config = None

    def set_username(self, username, wif=None, role=None, wifs=None):
        """Dynamically update the username and WIFs of the instance.

        :param username: a valid Hive account username
        :param wif: the WIF or private key (Default value = None)
        :param role: the equivalent authority of the WIF (Default value = None)
        :param wifs: a dictionary of roles and their equivalent WIFs (Default value = None)

        """
        if not isinstance(username, str):
            raise NektarException("Username must be a valid Hive account username.")
        self.username = username

        if isinstance(role, str) and isinstance(wif, str):
            self.appbase.append_wif(wif, role)
        elif isinstance(wifs, dict):
            self.appbase.append_wif(wifs)

        self.roles = list(self.appbase.wifs.keys())

    def refresh(self):
        """Get a more recent version of the account data."""
        data = self.appbase.condenser().get_accounts([[self.username]])
        if data:
            self.account = data[0]

    def resource_credits(self, account=None):
        """Get the current resource credits of an account.

        :param account: a valid Hive account username, default = initizalized account (Default value = None)

        """

        params = {}
        if account is None:
            account = self.username
        if not isinstance(account, str):
            raise NektarException("Account must be a string.")
        pattern = r"[\w][\w\d\.\-]{2,15}"
        if not len(re.findall(pattern, account)):
            raise NektarException("Account must be a string of length 3 - 16.")
        params["accounts"] = [account]

        data = self.appbase.rc().find_rc_accounts(params)["rc_accounts"]
        if not data:
            return {}
        return data[0]

    def manabar(self, account=None):
        """Returns the current manabar precentage.

        :param account: a valid Hive account username, default = initizalized account (Default value = None)

        """
        
        data = self.resource_credits(account)
        return (int(data["rc_manabar"]["current_mana"]) / int(data["max_rc"])) * 100
    
    def reputation(self, account=None, score=True):
        """Returns the current manabar precentage.

        :param account: a valid Hive account username, default = initizalized account (Default value = None)

        """
        value = int(self.account["reputation"])
        if account:
            data = self.appbase.condenser().get_accounts([[account]])
            if not data:
                raise NektarException(
                    "`account` must be a valid Hive account username."
                )
            value = int(data[0]["reputation"])
        if not score:
            return value
        result = ((math.log10(abs(value)) - 9) * 9) + 25
        if value < 0:
            return -result
        return result

    def get_config(self, field=None, fallback=None):
        """Get low-level blockchain constants.

        :param field: configuration field to get (Default value = None)
        :param fallback: a fallback value if field is not found (Default value = None)

        """
        # Hive Developer Portal > Understanding Configuration Values
        # https://developers.hive.io/tutorials-recipes/understanding-configuration-values.html
        if self.config is None:
            self.config = self.appbase.database().get_config({})
        if isinstance(field, str):
            return self.config.get(field, fallback)
        return self.config

    def get_dynamic_global_properties(self, api="condenser"):
        """Get the dynamic global properties.

        :param api: the API to access the global properties (Default value = "condenser")

        """
        ## use database_api
        return self.appbase.api(api).get_dynamic_global_properties({})

    def get_previous_block(self, head_block_number):
        """Get the previous block.

        :param head_block_number: value must be dynamically taken from the global properties.

        """
        block_number = head_block_number - 2
        blocks = self.appbase.block().get_block({"block_num": block_number})
        return blocks["block"]["previous"]

    def get_reference_block_data(self):
        """Get reference block data from the dynamic global properties."""
        properties = self.get_dynamic_global_properties("database")
        ref_block_num = properties["head_block_number"] - 3 & 0xFFFF
        previous = self.get_previous_block(properties["head_block_number"])
        ref_block_prefix = struct.unpack_from("<I", unhexlify(previous), 4)[0]
        return ref_block_num, ref_block_prefix

    def custom_json(
        self,
        json_id,
        json_data,
        required_auths,
        required_posting_auths,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Provides a generic way to add higher level protocols.

        :param json_id: a valid string in a lowercase and (snake_case or kebab-case) format
        :param json_data: any valid JSON data
        :param required_auths: list of usernames required to sign with private keys
        :param required_posting_auths: list of usernames required to sign with a `posting` private key
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        data = {}
        roles = "posting"  # initial required role

        if not isinstance(required_auths, list):
            raise NektarException(
                "The `required_auths` requires a list of valid usernames."
            )
        data["required_auths"] = required_auths

        # if required auths is not empty, include owner,
        # active and posting roles
        if len(required_auths):
            roles = "custom_json"
        if not _check_wifs(self.roles, roles):
            raise NektarException(
                "The `custom_json` operation requires"
                "one of the following private keys:" + ", ".join(ROLES[roles])
            )

        if not isinstance(required_posting_auths, list):
            raise NektarException(
                "The `required_posting_auths` requires a list of valid usernames."
            )
        data["required_posting_auths"] = required_posting_auths

        if len(re.findall(r"[^\w\-]+", json_id)):
            raise NektarException(
                "Custom JSON id must be a valid string preferrably in lowercase and (snake_case or kebab-case) format."
            )
        data["id"] = json_id

        if not isinstance(json_data, dict):
            raise NektarException("Custom JSON must be in dictionary format.")
        data["json"] = json.dumps(json_data).replace("'", '\\"')

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _true_or_false(synchronous, False)

        operations = [["custom_json", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous)

    def verify_authority(self, transaction):
        """Returns true if the transaction has all of the required signatures.

        :param transaction: a valid transaction data

        """
        return self.appbase.condenser().verify_authority(transaction, strict=False)

    def _broadcast(
        self, transaction, synchronous=False, strict=True, verify_only=False
    ):
        """Processes the transaction for broadcasting into the blockchain.

        :param transaction: the formatted transaction based on the API method
        :param synchronous: broadcasting     method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """
        method = "condenser_api.broadcast_transaction"
        if synchronous:
            method = "condenser_api.broadcast_transaction_synchronous"
            result = self.appbase.broadcast(method, transaction, strict, verify_only)
            if result:
                return result
        return self.appbase.broadcast(method, transaction, strict, verify_only)


class Waggle(Nektar):
    """Methods to interact with the Hive Blockchain.
    ~~~~~~~~~

    :param username: a valid Hive account username
    :param wif: the WIF or private key (Default value = None)
    :param role: the equivalent authority of the WIF (Default value = None)
    :param wifs: a dictionary of roles and their equivalent WIFs (Default value = None)
    :param app: the name of the app built with nektar (Default value = None)
    :param version: the version `x.y.x` of the app built with nektar (Default value = None)
    :param timeout: seconds before the request is dropped (Default value = 10)
    :param retries: times the request retries if errors are encountered (Default value = 3)
    :param warning: display warning messages (Default value = False)

    """

    def __init__(
        self,
        username,
        wif=None,
        role=None,
        wifs=None,
        app=None,
        version=None,
        timeout=10,
        retries=3,
        warning=False,
    ):
        self.appbase = AppBase(timeout=timeout, retries=retries, warning=warning)
        self.set_username(username, wif, role, wifs)

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
        """List all communities.

        :param last: last known community name `hive-*`, paging mechanism (Default value = None)
        :param sort: maximum limit of communities to list (Default value = "rank")
        :param limit: sort by `rank`, `new`, or `subs` (Default value = 100)
        :param query: additional filter keywords for search (Default value = None)

        """

        params = {}
        params["observer"] = self.username
        params["sort"] = "rank"
        if sort in ("new", "subs"):
            params["sort"] = sort
        if isinstance(last, str):
            params["query"] = query

        # custom limits by nektar, hive api limit: 100
        custom_limit = _within_range(limit, 1, 10000, 100)
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
            result = self.appbase.bridge().list_communities(params)
            results.extend(result)
            if len(result) < 100:
                break
            if len(results) >= custom_limit:
                break
            params["last"] = results[-1]["name"]
        return results[:custom_limit]

    def subscribers(self, community, last=None, limit=100):
        """Gets a list of subscribers for a given community.

        :param community: community name `hive-*`
        :param last: last known subscriber username, paging mechanism (Default value = None)
        :param limit: maximum limit of subscribers to list (Default value = 100)

        """

        params = {}

        params["community"] = community
        if isinstance(community, str):
            match = re.findall(r"\bhive-[\d]{1,6}\b", community)
            if not len(match):
                raise NektarException(
                    f"Community name '{community}' format is unsupported."
                )

        # custom limits by nektar, hive api limit: 100
        custom_limit = _within_range(limit, 1, 10000, 100)
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
            result = self.appbase.bridge().list_subscribers(params)
            results.extend(result)
            if len(result) < 100:
                break
            if len(results) >= custom_limit:
                break
            params["last"] = results[-1][0]
        return results[:custom_limit]

    def accounts(self, start=None, limit=100):
        """Looks up accounts starting with name.

        :param start: starting part of username to search (Default value = None)
        :param limit: maximum limit of accounts to list (Default value = 100)

        """

        params = ["", 1]

        # custom limits by nektar, hive api limit: 1000
        custom_limit = _within_range(limit, 1, 10000, 100)
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
                result = self.appbase.condenser().lookup_accounts(params)
                results.extend(result)
                if len(result) < 1000:
                    break
                if len(results) >= custom_limit:
                    return results[:custom_limit]
            if not len(start):
                break
        return results[:custom_limit]

    def followers(self, account=None, start=None, ignore=False, limit=1000):
        """Looks up accounts starting with name.

        :param account: a valid Hive account username, default = username (Default value = None)
        :param start: account to start from, paging mechanism (Default value = None)
        :param ignore: show all muted accounts if True (Default value = False)
        :param limit: maximum limit of accounts to list (Default value = 1000)

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
        custom_limit = _within_range(limit, 1, 10000, 100)
        crawls = custom_limit // 100
        params[3] = custom_limit
        if crawls > 0:
            params[3] = 1000

        results = []
        for _ in range(crawls):
            result = self.appbase.condenser().get_followers(params)
            for item in result:
                results.append(item["follower"])
            if len(result) < 1000:
                break
            if len(results) >= custom_limit:
                break
            params[1] = results[-1]["follower"]
        return results[:custom_limit]

    def history(self, account=None, start=-1, limit=1000, low=None, high=None):
        """Get a list of account history.

        :param account: any valid Hive account username, default = initialized username (Default value = None)
        :param start: upperbound range, or -1 for reverse history (Default value = -1)
        :param limit: upperbound range, or -1 for reverse history (Default value = 1000)
        :param low: operation id (Default value = None)
        :param high: operation id (Default value = None)

        """

        params = [self.username]
        if isinstance(account, str):
            params[0] = account

        if not (int(start) == -1 or int(start) > 999):
            raise NektarException(
                "Start be `-1` or an upperbound of value 1000 or higher."
            )
        params.append(start)

        limit = _within_range(limit, 1, 1000, 1000)
        params.append(limit)

        operations = list(range(len(BLOCKCHAIN_OPERATIONS)))
        if isinstance(low, int):
            ## for the first 64 blockchain operation
            if int(low) not in operations:
                raise NektarException(
                    "Operation Filter `low` is not a valid blockchain operation ID."
                )
            params.append(int("1".ljust(low + 1, "0"), 2))

        if isinstance(high, int):
            ## for the next 64 blockchain operation
            if high not in operations:
                raise NektarException(
                    "Operation Filter `high` is not a valid blockchain operation ID."
                )
            params.append(0)  # set to `operation_filter_low` zero
            params.append(int("1".ljust(high + 1, "0"), 2))

        return self.appbase.condenser().get_account_history(params)

    def delegators(self, account=None, active=False):
        """Get all account delegators and other related information.

        :param account: any valid Hive account username, default = initialized username (Default value = None)
        :param active: include all changes in delegations if false (Default value = False)

        """

        params = ["", -1, 1000, 0]

        params[0] = self.username
        if isinstance(account, str):
            params[0] = account

        operation_id = 40  # delegate_vesting_shares_operation
        params[3] = int("1".ljust(operation_id + 1, "0"), 2)

        results = {}
        while True:
            try:
                result = self.appbase.condenser().get_account_history(params)
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
                results[delegator][timestamp] = float(
                    item[1]["op"][1]["vesting_shares"].split(" ")[0]
                )
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
        """Get all account delegatees and other related information.

        :param account: any valid Hive account username, default = initialized username (Default value = None)
        :param active: include all changes in delegations if false (Default value = False)

        """

        params = ["", -1, 1000, 0]

        params[0] = self.username
        if isinstance(account, str):
            params[0] = account

        operation_id = 40  # delegate_vesting_shares_operation
        params[3] = int("1".ljust(operation_id + 1, "0"), 2)

        results = {}
        while True:
            try:
                result = self.appbase.condenser().get_account_history(params)
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
                results[delegatee][timestamp] = float(
                    item[1]["op"][1]["vesting_shares"].split(" ")[0]
                )
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
        """Get ranked posts based on tag.

        :param community: community name `hive-*` (Default value = None)
        :param sort: sort by `created`, `trending`, `hot`, `promoted`, `payout`, `payout_comments`, or `muted` (Default value = "created")
        :param paidout: return new (False), paidout (True), all (None) (Default value = None)
        :param limit: maximum limit of blogs (Default value = 100)

        """

        params = {}
        params["tag"] = ""
        if isinstance(community, str):
            match = re.findall(r"\bhive-[\d]{1,6}\b", community)
            if len(match):
                params["tag"] = community
        params["sort"] = "created"
        if sort in (
            "trending",
            "hot",
            "promoted",
            "payout",
            "payout_comments",
            "muted",
        ):
            params["sort"] = sort
        params["observer"] = self.username

        # custom limits by nektar, hive api limit: 100?
        limit = _within_range(limit, 1, 1000, 100)
        params["limit"] = limit

        results = []
        filter = [True, False]
        if isinstance(paidout, bool):
            filter = [paidout]
        result = self.appbase.bridge().get_ranked_posts(params)
        for post in result:
            if not post["depth"] and post["is_paidout"] in filter:
                results.append(post)
        return results

    def blogs(self, account=None, sort="posts", paidout=None, limit=20):
        """Lists posts related to a given account.

        :param account: any valid account, default = set username (Default value = None)
        :param sort: sort by `blog`, `feed`, `post`, `replies`, or `payout` (Default value = "posts")
        :param paidout: filter for all or paid out posts (Default value = None)
        :param limit: maximum limit of posts (Default value = 20)

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
        limit = _within_range(limit, 1, 100, 100)
        params["limit"] = limit

        results = []
        filter = [True, False]
        if isinstance(paidout, bool):
            filter = [paidout]
        result = self.appbase.bridge().get_account_posts(params)
        for post in result:
            if not post["depth"] and post["is_paidout"] in filter:
                results.append(post)
        return results

    def get_post(self, author, permlink, retries=1):
        """Get the current data of a post, if not found returns empty dictionary.

        :param author: username of author of the blog post being accessed
        :param permlink: permlink to the blog post being accessed
        :param retries: number of times to check the existence of the post, must be between 1-5 (Default value = 1)

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

        if not (1 <= int(retries) <= 5):
            raise NektarException("Retries must be between 1 to 5 times.")
        strict = retries == 1

        for _ in range(retries):
            data = self.appbase.bridge().get_post(params, strict=strict)
            if len(data):
                return data
        return {}

    def new_post(
        self,
        title,
        body,
        description=None,
        tags=None,
        community=None,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Broadcast a new post to the blockchain

        :param title: a human readable title of the post being submitted
        :param body: body of the post being submitted
        :param description: (Default value = None)
        :param tags: a space separated list of tags (Default value = None)
        :param community: the community to post e.g. `hive-*` (Default value = None)
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        if not _check_wifs(self.roles, "comment"):
            raise NektarException(
                "The `comment` operation requires"
                "one of the following private keys:" + ", ".join(ROLES["comment"])
            )

        data = {}
        data["author"] = self.username

        title = re.sub(r"[\r\n]", "", title)
        if not (1 <= len(title.encode("utf-8")) <= 256):
            raise NektarException("Title must be within 1 to 256 bytes.")
        data["title"] = title

        if not isinstance(body, str):
            raise NektarException("Body must be a UTF-8 string.")
        if not len(body.encode("utf-8")):
            raise NektarException("Body must be at least 1 byte.")
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
        pattern_images = (
            r"[!]\[[\w\ \-._~!$&'()*+,;=:@#\/?]*\]\([\w\-._~!$&'()*+,;=:@#\/?]+\)"
        )
        json_metadata["image"] = list(re.findall(pattern_images, body))
        data["json_metadata"] = json.dumps(json_metadata).replace("'", '\\"')

        ## initialize transaction data
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expiration = _make_expiration(expire)
        expire = _within_range(expire, 5, 120, 30)
        synchronous = _true_or_false(synchronous, False)
        strict = _true_or_false(strict, True)
        verify_only = _true_or_false(verify_only, False)

        operations = [["comment", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def reply(
        self,
        author,
        permlink,
        body,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Broadcast a new comment to a post.

        :param author: username of author of the blog post being replied to
        :param permlink: permlink to the blog post being replied to
        :param body: the content of the comment
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        if not _check_wifs(self.roles, "comment"):
            raise NektarException(
                "The `comment` operation requires"
                "one of the following private keys:" + ", ".join(ROLES["comment"])
            )

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
        pattern_images = (
            r"[!]\[[\w\ \-._~!$&'()*+,;=:@#\/?]*\]\([\w\-._~!$&'()*+,;=:@#\/?]+\)"
        )
        json_metadata["image"] = list(re.findall(pattern_images, body))
        data["json_metadata"] = json.dumps(json_metadata).replace("'", '\\"')

        ## initialize transaction data
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expiration = _make_expiration(expire)
        expire = _within_range(expire, 5, 120, 30)
        synchronous = _true_or_false(synchronous, False)
        strict = _true_or_false(strict, True)
        verify_only = _true_or_false(verify_only, False)

        operations = [["comment", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def vote(
        self,
        author,
        permlink,
        weight=10000,
        percent=None,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Perform vote on a blog post or comment.

        :param author: author of the post or comment being voted
        :param permlink: permlink of the post or comment being voted
        :param weight: vote weight between -10000 to 10000 (Default value = 10000)
        :param percent: override vote weight with percentage (Default value = None)
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        if not _check_wifs(self.roles, "vote"):
            raise NektarException(
                "The `comment` operation requires"
                "one of the following private keys:" + ", ".join(ROLES["vote"])
            )

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

        if isinstance(percent, (int, float)):
            percent = _within_range(percent, -100, 100)
            weight = 10000 * (percent / 100)

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        weight = _within_range(weight, -10000, 10000, 10000)
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _true_or_false(synchronous, False)
        strict = _true_or_false(strict, True)
        verify_only = _true_or_false(verify_only, False)

        operations = [
            [
                "vote",
                {
                    "voter": self.username,
                    "author": author,
                    "permlink": permlink,
                    "weight": weight,
                },
            ]
        ]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def memo(
        self,
        receiver,
        amount,
        asset,
        message,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Transfers asset from one account to another, precision is auto-adjusted based on the specified asset.

        :param receiver: a valid Hive account username
        :param amount: any positive value
        :param asset: asset type to send, `HBD` or `HIVE` only
        :param message: any UTF-8 string up to 2048 bytes only
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        if not _check_wifs(self.roles, "transfer"):
            raise NektarException(
                "The `transfer` operation requires"
                "one of the following private keys:" + ", ".join(ROLES["transfer"])
            )

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
        asset = asset.upper()
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
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _true_or_false(synchronous, False)
        strict = _true_or_false(strict, True)
        verify_only = _true_or_false(verify_only, False)

        operations = [["transfer", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }

        return self._broadcast(transaction, synchronous, strict, verify_only)


class Swarm(Nektar):
    """Methods for admins and moderators to manage communities.
    ~~~~~~~~~

    :param community: a valid Hive community name `hive-*`
    :param username: a valid Hive account username
    :param wif: the WIF or private key (Default value = None)
    :param role: the equivalent authority of the WIF (Default value = None)
    :param wifs: a dictionary of roles and their equivalent WIFs (Default value = None)
    :param app: the name of the app built with nektar (Default value = None)
    :param version: the version `x.y.x` of the app built with nektar (Default value = None)
    :param timeout: seconds before the request is dropped (Default value = 10)
    :param retries: times the request retries if errors are encountered (Default value = 3)
    :param warning: display warning messages (Default value = False)

    """

    def __init__(
        self,
        community,
        username,
        wif=None,
        role=None,
        wifs=None,
        app=None,
        version=None,
        timeout=10,
        retries=3,
        warning=False,
    ):
        self.appbase = AppBase(timeout=timeout, retries=retries, warning=warning)
        self.set_username(username, wif, role, wifs)

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
            raise NektarException(
                "Community must be a valid community name in `hive-*` format."
            )

        self._required_posting_auths = [self.username]

    def mute(
        self,
        author,
        permlink,
        notes,
        mute=True,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Mute posts or comments with a designated note.

        :param author: username of author of the blog post
        :param permlink: permlink to the blog post
        :param notes: reason for muting
        :param mute: mute author (Default value = True)
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        if not isinstance(author, str):
            raise NektarException("Username must be a valid Hive account username.")

        pattern = r"[\w][\w\d\-\%]{0,255}"
        if not len(re.findall(pattern, permlink)):
            raise NektarException("The permlink must be a valid url-escaped string.")

        if not isinstance(notes, str):
            raise NektarException("Notes must be in string format.")

        action = "mutePost"
        if not isinstance(mute, bool):
            raise NektarException("`mute` must be either `True` or `False` only.")
        if not mute:
            action = "unmutePost"

        data = {}
        data["required_auths"] = []
        data["required_posting_auths"] = [self.username]
        data["id"] = "community"

        json_data = {}
        json_data["community"] = self._community
        json_data["account"] = author
        json_data["permlink"] = permlink
        json_data["notes"] = notes
        operation = [action, json_data]
        data["json"] = json.dumps(operation).replace("'", '\\"')

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _true_or_false(synchronous, False)
        strict = _true_or_false(strict, True)
        verify_only = _true_or_false(verify_only, False)

        operations = [["custom_json", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def unmute(
        self,
        author,
        permlink,
        notes,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Unmute posts or comments with a designated note.

        :param author: username of author of the blog post
        :param permlink: permlink to the blog post
        :param notes: reason for unmuting
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """
        return self.mute(author, permlink, notes, False, expire, strict, verify_only)

    def mark_spam(
        self,
        author,
        permlink,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Muting post but noted as `spam` as standardized label for spams.

        :param author: a valid blockchain account username
        :param permlink: actual permlink to the specified author
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """
        self.mute(author, permlink, "spam", True, expire, strict, verify_only)

    def update(
        self,
        title,
        about,
        is_nsfw,
        description,
        flag_text,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Update community properties.

        :param title: username of author of the blog post
        :param about: permlink to the blog post
        :param is_nsfw: (not suitable or safe for work
        :param description: mute author (Default value = True)
        :param flag_text: mute author (Default value = True)
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        title = re.sub(r"[\r\n]", "", title)
        if not (1 <= len(title.encode("utf-8")) <= 20):
            raise NektarException("`title` parameter must be a string.")

        about = re.sub(r"[\r\n]", "", about)
        if not (0 <= len(about.encode("utf-8")) <= 120):
            raise NektarException("`about` parameter must be a string.")

        if not isinstance(is_nsfw, bool):
            raise NektarException("`is_nsfw` must be either `True` or `False` only.")

        if not (0 <= len(description.encode("utf-8")) <= 1000):
            raise NektarException("`description` parameter must be a string.")

        if not (0 <= len(flag_text.encode("utf-8")) <= 1000):
            raise NektarException("`flag_text` parameter must be a string.")

        data = {}
        data["required_auths"] = []
        data["required_posting_auths"] = [self.username]
        data["id"] = "community"

        props = {}
        props["title"] = title
        props["about"] = about
        props["is_nsfw"] = is_nsfw
        props["description"] = description
        props["flag_text"] = flag_text

        json_data = {}
        json_data["community"] = self._community
        json_data["props"] = props
        operation = ["updateProps", json_data]
        data["json"] = json.dumps(operation).replace("'", '\\"')

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _true_or_false(synchronous, False)
        strict = _true_or_false(strict, True)
        verify_only = _true_or_false(verify_only, False)

        operations = [["custom_json", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def subscribe(
        self,
        subscribe=True,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Subscribe to the community.

        :param mute: subscribe to the community (Default value = True)
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        action = "subscribe"
        if not isinstance(subscribe, bool):
            raise NektarException("`subscribe` must be either `True` or `False` only.")
        if not subscribe:
            action = "unsubscribe"

        data = {}
        data["required_auths"] = []
        data["required_posting_auths"] = [self.username]
        data["id"] = "community"

        operation = [action, {"community": self._community}]
        data["json"] = json.dumps(operation).replace("'", '\\"')

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _true_or_false(synchronous, False)
        strict = _true_or_false(strict, True)
        verify_only = _true_or_false(verify_only, False)

        operations = [["custom_json", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def unsubscribe(self, expire=30, synchronous=False, strict=True, verify_only=False):
        """Unsubscribe to the community.

        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        return self.subscribe(False, expire, synchronous, strict, verify_only)

    def pin(
        self,
        author,
        permlink,
        pin=True,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Pin post to the top of the community homepage.

        :param author: username of author of the blog post
        :param permlink: permlink to the blog post
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        if not isinstance(author, str):
            raise NektarException("Username must be a valid Hive account username.")

        pattern = r"[\w][\w\d\-\%]{0,255}"
        if not len(re.findall(pattern, permlink)):
            raise NektarException("The permlink must be a valid url-escaped string.")

        action = "pinPost"
        if not isinstance(pin, bool):
            raise NektarException("`pin` must be either `True` or `False` only.")
        if not pin:
            action = "unpinPost"

        data = {}
        data["required_auths"] = []
        data["required_posting_auths"] = [self.username]
        data["id"] = "community"

        json_data = {}
        json_data["community"] = self._community
        json_data["account"] = author
        json_data["permlink"] = permlink
        operation = [action, json_data]
        data["json"] = json.dumps(operation).replace("'", '\\"')

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _true_or_false(synchronous, False)
        strict = _true_or_false(strict, True)
        verify_only = _true_or_false(verify_only, False)

        operations = [["custom_json", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, verify_only)

    def unpin(
        self,
        author,
        permlink,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """Unpin post from the top of the community homepage.

        :param author: username of author of the blog post
        :param permlink: permlink to the blog post
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        self.pin(author, permlink, False, expire, synchronous, strict, verify_only)

    def flag(
        self,
        author,
        permlink,
        notes,
        expire=30,
        synchronous=False,
        strict=True,
        verify_only=False,
    ):
        """It’s up to the community to define what constitutes flagging.

        :param author: username of author of the blog post
        :param permlink: permlink to the blog post
        :param notes: reason for muting
        :param expire: transaction expiration in seconds (Default value = 30)
        :param synchronous: broadcasting method (Default value = False)
        :param strict: flag to cause exception upon encountering an error (Default value = True)
        :param verify_only: flag to verify required authority or to fully complete the broadcast operation (Default value = False)

        """

        if not isinstance(author, str):
            raise NektarException("Username must be a valid Hive account username.")

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
        operation = ["flagPost", json_data]
        data["json"] = json.dumps(operation).replace("'", '\\"')

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _true_or_false(synchronous, False)
        strict = _true_or_false(strict, True)
        verify_only = _true_or_false(verify_only, False)

        operations = [["custom_json", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, verify_only)


##############################
# utils                      #
##############################


def _check_wifs(roles, operation):
    """Check if supplied WIF is in the required authority for the specific operation.

    :param roles:
    :param operation:

    """
    return len([role for role in ROLES[operation] if role in roles])


def _make_expiration(secs=30):
    """Return a UTC datetime formatted for the blockchain.

    :param secs: (Default value = 30)

    """
    timestamp = time.time() + int(secs)
    return datetime.utcfromtimestamp(timestamp).strftime(DATETIME_FORMAT)


def _within_range(value, minimum, maximum, fallback=None):
    """Check if input is within the range, otherwise return fallback.

    :param value: value to be tested
    :param minimum: minimum value of the range
    :param maximum: maximum value of the range
    :param fallback: (Default value = None)

    """
    if not (minimum <= int(value) <= maximum):
        if fallback is not None:
            raise NektarException(f"Value must be within {minimum} to {maximum} only.")
        return fallback
    return value


def _true_or_false(value, fallback):
    """Check if input is boolean, otherwise return fallback.

    :param value: value to be tested
    :param fallback: default value if failing

    """
    if isinstance(value, bool):
        return value
    return fallback
