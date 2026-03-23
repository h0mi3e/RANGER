#!/usr/bin/env python3
"""
Simple mTLS Setup for Ranger C2
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent
CERTS_DIR = BASE_DIR / "certs"
CERTS_DIR.mkdir(exist_ok=True)

def run(cmd, desc):
    print(f"[+] {desc}...")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        print(f"    ✅ {desc}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    ❌ {desc} failed: {e.stderr.decode()}")
        return False

print("="*60)
print("Ranger C2 mTLS Setup")
print("="*60)

# 1. Generate CA
print("\n1. Generating Certificate Authority...")
run("openssl genrsa -out certs/ca.key 4096", "CA private key")
run('openssl req -new -x509 -days 3650 -key certs/ca.key -out certs/ca.crt -subj "/C=US/ST=CA/L=SF/O=Rogue/OU=C2/CN=Rogue CA"', "CA certificate")

# 2. Generate Server Certificate
print("\n2. Generating Server Certificate...")
run("openssl genrsa -out certs/server.key 2048", "Server private key")

# Create server config
server_conf = """[ req ]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[ req_distinguished_name ]
C = US
ST = California
L = San Francisco
O = Rogue Security
OU = C2 Server
CN = c2.rogue-c2.com

[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = c2.rogue-c2.com
DNS.2 = localhost
IP.1 = 127.0.0.1
"""

with open("certs/server.cnf", "w") as f:
    f.write(server_conf)

run("openssl req -new -key certs/server.key -out certs/server.csr -config certs/server.cnf", "Server CSR")
run("openssl x509 -req -days 365 -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial -out certs/server.crt -extfile certs/server.cnf -extensions v3_req", "Sign server cert")

# 3. Generate Client Certificates
print("\n3. Generating Client Certificates...")
for i in range(1, 6):
    client_name = f"implant_{i:03d}"
    run(f"openssl genrsa -out certs/{client_name}.key 2048", f"{client_name} private key")
    run(f'openssl req -new -key certs/{client_name}.key -out certs/{client_name}.csr -subj "/C=US/ST=CA/L=SF/O=Rogue/OU=Implant/CN={client_name}.rogue-c2.com"', f"{client_name} CSR")
    run(f"openssl x509 -req -days 365 -in certs/{client_name}.csr -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial -out certs/{client_name}.crt", f"Sign {client_name} cert")
    run(f"openssl pkcs12 -export -out certs/{client_name}.p12 -inkey certs/{client_name}.key -in certs/{client_name}.crt -certfile certs/ca.crt -password pass:rogue123", f"Create {client_name} PKCS12")

# 4. Verify
print("\n4. Verifying certificates...")
run("openssl verify -CAfile certs/ca.crt certs/server.crt", "Verify server cert")
run("openssl verify -CAfile certs/ca.crt certs/implant_001.crt", "Verify client cert")

# 5. Create test script
print("\n5. Creating test scripts...")
test_script = '''#!/usr/bin/env python3
import ssl
import socket

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile="certs/implant_001.crt", keyfile="certs/implant_001.key")
context.load_verify_locations(cafile="certs/ca.crt")

try:
    with socket.create_connection(('127.0.0.1', 4443)) as sock:
        with context.wrap_socket(sock, server_hostname='c2.rogue-c2.com') as ssock:
            print(f"✅ mTLS connection successful")
            print(f"   Cipher: {ssock.cipher()}")
            print(f"   Version: {ssock.version()}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("Note: Start C2 with mTLS first: python3 c2.py")
'''

with open("test_mtls.py", "w") as f:
    f.write(test_script)

# 6. Update C2 for mTLS
print("\n6. Updating C2 for mTLS...")
c2_code = '''
# mTLS Configuration
import ssl
MTLS_CERT = "certs/server.crt"
MTLS_KEY = "certs/server.key"
MTLS_CA = "certs/ca.crt"

def create_ssl_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain(certfile=MTLS_CERT, keyfile=MTLS_KEY)
    context.load_verify_locations(cafile=MTLS_CA)
    return context

# Start mTLS server
ssl_context = create_ssl_context()
print("[+] mTLS enabled on port 4443")

# Run both HTTP and HTTPS
import threading
def run_https():
    app.run(host=C2_HOST, port=4443, ssl_context=ssl_context, debug=False, threaded=True)

def run_http():
    app.run(host=C2_HOST, port=C2_PORT, debug=False, threaded=True)

https_thread = threading.Thread(target=run_https, daemon=True)
https_thread.start()
run_http()
'''

# Read current c2.py
with open("c2.py", "r") as f:
    lines = f.readlines()

# Find app.run() line
for i, line in enumerate(lines):
    if "app.run(" in line and "host=C2_HOST" in line:
        # Replace with mTLS version
        lines[i] = c2_code
        break

with open("c2.py", "w") as f:
    f.writelines(lines)

print("\n" + "="*60)
print("✅ mTLS SETUP COMPLETE")
print("="*60)
print("\nGenerated certificates:")
print("  certs/ca.crt          - Certificate Authority")
print("  certs/server.crt      - Server certificate")
print("  certs/implant_001.crt - Client certificate 1")
print("  ... up to implant_005.crt")
print("\nTo test:")
print("  1. Start C2: python3 c2.py")
print("  2. Test mTLS: python3 test_mtls.py")
print("\nC2 will run on:")
print("  HTTPS (mTLS): https://127.0.0.1:4443")
print("  HTTP (fallback): http://127.0.0.1:4444")
print("\nClient cert password: rogue123")
print("="*60)