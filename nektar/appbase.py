# -*- coding: utf-8 -*-
"""
    nektar.appbase
    ~~~~~~~~~

    Interact with the Hive APIs.

    :copyright: 2022 Rodney Maniego Jr.
    :license: MIT License
"""

import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .transactions import sign_transaction
from .constants import NEKTAR_VERSION, NODES, APPBASE_API, BLOCKCHAIN_OPERATIONS
from .exceptions import RPCNodeException, NodeException, APIException, APIMethodException

class AppBase:
    def __init__(self,
                    nodes=None,
                    api=None,
                    timeout=60,
                    retries=3):

        # set default to condenser api
        self._appbase_api = self.api(api)
        self.method = None
        self.rid = 0

        # set session retries
        self.retries = 3
        self.set_retries(retries)

        # set session timeout
        self.timeout = 60
        self.set_timeout(timeout)
        
        # initialize session
        self.session = requests.Session()
        max_retries = Retry(total=self.retries, backoff_factor=0.5, status_forcelist=[502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=max_retries))
        self.headers = { "User-Agent": f"Nektar v{NEKTAR_VERSION}", "content-type": "application/json; charset=utf-8" }
        
        self.nodes = NODES
        self.custom_nodes(nodes)
        
        self.wifs = []
        
    
    def custom_nodes(self, nodes):
        """
            Replace known nodes with custom nodes.
        """
        if nodes is None:
            return
        if isinstance(nodes, str):
            nodes = [nodes]
        self.node = []
        for node in nodes:
            patterns = [ r"http[s]{0,1}\:[\/]{2}", r"[\/][\w\W]+" ]
            for pattern in patterns:
                node = re.sub(pattern, "", node)
            if not len(node):
                raise APIException("Invalid node format.")
            self.nodes.append(node)

    def append_wif(self, wifs):
        if wifs is None:
            return
        if isinstance(wifs, str):
            wifs = [wifs]
        if not isinstance(wifs, list):
            raise WIFException("Invalid WIF format.")
        for wif in wifs:
            if wif not in self.wifs:
                self.wifs.append(wif)

    def set_retries(self, retries):
        if isinstance(retries, int):
            if 1 <= retries <= 10:
                self.retries = retries

    def set_timeout(self, timeout):
        if isinstance(timeout, int):
            if 5 <= timeout <= 120:
                self.timeout = timeout

    def api(self, name):
        if name is None:
            self._appbase_api = "condenser_api"
            return self
        if isinstance(name, str):
            name = name.replace("_api", "") + "_api"
        if name not in APPBASE_API:
            raise APIException(name + " is unsupported.")
        self._appbase_api = name
        return self

    def __getattr__(self, method):
        def callable(*args, **kwargs):
            return self._dynamic_api_call(method, *args, **kwargs)
        return callable

    def _dynamic_api_call(self, *args, **kwargs):
        method = args[0]
        if method not in APPBASE_API[self._appbase_api]:
            raise APIMethodException(name + " is unsupported.")
        method = self._appbase_api + "." + method
        
        params = []
        if len(args) > 1:
            params = args[1]
        else:
            if self._appbase_api == "condenser_api":
                params = {}
        
        # get full JSON-RPC response, or not
        truncated = True
        if "truncated" in kwargs:
            truncated = kwargs["truncated"]
        
        broadcast_methods = [
            "condenser_api.broadcast_transaction",
            "condenser_api.broadcast_transaction_synchronous"
        ]
        
        if method in broadcast_methods:
            return broadcast(method, params, truncated)
        
        temp = self.request(method, params, truncated)
        return temp

    def request(self, method, params, truncated):
        """
            Send predefined params as JSON-RPC request.
        """
        self.rid += 1
        payload = _format_payload(method, params, self.rid)
        return self._send_request(payload, truncated)
        

    def broadcast(self, method, transaction, truncated):
        ## check if operations are valid
        for operation in transaction["operations"]:
            if operation[0] not in BLOCKCHAIN_OPERATIONS:
                raise OperationException(operation[0] + " is unsupported")

        # transaction["signatures"] = []
        # if "signatures" in transaction:
        #    transaction.pop("signatures", None)

        ## serialize transaction and sign with private keys
        serialized_transaction = self._serialize(transaction)
        transaction["signatures"] = sign_transaction(serialized_transaction, self.wifs)
        
        self.rid += 1
        params = [transaction]
        payload = _format_payload(method, params, self.rid)
        print(payload)
        return self._send_request(payload, truncated)

    def _serialize(self, transaction):
        """
            Get a hexdump of the serialized binary form of a transaction.
        """
        
        self.rid += 1
        params = [transaction]
        method = "condenser_api.get_transaction_hex"
        payload = _format_payload(method, params, self.rid)
        return self._send_request(payload)

    def _send_request(self, payload, truncated=True):
        response = None
        for node in self.nodes:
            try:
                url = "https://" + node
                response = self.session.post(url,
                                        headers=self.headers,
                                        json=payload,
                                        timeout=self.timeout)
                break
            except:
                print(f"\nNode API '{node}' is offline, trying the next node....")
        if response is None:
            return {}
        response.raise_for_status()
        response = json.loads(response.content.decode("utf-8"))
        if not truncated:
            return response
        if "result" in response:
            return response["result"]
        if "error" in response:
            print(response)
            # raise RPCNodeException(response["error"].get("message"), code=response["error"].get("code"), raw_body=response)
        return {}

def _format_payload(method, params, rid):
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": rid }

def _make_expiration(secs=30):
    timestamp = time.time() + int(secs)
    return datetime.utcfromtimestamp(timestamp).strftime(BLOCKCHAIN_DT_FORMAT)