#!/usr/bin/env python3
"""
mTLS Setup for Ranger C2
Generate CA, server cert, client certs for mutual TLS authentication
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
BASE_DIR = Path(__file__).parent
CERTS_DIR = BASE_DIR / "certs"
CONFIG_DIR = BASE_DIR / "config"

# Create directories
CERTS_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

def run_command(cmd, description):
    """Run shell command with error handling."""
    print(f"[+] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(f"    ✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    ❌ {description} failed")
        print(f"    Error: {e.stderr}")
        return False

def generate_ca():
    """Generate Certificate Authority (CA)."""
    print("\n" + "="*60)
    print("Generating Certificate Authority (CA)")
    print("="*60)
    
    ca_key = CERTS_DIR / "ca.key"
    ca_cert = CERTS_DIR / "ca.crt"
    
    # Generate CA private key
    if not run_command(
        f"openssl genrsa -out {ca_key} 4096",
        "Generating CA private key (4096-bit RSA)"
    ):
        return False
    
    # Generate CA certificate
    ca_config = f"""
[ req ]
distinguished_name = req_distinguished_name
prompt = no

[ req_distinguished_name ]
C = US
ST = California
L = San Francisco
O = Rogue Security
OU = Red Team Operations
CN = Rogue C2 CA
emailAddress = ca@rogue-c2.com
"""
    
    config_path = CERTS_DIR / "ca.cnf"
    with open(config_path, 'w') as f:
        f.write(ca_config)
    
    if not run_command(
        f"openssl req -new -x509 -days 3650 -key {ca_key} -out {ca_cert} -config {config_path}",
        "Generating CA certificate (valid 10 years)"
    ):
        return False
    
    # Verify CA certificate
    if not run_command(
        f"openssl x509 -in {ca_cert} -text -noout",
        "Verifying CA certificate"
    ):
        return False
    
    print(f"\n✅ CA generated:")
    print(f"   Key:  {ca_key}")
    print(f"   Cert: {ca_cert}")
    return True

def generate_server_cert():
    """Generate server certificate for C2."""
    print("\n" + "="*60)
    print("Generating Server Certificate")
    print("="*60)
    
    server_key = CERTS_DIR / "server.key"
    server_csr = CERTS_DIR / "server.csr"
    server_cert = CERTS_DIR / "server.crt"
    
    # Generate server private key
    if not run_command(
        f"openssl genrsa -out {server_key} 2048",
        "Generating server private key (2048-bit RSA)"
    ):
        return False
    
    # Create CSR config
    server_config = f"""
[ req ]
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
emailAddress = admin@rogue-c2.com

[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = c2.rogue-c2.com
DNS.2 = *.rogue-c2.com
DNS.3 = localhost
IP.1 = 127.0.0.1
"""
    
    config_path = CERTS_DIR / "server.cnf"
    with open(config_path, 'w') as f:
        f.write(server_config)
    
    # Generate CSR
    if not run_command(
        f"openssl req -new -key {server_key} -out {server_csr} -config {config_path}",
        "Generating Certificate Signing Request (CSR)"
    ):
        return False
    
    # Sign with CA
    if not run_command(
        f"openssl x509 -req -days 365 -in {server_csr} -CA {CERTS_DIR/'ca.crt'} -CAkey {CERTS_DIR/'ca.key'} -CAcreateserial -out {server_cert} -extfile {config_path} -extensions v3_req",
        "Signing server certificate with CA (valid 1 year)"
    ):
        return False
    
    # Verify server certificate
    if not run_command(
        f"openssl verify -CAfile {CERTS_DIR/'ca.crt'} {server_cert}",
        "Verifying server certificate chain"
    ):
        return False
    
    print(f"\n✅ Server certificate generated:")
    print(f"   Key:  {server_key}")
    print(f"   Cert: {server_cert}")
    return True

def generate_client_cert(client_name="implant"):
    """Generate client certificate for implants."""
    print(f"\n" + "="*60)
    print(f"Generating Client Certificate: {client_name}")
    print("="*60)
    
    client_key = CERTS_DIR / f"{client_name}.key"
    client_csr = CERTS_DIR / f"{client_name}.csr"
    client_cert = CERTS_DIR / f"{client_name}.crt"
    client_p12 = CERTS_DIR / f"{client_name}.p12"
    
    # Generate client private key
    if not run_command(
        f"openssl genrsa -out {client_key} 2048",
        f"Generating {client_name} private key (2048-bit RSA)"
    ):
        return False
    
    # Create CSR config
    client_config = f"""
[ req ]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[ req_distinguished_name ]
C = US
ST = California
L = San Francisco
O = Rogue Security
OU = Implant Client
CN = {client_name}.implant.rogue-c2.com
emailAddress = {client_name}@rogue-c2.com

[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
"""
    
    config_path = CERTS_DIR / f"{client_name}.cnf"
    with open(config_path, 'w') as f:
        f.write(client_config)
    
    # Generate CSR
    if not run_command(
        f"openssl req -new -key {client_key} -out {client_csr} -config {config_path}",
        f"Generating CSR for {client_name}"
    ):
        return False
    
    # Sign with CA
    if not run_command(
        f"openssl x509 -req -days 365 -in {client_csr} -CA {CERTS_DIR/'ca.crt'} -CAkey {CERTS_DIR/'ca.key'} -CAcreateserial -out {client_cert} -extfile {config_path} -extensions v3_req",
        f"Signing {client_name} certificate with CA (valid 1 year)"
    ):
        return False
    
    # Create PKCS12 bundle (for easier client use)
    if not run_command(
        f"openssl pkcs12 -export -out {client_p12} -inkey {client_key} -in {client_cert} -certfile {CERTS_DIR/'ca.crt'} -password pass:rogue123",
        f"Creating PKCS12 bundle for {client_name}"
    ):
        return False
    
    # Verify client certificate
    if not run_command(
        f"openssl verify -CAfile {CERTS_DIR/'ca.crt'} {client_cert}",
        f"Verifying {client_name} certificate chain"
    ):
        return False
    
    print(f"\n✅ Client certificate generated for {client_name}:")
    print(f"   Key:  {client_key}")
    print(f"   Cert: {client_cert}")
    print(f"   PKCS12: {client_p12} (password: rogue123)")
    return True

def generate_bulk_client_certs(count=10):
    """Generate multiple client certificates."""
    print(f"\n" + "="*60)
    print(f"Generating {count} Client Certificates")
    print("="*60)
    
    success_count = 0
    for i in range(1, count + 1):
        client_name = f"implant_{i:03d}"
        if generate_client_cert(client_name):
            success_count += 1
    
    print(f"\n✅ Generated {success_count}/{count} client certificates")
    return success_count == count

def create_mtls_config():
    """Create mTLS configuration file."""
    print("\n" + "="*60)
    print("Creating mTLS Configuration")
    print("="*60)
    
    config = {
        "enabled": True,
        "require_client_cert": True,
        "verify_client": True,
        "ca_cert": str(CERTS_DIR / "ca.crt"),
        "server_cert": str(CERTS_DIR / "server.crt"),
        "server_key": str(CERTS_DIR / "server.key"),
        "client_cert_dir": str(CERTS_DIR),
        "allowed_client_cns": [
            "*.implant.rogue-c2.com",
            "admin.implant.rogue-c2.com"
        ],
        "certificate_pinning": {
            "server_fingerprint": "",
            "client_fingerprints": []
        },
        "renewal_days": 30,
        "revocation_check": False
    }
    
    # Get server certificate fingerprint
    try:
        result = subprocess.run(
            f"openssl x509 -in {CERTS_DIR/'server.crt'} -fingerprint -sha256 -noout",
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            config["certificate_pinning"]["server_fingerprint"] = result.stdout.strip().split('=')[1]
    except:
        pass
    
    # Get client certificate fingerprints
    client_certs = list(CERTS_DIR.glob("implant_*.crt"))
    for cert_path in client_certs[:5]:  # First 5 only
        try:
            result = subprocess.run(
                f"openssl x509 -in {cert_path} -fingerprint -sha256 -noout",
                shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                fingerprint = result.stdout.strip().split('=')[1]
                config["certificate_pinning"]["client_fingerprints"].append({
                    "cert": cert_path.name,
                    "fingerprint": fingerprint
                })
        except:
            pass
    
    config_path = CONFIG_DIR / "mtls_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ mTLS configuration saved: {config_path}")
    return True

def create_verification_script():
    """Create script to verify mTLS setup."""
    print("\n" + "="*60)
    print("Creating Verification Script")
    print("="*60)
    
    script = """#!/usr/bin/env python3
"""
    """
mTLS Verification Script for Ranger C2
"""

import ssl
import socket
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
CERTS_DIR = BASE_DIR / "certs"

def test_server_connection():
    """Test connecting to server with mTLS."""
    print("Testing mTLS server connection...")
    
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_verify_locations(CERTS_DIR / "ca.crt")
    context.load_cert_chain(
        certfile=CERTS_DIR / "implant_001.crt",
        keyfile=CERTS_DIR / "implant_001.key"
    )
    
    try:
        with socket.create_connection(('localhost', 4443)) as sock:
            with context.wrap_socket(sock, server_hostname='c2.rogue-c2.com') as ssock:
                print(f"✅ Connected to server")
                print(f"   Server certificate: {ssock.getpeercert()}")
                print(f"   Cipher: {ssock.cipher()}")
                print(f"   TLS version: {ssock.version()}")
                return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_certificate_verification():
    """Test certificate verification."""
    print("\\nTesting certificate verification...")
    
    # Load CA cert
    with open(CERTS_DIR / "ca.crt", 'rb') as f:
        ca_cert = f.read()
    
    # Load server cert
    with open(CERTS_DIR / "server.crt", 'rb') as f:
        server_cert = f.read()
    
    # Load client cert
    with open(CERTS_DIR / "implant_001.crt", 'rb') as f:
        client_cert = f.read()
    
    print(f"✅ CA certificate loaded: {len(ca_cert)} bytes")
    print(f"✅ Server certificate loaded: {len(server_cert)} bytes")
    print(f"✅ Client certificate loaded: {len(client_cert)} bytes")
    
    # Verify certificates
    import subprocess
    
    # Verify server cert
    result = subprocess.run(
        f"openssl verify -CAfile {CERTS_DIR/'ca.crt'} {CERTS_DIR/'server.crt'}",
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✅ Server certificate verification: {result.stdout.strip()}")
    else:
        print(f"❌ Server certificate verification failed: {result.stderr}")
    
    # Verify client cert
    result = subprocess.run(
        f"openssl verify -CAfile {CERTS_DIR/'ca.crt'} {CERTS_DIR/'implant_001.crt'}",
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✅ Client certificate verification: {result.stdout.strip()}")
    else:
        print(f"❌ Client certificate verification failed: {result.stderr}")
    
    return True

def get_certificate_info(cert_path):
    """Get certificate information."""
    import subprocess
    
    result = subprocess.run(
        f"openssl x509 -in {cert_path} -text -noout",
        shell=True, capture_output=True, text=True
    )
    
    if result.returncode == 0:
        lines = result.stdout.split('\\n')
        info = {}
        for line in lines:
            if 'Subject:' in line:
                info['subject'] = line.strip()
            elif 'Issuer:' in line:
                info['issuer'] = line.strip()
            elif 'Not Before:' in line:
                info['not_before'] = line.strip()
            elif 'Not After:' in line:
                info['not_after'] = line.strip()
        return info
    return {}

def main():
    """Main verification function."""
    print("="*60)
    print("mTLS Setup Verification")
    print("="*60)
    
    # Check files exist
    required_files = [
        CERTS_DIR / "ca.crt",
        CERTS_DIR / "ca.key",
        CERTS_DIR / "server.crt",
        CERTS_DIR / "server.key",
        CERTS_DIR / "implant_001.crt",
        CERTS_DIR / "implant_001.key"
    ]
    
    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            print(f"✅ {file_path.name} exists")
        else:
            print(f"❌ {file_path.name} missing")
            all_exist = False
    
    if not all_exist:
        print("\\n❌ Missing required certificate files")
        return 1
    
    # Test certificate verification
    test_certificate_verification()
    
    # Get certificate info
    print("\\nCertificate Information:")
    print("-"*40)
    
    certs = [
        ("CA", CERTS_DIR / "ca.crt"),
        ("Server", CERTS_DIR / "server.crt"),
        ("Client", CERTS_DIR / "implant_001.crt")
    ]
    
    for name, path in certs:
        info = get_certificate_info(path)
        print(f"\\n{name}:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    print("\\n" + "="*60)
    print("✅ mTLS setup verification complete")
    print("\\nNote: Server connection test requires C2 server running with mTLS")
    print("To test connection, start C2 with mTLS enabled first.")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
    
    script_path = BASE_DIR / "verify_mtls.py"
    with open(script_path, 'w') as f:
        f.write(script)
    
    # Make executable
    script_path.chmod(0o755)
    
    print(f"✅ Verification script created: {script_path}")
    return True

def create_openssl_commands_cheatsheet():
    """Create cheatsheet for OpenSSL commands."""
    print("\n" + "="*60)
    print("Creating OpenSSL Commands Cheatsheet")
    print("="*60)
    
    cheatsheet = """# OpenSSL mTLS Commands Cheatsheet
# ===========================================

# 1. View Certificate Information
openssl x