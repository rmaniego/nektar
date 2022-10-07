![](/resources/banner.png)

# nektar
nektar allows communication to the Hive blockchain using the Hive API.

## Official Release
**nektar** can now be used on your Python projects through PyPi by running pip command on a Python-ready environment.

`pip install hive-nektar --upgrade`

Current version is 0.9.\*, but more updates are coming soon.

This is compatible with Python 3.9 or later.

## WARNINGS:
 - This package is still under development, some future breakage is inevatable.
 - Some AppBase API methods are still under development and subject to change.
 - Do NOT copy your private keys in your codes!

## Features
**1.** Lightweight package for small Hive dApps or projects. <br>
**2.** Readily available methods using the `nektar.Waggle()` class. <br>
**3.** Highly costumizable via `appbase` module. <br>

## Nektar Module
**Import Module**
```python
from nektar import Waggle
```

**Basic Setup**
```python
from nektar import Waggle

username = "hive-username"
app = "nectar.app"
version = "2022.10.05"

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

username = "hive-nektar"
app_name = "nektar.app"
version = "2022.10.05"

hive = Waggle(username, app=app_name, version=version)

wifs = [ "5*" ]

hive.append_wif(wifs)
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

**Get Posts in a Community** 
Get posts in a community by sorting filter `created`, `trending`, `hot`, `promoted`, `payout`, `payout_comments`, or `muted`.
```python

community = "hive-1*"  # supply with a valid community name
posts = hive.posts(community, limit=100, sort="created")
print(posts[0]["author"])
print(posts[0]["permlink"])
print(posts[0]["title"])
```

**Get Posts with a Tag** 
Get posts in a community by sorting filter: `created`, `trending`, `hot`, `promoted`, `payout`, `payout_comments`, or `muted`.
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

**Get the List of Followers** 
```python

## followers of the initialized account
followers = hive.followers()
print(followers)

## or using a valid account username
followers = hive.followers(account="valid-username")
print(followers)
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
Get posts of an account by sorting filter: `blog`, `feed`, `post`, `replies`, or `payout`
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

**Vote on A Post** 
```python

author = ""
permlink = ""
weight = 10000  # -10000 to 10000, where 1000 = 100%

hive.vote(author, permlink, weight)
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

## AppBase Module
**Basic Usage**
```python
from appbase import AppBase

hive = AppBase(username)
hive.append_wif("5*")

props = hive.api("database").get_dynamic_global_properties({})

username = "nektar"
account = hive.api("condenser").get_accounts([[self.username]])

```