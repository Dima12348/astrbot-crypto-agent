#!/bin/bash
# AstrBot start script
set -e

cd /AstrBot

# Create data directories
mkdir -p data/skills data/config data/workspaces

# Copy crypto-research skill
if [ -d "skills/research/crypto-research" ]; then
    cp -r skills/research/crypto-research data/skills/
    echo "Skill crypto-research installed"
fi

# Generate config from env vars (if any env vars are set)
python3 setup_config.py

echo "Starting AstrBot..."
python3 main.py
