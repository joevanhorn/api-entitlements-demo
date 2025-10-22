#!/bin/bash
set -e

# Log all output
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "========================================="
echo "SCIM Entitlements Demo - Server Setup"
echo "Repository: ${github_repo}"
echo "Domain: ${domain_name}"
echo "========================================="

# Update system packages
echo "📦 Updating system packages..."
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python..."
apt-get install -y python3 python3-pip git curl

# Install Flask
echo "📚 Installing Flask..."
pip3 install Flask

# Install Caddy for automatic HTTPS
echo "🔒 Installing Caddy web server..."
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install caddy -y

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /opt/scim-demo
cd /opt/scim-demo

# Download SCIM server from GitHub
echo "⬇️  Downloading SCIM server from GitHub..."
curl -o demo_scim_server.py https://raw.githubusercontent.com/${github_repo}/main/app/demo_scim_server.py

# Verify download
if [ ! -f demo_scim_server.py ]; then
    echo "❌ Failed to download SCIM server code!"
    echo "Trying alternative method..."
    
    # Fallback: Clone the repo
    git clone https://github.com/${github_repo}.git temp_repo
    mv temp_repo/app/demo_scim_server.py .
    rm -rf temp_repo
fi

# Create systemd service for SCIM server
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/scim-demo.service <<EOF
[Unit]
Description=SCIM Entitlements Demo Server
Documentation=https://github.com/${github_repo}
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/scim-demo
Environment="SCIM_AUTH_TOKEN=${scim_auth_token}"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 /opt/scim-demo/demo_scim_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Start and enable SCIM service
echo "🚀 Starting SCIM service..."
systemctl daemon-reload
systemctl enable scim-demo
systemctl start scim-demo

# Wait for service to start
sleep 5

# Check if service is running
if systemctl is-active --quiet scim-demo; then
    echo "✅ SCIM service started successfully"
else
    echo "❌ SCIM service failed to start"
    journalctl -u scim-demo -n 50
fi

# Configure Caddy for automatic HTTPS
echo "🔒 Configuring Caddy for HTTPS..."
cat > /etc/caddy/Caddyfile << EOF
${domain_name} {
    reverse_proxy localhost:5000
    
    log {
        output file /var/log/caddy/access.log
        format json
    }
    
    encode gzip
    
    header {
        # Security headers
        Strict-Transport-Security "max-age=31536000;"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "no-referrer-when-downgrade"
    }
}
EOF

# Create Caddy log directory
mkdir -p /var/log/caddy
chown caddy:caddy /var/log/caddy

# Restart Caddy to apply configuration
echo "🔄 Restarting Caddy..."
systemctl restart caddy

# Verify Caddy is running
if systemctl is-active --quiet caddy; then
    echo "✅ Caddy started successfully"
else
    echo "❌ Caddy failed to start"
    journalctl -u caddy -n 50
fi

# Create a status check script
cat > /usr/local/bin/scim-status << 'STATUSEOF'
#!/bin/bash
echo "==================================="
echo "SCIM Demo Server Status"
echo "==================================="
echo ""
echo "SCIM Service:"
systemctl status scim-demo --no-pager | head -n 10
echo ""
echo "Caddy Service:"
systemctl status caddy --no-pager | head -n 10
echo ""
echo "Local Health Check:"
curl -s http://localhost:5000/health | python3 -m json.tool || echo "Service not responding"
echo ""
echo "==================================="
STATUSEOF

chmod +x /usr/local/bin/scim-status

# Final health check
echo "🏥 Running health check..."
sleep 10

for i in {1..5}; do
    if curl -s http://localhost:5000/health > /dev/null; then
        echo "✅ Health check passed!"
        break
    else
        echo "Attempt $i/5: Waiting for service..."
        sleep 5
    fi
done

echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo "Domain: ${domain_name}"
echo "Dashboard: https://${domain_name}"
echo "SCIM API: https://${domain_name}/scim/v2"
echo "Health: https://${domain_name}/health"
echo ""
echo "Run 'scim-status' to check services"
echo "Logs: /var/log/user-data.log"
echo "========================================="
