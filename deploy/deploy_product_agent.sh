#!/usr/bin/env bash
# Deploy Product Agent MCP Server to VPS

set -euo pipefail

VPS_HOST="${VPS_HOST:-sgp1.w9.nu}"
VPS_PORT="${VPS_PORT:-2204}"
VPS_USER="${VPS_USER:-root}"
SERVER_DIR="/opt/shb-workspace/product-agent"

echo "=== Deploying Product Agent MCP to $VPS_HOST ==="

# Sync code
rsync -avz -e "ssh -p $VPS_PORT" \
  --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
  ./servers/product-agent/ $VPS_USER@$VPS_HOST:$SERVER_DIR/

# Sync mcp_common
rsync -avz -e "ssh -p $VPS_PORT" \
  ./mcp_common/ $VPS_USER@$VPS_HOST:$SERVER_DIR/../mcp_common/

# Install deps and start service
ssh -p $VPS_PORT $VPS_USER@$VPS_HOST << 'ENDSSH'
set -euo pipefail
cd /opt/shb-workspace/product-agent

# Create venv if needed
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# Install deps
pip install --upgrade pip
pip install -r requirements.txt

# Install mcp_common
pip install -e ../mcp_common

# Install system deps (underthesea needs)
apt-get update && apt-get install -y python3-dev 2>/dev/null || true

# Restart service
systemctl daemon-reload
systemctl enable shb-product-agent
systemctl restart shb-product-agent

# Check status
systemctl status shb-product-agent --no-pager
ENDSSH

echo "=== Deploy complete ==="