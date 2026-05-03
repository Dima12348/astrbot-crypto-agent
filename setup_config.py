#!/usr/bin/env python3
"""Generate AstrBot config for Render.com deployment.

Creates a minimal but complete config so the dashboard works immediately.
All provider/platform configuration is done via the web dashboard.
"""
import json
import os

CONFIG_PATH = "data/cmd_config.json"

def create_config():
    port = int(os.environ.get("PORT", 6185))
    tz = os.environ.get("TZ", "Europe/Kyiv")

    config = {
        "config_version": 2,
        "dashboard": {
            "enable": True,
            "username": "astrbot",
            "password": "77b90590a8945a7d36c963981a307dc9",
            "port": port,
            "host": "0.0.0.0",
        },
        "platform": [],
        "provider": [],
        "provider_sources": [],
        "provider_settings": {},
        "timezone": tz,
        "admins_id": ["astrbot"],
        "platform_settings": {},
        "http_proxy": os.environ.get("HTTP_PROXY", ""),
    }

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Config created: port={port}, tz={tz}")
    print(f"Dashboard login: astrbot / astrbot")
    print(f"Open http://localhost:{port} to configure.")

if __name__ == "__main__":
    create_config()
