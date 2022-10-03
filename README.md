![](/resources/banner.png)

# nektar
nektar allows communication to the Hive blockchain using the Hive API.

## Official Release
**nektar** can now be used on your Python projects through PyPi by running pip command on a Python-ready environment.

`pip install hive-nektar --upgrade`

Current version is 0.1.\*, but more updates are coming soon.

This is compatible with Python 3.9 or later.

## WARNINGS:
 - This package is still under development, some future breakage is inevatable.
 - Some AppBase API methods are still under development and subject to change.

## Features
**1.** Lightweight package for small Hive dApps or projects. <br>
**2.** Readily available methods using the `nektar.Waggle()` class. <br>
**3.** Highly costumizable via `appbase` module. <br>

## Nektar Module
**Basic Usage**
```python
from nektar import Waggle

username = ""
dapp = Waggle(username)
dapp.append_wif("5*")

author = ""
permlink = ""
weight = 10000

dapp.vote(author, permlink, weight, synchrnous=True, strict=False)
```

## AppBase Module
**Basic Usage**
```python
from appbase import AppBase

dapp = AppBase(username)
dapp.append_wif("5*")

props = dapp.api("database").get_dynamic_global_properties({})

username = "nektar"
account = dapp.api("condenser").get_accounts([[self.username]])

```