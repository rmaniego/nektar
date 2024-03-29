# -*- coding: utf-8 -*-
"""
    nektar.constants
    ~~~~~~~~~

    This module contains all Hive blockchain and Nektar constants.
    Do not change to avoid unecessary breakage.
    
    Review the official Hive codebase and the API documentation
    before any modifications.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import re

NEKTAR_VERSION = "1.1.0"

# PublicKey prefix
PREFIX = "STM"

"""
    AppBase APIs and methods
    The Condenser API is stable and can be used in production.
    Other AppBase APIs methods are still under development and subject to change.
"""
APPBASE_API = {
    "condenser_api": [
        "broadcast_block",
        "broadcast_transaction",
        "broadcast_transaction_synchronous",
        "find_proposals",
        "find_recurrent_transfers",
        "get_account_count",
        "get_account_history",
        "get_account_reputations",
        "get_accounts",
        "get_active_votes",
        "get_active_witnesses",
        "get_block",
        "get_block_header",
        "get_blog",
        "get_blog_authors",
        "get_blog_entries",
        "get_chain_properties",
        "get_collateralized_conversion_requests",
        "get_comment_discussions_by_payout",
        "get_config",
        "get_content",
        "get_content_replies",
        "get_conversion_requests",
        "get_current_median_history_price",
        "get_discussions_by_active",
        "get_discussions_by_author_before_date",
        "get_discussions_by_blog",
        "get_discussions_by_cashout",
        "get_discussions_by_children",
        "get_discussions_by_comments",
        "get_discussions_by_created",
        "get_discussions_by_feed",
        "get_discussions_by_hot",
        "get_discussions_by_promoted",
        "get_discussions_by_trending",
        "get_discussions_by_votes",
        "get_dynamic_global_properties",
        "get_escrow",
        "get_expiring_vesting_delegations",
        "get_feed",
        "get_feed_entries",
        "get_feed_history",
        "get_follow_count",
        "get_followers",
        "get_following",
        "get_hardfork_version",
        "get_key_references",
        "get_market_history",
        "get_market_history_buckets",
        "get_next_scheduled_hardfork",
        "get_open_orders",
        "get_ops_in_block",
        "get_order_book",
        "get_owner_history",
        "get_post_discussions_by_payout",
        "get_potential_signatures",
        "get_reblogged_by",
        "get_recent_trades",
        "get_recovery_request",
        "get_replies_by_last_update",
        "get_required_signatures",
        "get_reward_fund",
        "get_savings_withdraw_from",
        "get_savings_withdraw_to",
        "get_state",
        "get_tags_used_by_author",
        "get_ticker",
        "get_trade_history",
        "get_transaction",
        "get_transaction_hex",
        "get_trending_tags",
        "get_version",
        "get_vesting_delegations",
        "get_volume",
        "get_withdraw_routes",
        "get_witness_by_account",
        "get_witness_count",
        "get_witness_schedule",
        "get_witnesses",
        "get_witnesses_by_vote",
        "is_known_transaction",
        "list_proposal_votes",
        "list_proposals",
        "lookup_account_names",
        "lookup_accounts",
        "lookup_witness_accounts",
        "verify_authority",
        "find_rc_accounts",
        "list_rc_accounts",
        "list_rc_direct_delegations"
    ],
    "account_by_key_api": ["get_key_references"],
    "bridge": [
        "account_notifications",
        "does_user_follow_any_lists",
        "get_account_posts",
        "get_community",
        "get_community_context",
        "get_discussion",
        "get_follow_list",
        "get_payout_stats",
        "get_post",
        "get_post_header",
        "get_profile",
        "get_ranked_posts",
        "get_relationship_between_accounts",
        "list_all_subscriptions",
        "list_communities",
        "list_community_roles",
        "list_pop_communities",
        "list_subscribers",
    ],
    "account_history_api": [
        "enum_virtual_ops",
        "get_account_history",
        "get_ops_in_block",
        "get_transaction",
    ],
    "block_api": ["get_block", "get_block_header", "get_block_range"],
    "database_api": [
        "find_account_recovery_requests",
        "find_accounts",
        "find_change_recovery_account_requests",
        "find_collateralized_conversion_requests",
        "find_comments",
        "find_decline_voting_rights_requests",
        "find_escrows",
        "find_hbd_conversion_requests",
        "find_limit_orders",
        "find_owner_histories",
        "find_proposals",
        "find_recurrent_transfers",
        "find_savings_withdrawals",
        "find_vesting_delegation_expirations",
        "find_vesting_delegations",
        "find_votes",
        "find_withdraw_vesting_routes",
        "find_witnesses",
        "get_active_witnesses",
        "get_comment_pending_payouts",
        "get_config",
        "get_current_price_feed",
        "get_dynamic_global_properties",
        "get_feed_history",
        "get_hardfork_properties",
        "get_order_book",
        "get_potential_signatures",
        "get_required_signatures",
        "get_reward_funds",
        "get_transaction_hex",
        "get_version",
        "get_witness_schedule",
        "is_known_transaction",
        "list_account_recovery_requests",
        "list_accounts",
        "list_change_recovery_account_requests",
        "list_collateralized_conversion_requests",
        "list_comments",
        "list_decline_voting_rights_requests",
        "list_escrows",
        "list_hbd_conversion_requests",
        "list_limit_orders",
        "list_owner_histories",
        "list_proposal_votes",
        "list_proposals",
        "list_savings_withdrawals",
        "list_vesting_delegation_expirations",
        "list_vesting_delegations",
        "list_votes",
        "list_withdraw_vesting_routes",
        "list_witness_votes",
        "list_witnesses",
        "verify_authority",
        "verify_signatures",
    ],
    "debug_node_api": [
        "debug_generate_blocks",
        "debug_generate_blocks_until",
        "debug_get_hardfork_property_object",
        "debug_get_json_schema",
        "debug_get_witness_schedule",
        "debug_has_hardfork",
        "debug_pop_block",
        "debug_push_blocks",
        "debug_set_hardfork",
    ],
    "follow_api": [
        "get_account_reputations",
        "get_blog",
        "get_blog_authors",
        "get_blog_entries",
        "get_feed",
        "get_feed_entries",
        "get_follow_count",
        "get_followers",
        "get_following",
        "get_reblogged_by",
    ],
    "market_history_api": [
        "get_market_history",
        "get_market_history_buckets",
        "get_order_book",
        "get_recent_trades",
        "get_ticker",
        "get_trade_history",
        "get_volume",
    ],
    "network_broadcast_api": ["broadcast_block", "broadcast_transaction"],
    "rc_api": ["find_rc_accounts", "get_resource_params", "get_resource_pool"],
    "reputation_api": ["get_account_reputations"],
}

DISCUSSIONS_BY = ("active", "blog", "cashout", "children", "created", "hot", "payout", "promoted", "trending", "votes")

"""
    Hive Blockchain Operations
    Indices reflect its equivalent integer value (w/ 128-bit bitmasking)
    WARNING: Do NOT change order of operations!
"""
BLOCKCHAIN_OPERATIONS = [
    "vote",
    "comment",
    "transfer",
    "transfer_to_vesting",
    "withdraw_vesting",
    "limit_order_create",
    "limit_order_cancel",
    "feed_publish",
    "convert",
    "account_create",
    "account_update",
    "witness_update",
    "account_witness_vote",
    "account_witness_proxy",
    "pow",
    "custom",
    "report_over_production",
    "delete_comment",
    "custom_json",
    "comment_options",
    "set_withdraw_vesting_route",
    "limit_order_create2",
    "claim_account",
    "create_claimed_account",
    "request_account_recovery",
    "recover_account",
    "change_recovery_account",
    "escrow_transfer",
    "escrow_dispute",
    "escrow_release",
    "pow2",
    "escrow_approve",
    "transfer_to_savings",
    "transfer_from_savings",
    "cancel_transfer_from_savings",
    "custom_binary",
    "decline_voting_rights",
    "reset_account",
    "set_reset_account",
    "claim_reward_balance",
    "delegate_vesting_shares",
    "account_create_with_delegation",
    "witness_set_properties",
    "account_update2",
    "create_proposal",
    "update_proposal_votes",
    "remove_proposal",
    "fill_convert_request",
    "author_reward",
    "curation_reward",
    "comment_reward",
    "liquidity_reward",
    "producer_reward",
    "interest",
    "fill_vesting_withdraw",
    "fill_order",
    "shutdown_witness",
    "fill_transfer_from_savings",
    "hardfork",
    "comment_payout_update",
    "return_vesting_delegation",
    "comment_benefactor_reward",
    "return_vesting_delegation",
    "comment_benefactor_reward",
    "producer_reward",
    "clear_null_account_balance",
    "proposal_pay",
    "sps_fund",
    "hardfork_hive",
    "hardfork_hive_restore",
]

# HIVE PRIVATE KEY ROLES
ROLES = {
    "all": ["owner", "active", "posting", "memo"],
    "comment": ["posting", "active", "owner"],
    "follow": ["posting", "active", "owner"],
    "vote": ["posting", "active", "owner"],
    "transfer_to_vesting": ["active", "owner"],
    "transfer_to_savings": ["active", "owner"],
    "transfer": ["active", "owner"],
    "custom_json": ["active"],
    "owner": ["owner"],
    "active": ["active"],
    "posting": ["posting"],
    "memo": ["memo"],
}

# HIVE ASSETS
ASSETS = {
    "HBD": {"nai": "@@000000013", "precision": 3},
    "HIVE": {"nai": "@@000000021", "precision": 3},
    "VESTS": {"nai": "@@000000037", "precision": 6},
}

# Blockchain Transaction Expiration Format in UTC
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%Z"

"""
    Hive Nodes
    Nodes availability and reliability may change.
    Custom nodes may be specified to override these options.
"""
NODES = [
    "api.hive.blog",
    "api.openhive.network",
    "anyx.io",
    "hived.privex.io",
    "rpc.ausbit.dev",
    "techcoderx.com",
    "rpc.ecency.com",
    "hive.roelandp.nl",
    "hived.emre.sh",
    "api.deathwing.me",
    "api.c0ff33a.uk",
    "hive-api.arcange.eu",
    # "api.pharesim.me",
]

        
RE_PROTOCOL = re.compile(r"http[s]{0,1}\:[\/]{2}")
RE_URL_PATH = re.compile(r"[\/][\w\W]+")
RE_USERNAME = re.compile(r"[a-z][\w\.\-]{2,15}")
RE_SNAKE_CASE = re.compile(r"[^\w\-]+")
RE_PERMLINK = re.compile(r"[\w\-\%]{0,255}")
RE_COMMUNITY = re.compile(r"\bhive-[\d]{1,}")
RE_DATETIME = re.compile(r"\d{4}\-\d{2}\-\d{2}T\d{2}:\d{2}:\d{2}")
RE_NEWLINES = re.compile(r"[\r\n]")
RE_WORDS = re.compile(r"[^\w\ ]")
RE_IMAGES = re.compile(r"!\[[^\]]*\]\([^\)]+\)")
RE_NUMERIC = re.compile(r"\d+")