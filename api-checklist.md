![](/resources/banner.png)

# nektar

[![](https://images.hive.blog/20x20/https://images.ecency.com/DQmQBYsZc8G6awKZcVbonRsJBUWJ1HTZy3WuTaMXvBreyhj/4511507.png) Nektar](#) a Hive API SDK for Python.

## API Checklist

Basically, you can access all supported APIs and methods using the `AppBase` class, but the following are wrapped in the `Nektar` class, so you can call and use it faster. 

| Available? | Condenser API Method                   | Nektar |
| ---------- | -------------------------------------- | ------ |
| *NA*       | ~~broadcast_block~~                    |        |
| /          | broadcast_transaction                  |        |
| /          | broadcast_transaction_synchronous      |        |
|            | find_proposals                         |        |
|            | find_rc_accounts                       |        |
|            | find_recurrent_transfers               |        |
| *NA*       | ~~get_account_bandwidth~~              |        |
|            | get_account_count                      |        |
| /          | get_account_history                    |        |
|            | get_account_references                 |        |
|            | get_account_reputations                |        |
|            | get_account_votes                      |        |
| /          | get_accounts                           |        |
| /          | get_active_votes                       |        |
|            | get_active_witnesses                   |        |
| /          | get_block                              |        |
| /          | get_block_header                       |        |
| /          | get_blog                               |        |
|            | get_blog_authors                       |        |
|            | get_blog_entries                       |        |
| /          | get_chain_properties                   |        |
|            | get_collateralized_conversion_requests |        |
|            | get_comment_discussions_by_payout      |        |
|            | get_config                             |        |
| /          | get_content                            |        |
| /          | get_content_replies                    |        |
|            | get_conversion_requests                |        |
|            | get_current_median_history_price       |        |
|            | get_discussions_by_active              |        |
|            | get_discussions_by_author_before_date  |        |
|            | get_discussions_by_blog                |        |
|            | get_discussions_by_cashout             |        |
|            | get_discussions_by_children            |        |
|            | get_discussions_by_comments            |        |
|            | get_discussions_by_created             |        |
|            | get_discussions_by_feed                |        |
|            | get_discussions_by_hot                 |        |
|            | get_discussions_by_promoted            |        |
|            | get_discussions_by_trending            |        |
|            | get_discussions_by_votes               |        |
| /          | get_dynamic_global_properties          |        |
|            | get_escrow                             |        |
|            | get_expiring_vesting_delegations       |        |
|            | get_feed                               |        |
|            | get_feed_entries                       |        |
|            | get_feed_history                       |        |
|            | get_follow_count                       |        |
| /          | get_followers                          |        |
| /          | get_following                          |        |
|            | get_hardfork_version                   |        |
|            | get_key_references                     |        |
|            | get_market_history                     |        |
|            | get_market_history_buckets             |        |
|            | get_next_scheduled_hardfork            |        |
|            | get_open_orders                        |        |
|            | get_ops_in_block                       |        |
|            | get_order_book                         |        |
|            | get_owner_history                      |        |
|            | get_post_discussions_by_payout         |        |
|            | get_potential_signatures               |        |
|            | get_reblogged_by                       |        |
|            | get_recent_trades                      |        |
|            | get_recovery_request                   |        |
|            | get_replies_by_last_update             |        |
|            | get_required_signatures                |        |
|            | get_reward_fund                        |        |
|            | get_savings_withdraw_from              |        |
|            | get_savings_withdraw_to                |        |
|            | get_state                              |        |
|            | get_tags_used_by_author                |        |
|            | get_ticker                             |        |
|            | get_trade_history                      |        |
|            | get_transaction                        |        |
| /          | get_transaction_hex                    |        |
|            | get_trending_tags                      |        |
|            | get_version                            |        |
|            | get_vesting_delegations                |        |
|            | get_volume                             |        |
|            | get_withdraw_routes                    |        |
|            | get_witness_by_account                 |        |
|            | get_witness_count                      |        |
|            | get_witness_schedule                   |        |
|            | get_witnesses                          |        |
|            | get_witnesses_by_vote                  |        |
|            | is_known_transaction                   |        |
|            | list_proposal_votes                    |        |
|            | list_proposals                         |        |
|            | list_rc_accounts                       |        |
|            | list_rc_direct_delegations             |        |
|            | lookup_account_names                   |        |
|            | lookup_accounts                        |        |
|            | lookup_witness_accounts                |        |
|            | verify_account_authority               |        |
| /          | verify_authority                       |        |