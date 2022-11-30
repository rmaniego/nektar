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
    RE_PERMLINK,
    RE_COMMUNITY,
    RE_DATETIME
)
from .exceptions import NektarException


class Nektar:
    """Nektar base class.
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
        wif=None,
        role=None,
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
        self.set_username(username, wif, role, wifs)

        self.account = None
        self.refresh()

        # lazy mode
        self.config = None

    ##################################################
    # raw condenser api methods                      #
    ##################################################
    def get_account_count(self):
        """Returns the number of accounts.
        https://developers.hive.io/apidefinitions/#condenser_api.get_account_count

        Returns
        -------
        int:
            The total number of blockchain accounts to date.
        """

        return self.appbase.condenser().get_account_count([])

    def get_account_history(self, account, start, limit, low=None, high=None):
        """Returns a history of all operations for a given account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_account_history https://gitlab.syncad.com/hive/hive/-/blob/master/libraries/protocol/include/hive/protocol/operations.hpp

        Parameters
        ----------
        account : str
            any valid Hive account username
        start : int
            starting range, or -1 for reverse history
        limit : int
            upperbound limit 1-1000
        low : int, optional
            operation id (Default is None)
        high : int, optional
            operation id (Default is None)

        Returns
        -------
        list:
            List of all transactions from start-limit to limit.
        """

        params = [self.username]
        if isinstance(account, str):
            params[0] = account
        params.append(_greater_than(start, -1))
        params.append(_within_range(limit, 1, 1000))

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

    def get_account_reputations(self, start, limit):
        """Returns a list of account reputations.
        https://developers.hive.io/apidefinitions/#condenser_api.get_account_reputations

        Parameters
        ----------
        start : str
            any valid Hive account username
        limit : int
            limit 1-1000

        Returns
        -------
        list:
            List of all account reputation.
        """

        _valid_string(start)
        _within_range(limit, 1, 1000)
        params = [start, int(limit)]
        return self.appbase.condenser().get_account_reputations(params)

    def get_accounts(self, accounts, delayed_votes_active):
        """Returns accounts, queried by name.
        https://developers.hive.io/apidefinitions/#condenser_api.get_accounts

        Parameters
        ----------
        accounts : list
            a list of any valid Hive account usernames
        delayed_votes_active : bool
            delayed votes hidden

        Returns
        -------
        list:
            List of all accounts and its information.
        """

        params = [accounts, delayed_votes_active]
        if not isinstance(accounts, list):
            raise NektarException("`accounts` must be a list of strings.")
        _is_boolean("delayed_votes_active", delayed_votes_active)

        return self.appbase.condenser().get_accounts(params)

    def get_active_votes(self, author, permlink):
        """Returns all votes for the given post.
        https://developers.hive.io/apidefinitions/#condenser_api.get_active_votes

        Parameters
        ----------
        author : list
            Author of the post.
        permlink : str
            Permlink of the post

        Returns
        -------
        list:
            List of all active votes on a post.
        """

        _valid_string(author)
        _valid_string(permlink)
        params = [author, permlink]
        return self.appbase.condenser().get_active_votes(params)

    def get_active_witnesses(self):
        """Returns the list of active witnesses.
        https://developers.hive.io/apidefinitions/#condenser_api.get_active_witnesses

        Returns
        -------
        list:
            List of active witnesses.
        """

        return self.appbase.condenser().get_active_witnesses([])

    def get_block(self, block_num):
        """Returns a block.
        https://developers.hive.io/apidefinitions/#condenser_api.get_block

        Parameters
        ----------
        block_num : int
            block number

        Returns
        -------
        dict:
            Dictionary of block information.
        """

        _greater_than(block_num, 0)
        return self.appbase.condenser().get_block([int(block_num)])

    def get_block_header(self, block_num):
        """Returns a block header.
        https://developers.hive.io/apidefinitions/#condenser_api.get_block_header

        Parameters
        ----------
        block_num : int
            block number

        Returns
        -------
        dict:
            Dictionary of block header information.
        """

        _greater_than(block_num, 0)
        return self.appbase.condenser().get_block_header([block_num])

    def get_blog(self, account, start, limit):
        """Returns the list of blog entries for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_blog

        Parameters
        ----------
        account : str
            any valid Hive account username
        start : int
            starting entry id
        limit : int
            maximum number of results 1-500

        Returns
        -------
        list:
            List of blogs and its information
        """

        _valid_string(account)
        start = _greater_than(start, 0)
        limit = _within_range(limit, 1, 500)
        params = [account, start, limit]
        return self.appbase.condenser().get_blog(params)

    def get_blog_authors(self, account):
        """Returns a list of authors that have had their content reblogged on a given blog account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_blog_authors

        Issue
        ---------
             Assert Exception:false: Supported by hivemind

        Parameters
        ----------
        account : str
            any valid Hive account username

        Returns
        -------
        dict:
            Dictionary of block header information.
        """

        _valid_string(account)
        return self.appbase.condenser().get_blog_authors([account])

    def get_blog_entries(self, account, start, limit):
        """Returns a list of blog entries for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_blog_entries

        Parameters
        ----------
        account : str
            any valid Hive account username
        start : int
            starting entry id
        limit : int
            maximum number of results 1-500

        Returns
        -------
        list:
            List of blogs and its basic information without the full blog data.
        """

        _valid_string(account)
        start = _greater_than(start, 0)
        limit = _within_range(limit, 1, 500)
        params = [account, start, limit]
        return self.appbase.condenser().get_blog_entries(params)

    def get_chain_properties(self):
        """Returns the chain properties.
        https://developers.hive.io/apidefinitions/#condenser_api.get_chain_properties

        Returns
        -------
        dict:
            Dictionary of chain properties and its data.
        """

        return self.appbase.condenser().get_chain_properties([])

    def get_comment_discussions_by_payout(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions based on payout.
        https://developers.hive.io/apidefinitions/#condenser_api.get_comment_discussions_by_payout

        Parameters
        ----------
        tag : str
            any valid string
        limit : int
            maximum number of results
        filter_tags : list, None
            list of valid tags
        select_authors : list, None
            list of valid account username
        select_tags : list, None
            list of valid tags
        truncate : int, optional
            truncate body (0, 1)

        Returns
        -------
        list:
            List of discussions.
        """

        data = {"tag": tag, "limit": limit, "truncate_body": truncate}
        _valid_string(tag)
        _within_range(limit, 1, 500)
        if not isinstance(filter_tags, list):
            if filter_tags is not None:
                raise NektarException("`filter_tags` must be a list.")
            filter_tags = []
        if filter_tags:
            data["filter_tags"] = filter_tags
        if not isinstance(select_authors, list):
            if select_authors is not None:
                raise NektarException("`select_authors` must be a list.")
            select_authors = []
        if select_authors:
            data["select_authors"] = select_authors
        if not isinstance(select_tags, list):
            if select_tags is not None:
                raise NektarException("`select_tags` must be a list.")
            select_tags = []
        if select_tags:
            data["select_tags"] = select_tags
        if int(truncate) not in (0, 1):
            raise NektarException("`truncate` must be `0` or `1`.")
        return self.appbase.condenser().get_comment_discussions_by_payout([data])

    def get_config(self):
        """Returns information about compile-time constants.
        https://developers.hive.io/apidefinitions/#condenser_api.get_config
        https://developers.hive.io/tutorials-recipes/understanding-configuration-values.html

        Parameters
        ----------
        pid : int
            proposal.id, not proposal.proposal_id


        Returns
        -------
        dict:
            A dictionary blockchain configurations.
        """

        return self.appbase.condenser().get_config([])

    def get_content(self, author, permlink):
        """Returns the content of a post or comment.
        https://developers.hive.io/apidefinitions/#condenser_api.get_content

        Parameters
        ----------
        author : list
            Author of the post.
        permlink : str
            Permlink of the post

        Returns
        -------
        dict:
            All data associated to a post or comment.
        """
        
        _valid_string(author)
        _valid_string(permlink)
        params = [author, permlink]
        return self.appbase.condenser().get_content(params)

    def get_content_replies(self, author, permlink):
        """Returns a list of replies.
        https://developers.hive.io/apidefinitions/#condenser_api.get_content_replies

        Parameters
        ----------
        author : list
            Author of the post.
        permlink : str
            Permlink of the post

        Returns
        -------
        list:
            List of replies to a post or comment.
        """

        _valid_string(author)
        _valid_string(permlink)
        params = [author, permlink]
        return self.appbase.condenser().get_content_replies(params)

    def get_conversion_requests(self, cid):
        """Returns a list of conversion request.
        https://developers.hive.io/apidefinitions/#condenser_api.get_conversion_requests

        Parameters
        ----------
        cid : int
            conversion request id

        Returns
        -------
        list:
            List of conversion requests.
        """

        _greater_than(cid, 0)
        return self.appbase.condenser().get_conversion_requests([cid])

    def get_current_median_history_price(self):
        """Returns the median history price.
        https://developers.hive.io/apidefinitions/#condenser_api.get_current_median_history_price

        Returns
        -------
        dict:
            Data on the median history price.
        """

        return self.appbase.condenser().get_current_median_history_price([])

    def get_discussions_by_active(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions based on active.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_active

        Parameters
        ----------
        tag : str
            any valid string
        limit : int
            maximum number of results
        filter_tags : list, None
            list of valid tags
        select_authors : list, None
            list of valid account username
        select_tags : list, None
            list of valid tags
        truncate : int, optional
            truncate body (0, 1)

        Returns
        -------
        list:
            List of discussions.
        """

        data = {"tag": tag, "limit": limit, "truncate_body": truncate}
        _valid_string(tag)
        _within_range(limit, 1, 500)
        if not isinstance(filter_tags, list):
            if filter_tags is not None:
                raise NektarException("`filter_tags` must be a list.")
            filter_tags = []
        if filter_tags:
            data["filter_tags"] = filter_tags
        if not isinstance(select_authors, list):
            if select_authors is not None:
                raise NektarException("`select_authors` must be a list.")
            select_authors = []
        if select_authors:
            data["select_authors"] = select_authors
        if not isinstance(select_tags, list):
            if select_tags is not None:
                raise NektarException("`select_tags` must be a list.")
            select_tags = []
        if select_tags:
            data["select_tags"] = select_tags
        if int(truncate) not in (0, 1):
            raise NektarException("`truncate` must be `0` or `1`.")
        return self.appbase.condenser().get_discussions_by_active([data])

    def get_discussions_by_author_before_date(self, author, permlink, date, limit):
        """Returns a list of discussions based on author before date.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_author_before_date

        Parameters
        ----------
        author : list
            Author of the post.
        permlink : str
            Permlink of the post
        date : str
            Date before e.g. 1970-01-01T00:00:00
        limit : int
            Maximum number of results.

        Returns
        -------
        list:
            List of posts and it corresponding data.
        """

        _valid_string(author)
        _valid_string(permlink)
        _valid_string(date, RE_DATETIME)
        _greater_than(limit, 0)
        params = [author, permlink, date, limit]
        return self.appbase.condenser().get_discussions_by_author_before_date(params)

    def get_discussions_by_blog(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions by blog.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_blog

        Parameters
        ----------
        tag : str
            any valid string
        limit : int
            maximum number of results
        filter_tags : list, None
            list of valid tags
        select_authors : list, None
            list of valid account username
        select_tags : list, None
            list of valid tags
        truncate : int, optional
            truncate body (0, 1)

        Returns
        -------
        list:
            List of discussions.
        """

        data = {"tag": tag, "limit": limit, "truncate_body": truncate}
        _valid_string(tag)
        _within_range(limit, 1, 500)
        if not isinstance(filter_tags, list):
            if filter_tags is not None:
                raise NektarException("`filter_tags` must be a list.")
            filter_tags = []
        if filter_tags:
            data["filter_tags"] = filter_tags
        if not isinstance(select_authors, list):
            if select_authors is not None:
                raise NektarException("`select_authors` must be a list.")
            select_authors = []
        if select_authors:
            data["select_authors"] = select_authors
        if not isinstance(select_tags, list):
            if select_tags is not None:
                raise NektarException("`select_tags` must be a list.")
            select_tags = []
        if select_tags:
            data["select_tags"] = select_tags
        if int(truncate) not in (0, 1):
            raise NektarException("`truncate` must be `0` or `1`.")
        return self.appbase.condenser().get_discussions_by_blog([data])

    def get_discussions_by_cashout(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions by cashout.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_cashout

        Parameters
        ----------
        tag : str
            any valid string
        limit : int
            maximum number of results
        filter_tags : list, None
            list of valid tags
        select_authors : list, None
            list of valid account username
        select_tags : list, None
            list of valid tags
        truncate : int, optional
            truncate body (0, 1)

        Returns
        -------
        list:
            List of discussions.
        """

        data = {"tag": tag, "limit": limit, "truncate_body": truncate}
        _valid_string(tag)
        _within_range(limit, 1, 500)
        if not isinstance(filter_tags, list):
            if filter_tags is not None:
                raise NektarException("`filter_tags` must be a list.")
            filter_tags = []
        if filter_tags:
            data["filter_tags"] = filter_tags
        if not isinstance(select_authors, list):
            if select_authors is not None:
                raise NektarException("`select_authors` must be a list.")
            select_authors = []
        if select_authors:
            data["select_authors"] = select_authors
        if not isinstance(select_tags, list):
            if select_tags is not None:
                raise NektarException("`select_tags` must be a list.")
            select_tags = []
        if select_tags:
            data["select_tags"] = select_tags
        if int(truncate) not in (0, 1):
            raise NektarException("`truncate` must be `0` or `1`.")
        return self.appbase.condenser().get_discussions_by_cashout([data])

    def get_discussions_by_children(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions by cashout.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_children

        Parameters
        ----------
        tag : str
            any valid string
        limit : int
            maximum number of results
        filter_tags : list, None
            list of valid tags
        select_authors : list, None
            list of valid account username
        select_tags : list, None
            list of valid tags
        truncate : int, optional
            truncate body (0, 1)

        Returns
        -------
        list:
            List of discussions.
        """

        data = {"tag": tag, "limit": limit, "truncate_body": truncate}
        _valid_string(tag)
        _within_range(limit, 1, 500)
        if not isinstance(filter_tags, list):
            if filter_tags is not None:
                raise NektarException("`filter_tags` must be a list.")
            filter_tags = []
        if filter_tags:
            data["filter_tags"] = filter_tags
        if not isinstance(select_authors, list):
            if select_authors is not None:
                raise NektarException("`select_authors` must be a list.")
            select_authors = []
        if select_authors:
            data["select_authors"] = select_authors
        if not isinstance(select_tags, list):
            if select_tags is not None:
                raise NektarException("`select_tags` must be a list.")
            select_tags = []
        if select_tags:
            data["select_tags"] = select_tags
        if int(truncate) not in (0, 1):
            raise NektarException("`truncate` must be `0` or `1`.")
        return self.appbase.condenser().get_discussions_by_children([data])

    def get_discussions_by_comments(
        self,
        author,
        permlink,
        limit,
    ):
        """Returns a list of discussions by cashout.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_comments

        Parameters
        ----------
        author : str
            Start string for author name.
        permlink : str
            Start string for permlink.
        limit : int

        Returns
        -------
        list:
            List of discussions.
        """

        _valid_string(author)
        # allow empty start permlink
        _valid_string(permlink)
        _within_range(limit, 1, 100)
        data = {"start_author": author, "start_permlink": permlink, "limit": limit}
        return self.appbase.condenser().get_discussions_by_comments([data])

    def get_discussions_by_created(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions by created
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_created

        Parameters
        ----------
        tag : str
            any valid string
        limit : int
            maximum number of results
        filter_tags : list, None
            list of valid tags
        select_authors : list, None
            list of valid account username
        select_tags : list, None
            list of valid tags
        truncate : int, optional
            truncate body (0, 1)

        Returns
        -------
        list:
            List of discussions.
        """

        data = {"tag": tag, "limit": limit, "truncate_body": truncate}
        _valid_string(tag)
        _within_range(limit, 1, 500)
        if not isinstance(filter_tags, list):
            if filter_tags is not None:
                raise NektarException("`filter_tags` must be a list.")
            filter_tags = []
        if filter_tags:
            data["filter_tags"] = filter_tags
        if not isinstance(select_authors, list):
            if select_authors is not None:
                raise NektarException("`select_authors` must be a list.")
            select_authors = []
        if select_authors:
            data["select_authors"] = select_authors
        if not isinstance(select_tags, list):
            if select_tags is not None:
                raise NektarException("`select_tags` must be a list.")
            select_tags = []
        if select_tags:
            data["select_tags"] = select_tags
        if int(truncate) not in (0, 1):
            raise NektarException("`truncate` must be `0` or `1`.")
        return self.appbase.condenser().get_discussions_by_created([data])

    def find_proposals(self, pid):
        """Finds proposals by proposal id.
        https://developers.hive.io/apidefinitions/#condenser_api.find_proposals

        Parameters
        ----------
        pid : int
            proposal.id, not proposal.proposal_id


        Returns
        -------
        dict:
            A dictionary format of the proposal data.
        """

        _greater_than(pid, 0)
        return self.appbase.condenser().find_proposals([[pid]])

    def list_proposal_votes(self, start, limit, order, direction=None, status=None):
        """Returns all proposal votes, starting with the specified voter or proposal.id.
        https://developers.hive.io/apidefinitions/#condenser_api.list_proposal_votes

        Parameters
        ----------
        start : int, str
            proposal id, or account name voting for the proposal
        limit : int
            number of votes, 0-1000
        order: str
            `by_voter_proposal` - order by proposal voter
            `by_proposal_voter` - order by proposal.id
        direction : str, None
            `ascending` or `descending`
        status : str, None
            `all`, `inactive`, `active`, `expired`, or `votable`

        Returns
        -------
        list:
            A list of proposals votes.
        """

        params = [[""], 1000, "by_voter_proposal", "ascending", "all"]

        if not isinstance(start, (str, int)):
            raise NektarException("`start` must be a voter acount name or proposal id.")
        params[0][0] = start

        params[1] = _within_range(limit, 0, 1000)
        if order not in ("by_voter_proposal", "by_proposal_voter"):
            raise NektarException("`order` is not supported.")
        params[2] = order

        if direction is not None:
            if direction not in ("ascending", "descending"):
                raise NektarException("`direction` is not supported.")
            params[3] = direction

        if status is not None:
            statuses = ("all", "inactive", "active", "expired", "votable")
            if status not in statuses:
                raise NektarException("`status` is not supported.")
            params[4] = status

        return self.appbase.condenser().list_proposal_votes(params)

    def list_proposals(self, start, limit, order, direction=None, status=None):
        """Returns all proposals, starting with the specified creator or start date.
        https://developers.hive.io/apidefinitions/#condenser_api.list_proposals

        Parameters
        ----------
        start : int, str
            `creator` - creator of the proposal
            `start_date` - start date of the proposal, e.g. "2022-11-27T00:00:00"
            `end_date` - end date of the proposal, e.g. "2022-11-27T00:00:00"
            `total_votes` - total votes of the proposal
        limit : int
            number of votes, 0-1000
        order: str
            `by_creator` - order by proposal creator
            `by_start_date` - order by proposal start date
            `by_end_date` - order by proposal end date
            `by_total_votes` - order by proposal total votes
        direction : str, None
            `ascending` or `descending`
        status : str, None
            `all`, `inactive`, `active`, `expired`, or `votable`

        Returns
        -------
        list:
            A list of proposals votes.
        """

        params = [[""], 1000, "by_creator", "ascending", "all"]

        if not isinstance(start, (str, int)):
            raise NektarException("`start` must be a voter acount name or proposal id.")
        params[0][0] = start
        params[1] = _within_range(limit, 0, 1000)

        orders = ("by_creator", "by_start_date", "by_end_date", "by_total_votes")
        if order not in orders:
            raise NektarException("`order` is not supported.")
        params[2] = order

        if direction is not None:
            if direction not in ("ascending", "descending"):
                raise NektarException("`direction` is not supported.")
            params[3] = direction

        if status is not None:
            statuses = ("all", "inactive", "active", "expired", "votable")
            if status not in statuses:
                raise NektarException("`status` is not supported.")
            params[4] = status

        return self.appbase.condenser().list_proposals(params)

    ##################################################
    # wrapped methods                                #
    ##################################################
    def set_username(self, username, wif=None, role=None, wifs=None):
        """Dynamically update the username and WIFs of the instance.

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

        Returns
        -------

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

    def verify_authority(self, transaction):
        """Returns true if the transaction has all of the required signatures.

        Parameters
        ----------
        transaction :
            a valid transaction data

        Returns
        -------

        """
        return self.appbase.condenser().verify_authority(transaction, strict=False)

    def _broadcast(self, transaction, synchronous=False, strict=True, debug=False):
        """Processes the transaction for broadcasting into the blockchain.

        Parameters
        ----------
        transaction :
            the formatted transaction based on the API method
        synchronous : bool, optional
            broadcasting     method (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """
        method = "condenser_api.broadcast_transaction"
        if synchronous:
            method = "condenser_api.broadcast_transaction_synchronous"
            result = self.appbase.broadcast(method, transaction, strict, debug)
            if result:
                return result
        return self.appbase.broadcast(method, transaction, strict, debug)

    def custom_json(
        self,
        id_,
        jdata,
        required_auths=[],
        required_posting_auths=[],
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        data = {}
        role = "posting"  # initial required role

        if not isinstance(required_auths, list):
            raise NektarException(
                "The `required_auths` requires a list of valid usernames."
            )
        data["required_auths"] = required_auths

        # if required auths is not empty, include owner,
        # active and posting roles
        if len(required_auths):
            role = "custom_json"
        if not _check_wifs(self.roles, role):
            raise NektarException(
                "The `custom_json` operation requires"
                "one of the following private keys:" + ", ".join(ROLES[role])
            )

        if not isinstance(required_posting_auths, list):
            raise NektarException(
                "The `required_posting_auths` requires a list of valid usernames."
            )
        data["required_posting_auths"] = required_posting_auths

        if len(re.findall(r"[^\w\-]+", id_)):
            raise NektarException(
                "Custom JSON id must be a valid string preferrably in lowercase and (snake_case or kebab-case) format."
            )
        data["id"] = id_

        if not isinstance(jdata, (list, dict)):
            raise NektarException("Custom JSON must be in dictionary format.")
        data["json"] = json.dumps(jdata).replace("'", '\\"')

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _is_boolean(synchronous, False)

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
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        asset = asset.upper()
        if asset not in ("HBD", "HIVE"):
            raise NektarException("Memo only accepts transfer of HBD and HIVE assets.")

        operations = [["transfer", {}]]
        if to is not None:
            if to not in ("savings", "vesting"):
                raise NektarException(
                    "Value of `to` must be `None`, `savings`, or `vesting` only."
                )
            if to == "vesting" and asset != "HIVE":
                raise NektarException(
                    "Transfer to vesting only accepts transfer of HIVE asset only."
                )
            operations[0][0] = "transfer_to_" + to

        data = {}
        data["from"] = self.username
        if not isinstance(receiver, str):
            raise NektarException("Receiver must be a valid Hive account user.")
        if to is None and (self.username == receiver):
            raise NektarException("Receiver must be unique from the sender.")
        data["to"] = receiver

        if not isinstance(amount, (int, float)):
            raise NektarException("Amount must be a positive numeric value.")
        if amount < 0.001:
            raise NektarException("Amount must be a positive numeric value.")

        precision = ASSETS[asset]["precision"]
        whole, fraction = str(float(amount)).split(".")
        fraction = fraction.ljust(precision, "0")[:precision]
        data["amount"] = whole + "." + fraction + " " + asset

        if to != "vesting":
            if not isinstance(message, str):
                raise NektarException("Memo message must be a UTF-8 string.")
            if not (len(message.encode("utf-8")) <= 2048):
                raise NektarException("Memo message must be not more than 2048 bytes.")
            data["memo"] = message
        operations[0][1] = data

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _is_boolean(synchronous, False)
        strict = _is_boolean(strict, True)
        debug = _is_boolean(debug, False)

        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }

        return self._broadcast(transaction, synchronous, strict, debug)

    def transfer_to_savings(
        self,
        receiver,
        amount,
        asset,
        message="",
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
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
            debug=debug,
        )

    def transfer_to_vesting(
        self,
        receiver,
        amount,
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
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
            debug=debug,
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
        wif=None,
        role=None,
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
            List of all transactions from start-limit to limit.
        """

        if account is None:
            account = self.username

        return self.get_account_history(account, start, limit, low, high)

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

        """

        params = ["", -1, 1000, 0]

        params[0] = self.username
        if isinstance(account, str):
            params[0] = account

        if int(start) < 1000 or (start % 1000 > 0):
            raise NektarException("`start` must be a value by the factor of 1000.")

        operation_id = 40  # delegate_vesting_shares_operation
        params[3] = int("1".ljust(operation_id + 1, "0"), 2)

        if not isinstance(inward, bool):
            raise NektarException("Inward must be `True` or `False` only.")

        key = "delegator"
        if not inward:
            key = "delegatee"

        top = 0
        results = {}
        while True:
            try:
                result = self.appbase.condenser().get_account_history(params)
            except:
                params[1] += 1000
                continue
            tids = [1000]
            for item in result:
                if top == 0:
                    tids.append(item[0])
                delegation = item[1]["op"][1]
                name = delegation[key]
                if name == self.username:
                    continue
                if name not in results:
                    results[name] = {}
                results[name][item[1]["timestamp"]] = float(
                    delegation["vesting_shares"].split(" ")[0]
                )
            if top == 0:
                params[1] = start
                top = (max(tids) // 1000) * 1000
            params[1] += 1000
            if params[1] > top:
                break
        if active:
            active_delegations = {}
            for d, data in results.items():
                recent = max(list(data.keys()))
                if data[recent]:
                    active_delegations[d] = data[recent]
            return active_delegations
        return results

    def delegators(self, account=None, active=False, start=-1):
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

    def delegatees(self, account=None, active=False, start=-1):
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
            raise NektarException("Author must be a string.")
        pattern = r"[\w][\w\.\-]{2,15}"
        if not len(re.findall(pattern, author)):
            raise NektarException("author must be a string of length 3 - 16.")
        params[0] = author
        pattern = r"[\w][\w\-\%]{0,255}"
        if not len(re.findall(pattern, permlink)):
            raise NektarException("permlink must be a valid url-escaped string.")
        params[1] = permlink

        if not (1 <= int(retries) <= 5):
            raise NektarException("Retries must be between 1 to 5 times.")
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
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

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
        synchronous = _is_boolean(synchronous, False)
        strict = _is_boolean(strict, True)
        debug = _is_boolean(debug, False)

        operations = [["comment", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, debug)

    def reblog(
        self,
        author,
        permlink,
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        if not _check_wifs(self.roles, "follow"):
            raise NektarException(
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
            debug=debug,
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
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

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

        uid = ""
        edit = _is_boolean(edit, True)
        if not edit:
            uid = _make_expiration(formatting="-%Y%m%d%H%M%S")
        data["permlink"] = ("re-" + permlink + uid)[:255]

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
        synchronous = _is_boolean(synchronous, False)
        strict = _is_boolean(strict, True)
        debug = _is_boolean(debug, False)

        operations = [["comment", data]]
        transaction = {
            "ref_block_num": ref_block_num,
            "ref_block_prefix": ref_block_prefix,
            "expiration": expiration,
            "operations": operations,
            "extensions": [],
        }
        return self._broadcast(transaction, synchronous, strict, debug)

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
            raise NektarException("Author must be a string.")
        pattern = r"[\w][\w\.\-]{2,15}"
        if not len(re.findall(pattern, author)):
            raise NektarException("author must be a string of length 3 - 16.")
        params[0] = author
        pattern = r"[\w][\w\-\%]{0,255}"
        if not len(re.findall(pattern, permlink)):
            raise NektarException("permlink must be a valid url-escaped string.")
        params[1] = permlink

        if not (1 <= int(retries) <= 5):
            raise NektarException("Retries must be between 1 to 5 times.")
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
            raise NektarException("Author must be a string.")
        pattern = r"[\w][\w\.\-]{2,15}"
        if not len(re.findall(pattern, author)):
            raise NektarException("author must be a string of length 3 - 16.")
        params[0] = author
        pattern = r"[\w][\w\-\%]{0,255}"
        if not len(re.findall(pattern, permlink)):
            raise NektarException("permlink must be a valid url-escaped string.")
        params[1] = permlink

        if not (1 <= int(retries) <= 5):
            raise NektarException("Retries must be between 1 to 5 times.")
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
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

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

        if _is_boolean(check, False):
            if self.voted(author, permlink):
                return {}

        if isinstance(percent, (int, float)):
            percent = _within_range(percent, -100, 100)
            weight = 10000 * (percent / 100)

        ref_block_num, ref_block_prefix = self.get_reference_block_data()
        weight = _within_range(weight, -10000, 10000, 10000)
        expire = _within_range(expire, 5, 120, 30)
        expiration = _make_expiration(expire)
        synchronous = _is_boolean(synchronous, False)
        strict = _is_boolean(strict, True)
        debug = _is_boolean(debug, False)

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
        return self._broadcast(transaction, synchronous, strict, debug)

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
            raise NektarException("Author must be a string.")
        pattern = r"[\w][\w\.\-]{2,15}"
        if not len(re.findall(pattern, author)):
            raise NektarException("author must be a string of length 3 - 16.")
        params[0] = author
        pattern = r"[\w][\w\-\%]{0,255}"
        if not len(re.findall(pattern, permlink)):
            raise NektarException("permlink must be a valid url-escaped string.")
        params[1] = permlink

        if not (1 <= int(retries) <= 5):
            raise NektarException("Retries must be between 1 to 5 times.")
        strict = retries == 1

        for _ in range(retries):
            data = self.appbase.condenser().get_active_votes(params, strict=strict)
            if len(data):
                return data
        return {}

    def voted(
        self, author, permlink, expire=30, synchronous=False, strict=True, debug=False
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
        debug : bool, optional
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
        debug=False,
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
        debug : bool, optional
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
            debug=False,
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
        wif=None,
        role=None,
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
        _valid_string(community, RE_COMMUNITY)
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
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        _valid_string(author)
        _valid_string(permlink, RE_PERMLINK)
        _valid_string(notes)

        operation = ["mutePost", {}]
        _is_boolean(mute)
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
            json_data=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            debug=debug,
        )

    def unmute(
        self,
        author,
        permlink,
        notes,
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """
        return self.mute(author, permlink, notes, False, expire, strict, debug)

    def mark_spam(
        self,
        author,
        permlink,
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """
        self.mute(author, permlink, "spam", True, expire, strict, debug)

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
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

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

        return self.custom_json(
            id_="community",
            json_data=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            debug=debug,
        )

    def subscribe(
        self,
        subscribe=True,
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        operation = ["subscribe", {"community": self._community}]
        _is_boolean(subscribe)
        if not subscribe:
            operation[0] = "unsubscribe"

        return self.custom_json(
            id_="community",
            json_data=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            debug=debug,
        )

    def unsubscribe(self, expire=30, synchronous=False, strict=True, debug=False):
        """Unsubscribe to the community.

        Parameters
        ----------
        expire : int, optional
            transaction expiration in seconds (Default is 30)
        synchronous : bool, optional
            flah to broadcasting method synchronously (Default is False)
        strict : bool, optional
            flag to cause exception upon encountering an error (Default is True)
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        return self.subscribe(False, expire, synchronous, strict, debug)

    def pin(
        self,
        author,
        permlink,
        pin=True,
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)
        pin :
             (Default is True)

        Returns
        -------

        """

        _valid_string(author)
        _valid_string(permlink, RE_PERMLINK)
        _is_boolean(pin)
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
            json_data=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            debug=debug,
        )

    def unpin(
        self,
        author,
        permlink,
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        self.pin(author, permlink, False, expire, synchronous, strict, debug)

    def flag(
        self,
        author,
        permlink,
        notes,
        expire=30,
        synchronous=False,
        strict=True,
        debug=False,
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
        debug : bool, optional
            flag to disable completion of the broadcast operation (Default is False)

        Returns
        -------

        """

        _valid_string(author)
        _valid_string(permlink, RE_PERMLINK)
        _valid_string(notes)

        data = {}
        data["community"] = self._community
        data["account"] = author
        data["permlink"] = permlink
        data["notes"] = notes
        operation = ["flagPost", data]

        return self.custom_json(
            id_="community",
            json_data=operation,
            required_auths=[],
            required_posting_auths=[self.username],
            expire=expire,
            synchronous=synchronous,
            strict=strict,
            debug=debug,
        )


##############################
# utils                      #
##############################


def _check_wifs(roles, operation):
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


def _make_expiration(seconds=30, formatting=None):
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
    _valid_string(formatting)
    return datetime.utcfromtimestamp(timestamp).strftime(formatting)

def _valid_string(value, pattern=None, fallback=None):
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

def _greater_than(value, minimum, fallback=None):
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


def _within_range(value, minimum, maximum, fallback=None):
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

def _is_boolean(value, fallback=None):
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
