#!/bin/bash
# AstrBot start script for Render.com
set -e

cd /AstrBot

# Create data directories
mkdir -p data/skills data/config data/workspaces

# Copy crypto-research skill
if [ -d "skills/research/crypto-research" ]; then
    cp -r skills/research/crypto-research data/skills/
    echo "✅ Skill crypto-research installed"
fi

# Generate config from env vars
python3 setup_config.py

echo ""
echo "========================================="
echo "  AstrBot Crypto Agent"
echo "  Dashboard: http://0.0.0.0:${PORT:-6185}"
echo "  Login: astrbot / astrbot"
echo "========================================="
echo ""

python3 main.py
