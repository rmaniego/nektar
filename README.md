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
**Basic Usage**
```python
from nektar import Waggle

username = ""
hive = Waggle(username)
hive.append_wif("5*")

communities = hive.communities(limit=1000, sort="subs")
for community in communities:
    print(community["name"] + "\t" + community["title"])


communities = {}
sorting = ["new", "rank", "subs"]
for sort in sorting:
    for community in hive.communities(limit=1000, sort=sort):
        communities.update({community["name"]: community})

subscribers = {}
community = list(communities.keys())[0]
for subscriber in hive.subscribers(community, limit=1000):
    subscribers.update({subscriber[0]: subscriber})
    print(subscriber[0])

accounts = hive.accounts(start="h", limit=1000)

community = community = list(communities.keys())[5]
posts = hive.posts(community, limit=100, sort="created")
print(posts[0])

tag = "nature"
posts = hive.posts(tag, limit=10, sort="created")
for post in posts:
    print(post["title"])

author = ""
permlink = ""
weight = 10000

hive.vote(author, permlink, weight, synchronous=True, strict=False)
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