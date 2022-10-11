import os
import json
from nektar import AppBase
from arkivist import Arkivist
from sometime import Sometime


def main():

    dt = Sometime().custom("%Y.%m.%d")

    counter = 0
    print("Initializing tests...")
    path = os.path.expanduser("~").replace("\\", "/")
    tests = Arkivist(path + "/nektar-tests.json", autosave=False)

    ##################################################
    # AppBase Class                                  #
    ##################################################

    counter += 1
    print(f"\nTEST #{counter}: Initialize AppBase Class.")
    hive = AppBase()

    counter += 1
    print(f"\nTEST #{counter}: Initialize AppBase Class with custom parameters.")
    custom_nodes = ["rpc.mock.site"]
    hive = AppBase(nodes=custom_nodes, timeout=5, retries=1, warning=True)

    counter += 1
    print(f"\nTEST #{counter}: Change to custom nodes.")
    hive.custom_nodes(custom_nodes)

    counter += 1
    print(f"\nTEST #{counter}: Add new WIF and equivalent role.")
    hive.append_wif(wif=tests["wifs0"]["posting"], role="posting")
    hive.append_wif(wif=tests["wifs0"]["active"], role="active")

    counter += 1
    print(f"\nTEST #{counter}: Add new dictionary of roles and their equivalent WIFs.")
    hive.append_wif(tests["wifs0"])  # {"posting": "5*", "active": "5*"}

    counter += 1
    print(f"\nTEST #{counter}: Change retries to custom value.")
    hive.set_timeout(15)

    ## Read the actual Hive API documentation for proper guidance
    ## https://developers.hive.io/apidefinitions/

    counter += 1
    print(f"\nTEST #{counter}: Access API and its methods - generic")
    hive.api("condenser")
    hive.api("condenser_api")

    counter += 1
    print(f"\nTEST #{counter}: `account_by_key_api.get_key_references`")
    # version = hive.api("account_by_key_api").*
    params = {"keys": [tests["publickey0"]]}
    data = hive.account_by_key().get_key_references(params)
    print("Account by public key: " + json.dumps(data, indent=2))

    counter += 1
    print(f"\nTEST #{counter}: `bridge.get_profile`")
    # version = hive.api("bridge").*
    params = {"account": tests["username0"], "observer": tests["username0"]}
    data = hive.bridge().get_profile(params)
    print("Profile: " + json.dumps(data, indent=2))

    counter += 1
    print(f"\nTEST #{counter}: `account_history_api.get_account_history`")
    # version = hive.api("account_history").*
    params = {
        "account": tests["username1"],
        "start": 1000,
        "limit": 1000,
        "include_reversible": True,
        "operation_filter_low": 0,
        "operation_filter_high": 1,
    }
    data = hive.account_history().get_account_history(params)
    print("Account history: " + json.dumps(data, indent=2))

    counter += 1
    print(f"\nTEST #{counter}: `block_api.get_block`")
    params = {"block_num": 8675309}
    data = hive.block().get_block(params)
    print("Block: " + json.dumps(data, indent=2))

    counter += 1
    print(f"\nTEST #{counter}: Create an instance for specific API only.")
    condenser = hive.condenser()

    params = [tests["username1"], tests["permlink1"]]
    data = condenser.get_content(params)
    print("Content #1: " + json.dumps(data, indent=2))

    params = [tests["username1"], 0, 10]
    data = condenser.get_blog(params)
    print("Content #2: " + json.dumps(data, indent=2))

    counter += 1
    print(f"\nTEST #{counter}: Using the `request` method.")
    method = "rc_api.find_rc_accounts"
    params = {"accounts": [tests["username1"]]}
    data = hive.request(method, params, strict=False)
    print("Accounts: " + json.dumps(data, indent=2))

    counter += 1
    print(f"\nTEST #{counter}: Using the `broadcast` method - `condenser_api`.")
    method = "condenser_api.get_transaction_hex"
    transaction = {
        "ref_block_num": 123456,
        "ref_block_prefix": 1234567890,
        "expiration": "2022-10-05T18:00:00",
        "operations": [
            [
                "vote",
                {
                    "voter": tests["username0"],
                    "author": tests["username1"],
                    "permlink": tests["permlink1"],
                    "weight": 10000,
                },
            ]
        ],
        "extensions": [],
    }
    data = hive.broadcast(method, transaction, strict=False)
    print("Transaction hex: " + data)


if __name__ == "__main__":
    main()
