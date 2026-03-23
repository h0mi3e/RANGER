#!/usr/bin/env python3
"""
Debug DNS Server
"""

import dns.resolver

print("Testing DNS server...")

# Test 1: Try to resolve our domain
resolver = dns.resolver.Resolver()
resolver.nameservers = ['127.0.0.1']
resolver.port = 5354

print("Test 1: Resolving test.updates.rogue-c2.com")
try:
    answer = resolver.resolve('test.updates.rogue-c2.com', 'A', lifetime=5)
    print(f"✅ Success: {answer}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\nTest 2: Resolving v1.chunk1.file.test.updates.rogue-c2.com")
try:
    answer = resolver.resolve('v1.chunk1.file.test.updates.rogue-c2.com', 'A', lifetime=5)
    print(f"✅ Success: {answer}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\nTest 3: Resolving google.com (should fail - not our domain)")
try:
    answer = resolver.resolve('google.com', 'A', lifetime=5)
    print(f"✅ Success (unexpected): {answer}")
except Exception as e:
    print(f"✅ Expected failure: {e}")

print("\nTest 4: Check if server is listening")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(3)

# Send a DNS query
import struct
query_id = 1234
flags = 0x0100  # Standard query, recursion desired
questions = 1

# Build DNS query
query = struct.pack('!HHHHHH', query_id, flags, questions, 0, 0, 0)
# Add domain: test.updates.rogue-c2.com
for part in b'test.updates.rogue-c2.com'.split(b'.'):
    query += struct.pack('B', len(part)) + part
query += b'\x00'  # End of domain
query += struct.pack('!HH', 1, 1)  # Type A, Class IN

try:
    sock.sendto(query, ('127.0.0.1', 5354))
    response, addr = sock.recvfrom(512)
    print(f"✅ DNS server responded to raw query")
    
    # Parse response
    header = struct.unpack('!HHHHHH', response[:12])
    print(f"   Response ID: {header[0]}, Flags: {hex(header[1])}")
    
except socket.timeout:
    print("❌ DNS server timeout (not responding)")
except Exception as e:
    print(f"❌ Error: {e}")

sock.close()