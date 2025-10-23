#!/bin/bash
set -e

# SCIM Demo Server Setup Script
# This script is run by cloud-init on first boot
# App Version: ${app_version}
# GitHub Repo: ${github_repo}

exec > >(tee -a /var/log/user-data.log)
exec 2>&1

echo "========================================"
echo "SCIM Demo Server Setup"
echo "========================================"
echo "Domain: ${domain_name}"
echo "App Version: ${app_version}"
echo "Started at: $(date)"
echo "========================================"

# Update system
echo "📦 Updating system packages..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https

# Install Caddy for reverse proxy and automatic HTTPS
echo "🔧 Installing Caddy..."
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y caddy

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /opt/scim-demo
cd /opt/scim-demo

# Clone repository
echo "📥 Cloning repository..."
git clone https://github.com/${github_repo}.git .

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --break-system-packages flask requests

# Configure Caddy
echo "🔧 Configuring Caddy..."
cat > /etc/caddy/Caddyfile << 'CADDYEOF'
${domain_name} {
    reverse_proxy localhost:5000
    
    # Enable compression
    encode gzip
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-XSS-Protection "1; mode=block"
    }
    
    # Logging
    log {
        output file /var/log/caddy/access.log
    }
}
CADDYEOF

# Create systemd service for SCIM server
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/scim-demo.service << 'SERVICEEOF'
[Unit]
Description=SCIM Entitlements Demo Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/scim-demo
Environment="SCIM_AUTH_TOKEN=${scim_auth_token}"
Environment="SCIM_BASIC_USER=${scim_basic_user}"
Environment="SCIM_BASIC_PASS=${scim_basic_pass}"
Environment="APP_VERSION=${app_version}"
ExecStart=/usr/bin/python3 /opt/scim-demo/demo_scim_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Reload systemd and start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable scim-demo
systemctl start scim-demo
systemctl enable caddy
systemctl restart caddy

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "✅ Checking service status..."
systemctl status scim-demo --no-pager || true
systemctl status caddy --no-pager || true

# Test local Flask app
echo "🧪 Testing Flask app..."
curl -f http://localhost:5000/health || echo "⚠️ Flask health check failed"

echo "========================================"
echo "✅ SETUP COMPLETE"
echo "========================================"
echo "Domain: ${domain_name}"
echo "App Version: ${app_version}"
echo "Dashboard: https://${domain_name}"
echo "SCIM API: https://${domain_name}/scim/v2"
echo "Completed at: $(date)"
echo "========================================"
