#!/bin/bash

# Create a directory for certificates
mkdir -p certs

# Check for OpenSSL config file or create one temporarily
OPENSSL_CONFIG=$(mktemp)

cat > "$OPENSSL_CONFIG" <<EOF
[req]
default_bits       = 2048
prompt             = no
default_md         = sha256
req_extensions     = req_ext
distinguished_name = dn

[dn]
CN = localhost

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1   = localhost
IP.1    = 127.0.0.1
EOF

echo "Generating self-signed certificate for localhost development..."

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/server.key \
  -out certs/server.crt \
  -config "$OPENSSL_CONFIG" \
  -extensions req_ext

# Clean up the temp config file
rm "$OPENSSL_CONFIG"

# Set proper permissions
chmod 600 certs/server.key
chmod 644 certs/server.crt

echo "Self-signed certificate generated successfully!"
echo "  - Certificate: certs/server.crt"
echo "  - Private key: certs/server.key"
echo ""
echo "Note: These certificates are for development only and will cause security warnings in browsers."

