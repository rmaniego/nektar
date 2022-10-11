# -*- coding: utf-8 -*-
"""
    nektar.appbase
    ~~~~~~~~~

    Interact with the Hive APIs.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import re
import json
import hashlib
import requests
import warnings
from binascii import hexlify, unhexlify
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .transactions import sign_transaction, as_bytes
from .constants import NEKTAR_VERSION, NODES, APPBASE_API, BLOCKCHAIN_OPERATIONS, ROLES
from .exceptions import NektarException


class AppBase:
    """Base SDK to communicate with the Hive APIs.
    ~~~~~~~~~

    :param nodes: a list of valid custom Hive nodes (Default value = None)
    :param api: a valid AppBase API (Default value = None)
    :param timeout: seconds before the request is dropped (Default value = 10)
    :param retries: a dictionary of roles and their equivalent WIFs (Default value = 3)
    :param warning: display warning messages (Default value = False)

    """

    def __init__(self, nodes=None, api=None, timeout=10, retries=3, warning=False):

        # set default to condenser api
        self._appbase_api = self.api(api)
        self.method = None
        self.rid = 0

        if not isinstance(warning, bool):
            raise NektarException("Warning must be `True` or `False` only.")
        if not warning:
            warnings.filterwarnings(
                "ignore",
                ".*unavailable.*",
            )

        # set session retries
        self.retries = 3
        self.set_retries(retries)

        # set session timeout
        self.timeout = 10
        self.set_timeout(timeout)

        # initialize session
        self.session = requests.Session()
        max_retries = Retry(
            total=self.retries, backoff_factor=0.5, status_forcelist=[502, 503, 504]
        )
        self.session.mount("http://", HTTPAdapter(max_retries=max_retries))
        self.headers = {
            "User-Agent": f"Nektar v{NEKTAR_VERSION}",
            "content-type": "application/json; charset=utf-8",
        }

        self.nodes = NODES
        self.custom_nodes(nodes)

        self.wifs = {}
        self.chain_id = self.api("database").get_version({})["chain_id"]
        self._transaction_id = None
        self.signed_transaction = None

    def custom_nodes(self, nodes):
        """Replace known nodes with custom nodes.

        :param nodes: a list of valid Hive nodes

        """
        if nodes is None:
            return
        if isinstance(nodes, str):
            nodes = [nodes]
        self.node = []
        for node in list(nodes):
            patterns = [r"http[s]{0,1}\:[\/]{2}", r"[\/][\w\W]+"]
            for pattern in patterns:
                node = re.sub(pattern, "", node)
            if not len(node):
                raise NektarException("Invalid node format.")
            self.nodes.append(node)

    def append_wif(self, wif, role=None):
        """Append WIF and the associated role of it for signing transactions.

        If `wif` is empty, role is expected to be a dictionary containing a valid role-wif pairs.

        :param wif: a valid private key (Default value = None)
        :param role: role of private key being appended, must be `owner`, `active`, `posting`, or `memo` only.

        """
        if isinstance(wif, dict):
            for r, w in wif.items():
                self.append_wif(w, r)
            return
        if not isinstance(wif, str) and not isinstance(role, str):
            raise NektarException("Role and WIF must be a valid string.")
        if role not in ROLES["all"]:
            raise NektarException(
                "Role must be `owner`, `active`, `posting`, or `memo` only."
            )
        if wif not in list(self.wifs.values()):
            self.wifs[role] = wif

    def set_retries(self, retries):
        """

        :param retries: the number of retries when reconnect with the URLs

        """
        if 1 <= int(retries) <= 10:
            self.retries = retries

    def set_timeout(self, timeout):
        """

        :param timeout: seconds before the request is dropped

        """
        if 5 <= int(timeout) <= 120:
            self.timeout = timeout

    ## AppBase APIs
    def api(self, name):
        """Set to a valid API.

        :param name: a valid AppBase API

        """
        if name is None:
            self._appbase_api = "condenser_api"
            return self
        if isinstance(name, str):
            name = name.replace("_api", "")
            if name not in ("bridge",):
                name += "_api"
        if name not in APPBASE_API:
            raise NektarException(name + " is unsupported.")
        self._appbase_api = name
        return self

    def condenser(self):
        """Set the active API to `condenser_api`."""
        self._appbase_api = "condenser_api"
        return self

    def account_by_key(self):
        """Set the active API to `account_by_key_api`."""
        self._appbase_api = "account_by_key_api"
        return self

    def bridge(self):
        """Set the active API to `bridge`."""
        self._appbase_api = "bridge"
        return self

    def account_history(self):
        """Set the active API to `account_history_api`."""
        self._appbase_api = "account_history_api"
        return self

    def block(self):
        """Set the active API to `block_api`."""
        self._appbase_api = "block_api"
        return self

    def database(self):
        """Set the active API to `database_api`."""
        self._appbase_api = "database_api"
        return self

    def debug_node(self):
        """Set the active API to `debug_node_api`."""
        self._appbase_api = "debug_node_api"
        return self

    def follow(self):
        """Set the active API to `follow_api`."""
        self._appbase_api = "follow_api"
        return self

    def market_history(self):
        """Set the active API to `market_history_api`."""
        self._appbase_api = "market_history_api"
        return self

    def network_broadcast(self):
        """Set the active API to `network_broadcast_api`."""
        self._appbase_api = "network_broadcast_api"
        return self

    def rc(self):
        """Set the active API to `rc_api`."""
        self._appbase_api = "rc_api"
        return self

    def reputation(self):
        """Set the active API to `reputation_api`."""
        self._appbase_api = "reputation_api"
        return self

    ## API methods
    def __getattr__(self, method):
        def callable(*args, **kwargs):
            """Dynamically send an API request using a method call.

            :param *args:
            :param **kwargs:

            """
            return self._dynamic_api_call(method, *args, **kwargs)

        return callable

    def _dynamic_api_call(self, *args, **kwargs):
        """Dynamically send an API request using a method call.

        :param *args:
        :param **kwargs:

        """
        method = args[0]
        if method not in APPBASE_API[self._appbase_api]:
            raise NektarException(name + " is unsupported.")
        method = self._appbase_api + "." + method

        params = []
        if len(args) > 1:
            params = args[1]
        else:
            if self._appbase_api == "condenser_api":
                params = {}

        # raise exception on error or not
        strict = True
        if "strict" in kwargs:
            strict = kwargs["strict"]

        ## do not change sorting order !!
        broadcast_methods = [
            "condenser_api.verify_authority",
            "condenser_api.broadcast_transaction",
            "condenser_api.broadcast_transaction_synchronous",
            "database_api.get_potential_signatures",
            "database_api.get_required_signatures",
            "database_api.get_transaction_hex",
            "database_api.verify_authority",
            "network_broadcast_api.broadcast_transaction",
        ]

        if method in broadcast_methods:
            params = [params]
            if method in broadcast_methods[3:]:
                params = {"trx": params[0]}

        if method in broadcast_methods[1:]:
            return self.broadcast(method, params, strict=strict)
        return self.request(method, params, strict=strict)

    def request(self, method, params, strict=True):
        """Send predefined params as JSON-RPC request.

        :param method:
        :param params:

        """
        self.rid += 1
        payload = _format_payload(method, params, self.rid)
        return self._send_request(payload, strict=strict)

    def broadcast(self, method, transaction, strict=True, verify_only=False):
        """Broadcast a transaction to the blockchain.

        :param method:
        :param transaction:
        :param strict:  (Default value = True)
        :param verify_only:  (Default value = False)

        """

        ## check if operations are valid
        operation = ""
        for op in transaction["operations"]:
            if op[0] not in BLOCKCHAIN_OPERATIONS:
                raise NektarException(op[0] + " is unsupported")
            operation = op[0]
            # avoid unnecessary signatures
            if operation == "custom_json":
                if not len(op[1]["required_auths"]):
                    operation = "posting"

        signatures = []
        if "signatures" in transaction:
            signatures = transaction["signatures"]
            transaction.pop("transaction", None)

        ## serialize transaction and sign with private keys
        serialized_transaction = self._serialize(transaction)

        ## generate transaction id
        hashed = hashlib.sha256(unhexlify(serialized_transaction)).digest()
        self._transaction_id = hexlify(hashed[:20]).decode("ascii")

        ## update transaction signature
        wifs = _get_necessary_wifs(self.wifs, operation)
        signatures.extend(sign_transaction(self.chain_id, serialized_transaction, wifs))
        transaction["signatures"] = list(set(signatures))
        self.signed_transaction = transaction

        verified = self.api("condenser").verify_authority(transaction)
        if strict and not verified:
            raise NektarException("Transaction does not contain required signatures.")
        if verify_only:
            return verified

        self.rid += 1
        params = [transaction]
        payload = _format_payload(method, params, self.rid)
        result = self._send_request(payload, strict)
        if method == "condenser_api.broadcast_transaction" and not strict:
            ## not working
            return self.api("condenser_api").get_transaction([transaction_id])
        return result

    def _serialize(self, transaction):
        """Get a hexdump of the serialized binary form of a transaction.

        :param transaction:

        """
        return self.api("condenser").get_transaction_hex([transaction])

    def _send_request(self, payload, strict=True):
        """Send an API request with a valid payload, as defined by the Hive API documentation.

        :param payload: a formatted and valid payload.
        :param strict: flag to cause exception upon encountering an error (Default value = True)

        """
        response = None
        for node in self.nodes:
            try:
                url = "https://" + node
                response = self.session.post(
                    url, headers=self.headers, json=payload, timeout=self.timeout
                )
                response.raise_for_status()
                response = json.loads(response.content.decode("utf-8"))
                break
            except:
                warnings.warn(
                    f"Node '{node}' is unavailable, retrying with the next node."
                )
        if response is None:
            return {}
        if "result" in response:
            return response["result"]
        if "error" in response:
            if strict:
                raise NektarException(response["error"].get("message"))
        return {}


#########################
# utils                 #
#########################


def _get_necessary_wifs(wifs, operation):
    """

    :param wifs: a list of WIFs
    :param operation: a valid operation to be performed in the Hive blockchain.

    """
    for role in ROLES[operation]:
        if role in wifs:
            return [wifs[role]]
    return []


def _format_payload(method, params, rid):
    """Format API method parameters to conform to the Hive API documentation.

    :param method: the API method
    :param params: the required parameters to successfully perform the operation or request
    :param rid: the unique RPC id used for debugging purposes

    """
    return {"jsonrpc": "2.0", "method": method, "params": params, "id": rid}


def _make_expiration(secs=30):
    """Create an expiration time based on the current UTC datetime.

    :param expire: transaction expiration in seconds (Default value = 30)

    """
    timestamp = time.time() + int(secs)
    return datetime.utcfromtimestamp(timestamp).strftime(BLOCKCHAIN_DT_FORMAT)
