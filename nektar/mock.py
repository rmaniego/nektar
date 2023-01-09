# -*- coding: utf-8 -*-
"""
    nektar.mock
    ~~~~~~~~~

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""


def mock_server(payload):
    """Returns a mock result based on the payload.

    Parameters
    ----------
    payload :
        a valid transaction payload
    """
    if not isinstance(payload, dict):
        raise TypeError("`payload` must be a valid JSON RPC v2.0 transaction.")
    method = payload.get("method")

    if method is None:
        raise ValueError("`method` is missing on payload.")

    if method in (
        "condenser_api.get_account_history",
        "condenser_api.get_account_reputations",
        "condenser_api.get_active_witnesses",
        "condenser_api.get_blog",
        "condenser_api.get_blog_entries",
        "condenser_api.get_comment_discussions_by_payout",
        "condenser_api.get_conversion_requests",
        "condenser_api.get_discussions_by_active",
        "condenser_api.get_discussions_by_author_before_date",
        "condenser_api.get_discussions_by_blog",
        "condenser_api.get_discussions_by_cashout",
        "condenser_api.get_discussions_by_children",
        "condenser_api.get_discussions_by_comments",
        "condenser_api.get_discussions_by_created",
        "condenser_api.get_discussions_by_feed",
        "condenser_api.get_discussions_by_hot",
        "condenser_api.get_discussions_by_promoted",
        "condenser_api.get_discussions_by_trending",
        "condenser_api.get_discussions_by_votes",
        "condenser_api.get_expiring_vesting_delegations",
        "condenser_api.get_feed",
        "condenser_api.get_feed_entries",
        "condenser_api.get_followers",
        "condenser_api.get_following",
        "condenser_api.get_key_references",
        "condenser_api.get_market_history",
        "condenser_api.get_market_history_buckets",
        "condenser_api.get_open_orders",
        "condenser_api.get_ops_in_block",
        "condenser_api.get_owner_history",
        "condenser_api.get_post_discussions_by_payout",
        "condenser_api.get_potential_signatures",
        "condenser_api.get_reblogged_by",
        "condenser_api.get_replies_by_last_update",
        "condenser_api.get_required_signatures",
        "condenser_api.get_savings_withdraw_from",
        "condenser_api.get_savings_withdraw_to",
        "condenser_api.get_trade_history",
        "condenser_api.get_trending_tags",
        "condenser_api.get_vesting_delegations",
        "condenser_api.get_withdraw_routes",
        "condenser_api.get_witnesses",
        "condenser_api.get_witnesses_by_vote",
        "condenser_api.lookup_accounts",
        "condenser_api.lookup_witness_accounts",
        "condenser_api.get_account_references",
        "condenser_api.find_proposals",
        "condenser_api.list_proposal_votes",
        "condenser_api.list_proposals",
        "condenser_api.get_collateralized_conversion_requests",
        "condenser_api.find_recurrent_transfers",
        "condenser_api.find_rc_accounts",
        "condenser_api.list_rc_accounts",
        "condenser_api.list_rc_direct_delegations",
        "bridge.get_ranked_posts",
        "bridge.account_notifications",
        "bridge.get_account_posts",
        "bridge.get_follow_list",
        "bridge.list_communities",
        "bridge.list_pop_communities",
        "bridge.list_subscribers",
        "bridge.list_community_roles",
        "bridge.list_all_subscriptions",
        "jsonrpc.get_methods",
        "wallet_bridge_api.find_rc_accounts",
        "wallet_bridge_api.find_recurrent_transfers",
        "wallet_bridge_api.get_account_history",
        "wallet_bridge_api.get_accounts",
        "wallet_bridge_api.get_collateralized_conversion_requests",
        "wallet_bridge_api.get_conversion_requests",
        "wallet_bridge_api.get_open_orders",
        "wallet_bridge_api.get_withdraw_routes",
        "wallet_bridge_api.list_accounts",
        "wallet_bridge_api.list_my_accounts",
        "wallet_bridge_api.list_rc_accounts",
        "wallet_bridge_api.list_rc_direct_delegations",
    ):
        return []

    if method in (
        "condenser_api.get_transaction_hex",
        "condenser_api.get_hardfork_version",
        "wallet_bridge_api.get_hardfork_version",
    ):
        return ""

    if method in ("condenser_api.verify_authority",):
        return True

    if method in ("condenser_api.get_account_count","condenser_api.get_witness_count"):
        return 0

    return {}
