# -*- coding: utf-8 -*-
"""
    nektar.transactions
    ~~~~~~~~~

    Sign serialized transactions with the private keys.

    :copyright: 2022 Rodney M. Maniego Jr.
    :license: MIT License
"""

import time
import array
import ecdsa
import struct
import hashlib
from binascii import hexlify, unhexlify

from .keys import PrivateKey

def sign_transaction(chain_id, serialized_transaction, wifs):
    """
        Sign serialized transaction with the private keys.
        
        :chain_id: dynamically accessed chain id
        :serialized_transaction: serialized transaction
        :wifs: list of private keys
    """
    
    message = unhexlify(chain_id + serialized_transaction[:-2])
    digest = hashlib.sha256(message).digest()

    signatures = []
    for wif in wifs:
        i = 0
        p = as_bytes(PrivateKey(wif))
        sk = ecdsa.SigningKey.from_string(p, curve=ecdsa.SECP256k1)
        while True:
            k = ecdsa.rfc6979.generate_k(
                sk.curve.generator.order(),
                sk.privkey.secret_multiplier,
                hashlib.sha256,
                hashlib.sha256(digest + struct.pack("d", time.time())).digest())

            sigder = sk.sign_digest(digest, sigencode=ecdsa.util.sigencode_der, k=k)

            r, s = ecdsa.util.sigdecode_der(sigder, sk.curve.generator.order())
            signature = ecdsa.util.sigencode_string(r, s, sk.curve.generator.order())

            sigder = array.array("B", sigder)
            lenR = sigder[3]
            lenS = sigder[5 + lenR]
            if lenR == 32 and lenS == 32:
                i = recover_pubkey_parameter(digest, signature, sk.get_verifying_key())
                i += 31  # compressed 4 + compact 27
                break

        sigstr = struct.pack('<B', i)
        sigstr += signature
        signatures.append(hexlify(sigstr).decode("ascii"))
    return signatures

def recover_pubkey_parameter(digest, signature, pubkey):
    for i in range(0, 4):
        pk = recover_public_key(digest, signature, i)
        
        p = pk.pubkey.point
        order = pk.curve.generator.order()
        x = ecdsa.util.number_to_string(p.x(), order)
        compressed_pk = as_bytes(chr(2 + (p.y() & 1)), "ascii") + x
        
        if pubkey.to_string() in (pk.to_string(), compressed_pk):
            return i
    return None

def recover_public_key(digest, signature, i):
    curve = ecdsa.SECP256k1.curve
    G = ecdsa.SECP256k1.generator
    order = ecdsa.SECP256k1.order
    r, s = ecdsa.util.sigdecode_string(signature, order)
    x = r + (i // 2) * order
    alpha = ((x**3) + (curve.a() * x) + curve.b()) % curve.p()
    beta = ecdsa.numbertheory.square_root_mod_prime(alpha, curve.p())
    y = beta
    if (beta - (i % 2)) % 2 != 0:
        y = curve.p() - beta
    e = ecdsa.util.string_to_number(digest)
    R = ecdsa.ellipticcurve.Point(curve, x, y, order)
    Q = ecdsa.numbertheory.inverse_mod(r, order) * (s * R +
                                                    (-e % order) * G)
    if not ecdsa.VerifyingKey.from_public_point(
            Q, curve=ecdsa.SECP256k1).verify_digest(
                signature, digest, sigdecode=ecdsa.util.sigdecode_string):
        return None
    return ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1)

def as_bytes(item, encoding=None):
    if hasattr(item, "__bytes__"):
        return item.__bytes__()
    if encoding:
        return bytes(item, encoding)
    return bytes(item)