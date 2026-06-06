from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Tuple


def _derive_key(secret: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, 120_000, dklen=32)


def _keystream(key: bytes, length: int) -> bytes:
    blocks = []
    counter = 0
    produced = 0
    while produced < length:
        counter_bytes = counter.to_bytes(8, "big")
        block = hashlib.sha256(key + counter_bytes).digest()
        blocks.append(block)
        produced += len(block)
        counter += 1
    return b"".join(blocks)[:length]


def encrypt_text(plaintext: str, secret: str) -> str:
    salt = os.urandom(16)
    key = _derive_key(secret, salt)
    data = plaintext.encode("utf-8")
    cipher = bytes(a ^ b for a, b in zip(data, _keystream(key, len(data))))
    signature = hmac.new(key, cipher, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(salt + signature + cipher).decode("ascii")


def decrypt_text(ciphertext: str, secret: str) -> str:
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    salt, signature, cipher = raw[:16], raw[16:48], raw[48:]
    key = _derive_key(secret, salt)
    expected = hmac.new(key, cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Vault payload integrity check failed.")
    plain = bytes(a ^ b for a, b in zip(cipher, _keystream(key, len(cipher))))
    return plain.decode("utf-8")


def encrypt_bytes(payload: bytes, secret: str) -> Tuple[bytes, bytes]:
    salt = os.urandom(16)
    key = _derive_key(secret, salt)
    cipher = bytes(a ^ b for a, b in zip(payload, _keystream(key, len(payload))))
    signature = hmac.new(key, cipher, hashlib.sha256).digest()
    return salt + signature + cipher, key


def decrypt_bytes(payload: bytes, secret: str) -> bytes:
    salt, signature, cipher = payload[:16], payload[16:48], payload[48:]
    key = _derive_key(secret, salt)
    expected = hmac.new(key, cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Backup integrity check failed.")
    return bytes(a ^ b for a, b in zip(cipher, _keystream(key, len(cipher))))
