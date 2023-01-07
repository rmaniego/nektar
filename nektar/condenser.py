# -*- coding: utf-8 -*-
"""
    nektar.condenser
    ~~~~~~~~~

    Interact with Hive API in Python.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

from .appbase import AppBase
from .constants import (
    NEKTAR_VERSION,
    BLOCKCHAIN_OPERATIONS,
    DISCUSSIONS_BY,
    ASSETS,
    ROLES,
    DATETIME_FORMAT,
    RE_PERMLINK,
    RE_COMMUNITY,
    RE_DATETIME,
)
from .utils import (
    check_wifs,
    make_expiration,
    valid_string,
    greater_than,
    within_range,
    is_boolean,
)


class Condenser:
    """Condenser class.
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
    """

    def __init__(
        self,
        nodes=None,
        chain_id=None,
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
        self.api = self.appbase.condenser()

    def get_account_count(self):
        """Returns the number of accounts.
        https://developers.hive.io/apidefinitions/#condenser_api.get_account_count

        Returns
        -------
        int:
        """

        return self.api.get_account_count([])

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
            upperbound limit from 1 up to 1000
        low : int, optional
            operation id (Default is None)
        high : int, optional
            operation id (Default is None)

        Returns
        -------
        list:
        """

        valid_string(account)
        greater_than(start, -1)
        within_range(limit, 1, 1000)
        params = [account, start, limit]
        operations = list(range(len(BLOCKCHAIN_OPERATIONS)))
        if isinstance(low, int):
            ## for the first 64 blockchain operation
            if int(low) not in operations:
                raise ValueError(
                    "Operation Filter `low` is not a valid blockchain operation ID."
                )
            params.append(int("1".ljust(low + 1, "0"), 2))

        if isinstance(high, int):
            ## for the next 64 blockchain operation
            if int(high) not in operations:
                raise ValueError(
                    "Operation Filter `high` is not a valid blockchain operation ID."
                )
            params.append(0)  # set to `operation_filter_low` zero
            params.append(int("1".ljust(high + 1, "0"), 2))

        return self.api.get_account_history(params)

    def get_account_reputations(self, start, limit):
        """Returns a list of account reputations.
        https://developers.hive.io/apidefinitions/#condenser_api.get_account_reputations

        Parameters
        ----------
        start : str
            any valid Hive account username
        limit : int
            Maximum number of results, from 1 up to 1000.

        Returns
        -------
        list:
        """

        valid_string(start)
        within_range(limit, 1, 1000)
        params = [start, limit]
        return self.api.get_account_reputations(params)

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
        """

        params = [accounts, delayed_votes_active]
        if not isinstance(accounts, list):
            raise TypeError("`accounts` must be a list of strings.")
        is_boolean(delayed_votes_active)
        return self.api.get_accounts(params)

    def get_active_votes(self, author, permlink):
        """Returns all votes for the given post.
        https://developers.hive.io/apidefinitions/#condenser_api.get_active_votes

        Parameters
        ----------
        author : str
            Author of the post.
        permlink : str
            Permlink of the post

        Returns
        -------
        list:
        """

        valid_string(author)
        valid_string(permlink, RE_PERMLINK)
        return self.api.get_active_votes([author, permlink])

    def get_active_witnesses(self):
        """Returns the list of active witnesses.
        https://developers.hive.io/apidefinitions/#condenser_api.get_active_witnesses

        Returns
        -------
        list:
        """

        return self.api.get_active_witnesses([])

    def get_block(self, number):
        """Returns a block.
        https://developers.hive.io/apidefinitions/#condenser_api.get_block

        Parameters
        ----------
        number : int
            block number

        Returns
        -------
        dict:
            Dictionary of block information.
        """

        greater_than(number, 0)
        return self.api.get_block([number])

    def get_block_header(self, number):
        """Returns a block header.
        https://developers.hive.io/apidefinitions/#condenser_api.get_block_header

        Parameters
        ----------
        number : int
            block number

        Returns
        -------
        dict:
            Dictionary of block header information.
        """

        greater_than(number, 0)
        return self.api.get_block_header([number])

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
            maximum number of results 1 up to 500

        Returns
        -------
        list:
        """

        valid_string(account)
        start = greater_than(start, 0)
        limit = within_range(limit, 1, 500)
        params = [account, start, limit]
        return self.api.get_blog(params)

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

        valid_string(account)
        return self.api.get_blog_authors([account])

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
            maximum number of results 1 up to 500

        Returns
        -------
        list:
            List of blogs and its basic information without the full blog data.
        """

        valid_string(account)
        start = greater_than(start, 0)
        limit = within_range(limit, 1, 500)
        params = [account, start, limit]
        return self.api.get_blog_entries(params)

    def get_chain_properties(self):
        """Returns the chain properties.
        https://developers.hive.io/apidefinitions/#condenser_api.get_chain_properties

        Returns
        -------
        dict:
        """

        return self.api.get_chain_properties([])

    def get_config(self):
        """Returns information about compile-time constants.
        https://developers.hive.io/apidefinitions/#condenser_api.get_config
        https://developers.hive.io/tutorials-recipes/understanding-configuration-values.html

        Returns
        -------
        dict:
            A dictionary blockchain configurations.
        """

        return self.api.get_config([])

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
        """

        valid_string(author)
        valid_string(permlink)
        params = [author, permlink]
        return self.api.get_content(params)

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

        valid_string(author)
        valid_string(permlink)
        params = [author, permlink]
        return self.api.get_content_replies(params)

    def get_conversion_requests(self, account):
        """Returns a list of conversion request.
        https://developers.hive.io/apidefinitions/#condenser_api.get_conversion_requests

        Parameters
        ----------
        account : str
            Any valid Hive account username.

        Returns
        -------
        list:
        """

        valid_string(account)
        return self.api.get_conversion_requests([account])

    def get_current_median_history_price(self):
        """Returns the median history price.
        https://developers.hive.io/apidefinitions/#condenser_api.get_current_median_history_price

        Returns
        -------
        dict:
        """

        return self.api.get_current_median_history_price([])

    def get_discussions(
        self,
        by,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
        comment=False,
    ):
        """Returns a list of discussions.

        Parameters
        ----------
        by : str
            Discussion type: `active`, `blog`, `cashout`, `children`, `created`, `hot`, `payout`, `promoted`, `trending`, OR `votes`.
        tag : str
            Any valid string
        limit : int
            Maximum number of results
        filter_tags : list, None
            List of valid tags
        select_authors : list, None
            List of valid account username
        select_tags : list, None
            List of valid tags
        truncate : int, optional
            Truncate body (0, 1)
        comment : bool, optional
            Comment discussion, default is False.

        Returns
        -------
        list:
            List of discussions.
        """

        valid_string(by)
        if by not in DISCUSSIONS_BY:
            raise ValueError("`by` must be a value in:", ",".join(DISCUSSIONS_BY))

        valid_string(tag)
        within_range(limit, 1, 500)
        within_range(truncate, 0, 1)

        # initial parameters
        data = {"tag": tag, "limit": limit, "truncate_body": truncate}

        # custom filters
        if not isinstance(filter_tags, list):
            if filter_tags is not None:
                raise TypeError("`filter_tags` must be a list.")
            filter_tags = []
        if filter_tags:
            data["filter_tags"] = filter_tags
        if not isinstance(select_authors, list):
            if select_authors is not None:
                raise TypeError("`select_authors` must be a list.")
            select_authors = []
        if select_authors:
            data["select_authors"] = select_authors
        if not isinstance(select_tags, list):
            if select_tags is not None:
                raise TypeError("`select_tags` must be a list.")
            select_tags = []
        if select_tags:
            data["select_tags"] = select_tags

        match by:
            case "active":
                return self.api.get_discussions_by_active([data])
            case "blog":
                return self.api.get_discussions_by_blog([data])
            case "cashout":
                return self.api.get_discussions_by_cashout([data])
            case "children":
                return self.api.get_discussions_by_children([data])
            case "created":
                return self.api.get_discussions_by_created([data])
            case "hot":
                return self.api.get_discussions_by_hot([data])
            case "payout":
                if comment:
                    return self.api.get_comment_discussions_by_payout([data])
                return self.api.get_post_discussions_by_payout([data])
            case "promoted":
                return self.api.get_discussions_by_promoted([data])
            case "trending":
                return self.api.get_discussions_by_trending([data])
            case "votes":
                return self.api.get_discussions_by_trending([data])

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

        by = "active"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

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

        by = "blog"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

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

        by = "cashout"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

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

        by = "children"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

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

        by = "created"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

    def get_discussions_by_hot(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions by hot.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_hot

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

        by = "hot"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

    def get_discussions_by_promoted(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions by promoted
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_promoted

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

        by = "promoted"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

    def get_discussions_by_trending(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions by trending.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_trending

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

        by = "trending"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

    def get_discussions_by_votes(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of discussions by trending.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_votes

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

        by = "votes"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

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
        """

        by = "payout"
        comment = True
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate, comment
        )

    def get_post_discussions_by_payout(
        self,
        tag,
        limit,
        filter_tags=None,
        select_authors=None,
        select_tags=None,
        truncate=0,
    ):
        """Returns a list of post discussions by payout.
        https://developers.hive.io/apidefinitions/#condenser_api.get_post_discussions_by_payout

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
        """

        by = "payout"
        return self.get_discussions(
            by, tag, limit, filter_tags, select_authors, select_tags, truncate
        )

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
        """

        valid_string(author)
        valid_string(permlink)
        valid_string(date, RE_DATETIME)
        greater_than(limit, 0)
        params = [author, permlink, date, limit]
        return self.api.get_discussions_by_author_before_date(params)

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

        valid_string(author)
        # allow empty start permlink
        valid_string(permlink)
        within_range(limit, 1, 100)
        data = {"start_author": author, "start_permlink": permlink, "limit": limit}
        return self.api.get_discussions_by_comments([data])

    def get_discussions_by_feed(
        self,
        tag,
        author,
        permlink,
        limit,
    ):
        """Returns a list of discussions by feed.
        https://developers.hive.io/apidefinitions/#condenser_api.get_discussions_by_feed

        Parameters
        ----------
        tag : str
            any valid string
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

        valid_string(tag)
        valid_string(author)
        # allow empty start permlink
        valid_string(permlink)
        within_range(limit, 1, 100)
        data = {
            "tag": tag,
            "start_author": author,
            "start_permlink": permlink,
            "limit": limit,
        }
        return self.api.get_discussions_by_feed([data])

    def get_dynamic_global_properties(self):
        """Returns the current dynamic global properties.
        https://developers.hive.io/apidefinitions/#condenser_api.get_dynamic_global_properties
        https://developers.hive.io/tutorials-recipes/understanding-dynamic-global-properties.html

        Returns
        -------
        dict:
        """

        return self.api.get_dynamic_global_properties([])

    def get_escrow(self, account, eid):
        """Returns the escrow for a certain account by id.
        https://developers.hive.io/apidefinitions/#condenser_api.get_escrow

        Parameters
        ----------
        account : str
            Any valid Hive account username.
        eid : int
            escrow id

        Returns
        -------
        null:
        """

        valid_string(account)
        greater_than(eid, -1)
        return self.api.get_escrow([account, eid])

    def get_expiring_vesting_delegations(self, account, after):
        """Returns the expiring vesting delegations for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_expiring_vesting_delegations

        Parameters
        ----------
        account : str
            Any valid Hive account username.
        after : str
            Valid blockchain timestamp, e.g. "2018-01-01T00:00:00"

        Returns
        -------
        list:
        """

        valid_string(account)
        valid_string(after, RE_DATETIME)
        return self.api.get_expiring_vesting_delegations([account, after])

    def get_feed(self, account, eid, limit):
        """Returns a list of items in an account’s feed.
        https://developers.hive.io/apidefinitions/#condenser_api.get_feed

        Parameters
        ----------
        account : str
            Any valid Hive account.
        eid : int
            Starting entry id.
        limit : int
            Maximum number of results, 1 up to 500.

        Returns
        -------
        list:
            List of posts and its corresponding information
        """

        valid_string(account)
        greater_than(eid, -1)
        greater_than(limit, 0)
        return self.api.get_feed([account, eid, limit])

    def get_feed_entries(self, account, eid, limit):
        """Returns a list of entries in an account’s feed.
        https://developers.hive.io/apidefinitions/#condenser_api.get_feed_entries

        Parameters
        ----------
        account : str
            Any valid Hive account.
        eid : int
            Starting entry id.
        limit : int
            Maximum number of results, 1 up to 500.

        Returns
        -------
        list:
            List of posts and its corresponding information
        """

        valid_string(account)
        greater_than(eid, -1)
        within_range(limit, 1, 500)
        return self.api.get_feed_entries([account, eid, limit])

    def get_feed_history(self):
        """Returns the history of price feed values
        https://developers.hive.io/apidefinitions/#condenser_api.get_feed_history

        Returns
        -------
        dict:
        """

        return self.api.get_feed_history([])

    def get_follow_count(self, account):
        """Returns the count of followers/following for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_follow_count

        Parameters
        ----------
        account : str
            Any valid Hive account.

        Returns
        -------
        dict:
        """

        valid_string(account)
        return self.api.get_follow_count([account])

    def get_followers(self, account, start, ftype, limit):
        """Returns the list of followers for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_followers

        Parameters
        ----------
        account : str
            Any valid Hive account.
        start : str
            Starting character/s of the follower usernames.
        ftype : str
            Follow type, `blog` or `ignore`.
        limit : int
            Maximum number of results from 1 up to 1000.

        Returns
        -------
        list:
        """

        valid_string(account)
        valid_string(start)
        valid_string(ftype)
        within_range(limit, 1, 1000)
        params = [account, start, ftype, limit]
        return self.api.get_followers(params)

    def get_following(self, account, start, ftype, limit):
        """Returns the list of accounts that are following an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_following

        Parameters
        ----------
        account : str
            Any valid Hive account.
        start : str
            Starting character/s of the follower usernames.
        ftype : str
            Follow type, `blog` or `ignore`.
        limit : int
            Maximum number of results from 1 up to 1000.

        Returns
        -------
        list:
        """

        valid_string(account)
        valid_string(start)
        valid_string(ftype)
        within_range(limit, 1, 1000)
        params = [account, start, ftype, limit]
        return self.api.get_following(params)

    def get_hardfork_version(self):
        """Returns the current hardfork version.
        https://developers.hive.io/apidefinitions/#condenser_api.get_hardfork_version

        Returns
        -------
        str:
        """

        return self.api.get_hardfork_version([])

    def get_key_references(self, keys):
        """Returns all accounts that have the key associated with their owner or active authorities.
        https://developers.hive.io/apidefinitions/#condenser_api.get_key_references

        Parameters
        ----------
        keys : str, list
            List of valid Hive public keys.

        Returns
        -------
        list:
        """

        params = [[keys]]
        if not isinstance(keys, str):
            if not isinstance(keys, list):
                raise TypeError("`keys` must be a list of strings.")
            if not all([0 for k in keys if not isinstance(k, str)]):
                raise TypeError("`keys` must be a list of strings.")
            params = [keys]
        return self.api.get_key_references(params)

    def get_market_history(self, seconds, start, end):
        """Returns the market history for the internal HBD:HIVE market.
        https://developers.hive.io/apidefinitions/#condenser_api.get_market_history

        Parameters
        ----------
        seconds : int
            bucket seconds: 15, 60 (1 minute), 300 (5 mins), 3600 (1 hour), 86400 (1 day)
        start : str
            Valid starting blockchain timestamp, e.g. "2017-01-01T00:00:00"
        end : str
            Valid ending blockchain timestamp, e.g. "2018-01-01T00:00:00"

        Returns
        -------
        list:
        """

        if int(seconds) not in (15, 60, 300, 3600, 86400):
            raise ValueError(
                "`seconds` is not supported, see get_market_history_buckets."
            )
        valid_string(start, RE_DATETIME)
        valid_string(end, RE_DATETIME)
        return self.api.get_market_history([seconds, start, end])

    def get_market_history_buckets(self):
        """Returns the bucket seconds being tracked by the plugin.
        https://developers.hive.io/apidefinitions/#condenser_api.get_market_history_buckets

        Returns
        -------
        list:
        """

        return self.api.get_market_history_buckets([])

    def get_next_scheduled_hardfork(self):
        """Returns the next scheduled hardfork.
        https://developers.hive.io/apidefinitions/#condenser_api.get_next_scheduled_hardfork

        Returns
        -------
        dict:
        """

        return self.api.get_next_scheduled_hardfork([])

    def get_open_orders(self, account):
        """Returns the open orders for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_open_orders

        Parameters
        ----------
        account : str
            Any valid Hive account.

        Returns
        -------
        list:
        """

        valid_string(account)
        return self.api.get_open_orders([account])

    def get_ops_in_block(self, number, virtual):
        """Returns the open orders for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_ops_in_block

        Parameters
        ----------
        number : int
            Block number.
        virtual : bool
            Virtual operation or not, `True` or `False`.

        Returns
        -------
        list:
        """

        greater_than(number, 1)
        is_boolean(virtual)
        return self.api.get_ops_in_block([number, virtual])

    def get_order_book(self, limit):
        """Returns the internal market order book.
        https://developers.hive.io/apidefinitions/#condenser_api.get_order_book

        Parameters
        ----------
        limit : int
            Maximum number of results, from 1 up to 500.

        Returns
        -------
        dict:
        """

        greater_than(limit, 1)
        return self.api.get_order_book([limit])

    def get_owner_history(self, account):
        """Returns the owner history of an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_owner_history

        Parameters
        ----------
        account : str
            any valid Hive account username

        Returns
        -------
        dict:
            Dictionary of block header information.
        """

        valid_string(account)
        return self.api.get_owner_history([account])

    def get_potential_signatures(self, transaction):
        """This method will return the set of all public keys that could possibly sign for a given transaction.
        https://developers.hive.io/apidefinitions/#condenser_api.get_potential_signatures

        Parameters
        ----------
        transaction : dict
            Any valid unsigned transaction.

        Returns
        -------
        list:
        """

        if not isinstance(transaction, dict):
            raise ValueError("`transaction` must be a dictionary.")
        return self.api.get_potential_signatures([transaction])

    def get_reblogged_by(self, author, permlink):
        """Returns a list of authors that have reblogged a post.
        https://developers.hive.io/apidefinitions/#condenser_api.get_reblogged_by

        Parameters
        ----------
        author : list
            Author of the post.
        permlink : str
            Permlink of the post

        Returns
        -------
        list:
        """

        valid_string(author)
        valid_string(permlink, RE_PERMLINK)
        return self.api.get_reblogged_by([author, permlink])

    def get_recent_trades(self, limit):
        """Returns the most recent trades for the internal HBD:HIVE market.
        https://developers.hive.io/apidefinitions/#condenser_api.get_recent_trades

        Parameters
        ----------
        limit : int
            Maximum number of results, from 1 up to 1000.

        Returns
        -------
        list:
        """

        within_range(limit, 1, 1000)
        return self.api.get_recent_trades([limit])

    def get_recovery_request(self, account):
        """Returns the recovery request for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_recovery_request

        Parameters
        ----------
        account : str
            Any valid Hive account username.

        Returns
        -------
        null:
        """

        valid_string(account)
        return self.api.get_recovery_request([account])

    def get_replies_by_last_update(self, author, permlink, limit):
        """Returns a list of replies by last update.
        https://developers.hive.io/apidefinitions/#condenser_api.get_replies_by_last_update

        Parameters
        ----------
        author : str
            Start pattern for the post author.
        permlink : str
            Start pattern for the post permlink.
        limit : int
            Maximum number of results, from 1 up to 100.

        Returns
        -------
        list:
        """

        valid_string(author)
        # allow empty permlink
        valid_string(permlink)
        within_range(limit, 1, 100)
        return self.api.get_replies_by_last_update([author, permlink, limit])

    def get_required_signatures(self, transaction, keys):
        """This API will take a partially signed transaction
        and a set of public keys that the owner has the ability
        to sign for and return the minimal subset of public keys
        that should add signatures to the transaction.
        https://developers.hive.io/apidefinitions/#condenser_api.get_required_signatures

        Parameters
        ----------
        account : dict
            any valid unsigned transaction.

        Returns
        -------
        list:
        """

        if not isinstance(transaction, dict):
            raise ValueError("`transaction` must be a dictionary.")
        if not isinstance(keys, list):
            raise ValueError("`keys` must be a list of strings.")
        if not all([0 for k in keys if not isinstance(k, str)]):
            raise ValueError("`keys` must be a list of strings.")
        return self.api.get_required_signatures([transaction, keys])

    def get_reward_fund(self, action):
        """Returns information about the current reward funds.
        https://developers.hive.io/apidefinitions/#condenser_api.get_reward_fund

        Parameters
        ----------
        action : str
            `post`

        Returns
        -------
        null:
        """

        valid_string(action)
        return self.api.get_reward_fund([action])

    def get_savings_withdraw_from(self, account):
        """Returns savings withdraw from an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_savings_withdraw_from

        Parameters
        ----------
        account : str
            Any valid Hive account username.

        Returns
        -------
        list:
        """

        valid_string(account)
        return self.api.get_savings_withdraw_from([account])

    def get_savings_withdraw_to(self, account):
        """Returns savings withdraw from an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_savings_withdraw_to

        Parameters
        ----------
        account : str
            Any valid Hive account username.

        Returns
        -------
        list:
        """

        valid_string(account)
        return self.api.get_savings_withdraw_to([account])

    def get_tags_used_by_author(self, account):
        """Returns a list of tags used by an author.
        https://developers.hive.io/apidefinitions/#condenser_api.get_tags_used_by_author

        Parameters
        ----------
        account : str
            Any valid Hive account username.

        Returns
        -------
        list:
        """

        valid_string(account)
        return self.api.get_tags_used_by_author([account])

    def get_ticker(self):
        """Returns the market ticker for the internal HBD:HIVE market.
        https://developers.hive.io/apidefinitions/#condenser_api.get_ticker

        Returns
        -------
        dict:
        """

        return self.api.get_ticker([])

    def get_trade_history(self, start, end, limit):
        """Returns the expiring vesting delegations for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_trade_history

        Parameters
        ----------
        start : str
            Valid starting blockchain timestamp, e.g. "2017-01-01T00:00:00"
        end : str
            Valid ending blockchain timestamp, e.g. "2018-01-01T00:00:00"
        limit : int
            Maximum number of results, from 1 up to 100.

        Returns
        -------
        list:
        """

        valid_string(start, RE_DATETIME)
        valid_string(end, RE_DATETIME)
        within_range(limit, 1, 1000)
        return self.api.get_trade_history([start, end, limit])

    def get_transaction(self, tid):
        """Returns the details of a transaction based on a transaction id.
        https://developers.hive.io/apidefinitions/#condenser_api.get_transaction

        Parameters
        ----------
        tid : str
            Any valid transaction id.

        Returns
        -------
        list:
        """

        valid_string(tid)
        return self.api.get_transaction([tid])

    def get_transaction_hex(self, transaction):
        """This API will take a partially signed transaction
        and a set of public keys that the owner has the ability
        to sign for and return the minimal subset of public keys
        that should add signatures to the transaction.
        https://developers.hive.io/apidefinitions/#condenser_api.get_transaction_hex

        Parameters
        ----------
        transaction : dict
            Any valid unsigned transaction.

        Returns
        -------
        str:
        """

        if not isinstance(transaction, dict):
            raise ValueError("`transaction` must be a dictionary.")
        return self.api.get_transaction_hex([transaction])

    def get_trending_tags(self, start, limit):
        """Returns the list of trending tags.
        https://developers.hive.io/apidefinitions/#condenser_api.get_trending_tags

        Parameters
        ----------
        start : str
            Starting pattern for tags.
        limit : int
            Maximum number of results, from 1 up to 100.

        Returns
        -------
        list:
        """

        valid_string(start)
        within_range(limit, 1, 100)
        return self.api.get_trending_tags([start, limit])

    def get_version(self):
        """Returns the versions of blockchain, hive, and FC.
        https://developers.hive.io/apidefinitions/#condenser_api.get_version

        Returns
        -------
        dict:
        """

        return self.api.get_version([])

    def get_vesting_delegations(self, account, start, limit):
        """Returns the vesting delegations by an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_vesting_delegations

        Parameters
        ----------
        account : str
            Any valid Hive account username, delegator.
        start : str
            Starting pattern for delegatee username.
        limit : int
            Maximum number of results, from 1 up to 1000.

        Returns
        -------
        list:
        """

        valid_string(account)
        valid_string(start)
        within_range(limit, 1, 100)
        return self.api.get_vesting_delegations([account, start, limit])

    def get_volume(self):
        """Returns the market volume for the past 24 hours.
        https://developers.hive.io/apidefinitions/#condenser_api.get_volume

        Returns
        -------
        dict:
        """

        return self.api.get_volume([])

    def get_withdraw_routes(self, account, route):
        """Returns the withdraw routes for an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_withdraw_routes

        Parameters
        ----------
        account : str
            Any valid Hive account username, delegator.
        rout : str
            `all`, `outgoing`, or `incoming

        Returns
        -------
        list:
        """

        valid_string(account)
        valid_string(route)
        routes = ("incoming", "outgoing", "all")
        if route not in routes:
            raise ValueError("`route` must be a value in:", ",".join(routes))
        return self.api.get_withdraw_routes([account, route])

    def get_witness_by_account(self, account):
        """Returns the witness of an account.
        https://developers.hive.io/apidefinitions/#condenser_api.get_witness_by_account

        Parameters
        ----------
        account : str
            Any valid Hive account username.

        Returns
        -------
        null:
        """

        valid_string(account)
        return self.api.get_witness_by_account([account])

    def get_witness_count(self):
        """Return the number of witnesses.
        https://developers.hive.io/apidefinitions/#condenser_api.get_witness_count

        Returns
        -------
        int:
        """

        return self.api.get_witness_count([])

    def get_witness_schedule(self):
        """Returns the current witness schedule.
        https://developers.hive.io/apidefinitions/#condenser_api.get_witness_schedule

        Returns
        -------
        list:
        """

        return self.api.get_witness_schedule([])

    def get_witnesses(self, indices):
        """Returns current witnesses.
        https://developers.hive.io/apidefinitions/#condenser_api.get_witnesses

        Parameters
        ----------
        indices : int, list
            List of integers, from 0 up to the current number of witnesses.

        Returns
        -------
        list:
        """

        params = [[indices]]
        if not isinstance(indices, int):
            if not isinstance(indices, list):
                raise ValueError("`indices` must be a list of integers.")
            if not all([0 for i in indices if not isinstance(i, int)]):
                raise ValueError("`indices` must be a list of integers.")
            params = [indices]

        return self.api.get_witnesses(params)

    def get_witnesses_by_vote(self, start, limit):
        """Returns current witnesses by vote.
        https://developers.hive.io/apidefinitions/#condenser_api.get_witnesses_by_vote

        Parameters
        ----------
        start : str
            Starting pattern for witness username.
        limit : int
            Maximum number of results, from 1 up to 1000.

        Returns
        -------
        list:
        """

        valid_string(start)
        within_range(limit, 1, 1000)
        return self.api.get_witnesses_by_vote([start, limit])

    def lookup_account_names(self, accounts, delayed_votes_active):
        """Returns accounts, queried by name.
        https://developers.hive.io/apidefinitions/#condenser_api.lookup_account_names

        Parameters
        ----------
        accounts : list
            a list of any valid Hive account usernames
        delayed_votes_active : bool
            delayed votes active

        Returns
        -------
        list:
        """

        params = [[accounts], delayed_votes_active]
        is_boolean(delayed_votes_active)
        if not isinstance(accounts, str):
            if not isinstance(accounts, list):
                raise ValueError("`accounts` must be a list of strings.")
            if not all([0 for k in accounts if not isinstance(k, str)]):
                raise ValueError("`accounts` must be a list of strings.")
            params[0] = accounts
        return self.api.lookup_account_names(params)

    def lookup_accounts(self, start, limit):
        """Looks up accounts starting with name.
        https://developers.hive.io/apidefinitions/#condenser_api.lookup_accounts

        Parameters
        ----------
        start : str
            Starting pattern for Hive account username.
        limit : int
            Maximum number of results, from 1 up to 1000.

        Returns
        -------
        list:
        """

        valid_string(start)
        within_range(limit, 1, 1000)
        return self.api.lookup_accounts([start, limit])

    def lookup_witness_accounts(self, start, limit):
        """Looks up witness accounts starting with name.
        https://developers.hive.io/apidefinitions/#condenser_api.lookup_witness_accounts

        Parameters
        ----------
        start : str
            Starting pattern for Hive account username.
        limit : int
            Maximum number of results, from 1 up to 1000.

        Returns
        -------
        list:
        """

        valid_string(start)
        within_range(limit, 1, 1000)
        return self.api.lookup_witness_accounts([start, limit])

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
        """

        greater_than(pid, 0)
        return self.api.find_proposals([[pid]])

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
        """

        params = [[""], 1000, "by_voter_proposal", "ascending", "all"]

        if not isinstance(start, (str, int)):
            raise ValueError("`start` must be a voter acount name or proposal id.")
        params[0][0] = start

        params[1] = within_range(limit, 0, 1000)
        if order not in ("by_voter_proposal", "by_proposal_voter"):
            raise ValueError("`order` is not supported.")
        params[2] = order

        if direction is not None:
            if direction not in ("ascending", "descending"):
                raise ValueError("`direction` is not supported.")
            params[3] = direction

        if status is not None:
            statuses = ("all", "inactive", "active", "expired", "votable")
            if status not in statuses:
                raise ValueError("`status` is not supported.")
            params[4] = status

        return self.api.list_proposal_votes(params)

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
        """

        params = [[""], 1000, "by_creator", "ascending", "all"]

        if not isinstance(start, (str, int)):
            raise ValueError("`start` must be a voter acount name or proposal id.")
        params[0][0] = start
        params[1] = within_range(limit, 0, 1000)

        orders = ("by_creator", "by_start_date", "by_end_date", "by_total_votes")
        if order not in orders:
            raise ValueError("`order` is not supported.")
        params[2] = order

        if direction is not None:
            if direction not in ("ascending", "descending"):
                raise ValueError("`direction` is not supported.")
            params[3] = direction

        if status is not None:
            statuses = ("all", "inactive", "active", "expired", "votable")
            if status not in statuses:
                raise ValueError("`status` is not supported.")
            params[4] = status

        return self.api.list_proposals(params)

    def is_known_transaction(self, tid):
        """Only return true if the transaction has not expired
        or been invalidated. If this method is called
        with a VERY old transaction we will return false,
        use account_history_api.get_transaction.
        https://developers.hive.io/apidefinitions/#condenser_api.is_known_transaction

        Parameters
        ----------
        tid : str
            Any valid transaction id.

        Returns
        -------
        list:
        """

        valid_string(tid)
        return self.api.is_known_transaction([tid])

    def get_collateralized_conversion_requests(self, account):
        """Returns objects corresponding with `collateralized_convert` operations.
        https://developers.hive.io/apidefinitions/#condenser_api.get_collateralized_conversion_requests

        Parameters
        ----------
        account : str
            Any valid Hive account username.

        Returns
        -------
        list:
        """

        valid_string(account)
        return self.api.get_collateralized_conversion_requests([account])

    def find_recurrent_transfers(self, account):
        """Finds transfers of any liquid asset every fixed amount of time from one account to another.
        https://developers.hive.io/apidefinitions/#condenser_api.find_recurrent_transfers

        Parameters
        ----------
        account : str
            Any valid Hive account username.

        Returns
        -------
        list:
        """

        valid_string(account)
        return self.api.find_recurrent_transfers([account])

    def find_rc_accounts(self, accounts):
        """Find RC delegations from accounts.
        https://developers.hive.io/apidefinitions/#condenser_api.find_rc_accounts

        Parameters
        ----------
        accounts : list
            a list of any valid Hive account usernames

        Returns
        -------
        list:
        """

        params = [[accounts]]
        if not isinstance(accounts, str):
            if not isinstance(accounts, list):
                raise ValueError("`accounts` must be a list of strings.")
            if not all([0 for k in accounts if not isinstance(k, str)]):
                raise ValueError("`accounts` must be a list of strings.")
            params[0] = accounts
        return self.api.find_rc_accounts(params)

    def list_rc_accounts(self, start, limit):
        """List all RC delegations starting from the specified account.
        https://developers.hive.io/apidefinitions/#condenser_api.list_rc_accounts

        Parameters
        ----------
        start : str
            Hive account username, lower bound.
        limit : int
            Maximum number of results, from 1 up to ?.

        Returns
        -------
        list:
        """

        valid_string(start)
        within_range(limit, 1, 1000)
        return self.api.list_rc_accounts([start, limit])

    def list_rc_direct_delegations(self, delegator, delegatee, limit):
        """List all RC delegations starting from the specified account.
        https://developers.hive.io/apidefinitions/#condenser_api.list_rc_direct_delegations

        Parameters
        ----------
        account : str
            Hive account username, lower bound.
        limit : int
            Maximum number of results, from 1 up to ?.

        Returns
        -------
        list:
        """

        valid_string(delegator)
        valid_string(delegatee)
        within_range(limit, 1, 1000)
        return self.api.list_rc_direct_delegations([[delegator, delegatee], limit])
