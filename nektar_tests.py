import os
import json
import logging
from arkivist import Arkivist
from nektar import Waggle, Swarm
from sometime import Sometime

logging.basicConfig(
    filename="nektar.tests.log",
    format="%(asctime)s %(message)s",
    filemode="a+",
    level=logging.DEBUG,
)


def main():

    dt = Sometime().custom("%Y.%m.%d")

    counter = 0
    logging.info("Initializing tests...")
    path = os.path.expanduser("~").replace("\\", "/")
    tests = Arkivist(path + "/nektar-tests.json", autosave=False)

    ##################################################
    # AppBase Class                                  #
    ##################################################

    ##################################################
    # Nektar Class / Base Class                      #
    ##################################################

    ##################################################
    # Waggle Class                                   #
    # Methods for blogging and engagement            #
    ##################################################

    counter += 1
    logging.info(f"\nTEST #{counter}: Initialize Waggle class.")
    hive = Waggle(tests["username0"], wif=tests["wifs0"]["posting"], role="posting")

    counter += 1
    logging.info(f"\nTEST #{counter}: Initialize Waggle class with dictionary of WIFs.")
    hive = Waggle(tests["username0"], wifs=tests["wifs0"])

    counter += 1
    logging.info(f"\nTEST #{counter}: Initialize Waggle class with app and version")
    hive = Waggle(tests["username0"], wifs=tests["wifs0"], app="nektar.app", version=dt)

    counter += 1
    logging.info(f"\nTEST #{counter}: Get the list of blockchain constants")
    # Hive Developer Portal > Understanding Configuration Values
    # https://developers.hive.io/tutorials-recipes/understanding-configuration-values.html
    data = hive.get_config()
    logging.info(json.dumps(data, indent=2))

    counter += 1
    logging.info(f"\nTEST #{counter}: Get the list of blockchain constants")
    data = hive.get_config(field="HIVE_CHAIN_ID", fallback="bee*")
    logging.info("HIVE_CHAIN_ID: " + str(data))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the initialized account's recent resource credits."
    )
    data = hive.resource_credits()
    logging.info(data)

    counter += 1
    logging.info(f"\nTEST #{counter}: Get another account's recent resource credits.")
    data = hive.resource_credits(tests["username1"])
    logging.info(data)

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the initialized account's remaining mana in percentage."
    )
    percentage = hive.manabar()
    logging.info("Current Mana: " + str(int(percentage)) + "%")

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get another account's remaining mana in percentage."
    )
    percentage = hive.manabar()
    logging.info("Current Mana: " + str(int(percentage)) + "%")

    counter += 1
    logging.info(f"\nTEST #{counter}: Get the list of communities")
    communities = {}
    sorting = ["new", "rank", "subs"]
    for sort in sorting:
        for community in hive.communities(limit=100, sort=sort):
            communities.update({community["name"]: community})
    community = list(communities.keys())[5]
    logging.info(", ".join(list(communities.keys())))

    counter += 1
    logging.info(f"\nTEST #{counter}: Get the name and title of each community")
    logging.info(len(communities))
    for name, data in communities.items():
        logging.info(name + "\t" + data["title"])
        break

    counter += 1
    logging.info(f"\nTEST #{counter}: Get the subscribers of a community.")
    subscribers = {}
    for subscriber in hive.subscribers(community, limit=10):
        subscribers.update({subscriber[0]: subscriber})
        logging.info(subscriber[0])
        break

    counter += 1
    logging.info(f"\nTEST #{counter}: Get the list of 100 Hive blockchain accounts.")
    accounts = {}
    for account in hive.accounts():
        logging.info(account)
        break

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of 10 Hive blockchain starting with `a`."
    )
    accounts = {}
    for account in hive.accounts(start="a", limit=10):
        logging.info(account)

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of 10 community posts in order of creation and not yet paid out."
    )
    posts = hive.posts(community, limit=10, sort="created", paidout=False)
    for post in posts:
        logging.info(post["title"])

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of 1000 followers of the initialized account."
    )
    followers = hive.followers()
    logging.info(", ".join(followers))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of 10 muted followers of another account."
    )
    followers = hive.followers(account=tests["username1"], ignore=True, limit=10)
    logging.info(", ".join(followers))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of up to 1000 account transactions, most recent first."
    )
    transactions = hive.history()
    logging.info("Transactions:", json.dumps(transactions[1], indent=2))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of up to 1000 account transactions of another account."
    )
    transactions = hive.history(account=tests["username1"], start=1000, low=0)
    logging.info("Transactions:", json.dumps(transactions[1], indent=2))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of up to 100 account transactions of another account starting from the 5000th transaction to the oldest."
    )
    transactions = hive.history(account=tests["username1"], start=5000, limit=100)
    for transaction in transactions[:1]:
        logging.info(transaction[0], transaction[1]["op"])

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of account delegators with the corresponding changes in delegations."
    )
    delegators = hive.delegators()
    logging.info(json.dumps(delegators, indent=2))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of active account delegators of another account."
    )
    delegators = hive.delegators(account=tests["username1"], active=True)
    logging.info(json.dumps(delegators, indent=2))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of account delegatees with the corresponding changes in delegations."
    )
    delegatees = hive.delegatees()
    logging.info(json.dumps(delegatees, indent=2))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of active account delegators of another account."
    )
    delegatees = hive.delegatees(account=tests["username1"], active=True)
    logging.info(json.dumps(delegatees, indent=2))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of posts of the initizalized account."
    )
    blogs = hive.blogs()
    logging.info(json.dumps(blogs[0], indent=2))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Get the list of posts of another account with non-default values."
    )
    blogs = hive.blogs(account=tests["username1"], sort="created", paidout=True, limit=100)
    logging.info(json.dumps(blogs[0], indent=2))

    counter += 1
    logging.info(f"\nTEST #{counter}: Get the post data.")
    author = tests["username1"]
    permlink = tests["permlink1"]
    data = hive.get_post(author, permlink)
    logging.info(json.dumps(data, indent=2))

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Try to get the post data, return empty if not yet present in the blockchain."
    )
    author = tests["username1"]
    permlink = "abc-123-def-456"
    data = hive.get_post(author, permlink, retries=2)
    logging.info(json.dumps(data, indent=2))

    counter += 1
    logging.info(f"\nTEST #{counter}: Publish a new post.")
    title = "NEW! Connect to Hive with Nektar for Python"
    body = 'Introducing Nektar!\n"How do I connect to Hive?"\nWell, you can now use Nektar.\n**[Nektar](https://github.com/rmaniego/nektar)** allows you to to the Hive blockchain using the Hive API.\n<br>---<br>*More updates coming soon!*'
    description = "Nektar is here!"
    tags = "nektar hive api coderundebug"
    community = tests["community2"]
    hive.new_post(title, body, description, tags, community, verify_only=True)

    counter += 1
    logging.info(f"\nTEST #{counter}: Reply a comment to a post or another comment.")
    author = tests["username1"]
    permlink = tests["permlink1"]
    body = "Great work in there, keep it up!\n\n---\n" "Check our [community](#) page!"
    hive.reply(author, permlink, body, verify_only=True)

    counter += 1
    logging.info(f"\nTEST #{counter}: Reply a comment to a post or another comment.")
    author = tests["username2"]
    permlink = tests["permlink2"]
    weight = 100
    hive.vote(author, permlink, weight, verify_only=True)

    counter += 1
    logging.info(f"\nTEST #{counter}: Get a recently signed transaction.")
    signed_transaction = hive.appbase.signed_transaction

    counter += 1
    logging.info(
        f"\nTEST #{counter}: Verify if signed transaction contains required auths."
    )
    verified = hive.verify_authority(signed_transaction)
    logging.info("OK:" + str(verified))

    counter += 1
    logging.info(f"\nTEST #{counter}: Transfer HBD to another account with a message.")
    receiver = tests["username1"]
    amount = 0.001
    asset = "HBD"
    message = "Thanks for supporting us!"
    hive.memo(receiver, amount, asset, message, verify_only=True)

    counter += 1
    logging.info(f"\nTEST #{counter}: Transfer HIVE to another account with a message.")
    receiver = tests["username1"]
    amount = 0.001
    asset = "HIVE"
    message = "Thanks for supporting us!"
    hive.memo(receiver, amount, asset, message, verify_only=True)

    counter += 1
    logging.info(f"\nTEST #{counter}: Broadcast a custom JSON.")
    app = tests["username0"] + ".app" + "/" + Sometime().custom("%Y.%m.%d")
    dt = Sometime().custom("%Y-%m-%dT%H:%M:%S%Z")
    protocol_id = tests["username0"]
    json_data = {
        "app": app,
        "activity": "test",
        "worker": tests["username0"],
        "timestamp": dt,
    }
    required_auths = [tests["username0"]]
    required_posting_auths = []
    hive.custom_json(
        protocol_id, json_data, required_auths, required_posting_auths, verify_only=True
    )

    ##################################################
    # Drone Class                                    #
    # Custom JSON methods                            #
    ##################################################

    ##################################################
    # Swarm Class                                    #
    # Community Management methods                   #
    ##################################################

    counter += 1
    logging.info(f"\nTEST #{counter}: Broadcast a custom JSON.")
    hive = Swarm(tests["community1"], tests["username0"], wifs=tests["wifs0"])
    # hive.mute("")


if __name__ == "__main__":
    main()
