# nektar
[![](https://images.hive.blog/20x20/https://images.ecency.com/DQmQBYsZc8G6awKZcVbonRsJBUWJ1HTZy3WuTaMXvBreyhj/4511507.png) Nektar](#) a Hive API SDK for Python.

## Nektar Module > Condenser Specific
The condenser methods can directly be used using the AppBase class, but will require valid formatting of the parameters. Using the Nektar class easily create an abstraction for easier usage of the API methods.

Check the ReadMe for the initialization process.

**get_account_count**
```python
hive.find_proposals(0)
```

**list_proposal_votes, by proposal voter**
```python
pid = 0
limit = 10
order = "by_proposal_voter"
direction = "ascending"
status = "all"
result = hive.list_proposal_votes(pid, limit, order, direction, status)
print(json.dumps(result, indent=2))
```

**list_proposal_votes, by voter proposal**
```python
pid = 0
limit = 10
order = "by_voter_proposal"
direction = "ascending"
status = "all"
result = hive.list_proposal_votes(pid, limit, order, direction, status)
print(json.dumps(result, indent=2))
```

**list_proposal_votes, by voter proposal**
```python
voter = "valid-username"
limit = 10
order = "by_voter_proposal"
direction = "descending"
status = "active"
result = hive.list_proposal_votes(voter, limit, order, direction, status)
print(json.dumps(result, indent=2))
```

**list_proposals, by creator**
```python
start = "gtg"
limit = 10
order = "by_creator"
direction = "ascending"
status = "active"
result = hive.list_proposals(start, limit, order, direction, status)
print(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
```