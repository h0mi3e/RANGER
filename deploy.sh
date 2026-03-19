#!/bin/bash
# deploy.sh - One-click deployment of Nginx mask and C2

set -e

echo "[*] RogueRANGER Deployment Script"
echo "================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "[-] Please run as root (sudo)"
    exit 1
fi

# Install dependencies
echo "[*] Installing dependencies..."
apt-get update
apt-get install -y nginx openssl python3-pip

# Install Python packages
pip3 install flask cryptography pycryptodome

# Generate self-signed certificate (for testing)
echo "[*] Generating self-signed certificate..."
mkdir -p /etc/ssl/private /etc/ssl/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt \
    -subj "/C=US/ST=WA/L=Seattle/O=IT/CN=localhost"

# Copy Nginx config
echo "[*] Deploying Nginx configuration..."
cp nginx/wordpress-mask.conf /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/wordpress-mask.conf /etc/nginx/sites-enabled/

# Test and reload Nginx
nginx -t && systemctl reload nginx

# Create fake WordPress directory (optional)
if [ ! -d "/var/www/html" ]; then
    echo "[*] Creating fake WordPress directory..."
    mkdir -p /var/www/html
    echo "<?php phpinfo(); ?>" > /var/www/html/index.php
fi

echo "[+] Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Start the C2 server: python3 c2_malleable.py"
echo "  2. Update your implant with the domain"
echo "  3. Test connection: curl -k https://localhost/wp-admin/admin-ajax.php"
echo ""
echo "Your C2 is now masked as a WordPress site!"
