# -*- coding: utf-8 -*-
"""
    nektar.nektar
    ~~~~~~~~~

    Interact with Hive API in Python.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import json
import math
import struct
from binascii import hexlify, unhexlify

from .appbase import AppBase
from .constants import (
    NEKTAR_VERSION,
    BLOCKCHAIN_OPERATIONS,
    ASSETS,
    ROLES,
    DATETIME_FORMAT,
    RE_USERNAME,
    RE_SNAKE_CASE,
    RE_COMMUNITY,
    RE_NEWLINES,
    RE_PERMLINK,
    RE_WORDS,
    RE_IMAGES,
)
from .utils import (
    check_wifs,
    make_expiration,
    valid_string,
    greater_than,
    within_range,
    is_boolean,
)

class Nektar:
    """Nektar base class.
    ~~~~~~~~~

    Parameters
    ----------
    username :
        a valid Hive account username
    wifs :
        a dictionary of roles and their equivalent WIFs (Default is None)
    app :
        the name of the app built with nektar (Default is None)
    version :
        the version `x.y.x` of the app built with nektar (Default is None)
    timeout :
        seconds before the request is dropped (Default is 10)
    retries :
        times the request retries if errors are encountered (Default is 3)
    warning :
        display warning messages (Default is False)

    Returns
    -------

    """

    def __init__(
        self,
        username,
        wifs=None,
        nodes=None,
        chain_id=None,
        app=None,
        version=None,
        timeout=10,
        retries=3,
        warning=False,
    ):
        self.appbase = AppBase(
            nodes=nodes,
            chain_id=chain_id,
            timeout=timeout,
            retries=retries,
            warning=warning,
        )
        self.roles = []
        self.set_username(username, wifs)

        self.account = None
        self.refresh()

        # lazy mode
        self.config = None

    ##################################################
    # wrapped methods                                #
    ##################################################
    def set_username(self, username, wifs=None):
        """Dynamically update the username and WIFs of the instance.

        Parameters
        ----------
        username :
            a valid Hive account username
        wifs :
            a dictionary of roles and their equivalent WIFs (Default is None)
        """

        if not isinstance(username, str):
            raise TypeError("`username` must be a valid Hive account username.")
        self.username = username
        if wifs is not None:
            if not isinstance(wifs, dict):
                raise TypeError("`wifs` must be a valid WIF dictionary.")
            self.appbase.append_wif(wifs)
            self.roles = list(self.appbase.wifs.keys())

    def refresh(self):
        """Get a more recent version of the account data."""
        data = self.appbase.condenser().get_accounts([[self.username]])
        if data:
            self.account = data[0]

    def get_config(self, field=None, fallback=None):
        """Returns information about compile-time constants.
        https://developers.hive.io/apidefinitions/#condenser_api.get_config
        https://developers.hive.io/tutorials-recipes/understanding-configuration-values.html

        Returns
        -------
        dict:
            A dictionary blockchain configurations.
        """

        config = self.appbase.condenser().get_config([])
        if field is None:
            return config
        return config.get(field, fallback)

    def resource_credits(self, account=None):
        """Get the current resource credits of an account.

        Parameters
        ----------
        account :
            a valid Hive account username, default = initizalized account (Default is None)

        Returns
        -------

        """

        params = {}
        if account is None:
            account = self.username
        if not isinstance(account, str):
            raise TypeError("`account` must be a string.")
        if not len(RE_USERNAME.findall(account)):
            raise ValueError("`account` must be a string of length 3 - 16.")
        params["accounts"] = [account]

        data = self.appbase.rc().find_rc_accounts(params)["rc_accounts"]
        if not data:
            return {}
        return data[0]

    def manabar(self, account=None):
        """Returns the current manabar precentage.

        Parameters
        ----------
        account :
            a valid Hive account username, default = initizalized account (Default is None)

        Returns
        -------

        """

        data = self.resource_credits(account)
        return (int(data["rc_manabar"]["current_mana"]) / int(data["max_rc"])) * 100

    def reputation(self, account=None, score=True):
        """Returns the current manabar precentage.

        Parameters
        ----------
        account :
            a valid Hive account username, default = initizalized account (Default is None)
        score :
             (Default is True)

        Returns
        -------

        """
        value = int(self.account["reputation"])
        if account:
            data = self.appbase.condenser().get_accounts([[account]])
            if not data:
                raise ValueError("`account` must be a valid Hive account username.")
            value = int(data[0]["reputation"])
        if not score:
            return value
        result = ((math.log10(abs(value)) - 9) * 9) + 25
        if value < 0:
            return -result
        return result

    def config(self, field=None, fallback=None):
        """Get low-level blockchain constants.

        Parameters
        ----------
        field :
            configuration field to get (Default is None)
        fallback :
            a fallback value if field is not found (Default is None)

        Returns
        -------

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

        Parameters
        ----------
        api :
            the API to access the global properties (Default is "condenser")

        Returns
        -------

        """
        ## use database_api
        return self.appbase.api(api).get_dynamic_global_properties({})

    def get_previous_block(self, head_block_number):
        """Get the previous block.

        Parameters
        ----------
        head_block_number :
            value must be dynamically taken from the global properties.

        Returns
        -------

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

    def verify_authority(self, transaction, mock=False):
        """Returns true if the transaction has all of the required signatures.

        Parameters
        ----------
        transaction :
            a valid transaction data
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """
        return self.appbase.condenser().verify_authority(transaction, strict=False, mock=mock)

    def _broadcast(self, transaction, synchronous=False, strict=True, mock=False):
        """Processes the transaction for broadcasting into the blockchain.

        Parameters
        ----------
        transaction :
            the formatted transaction based on the API method
        synchronous : bool, optional
            broadcasting     method (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """
        method = "condenser_api.broadcast_transaction"
        if synchronous:
            method = "condenser_api.broadcast_transaction_synchronous"
            result = self.appbase.broadcast(method, transaction, strict, mock)
            if result:
                return result
        return self.appbase.broadcast(method, transaction, strict, mock)

    def custom_json(
        self,
        id_,
        jdata,
        required_auths=[],
        required_posting_auths=[],
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Provides a generic way to add higher level protocols.

        Parameters
        ----------
        id_ :
            a valid string in a lowercase and (snake_case or kebab-case) format
        jdata :
            any valid JSON data
        required_auths :
            list of usernames required to sign with private keys (Default is [])
        required_posting_auths :
            list of usernames required to sign with a `posting` private key (Default is [])
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        data = {}
        role = "posting"  # initial required role

        if not isinstance(required_auths, list):
            raise TypeError("The `required_auths` requires a list of valid usernames.")
        data["required_auths"] = required_auths

        # if required auths is not empty, include owner,
        # active and posting roles
        if len(required_auths):
            role = "custom_json"
        if not check_wifs(self.roles, role):
            raise ValueError(
                "The `custom_json` operation requires "
                "one of the following private keys: " + ", ".join(ROLES[role])
            )

        if not isinstance(required_posting_auths, list):
            raise TypeError(
                "The `required_posting_auths` requires a list of valid usernames."
            )
        data["required_posting_auths"] = required_posting_auths

        if len(RE_SNAKE_CASE.findall(id_)):
            raise ValueError(
                "Custom JSON id must be a valid string preferrably in lowercase and (snake_case or kebab-case) format."
            )
        data["id"] = id_

        if not isinstance(jdata, (list, dict)):
            raise TypeError("Custom JSON must be in dictionary format.")
        data["json"] = json.dumps(jdata).replace("'", '\\"')

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        within_range(expire, 5, 120)
        expiration = make_expiration(expire)
        is_boolean(synchronous)

        operations = [["custom_json", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous)

    def memo(
        self,
        receiver,
        amount,
        asset,
        message="",
        to=None,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Transfers asset from one account to another, precision is auto-adjusted based on the specified asset.

        Parameters
        ----------
        receiver :
            a valid Hive account username
        amount :
            any positive value
        asset :
            asset type to send, `HBD` or `HIVE` only
        message :
            any UTF-8 string up to 2048 bytes only (Default is "")
        to :
            transfer to `None`, `savings`, or `vesting` (Default = None)
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        asset = asset.upper()
        if asset not in ("HBD", "HIVE"):
            raise ValueError("Memo only accepts transfer of HBD and HIVE assets.")

        operations = [["transfer", {}]]
        if to is not None:
            if to not in ("savings", "vesting"):
                raise ValueError(
                    "Value of `to` must be `None`, `savings`, or `vesting` only."
                )
            if to == "vesting" and asset != "HIVE":
                raise ValueError(
                    "Transfer to vesting only accepts transfer of HIVE asset only."
                )
            operations[0][0] = f"transfer_to_{to}"

        data = {}
        data["from"] = self.username
        if not isinstance(receiver, str):
            raise ValueError("Receiver must be a valid Hive account user.")
        if to is None and (self.username == receiver):
            raise ValueError("Receiver must be unique from the sender.")
        data["to"] = receiver

        if not isinstance(amount, (int, float)):
            raise TypeError("Amount must be a positive numeric value.")
        if amount < 0.001:
            raise TypeError("Amount must be a positive numeric value.")

        precision = ASSETS[asset]["precision"]
        whole, fraction = str(float(amount)).split(".")
        fraction = fraction.ljust(precision, "0")[:precision]
        data["amount"] = f"{whole}.{fraction} {asset}"

        if to != "vesting":
            if not isinstance(message, str):
                raise TypeError("Memo message must be a UTF-8 string.")
            if not (len(message.encode("utf-8")) <= 2048):
                raise ValueError("Memo message must be not more than 2048 bytes.")
            data["memo"] = message
        operations[0][1] = data

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        within_range(expire, 5, 120)
        expiration = make_expiration(expire)
        is_boolean(synchronous)
        is_boolean(strict)
        is_boolean(mock)

        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }

        return self._broadcast(transaction, synchronous, strict, mock)

    def transfer_to_savings(
        self,
        receiver,
        amount,
        asset,
        message="",
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """For time locked savings accounts.

        Parameters
        ----------
        receiver :
            a valid Hive account username
        amount :
            any positive value
        asset :
            asset type to send, `HBD` or `HIVE` only
        message :
            any UTF-8 string up to 2048 bytes only (Default is "")
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        return self.memo(
            receiver,
            amount,
            asset,
            message,
            to="savings",
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            mock=mock,
        )

    def transfer_to_vesting(
        self,
        receiver,
        amount,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """For time locked savings accounts.

        Parameters
        ----------
        receiver :
            a valid Hive account username
        amount :
            any positive value
        message :
            any UTF-8 string up to 2048 bytes only
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        asset = "HIVE"
        return self.memo(
            receiver,
            amount,
            asset,
            to="vesting",
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            mock=mock,
        )

class Waggle(Nektar):
    """Methods to interact with the Hive Blockchain.
    ~~~~~~~~~

    Parameters
    ----------
    username :
        a valid Hive account username
    wif :
        the WIF or private key (Default is None)
    role :
        the equivalent authority of the WIF (Default is None)
    wifs :
        a dictionary of roles and their equivalent WIFs (Default is None)
    app :
        the name of the app built with nektar (Default is None)
    version :
        the version `x.y.x` of the app built with nektar (Default is None)
    timeout :
        seconds before the request is dropped (Default is 10)
    retries :
        times the request retries if errors are encountered (Default is 3)
    warning :
        display warning messages (Default is False)

    Returns
    -------

    """

    def __init__(
        self,
        username,
        wifs=None,
        nodes=None,
        chain_id=None,
        app=None,
        version=None,
        timeout=10,
        retries=3,
        warning=False,
    ):
        self.appbase = AppBase(
            nodes=nodes,
            chain_id=chain_id,
            timeout=timeout,
            retries=retries,
            warning=warning,
        )
        self.set_username(username, wifs)

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

        Parameters
        ----------
        last :
            last known community name `hive-*`, paging mechanism (Default is None)
        sort :
            maximum limit of communities to list (Default is "rank")
        limit :
            sort by `rank`, `new`, or `subs` (Default is 100)
        query :
            additional filter keywords for search (Default is None)

        Returns
        -------

        """

        params = {}
        params["observer"] = self.username
        params["sort"] = "rank"
        if sort in ("new", "subs"):
            params["sort"] = sort
        if isinstance(last, str):
            params["query"] = query

        # custom limits by nektar, hive api limit: 100
        within_range(limit, 1, 10000)
        crawls = limit // 100
        params["limit"] = limit
        if crawls > 0:
            params["limit"] = 100

        if isinstance(last, str):
            if len(RE_COMMUNITY.findall(last)):
                params["last"] = last

        results = []
        for _ in range(crawls):
            result = self.appbase.bridge().list_communities(params)
            results.extend(result)
            if len(result) < 100:
                break
            if len(results) >= limit:
                break
            params["last"] = results[-1]["name"]
        return results[:limit]

    def subscribers(self, community, last=None, limit=100):
        """Gets a list of subscribers for a given community.

        Parameters
        ----------
        community :
            community name `hive-*`
        last :
            last known subscriber username, paging mechanism (Default is None)
        limit :
            maximum limit of subscribers to list (Default is 100)

        Returns
        -------

        """

        params = {}

        params["community"] = community
        if isinstance(community, str):
            if not len(RE_COMMUNITY.findall(community)):
                raise ValueError(f"Community name '{community}' format is unsupported.")

        # custom limits by nektar, hive api limit: 100
        within_range(limit, 1, 10000)
        crawls = limit // 100
        params["limit"] = limit
        if crawls > 0:
            params["limit"] = 100

        if isinstance(last, str):
            if len(RE_USERNAME.findall(last)):
                params["last"] = last

        results = []
        for _ in range(crawls):
            result = self.appbase.bridge().list_subscribers(params)
            results.extend(result)
            if len(result) < 100:
                break
            if len(results) >= limit:
                break
            params["last"] = results[-1][0]
        return results[:limit]

    def accounts(self, start=None, limit=100):
        """Looks up accounts starting with name.

        Parameters
        ----------
        start :
            starting part of username to search (Default is None)
        limit :
            maximum limit of accounts to list (Default is 100)

        Returns
        -------

        """

        params = ["", 1]

        # custom limits by nektar, hive api limit: 1000
        within_range(limit, 1, 10000)
        crawls = limit // 100
        params[1] = limit
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
                if len(results) >= limit:
                    return results[:limit]
            if not len(start):
                break
        return results[:limit]

    def followers(self, account=None, start=None, ignore=False, limit=1000):
        """Looks up accounts starting with name.

        Parameters
        ----------
        account :
            a valid Hive account username, default = username (Default is None)
        start :
            account to start from, paging mechanism (Default is None)
        ignore :
            show all muted accounts if True (Default is False)
        limit :
            maximum limit of accounts to list (Default is 1000)

        Returns
        -------

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
        within_range(limit, 1, 10000)
        crawls = limit // 100
        params[3] = limit
        if crawls > 0:
            params[3] = 1000

        results = []
        for _ in range(crawls):
            result = self.appbase.condenser().get_followers(params)
            for item in result:
                results.append(item["follower"])
            if len(result) < 1000:
                break
            if len(results) >= limit:
                break
            params[1] = results[-1]["follower"]
        return results[:limit]

    def history(self, account=None, start=-1, limit=1000, low=None, high=None):
        """Get a list of account history.

        Parameters
        ----------
        account :
            any valid Hive account username, default = initialized username (Default is None)
        start :
            starting range, or -1 for reverse history (Default is -1)
        limit :
            upperbound limit 1-1000 (Default is 1000)
        low :
            operation id (Default is None)
        high :
            operation id (Default is None)

        Returns
        -------
        list:
        """

        if account is None:
            account = self.username

        greater_than(start, -2)
        params = [self.username, start, limit]
        if isinstance(account, str):
            params[0] = account
        if isinstance(low, int):
            params.append(int("1".ljust(low + 1, "0"), 2))
        if isinstance(high, int):
            params.append(int("1".ljust(0 + 1, "0"), 2))
            params.append(int("1".ljust(high + 1, "0"), 2))
        return self.appbase.condenser().get_account_history(params)

    def delegations(self, account=None, active=False, start=1000, inward=True):
        """Get all account delegators/delegatees and other related information.

        Parameters
        ----------
        account :
            any valid Hive account username, default = initialized username (Default is None)
        active :
            include all changes in delegations if false (Default is False)
        start :
            initial starting transaction (Default is 1000)
        inward :
            inward delegations to the specified account (Default is True)

        Returns
        -------
        dict:
        """

        params = [self.username, -1, 1000]
        if isinstance(account, str):
            params[0] = account
        # delegate_vesting_shares_operation
        params.append(int("1".ljust(40 + 1, "0"), 2))
        greater_than(start, 0)
        is_boolean(inward)
            

        results = {}
        action = ("delegator", "delegatee")[(not inward)]
        while params[1] >= -1:
            try:
                result = self.appbase.condenser().get_account_history(params)
            except:
                params[1] -= 1000
                continue
            for item in result:
                delegation = item[1]["op"][1]
                name = delegation[action]
                if name == self.username:
                    continue
                if name not in results:
                    results[name] = {}
                results[name][item[1]["timestamp"]] = float(
                    delegation["vesting_shares"].split(" ")[0]
                )
            params[1] = ((result[-1][0] // 1000) * 1000)

        if not active:
            return results

        active_delegations = {}
        for name, data in results.items():
            recent = max(data.keys())
            if not data[recent]:
                continue
            active_delegations[name] = data[recent]
        return active_delegations

    def delegators(self, account=None, active=False, start=1000):
        """Get all account delegators and other related information.

        Parameters
        ----------
        account :
            any valid Hive account username, default = initialized username (Default is None)
        active :
            include all changes in delegations if false (Default is False)
        start :
            initial starting transaction (Default is -1)

        Returns
        -------

        """

        return self.delegations(account=account, active=active, start=start)

    def delegatees(self, account=None, active=False, start=1000):
        """Get all account delegatees and other related information.

        Parameters
        ----------
        account :
            any valid Hive account username, default = initialized username (Default is None)
        active :
            include all changes in delegations if false (Default is False)
        start :
            initial starting transaction (Default is -1)

        Returns
        -------

        """

        return self.delegations(
            account=account, active=active, start=start, inward=False
        )

    def posts(self, tag=None, sort="created", paidout=None, limit=100):
        """Get ranked posts based on tag.

        Parameters
        ----------
        tag :
            any valid tags (Default is None)
        sort :
            sort by `created`, `trending`, `hot`, `promoted`, `payout`, `payout_comments`, or `muted` (Default is "created")
        paidout :
            return new (False), paidout (True), all (None) (Default is None)
        limit :
            maximum limit of blogs (Default is 100)

        Returns
        -------

        """

        params = {}
        params["tag"] = ""
        if isinstance(tag, str):
            params["tag"] = tag
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
        within_range(limit, 1, 1000)
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

        Parameters
        ----------
        account :
            any valid account, default = set username (Default is None)
        sort :
            sort by `blog`, `feed`, `post`, `replies`, or `payout` (Default is "posts")
        paidout :
            filter for all or paid out posts (Default is None)
        limit :
            maximum limit of posts (Default is 20)

        Returns
        -------

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
        within_range(limit, 1, 100)
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
        """Get the current data of a post, if not found returns empty dictionary, using the bridge API.

        Parameters
        ----------
        author :
            username of author of the blog post being accessed
        permlink :
            permlink to the blog post being accessed
        retries :
            number of times to check the existence of the post, must be between 1-5 (Default is 1)

        Returns
        -------

        """

        params = {}
        if not isinstance(author, str):
            raise TypeError("Author must be a string.")
        if not len(RE_USERNAME.findall(author)):
            raise ValueError("author must be a string of length 3 - 16.")
        params["author"] = author

        if not len(RE_PERMLINK.findall(permlink)):
            raise ValueError("permlink must be a valid url-escaped string.")
        params["permlink"] = permlink
        params["observer"] = self.username

        if not (1 <= int(retries) <= 5):
            raise ValueError("Retries must be between 1 to 5 times.")
        strict = retries == 1

        for _ in range(retries):
            data = self.appbase.bridge().get_post(params, strict=strict)
            if len(data):
                return data
        return {}

    def get_content(self, author, permlink, retries=1):
        """Returns the content (post or comment), using the condenser API.

        Parameters
        ----------
        author :
            username of author of the blog post being accessed
        permlink :
            permlink to the blog post being accessed
        retries :
            number of times to check the existence of the post, must be between 1-5 (Default is 1)

        Returns
        -------

        """

        params = ["", ""]
        if not isinstance(author, str):
            raise TypeError("Author must be a string.")

        if not len(RE_USERNAME.findall(author)):
            raise ValueError("author must be a string of length 3 - 16.")
        params[0] = author

        if not len(RE_PERMLINK.findall(permlink)):
            raise ValueError("permlink must be a valid url-escaped string.")
        params[1] = permlink

        if not (1 <= int(retries) <= 5):
            raise ValueError("Retries must be between 1 to 5 times.")
        strict = retries == 1

        for _ in range(retries):
            data = self.appbase.condenser().get_content(params, strict=strict)
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
        mock=False,
    ):
        """Broadcast a new post to the blockchain

        Parameters
        ----------
        title :
            a human readable title of the post being submitted
        body :
            body of the post being submitted
        description :
            Default is None)
        tags :
            a space separated list of tags (Default is None)
        community :
            the community to post e.g. `hive-*` (Default is None)
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        if not check_wifs(self.roles, "comment"):
            raise ValueError(
                "The `comment` operation requires"
                "one of the following private keys:" + ", ".join(ROLES["comment"])
            )

        data = {}
        data["author"] = self.username

        title = RE_NEWLINES.sub("", title)
        if not (1 <= len(title.encode("utf-8")) <= 256):
            raise ValueError("Title must be within 1 to 256 bytes.")
        data["title"] = title

        if not isinstance(body, str):
            raise TypeError("Body must be a UTF-8 string.")
        if not len(body.encode("utf-8")):
            raise ValueError("Body must be at least 1 byte.")
        data["body"] = body

        permlink = RE_WORDS.sub("", title.lower())
        permlink = permlink.replace(" ", "-")
        data["permlink"] = permlink
        data["parent_author"] = ""

        ## set parent permlink as empty, or the community being posted to
        data["parent_permlink"] = ""
        if isinstance(community, str):
            if not len(RE_COMMUNITY.findall(community)):
                raise ValueError("Community name must follow `hive-*` format.")
            data["parent_permlink"] = community

        ## create blog metadata
        json_metadata = {}
        json_metadata["description"] = ""
        if isinstance(description, str):
            description = RE_NEWLINES.sub("", description)
            json_metadata["description"] = description
        ## make sure tags are valid
        ## accept more than 5, but only looks for the first five
        json_metadata["tags"] = []
        if isinstance(tags, str):
            json_metadata["tags"] = list(RE_WORDS.sub("", tags).split(" "))
        json_metadata["format"] = "markdown"
        json_metadata["app"] = f"{self.app}/{self.version}"
        json_metadata["image"] = list(RE_IMAGES.findall(body))
        data["json_metadata"] = json.dumps(json_metadata).replace("'", '\\"')

        ## initialize transaction data
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expiration = make_expiration(expire)
        within_range(expire, 5, 120)
        is_boolean(synchronous)
        is_boolean(strict)
        is_boolean(mock)

        operations = [["comment", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, mock)

    def reblog(
        self,
        author,
        permlink,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Reblog post.

        Parameters
        ----------
        author :
            username of author of the blog post  to reblog
        permlink :
            permlink to the blog post to reblog
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        if not check_wifs(self.roles, "follow"):
            raise ValueError(
                "The `follow` operation requires"
                "one of the following private keys:" + ", ".join(ROLES["follow"])
            )
        jdata = [
            "reblog",
            {"account": self.username, "author": author, "permlink": permlink},
        ]
        return self.custom_json(
            "follow",
            jdata,
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            mock=mock,
        )

    def reply(
        self,
        author,
        permlink,
        body,
        edit=True,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Broadcast a new comment to a post.

        Parameters
        ----------
        author :
            username of author of the blog post being replied to
        permlink :
            permlink to the blog post being replied to
        body :
            the content of the comment
        edit :
            edit existing comment on post (Default is True)
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        if not check_wifs(self.roles, "comment"):
            raise ValueError(
                "The `comment` operation requires"
                "one of the following private keys:" + ", ".join(ROLES["comment"])
            )

        data = {}
        data["author"] = self.username
        data["title"] = ""

        data["parent_author"] = author
        data["parent_permlink"] = permlink

        if not isinstance(body, str):
            raise TypeError("Body must be a UTF-8 string.")
        if not len(body.encode("utf-8")):
            raise ValueError("Body must be at least 1 byte.")
        data["body"] = body

        uid = ""
        is_boolean(edit)
        if not edit:
            uid = make_expiration(formatting="-%Y%m%d%H%M%S")
        data["permlink"] = f"re-{permlink}{uid}"[:255]

        ## create comment metadata
        json_metadata = {}
        json_metadata["description"] = ""
        json_metadata["format"] = "markdown"
        json_metadata["app"] = f"{self.app}/{self.version}"
        json_metadata["image"] = list(RE_IMAGES.findall(body))
        data["json_metadata"] = json.dumps(json_metadata).replace("'", '\\"')

        ## initialize transaction data
        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expiration = make_expiration(expire)
        within_range(expire, 5, 120)
        is_boolean(synchronous)
        is_boolean(strict)
        is_boolean(mock)

        operations = [["comment", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, mock)

    def replies(self, author, permlink, retries=1):
        """Returns a list of replies.

        Parameters
        ----------
        author :
            username of author of the blog post being accessed
        permlink :
            permlink to the blog post being accessed
        retries :
            number of times to check the existence of the post, must be between 1-5 (Default is 1)

        Returns
        -------

        """

        params = ["", ""]
        if not isinstance(author, str):
            raise TypeError("Author must be a string.")

        if not len(RE_USERNAME.findall(author)):
            raise ValueError("author must be a string of length 3 - 16.")
        params[0] = author

        if not len(RE_PERMLINK.findall(permlink)):
            raise ValueError("permlink must be a valid url-escaped string.")
        params[1] = permlink

        if not (1 <= int(retries) <= 5):
            raise ValueError("Retries must be between 1 to 5 times.")
        strict = retries == 1

        for _ in range(retries):
            data = self.appbase.condenser().get_content_replies(params, strict=strict)
            if len(data):
                return data
        return {}

    def reblogs(self, author, permlink, retries=1):
        """Returns a list of authors that have reblogged a post.

        Parameters
        ----------
        author :
            username of author of the blog post being accessed
        permlink :
            permlink to the blog post being accessed
        retries :
            number of times to check the existence of the post, must be between 1-5 (Default is 1)

        Returns
        -------

        """

        params = ["", ""]
        if not isinstance(author, str):
            raise TypeError("Author must be a string.")

        if not len(RE_USERNAME.findall(author)):
            raise ValueError("author must be a string of length 3 - 16.")
        params[0] = author

        if not len(RE_PERMLINK.findall(permlink)):
            raise ValueError("permlink must be a valid url-escaped string.")
        params[1] = permlink

        if not (1 <= int(retries) <= 5):
            raise ValueError("Retries must be between 1 to 5 times.")
        strict = retries == 1

        for _ in range(retries):
            data = self.appbase.condenser().get_reblogged_by(params, strict=strict)
            if len(data):
                return data
        return []

    def vote(
        self,
        author,
        permlink,
        weight=10000,
        percent=None,
        check=False,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Perform vote on a blog post or comment.

        Parameters
        ----------
        author :
            Author of the post. or comment being voted
        permlink :
            Permlink of the post or comment being voted
        weight :
            vote weight between -10000 to 10000 (Default is 10000)
        percent :
            override vote weight with percentage (Default is None)
        check :
            check if account had already voted on the post (Default is False)
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        if not check_wifs(self.roles, "vote"):
            raise ValueError(
                "The `comment` operation requires"
                "one of the following private keys:" + ", ".join(ROLES["vote"])
            )

        if not isinstance(author, str):
            raise TypeError("Author must be a string.")

        if not len(RE_USERNAME.findall(author)):
            raise ValueError("author must be a string of length 3 - 16.")

        if not len(RE_PERMLINK.findall(permlink)):
            raise ValueError("permlink must be a valid url-escaped string.")

        is_boolean(check)
        if check:
            if self.voted(author, permlink):
                return {}

        if isinstance(percent, (int, float)):
            within_range(percent, -100, 100)
            weight = 10000 * (percent / 100)

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        within_range(weight, -10000, 10000)
        within_range(expire, 5, 120)
        expiration = make_expiration(expire)
        is_boolean(synchronous)
        is_boolean(strict)
        is_boolean(mock)

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
        return self._broadcast(transaction, synchronous, strict, mock)

    def votes(self, author, permlink, retries=1):
        """Returns all votes for the given post.

        Parameters
        ----------
        author :
            username of author of the blog post being accessed
        permlink :
            permlink to the blog post being accessed
        retries :
            number of times to check the existence of the post, must be between 1-5 (Default is 1)

        Returns
        -------

        """

        params = ["", ""]
        if not isinstance(author, str):
            raise TypeError("Author must be a string.")

        if not len(RE_USERNAME.findall(author)):
            raise ValueError("author must be a string of length 3 - 16.")
        params[0] = author

        if not len(RE_PERMLINK.findall(permlink)):
            raise ValueError("permlink must be a valid url-escaped string.")
        params[1] = permlink

        if not (1 <= int(retries) <= 5):
            raise ValueError("Retries must be between 1 to 5 times.")
        strict = retries == 1

        for _ in range(retries):
            data = self.appbase.condenser().get_active_votes(params, strict=strict)
            if len(data):
                return data
        return {}

    def voted(
        self, author, permlink, expire=30, synchronous=False, strict=True, mock=False
    ):
        """

        Parameters
        ----------
        author :

        permlink :

        expire : int, optional
             (Default is 30)
        synchronous : bool, optional
             (Default is False)
        strict : bool, optional
             (Default is True)
        mock : bool, optional
             (Default is False)

        Returns
        -------

        """

        votes = self.votes(author, permlink)
        votes = len([1 for v in votes if (v.get("voter") == self.username)])
        return bool(votes)

    def power_up(
        self,
        receiver,
        amount,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """

        Parameters
        ----------
        receiver : str

        amount : optional

        expire : int, optional
             (Default is 30)
        synchronous : bool, optional
             (Default is False)
        strict : bool, optional
             (Default is True)
        mock : bool, optional
             (Default is False)

        Returns
        -------

        """

        self.transfer_to_vesting(
            receiver,
            amount,
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            mock=mock,
        )

class Swarm(Nektar):
    """Methods for admins and moderators to manage communities.
    ~~~~~~~~~

    Parameters
    ----------
    community : str
        a valid Hive community name `hive-*`
    username : str
        a valid Hive account username
    wif : str, optional
        the WIF or private key (Default is None)
    role : str, optional
        the equivalent authority of the WIF (Default is None)
    wifs : dict, optional
        a dictionary of roles and their equivalent WIFs (Default is None)
    app : str, optional
        the name of the app built with nektar (Default is None)
    version : str, optional
        the version `x.y.x` of the app built with nektar (Default is None)
    timeout : int, optional
        seconds before the request is dropped (Default is 10)
    retries : int, optional
        times the request retries if errors are encountered (Default is 3)
    warning : boo, optional
        display warning messages (Default is False)

    """

    def __init__(
        self,
        community,
        username,
        wifs=None,
        nodes=None,
        chain_id=None,
        app=None,
        version=None,
        timeout=10,
        retries=3,
        warning=False,
    ):
        self.appbase = AppBase(
            nodes=nodes,
            chain_id=chain_id,
            timeout=timeout,
            retries=retries,
            warning=warning,
        )
        self.roles = []
        self.set_username(username, wifs)
        self.account = None
        self.refresh()

        self.app = "nektar.swarm"
        if isinstance(app, str):
            self.app = app

        self.version = NEKTAR_VERSION
        if isinstance(version, str):
            self.version = version

        self._community = community
        valid_string(community, RE_COMMUNITY)
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
        mock=False,
    ):
        """Mute posts or comments with a designated note.

        Parameters
        ----------
        author :
            username of author of the blog post
        permlink :
            permlink to the blog post
        notes :
            reason for muting
        mute :
            mute author (Default is True)
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        valid_string(author)
        valid_string(permlink, RE_PERMLINK)
        valid_string(notes)

        operation = ["mutePost", {}]
        is_boolean(mute)
        if not mute:
            operation[0] = "unmutePost"
        operation[1] = {
            "community": self._community,
            "account": author,
            "permlink": permlink,
            "notes": notes,
        }

        return self.custom_json(
            id_="community",
            jdata=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            mock=mock,
        )

    def unmute(
        self,
        author,
        permlink,
        notes,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Unmute posts or comments with a designated note.

        Parameters
        ----------
        author :
            username of author of the blog post
        permlink :
            permlink to the blog post
        notes :
            reason for unmuting
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """
        return self.mute(author, permlink, notes, False, expire, strict, mock)

    def mark_spam(
        self,
        author,
        permlink,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Muting post but noted as `spam` as standardized label for spams.

        Parameters
        ----------
        author :
            a valid blockchain account username
        permlink :
            actual permlink to the specified author
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """
        self.mute(author, permlink, "spam", True, expire, strict, mock)

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
        mock=False,
    ):
        """Update community properties.

        Parameters
        ----------
        title :
            username of author of the blog post
        about :
            permlink to the blog post
        is_nsfw :
            not suitable or safe for work
        description :
            mute author (Default is True)
        flag_text :
            mute author (Default is True)
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        title = RE_NEWLINES.sub("", title)
        if not (1 <= len(title.encode("utf-8")) <= 20):
            raise ValueError("`title` parameter must be a string of length 1 to 20.")

        about = RE_NEWLINES.sub("", about)
        if not (0 <= len(about.encode("utf-8")) <= 120):
            raise ValueError("`about` parameter must be a string of length 0 to 120.")

        if not isinstance(is_nsfw, bool):
            raise TypeError("`is_nsfw` must be either `True` or `False` only.")

        if not (0 <= len(description.encode("utf-8")) <= 1000):
            raise ValueError(
                "`description` parameter must be a string of length 0 to 1000."
            )

        if not (0 <= len(flag_text.encode("utf-8")) <= 1000):
            raise ValueError(
                "`flag_text` parameter must be a string of length 0 to 1000."
            )

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

        return self.custom_json(
            id_="community",
            jdata=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            mock=mock,
        )

    def subscribe(
        self,
        subscribe=True,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Subscribe to the community.

        Parameters
        ----------
        subscribe : bool, optional
            Subscribe to the community (Default is True)
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        operation = ["subscribe", {"community": self._community}]
        is_boolean(subscribe)
        if not subscribe:
            operation[0] = "unsubscribe"

        return self.custom_json(
            id_="community",
            jdata=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            mock=mock,
        )

    def unsubscribe(self, expire=30, synchronous=False, strict=True, mock=False):
        """Unsubscribe to the community.

        Parameters
        ----------
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        return self.subscribe(False, expire, synchronous, strict, mock)

    def pin(
        self,
        author,
        permlink,
        pin=True,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Pin post to the top of the community homepage.

        Parameters
        ----------
        author :
            username of author of the blog post
        permlink :
            permlink to the blog post
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)
        pin :
             (Default is True)

        Returns
        -------

        """

        valid_string(author)
        valid_string(permlink, RE_PERMLINK)
        is_boolean(pin)
        action = "pinPost"
        if not pin:
            action = "unpinPost"

        data = {}
        data["community"] = self._community
        data["account"] = author
        data["permlink"] = permlink
        operation = [action, data]

        return self.custom_json(
            id_="community",
            jdata=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            mock=mock,
        )

    def unpin(
        self,
        author,
        permlink,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """Unpin post from the top of the community homepage.

        Parameters
        ----------
        author :
            username of author of the blog post
        permlink :
            permlink to the blog post
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        self.pin(author, permlink, False, expire, synchronous, strict, mock)

    def flag(
        self,
        author,
        permlink,
        notes,
        expire=30,
        synchronous=False,
        strict=True,
        mock=False,
    ):
        """It’s up to the community to define what constitutes flagging.

        Parameters
        ----------
        author :
            username of author of the blog post
        permlink :
            permlink to the blog post
        notes :
            reason for muting
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        mock : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        valid_string(author)
        valid_string(permlink, RE_PERMLINK)
        valid_string(notes)

        data = {}
        data["community"] = self._community
        data["account"] = author
        data["permlink"] = permlink
        data["notes"] = notes
        operation = ["flagPost", data]

        return self.custom_json(
            id_="community",
            jdata=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            mock=mock,
        )
