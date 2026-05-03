#!/usr/bin/env python3
"""Generate minimal AstrBot config for Render.com deployment.

All providers and platforms are configured via the web dashboard (port 6185).
This script only sets the dashboard port from the PORT env var.
"""
import json
import os

CONFIG_PATH = "data/cmd_config.json"

def create_config():
    dashboard_port = int(os.environ.get("PORT", 6185))

    config = {
        "config_version": 2,
        "dashboard": {
            "port": dashboard_port,
            "host": "0.0.0.0",
        },
    }

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Dashboard config: port {dashboard_port}")
    print("Configure providers and platforms at the web dashboard.")

if __name__ == "__main__":
    create_config()
