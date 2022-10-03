![](/resources/banner.png)

# nektar
nektar allows communication to the Hive blockchain using the Hive API.

## Official Release
**nektar** can now be used on your Python projects through PyPi by running pip command on a Python-ready environment.

`pip install hive-nektar --upgrade`

Current version is 0.0.9, but more updates are coming soon.

This is compatible with Python 3.9 or later.

## Use-cases
**1.** !!! <br>
**2.** !!! <br>
**3.** !!! <br>

## Usage
**1. Import Package**
```python
from nektar import Waggle

username = ""
wif = ""

dapp = Waggle(username)
dapp.append_wif(wif)

author = ""
permlink = ""
weight = 10000

dapp.vote(author, permlink, weight)
```