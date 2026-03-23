#!/usr/bin/env python3
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
