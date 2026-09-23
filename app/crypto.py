import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def load_key(key_b64: str) -> bytes:
    return base64.urlsafe_b64decode(key_b64)


def encrypt(key: bytes, plaintext: bytes, aad: str) -> bytes:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext, aad.encode())
    return nonce + ct


def decrypt(key: bytes, raw: bytes, aad: str) -> bytes:
    nonce = raw[:12]
    ct = raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, aad.encode())