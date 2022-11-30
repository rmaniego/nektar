# nektar
[![](https://images.hive.blog/20x20/https://images.ecency.com/DQmQBYsZc8G6awKZcVbonRsJBUWJ1HTZy3WuTaMXvBreyhj/4511507.png) Nektar](#) a Hive API SDK for Python.

## Nektar Module > Condenser Specific
The condenser methods can directly be used using the AppBase class, but will require valid formatting of the parameters. Using the Nektar class easily create an abstraction for easier usage of the API methods.

**Initialization**
```python
hive = Condenser()
```

**get_account_count**
```python
count = hive.get_account_count()
print("Accounts:", count)
```

**get_account_history**
```python
# hive.get_account_history(account, start, limit, low=0)
result = hive.get_account_history("valid-username", -1, 1)
print("latest:", json.dumps(result, indent=2))

result = hive.get_account_history("valid-username", 1, 1)
print("first:", json.dumps(result, indent=2))

result = hive.get_account_history("valid-username", 1000, 1000)
print(json.dumps(result, indent=2))
```

**get_account_reputations**
```python
# hive.get_account_reputations(start, limit)
result = hive.get_account_reputations("ba", 1000)
print(json.dumps(result, indent=2))
```

**get_accounts**
```python
# hive.get_accounts(accounts, delayed_votes_active)
accounts = ["gtg"]
result = hive.get_accounts(accounts, True)
print(json.dumps(result, indent=2))

accounts = ["gtg", "abc"]
result = hive.get_accounts(accounts, False)
print(json.dumps(result, indent=2))
```

**get_active_votes**
```python
author = "hivehealth"
permlink = "the-updated-easy-onboarding-manual"
result = hive.get_active_votes(author, permlink)
print(json.dumps(result, indent=2))
```

**get_active_witnesses**
```python
result = hive.get_active_witnesses()
print(json.dumps(result, indent=2))
```

**get_active_witnesses**
```python
result = hive.get_active_witnesses()
print(json.dumps(result, indent=2))
```

**get_block**
```python
# hive.get_block(block_num)
result = hive.get_block(1)
print(json.dumps(result, indent=2))
```

**get_block_header**
```python
# hive.get_block_header(block_num)
result = hive.get_block_header(1)
print(json.dumps(result, indent=2))
```

**get_blog**
```python
# hive.get_blog(account, start_entry_id, limit)
result = hive.get_blog("valid-username", 0, 500)
print(json.dumps(result, indent=2))
```

**get_blog_authors**
`WARNING:` Assert Exception:false: Supported by hivemind 
```python
# hive.get_blog_authors(account)
result = hive.get_blog_authors("valid-username")
print(json.dumps(result, indent=2))
```

**get_blog_authors**
```python
# hive.get_blog_entries(account, start_entry_id, limit)
result = hive.get_blog_entries("valid-username", 0, 500)
print(json.dumps(result, indent=2))
```

**get_chain_properties**
```python
result = hive.get_chain_properties()
print(json.dumps(result, indent=2))
```

**get_comment_discussions_by_payout**
```python
# hive.get_comment_discussions_by_payout(tag, limit, filter_tags, select_authors, select_tags, truncate_body)
result = hive.get_comment_discussions_by_payout("hive", 10, truncate_body=0)
print(json.dumps(result, indent=2))
```

**list_proposal_votes, by proposal voter**
```python
# hive.list_proposal_votes(pid, limit, order, direction, status)
result = hive.list_proposal_votes(0, 10, "by_proposal_voter", "ascending", "all")
print(json.dumps(result, indent=2))
```

**list_proposal_votes, by voter proposal**
```python
# hive.list_proposal_votes(pid, limit, order, direction, status)
result = hive.list_proposal_votes(0, 10, "by_voter_proposal", "ascending", "all")
print(json.dumps(result, indent=2))
```

**list_proposal_votes, by voter proposal**
```python
# hive.list_proposal_votes(voter, limit, order, direction, status)
result = hive.list_proposal_votes("valid-username", 5, "by_voter_proposal", "descending", "active")
print(json.dumps(result, indent=2))
```

**list_proposals, by creator**
```python
# hive.list_proposals(start, limit, order, direction, status)
result = hive.list_proposals("valid-username", 1000, "by_creator", "ascending", "active")
print(json.dumps(result, indent=2))
```