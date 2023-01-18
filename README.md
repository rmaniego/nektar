![](/resources/banner.png)

# nektar
[![](https://images.hive.blog/20x20/https://images.ecency.com/DQmQBYsZc8G6awKZcVbonRsJBUWJ1HTZy3WuTaMXvBreyhj/4511507.png) Nektar](#) a Hive API SDK for Python.

## Official Release
**nektar** can now be used on your Python projects through PyPi by running pip command on a Python-ready environment.

`pip install hive-nektar --upgrade`

Current version is 0.9.\*, but more updates are coming soon.

This is compatible with Python 3.9 or later.

## WARNINGS:
 - This package is still under development, some future breakage is inevitable.
 - Some AppBase API methods are still under development and subject to change.
 - Do NOT copy your private keys in your codes!

## Features
**1.** Lightweight package for small Hive dApps or projects. <br>
**2.** Readily available methods using the `nektar.Waggle()` class. <br>
**3.** Highly costumizable via `appbase` module. <br>

## Nektar Module
Contains the Waggle, Swarm, and Drone classes. 

***WARNING:*** Store WIFs securely in a separate file!

**Import Module**
```python
from nektar import Nektar
import json

wifs = { "active": "5*" , "posting": "5*"}
hive = Nektar(username, wifs=wifs)

# Hive Developer Portal > Understanding Configuration Values
# https://developers.hive.io/tutorials-recipes/understanding-configuration-values.html
data = hive.get_config()
print(json.dumps(data, indent=2))

# get configuration values
data = hive.get_config(field="HIVE_CHAIN_ID", fallback="bee*")
print("HIVE_CHAIN_ID: " + str(data))

# get user's resource credits
prin(hive.resource_credits())
print(hive.resource_credits("valid-username"))

# get user's manabar
percentage = hive.manabar()
print("Current Mana: " + str(int(percentage)) + "%")

# transfer HBD to another account
receiver = "valid-username"
amount = 0.001
asset = "HBD"
message = "Thanks for supporting us!"
hive.memo(receiver, amount, asset, message)

# transfer HIVE to another account
receiver = "valid-username"
amount = 0.001
asset = "HIVE"
message = "Thanks for supporting us!"
result = hive.memo(receiver, amount, asset, message)

# transfer HBD to savings
receiver = "valid-username"
amount = 0.001
asset = "HBD"
message = "Thanks for supporting us!"
hive.transfer_to_savings(receiver, amount, asset, message)

# transfer HIVE to savings
receiver = "valid-username"
amount = 0.001
asset = "HIVE"
message = "Thanks for supporting us!"
hive.transfer_to_savings(receiver, amount, asset, message)

# transfer HIVE to vesting (power up)
receiver = "valid-username"
amount = 0.001
hive.transfer_to_vesting(receiver, amount)

# Broadcasting a custom JSON (Posting key)
hive.custom_json(
    id_="nektar-tests",
    jdata={ "test": "nektar" },
    required_posting_auths=["valid-username"]

# Broadcasting a custom JSON (Active key)
hive.custom_json(
    id_="nektar-tests",
    jdata={ "test": "nektar" },
    required_auths=["valid-username"]

```

**Import Module**
```python
from nektar import Nektar
import json

wifs = { "active": "5*" , "posting": "5*"}
hive = Nektar(username, wifs=wifs)
```

## Waggle Class 
Methods for blogging and engagement
**Import Module**
```python
from nektar import Waggle
import json
```

**Basic Setup**
```python
from nektar import Waggle

hive = Waggle(username)
```

**Setup Application**
```python

username = "hive-nektar"
app_name = "nektar.app"
version = "2022.10.05"

hive = Waggle(username, app=app_name, version=version)
```

**Setup Application with WIF/s** 

***WARNING:*** Store WIFs securely in a separate file!
```python

## option 1
wif = "5*"
role="posting"
username = "hive-nektar"

hive = Waggle(username, wif=wif, role=role)

## option 2
username = "hive-nektar"

wifs = { "active": "5*" }
hive = Waggle(username, wifs=wifs)

```

**Initialize with Custom Parmeters**
```python

custom_nodes = ["testnet.openhive.network"]
CHAIN_ID_TESTNET = "18dcf0a285365fc58b71f18b3d3fec954aa0c141c44e4e5cb4cf777b9eab274e"
hive = Waggle("valid-username", wifs=wifs, nodes=custom_nodes, chain_id=CHAIN_ID_TESTNET, timeout=25, retries=1, warning=True)

```

**Get account details**
```python
metadata = json.loads(hive.account["posting_json_metadata"])
name = metadata["profile"]["name"]
```

**Get Blockchain Constants** 

```python
# Hive Developer Portal > Understanding Configuration Values
# https://developers.hive.io/tutorials-recipes/understanding-configuration-values.html
data = hive.get_config()
print(json.dumps(data, indent=4))
    
data = hive.get_config(field="HIVE_CHAIN_ID", fallback="bee*")
print("HIVE_CHAIN_ID: " + str(data))
```

**Browse Communities** 
```python

## get up to 200 communities by rank
communities = hive.communities(limit=200)
for community in communities:
    print(community["name"] + "\t" + community["title"])

communities = {}
sorting = ["new", "rank", "subs"]
for sort in sorting:
    ## get up to 1000 communities per sorting filter
    for community in hive.communities(sort=sort):
        communities.update({community["name"]: community})
```

**Get Posts with tag** 
Get posts in a community by sorting filter:
 - `created`
 - `trending`
 - `hot`
 - `promoted`
 - `payout`
 - `payout_comments`
 - `muted`

```python
tag = "travel"
posts = hive.posts(tag, limit=100, sort="created")
print(posts[0]["author"])
print(posts[0]["permlink"])
print(posts[0]["title"])
```

**Get Posts in a Community** 
Get posts in a community by sorting filter:
 - `created`
 - `trending`
 - `hot`
 - `promoted`
 - `payout`
 - `payout_comments`
 - `muted`

```python

community = "hive-1*"  # supply with a valid community name
posts = hive.posts(community, limit=100, sort="created")
print(posts[0]["author"])
print(posts[0]["permlink"])
print(posts[0]["title"])
```

**Get Posts with a Tag** 
Get posts in a community by sorting filter:
 - `created`
 - `trending`
 - `hot`
 - `promoted`
 - `payout`
 - `payout_comments`
 - `muted`.

```python
tag = "nature"
posts = hive.posts(tag, limit=10, sort="created")
for post in posts:
    print(post["title"])
```

**Get Community Sunscribers** 
```python

subscribers = {}
community = "hive-1*"  # supply with a valid community name
for subscriber in hive.subscribers(community, limit=1000):
    subscribers.update({subscriber[0]: subscriber})
    print(subscriber[0])
```

**Search Accounts Starting with a *pattern*** 
```python
accounts = hive.accounts(start="h", limit=1000)
```

**Get Account `raw` Current Resource Credits** 
```python
## resource credit of the initialized account
data = hive.resource_credits()
print(json.dumps(data, indent=4))

## specify another account
data = hive.resource_credits("valid-account")
print(json.dumps(data, indent=4))
```

**Get Account Manabar Percentage** 
```python
## manabar of the initialized account
percentage = hive.manabar()
print("Current Mana: " + str(int(percentage)) + "%")

## specify another account
percentage = hive.manabar("valid-account")
print("Current Mana: " + str(int(percentage)) + "%")
```

**Get Account Reputation** 
```python
## reputation of the initialized account
reputation = hive.reputation(score=False)
print("Reputation: " + str(reputation))

## reputation of the initialized account, converted to score
score = hive.reputation()
print("Reputation score: " + str(score))

## specify another account, converted to score
score = hive.reputation(account="valid-username")
print("Reputation score: " + str(score))
```

**Get the List of Followers** 
```python

## followers of the initialized account
followers = hive.followers()
print(followers)

## or using a valid account username
followers = hive.followers(account="valid-username")
print(followers)
```

**Follow or Unfollow an Account**
```python
account = "valid-username"
hive.follow(account)

# options to unfollow
hive.follow(account, unfollow=True)
hive.unfollow(account)
```

**Get List of Account History** 
```python
    
# up to 1000 operations, most recent first
transactions = hive.history()
print("Transactions:", json.dumps(transactions[1], indent=4))

# up to 1000 upvote operations of another acount
transactions = hive.history(account="oniemaniego", start=1000, low=0)
print("Transactions:", json.dumps(transactions[1], indent=4))
    
# up to 100 operations of another acount
transactions = hive.history(account="oniemaniego", start=1000, limit=100)
for transaction in transactions[:1]:
    print(transaction[0], transaction[1]["op"])
```

**Get the List of Delegators** 
```python

## followers of the initialized account
delegators = hive.delegators()
for delegator, data in delegators.items():
    print(delegator)
    for dt, vests in data.items():
        print(dt, vests)


## or using a valid account username
delegators = hive.delegators("valid-username")
for delegator, data in delegators.items():
    print(delegator)
    for dt, vests in data.items():
        print(dt, vests)

## only show active delegations
delegators = hive.delegators(active=True)
for delegator, vests in delegators.items():
    print(delegator, vests)
```

**Get the List of Delegatees** 
```python

## followers of the initialized account
delegatees = hive.delegatees()
for delegatee, data in delegatees.items():
    print(delegatee)
    for dt, vests in data.items():
        print(dt, vests)


## or using a valid account username
delegatees = hive.delegatees("valid-username")
for delegatee, data in delegatees.items():
    print(delegatee)
    for dt, vests in data.items():
        print(dt, vests)

## only show active delegations
delegatees = hive.delegatees(active=True)
for delegatee, vests in delegatees.items():
    print(delegatee, vests)
```

**Get Blog Posts** 
Get posts of an account by sorting filter:
 - `blog`
 - `feed`
 - `post`
 - `replies`
 - `payout`

```python
## blog posts of the initialized account
blogs = hive.blogs(limit=10)
for blog in blogs:
    for key, value in blog.items():
        print(key + ":", value)
        
## customized blog search from another account
blogs = hive.blogs(account="valid-username", sort="blog")
for blog in blogs:
    for key, value in blog.items():
        print(key + ":", value)
```

**Get Outward Comments** 
Get comments made by an account/

```python
comments = hive.comments(limit=20)
for comment in comments:
    print(comment["body"])

## comments of another account
comments = hive.comments(username="valid-username", limit=100)
for comment in comments:
    print(json.dumps(comment, indent=2))
```

**Access a Blog Post/Comment (Bridge API)** 
If the post or comment does not exists in the blockchain, it will return an empty dictionary.

```python

author = "valid-username"
permlink = "valid-permlink"
content = hive.get_post(author, permlink)
print(json.dumps(content, indent=4))
    
author = "valid-username"
permlink = "test-permlink-abc-123-def-456"
content = hive.get_post(author, permlink, retries=5)
if not content:
    print("The post is not yet in the blockchain.")
print(json.dumps(content, indent=2))
```

**Access a Blog Post/Comment (Condenser API)** 
If the post or comment does not exists in the blockchain, it will return an empty dictionary.

```python

author = "valid-username"
permlink = "valid-permlink"
content = hive.get_post(author, permlink)
print(json.dumps(content, indent=4))
    
author = "valid-username"
permlink = "test-permlink-abc-123-def-456"
content = hive.get_content(author, permlink, retries=2)
if not content:
    print("The post is not yet in the blockchain.")
print(json.dumps(content, indent=2))
```

**Create a Post Programmatically** 

***WARNING:*** Do NOT abuse Hive, post only quality contents not more than once a day.

```python
    
title = "Make Your Title Catchy, But Not ClickBait-y"
body =  "# This is a header\n\n" \
        "## Adding a `h2` Header" \
        "![Image Caption](https://image.link.goes/here)\n\n" \
        "<center>How to center a text?</center>\n\n" \
        "This is how to make it *itzlic*, **bold**, or ***both***!\n\n" \
        "Drink more H<sub>2</sub>O<sup>[citatation needed]</sup> everyday.\n\n" \
        "<br> this is a line break, below is a horizontal rule:\n\n" \
        "---" \
        "Click this [link](https://www.markdownguide.org/) to learn more about Markdowwn.\n\n"
description = "My first blog using Nektar!"
tags = "devtalk nektar hive api coderundebug"
community = "hive-1*"  # use a valid community name

hive.new_post(title, body, description, tags, community)
```

**Reblog a Post**
```python
author = "valid-username"
permlink = "valid-permlink"
hive.reblog(author, permlink)
```

**Reply to a Post** 
***WARNING:*** Do NOT abuse Hive, do not create spam comments.
```python

author = "valid-username"
permlink = "valid-permlink"
body = "Allows markdown formatted text."
hive.reply(author, permlink, body)
```

**Get all replies on a blog post.** 
```python

author = ""
permlink = ""

replies = hive.replies(author, permlink)
print(json.dumps(replies, indent=2))
```

**Get all accounts who reblogged the blog post.** 
```python

author = ""
permlink = ""

accounts = hive.reblogs(author, permlink)
print("Reblogged by: " + ", ".join(accounts))
```

**Vote on A Post** 
```python

author = ""
permlink = ""
weight = 10000  # -10000 to 10000, where 1000 = 100%

hive.vote(author, permlink, weight)
```

**Get active votes on a blog post.** 
```python

author = ""
permlink = ""

votes = hive.votes(author, permlink)
print(json.dumps(votes, indent=2))
```

**Send a Memo** 
```python

receiver = "valid-username"
amount = 0.001
asset = "HBD"
message = "Sending you some HBDs..."
hive.memo(receiver, amount, asset, message)
```

**Create a Custom JSON (Active Key)** 
```python

protocol_id = "nektar_admin"
json_data = { "app": "nektar.app/2022.10.05" }
required_auths = ["valid-username"]
required_posting_auths = []
hive.custom_json(protocol_id, json_data, required_auths, required_posting_auths)
```

**Check if Transaction has the Neccessary Auths** 
Will only check if the necessary WIF has signed the transaction, will not broadcast it.
This is also available in `post`, `reply`, `vote`, and `memo` methods.
```python
protocol_id = "nektar_admin"
json_data = { "app": "nektar.app/2022.10.05" }
required_auths = ["valid-username"]
required_posting_auths = []
hive.custom_json(protocol_id, json_data, required_auths, required_posting_auths, verify_only=True)
```

**Check if a Custom Transaction has the Necessary Signatures** 
Will only check if the necessary WIF has signed the transaction, will not broadcast it.
This is also available in `post`, `reply`, `vote`, and `memo` methods.
```python

signed_transaction = [ { "ref_block_num": 0, "ref_block_prefix": 0, "expiration": "1970-01-01T00:00:00", "operations": [], "extensions": [], "signatures": [] }]

verified = hive.verify_authority(signed_transaction)
print("OK:", verified)
```

**Power Up** 
```python
hive.power_up("valid-username", 100)
```

## Swarm Class 
Community Management methods
```python
from nektar import Swarm

## Initialize Swarm class
hive = Swarm("hive-*", "valid-username", wif="5*", role="posting")

## Initialize Swarm class with dictionary of WIFs
hive = Swarm("hive-*", "valid-username", wifs=wifs)

## Initialize Swarm class with app and version")
hive = Swarm("hive-*", "valid-username", app="nektar.app", version="2022.10.05")

## Initialize Swarm class with custom parameters")
hive = Swarm("hive-*", "valid-username", wifs=wifs, timeout=25, retries=1, warning=True)

## Mute a post
hive.mute("valid-username", "valid-permlink", "Offtopic")
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Unmute a post - option 1
hive.mute("valid-username", "valid-permlink", "Offtopic", mute=False)
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Unmute a post - option 2
hive.unmute("valid-username", "valid-permlink", "On topic, apologies")
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Mark post as spam
hive.mark_spam("valid-username", "valid-permlink")
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Update community properties
title = "Community Name"
about = "About information"
is_nsfw = False
description = "This is a description"
flag_text = "..."
hive.update(title, about, is_nsfw, description, flag_text)
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Subscribe to a community
hive.subscribe()
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Unsubscribe to a community - option 1
hive.subscribe(subscribe=False)
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Unsubscribe to a community - option 2
hive.unsubscribe()
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Pin a post
hive.pin("valid-username", "valid-permlink")
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Unpin a post - option 1
hive.pin("valid-username", "valid-permlink", pin=False)
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Unpin a post - option 2
hive.unpin("valid-username", "valid-permlink")
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))

## Flag a post
hive.flag("valid-username", "valid-permlink", "flagging post for reason...")
print("Transaction: " + json.dumps(hive.appbase.signed_transaction, indent=2))
```

## AppBase Module
**Basic Usage**
```python
from appbase import AppBase

CHAIN_ID_MAINNET = "beeab0de00000000000000000000000000000000000000000000000000000000"
CHAIN_ID_TESTNET = "18dcf0a285365fc58b71f18b3d3fec954aa0c141c44e4e5cb4cf777b9eab274e"

## Initialize AppBase Class
hive = AppBase()

## Initialize AppBase Class with custom parameters
custom_nodes = ["testnet.openhive.network"]
hive = AppBase(nodes=custom_nodes, chain_id=CHAIN_ID_TESTNET, timeout=5, retries=1, warning=True)

## Change to custom nodes
hive.custom_nodes(custom_nodes)

## Add new WIF and equivalent role
hive.append_wif(wif="5*", role="posting")
hive.append_wif(wif="5*", role="active")

## Add new dictionary of roles and their equivalent WIFs
wifs = {"posting": "5*", "active": "5*"}
hive.append_wif(wifs)

## Change retries to custom value
hive.set_timeout(15)

## Read the actual Hive API documentation for proper guidance
## https://developers.hive.io/apidefinitions/

## Access API and its methods - generic
hive.api("condenser")
hive.api("condenser_api")

## `account_by_key_api.get_key_references`
# version = hive.api("account_by_key_api").*
params = {"keys": "STM*"]}
data = hive.account_by_key().get_key_references(params)
print("Account by public key: " + json.dumps(data, indent=2))

## `bridge.get_profile`
# version = hive.api("bridge").*
params = {"account": "valid-username1", "observer": "valid-username2"}
data = hive.bridge().get_profile(params)
print("Profile: " + json.dumps(data, indent=2))

## `account_history_api.get_account_history`
# version = hive.api("account_history").*
params = {
    "account": "valid-username",
    "start": 1000,
    "limit": 1000,
    "include_reversible": True,
    "operation_filter_low": 0,
    "operation_filter_high": 1,
}
data = hive.account_history().get_account_history(params)
print("Account history: " + json.dumps(data, indent=2))

## `block_api.get_block`
params = {"block_num": 8675309}
data = hive.block().get_block(params)
print("Block: " + json.dumps(data, indent=2))

## Create an instance for specific API only.
condenser = hive.condenser()

params = "valid-username", "valid-permlink"]
data = condenser.get_content(params)
print("Content #1: " + json.dumps(data, indent=2))

params = "valid-username", 0, 10]
data = condenser.get_blog(params)
print("Content #2: " + json.dumps(data, indent=2))

## Using the `request` method
method = "rc_api.find_rc_accounts"
params = {"accounts": "valid-username"]}
data = hive.request(method, params, strict=False)
print("Accounts: " + json.dumps(data, indent=2))

## Using the `broadcast` method - `condenser_api`
method = "condenser_api.get_transaction_hex"
transaction = {
    "ref_block_num": 123456,
    "ref_block_prefix": 1234567890,
    "expiration": "2022-10-05T18:00:00",
    "operations": [
        [
            "vote",
            {
                "voter": "valid-username1",
                "author": "valid-username2",
                "permlink": "valid-permlink",
                "weight": 10000,
            },
        ]
    ],
    "extensions": [],
}
data = hive.broadcast(method, transaction, strict=False)
print("Transaction hex: " + data)

```