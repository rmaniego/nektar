import os
import json
from arkivist import Arkivist
from nektar import Waggle, Swarm
from sometime import Sometime


def main():

    path = os.path.expanduser("~").replace("\\", "/")
    tests = Arkivist(path + "/nektar-tests.json", autosave=False)

    hive = Waggle(tests["username0"], wifs=tests["wifs0"])

    # Hive Developer Portal > Understanding Configuration Values
    # https://developers.hive.io/tutorials-recipes/understanding-configuration-values.html
    data = hive.get_config()  # all
    print(json.dumps(data, indent=4))

    data = hive.get_config(field="HIVE_CHAIN_ID", fallback="bee*")
    print("HIVE_CHAIN_ID: " + str(data))

    data = hive.resource_credits()
    print(data)

    percentage = hive.manabar()
    print("Current Mana: " + str(int(percentage)) + "%")

    communities = {}
    sorting = ["new", "rank", "subs"]
    for sort in sorting:
        for community in hive.communities(limit=100, sort=sort):
            communities.update({community["name"]: community})
    community = list(communities.keys())[5]

    print(len(communities))
    for name, data in communities.items():
        print(name + "\t" + data["title"])
        break

    subscribers = {}
    for subscriber in hive.subscribers(community, limit=10):
        subscribers.update({subscriber[0]: subscriber})
        print(subscriber[0])
        break

    accounts = {}
    for account in hive.accounts():
        print(account)
        break

    posts = hive.posts(community, limit=10, sort="created", paidout=False)
    for post in posts:
        print(post["title"])

    followers = hive.followers()
    print(followers)

    # up to 1000 operations, most recent first
    transactions = hive.history()
    print("Transactions:", json.dumps(transactions[1], indent=4))

    # up to 1000 upvote operations of another acount
    transactions = hive.history(account=tests["username1"], start=1000, low=0)
    print("Transactions:", json.dumps(transactions[1], indent=4))

    # up to 100 operations of another acount
    transactions = hive.history(account=tests["username1"], start=1000, limit=100)
    for transaction in transactions[:1]:
        print(transaction[0], transaction[1]["op"])

    delegators = hive.delegators()
    print(json.dumps(delegators, indent=4))

    delegators = hive.delegators(active=True)
    print(json.dumps(delegators, indent=4))

    delegatees = hive.delegatees()
    print(json.dumps(delegatees, indent=4))

    delegatees = hive.delegatees(active=True)
    print(json.dumps(delegatees, indent=4))

    blogs = hive.blogs()
    print(json.dumps(blogs[0], indent=4))

    author = tests["username1"]
    permlink = tests["permlink1"]
    data = hive.get_post(author, permlink)
    print(json.dumps(data, indent=4))

    author = tests["username1"]
    permlink = "abc-123-def-456"
    data = hive.get_post(author, permlink, retries=2)
    print(json.dumps(data, indent=4))

    ## Blog Post
    title = "NEW! Connect to Hive with Nektar for Python"
    body = (
        "Introducing Nektar!\n"
        '"How do I connect to Hive?"\n'
        "Well, you can now use Nektar.\n"
        "**[Nektar](https://github.com/rmaniego/nektar)** allows you to to the Hive blockchain using the Hive API.\n"
        "<br>---<br>*More updates coming soon!*"
    )
    description = "Nektar is here!"
    tags = "nektar hive api coderundebug"
    community = tests["community2"]
    hive.new_post(title, body, description, tags, community, verify_only=True)

    ## Blog Comment
    author = tests["username1"]
    permlink = tests["permlink1"]
    body = "Great work in there, keep it up!\n\n---\n" "Check our [community](#) page!"
    hive.reply(author, permlink, body, verify_only=True)

    author = tests["username2"]
    permlink = tests["permlink2"]
    weight = 100
    hive.vote(author, permlink, weight, verify_only=True)

    signed_transaction = hive.appbase.signed_transaction
    verified = hive.verify_authority(signed_transaction)
    print("OK:", verified)

    ## Send Memo
    receiver = tests["username1"]
    amount = 0.001
    asset = "HBD"
    message = "Thanks for supporting us!"
    hive.memo(receiver, amount, asset, message, verify_only=True)

    ## Custom JSON
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

    hive = Swarm(tests["community1"], tests["username0"], wifs=tests["wifs0"])
    # hive.mute("")


if __name__ == "__main__":
    main()
