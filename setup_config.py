#!/usr/bin/env python3
"""Generate AstrBot config from environment variables."""
import json
import os

CONFIG_PATH = "data/cmd_config.json"

def create_config():
    nvidia_key = os.environ.get("NVIDIA_API_KEY", "")
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    model = os.environ.get("DEFAULT_MODEL", "deepseek-ai/deepseek-v4-pro")
    allowed = os.environ.get("TELEGRAM_ALLOWED_USERS", "")

    # Use PORT env var for dashboard (Render.com / HF Spaces)
    dashboard_port = int(os.environ.get("PORT", 6185))

    config = {
        "config_version": 2,
        "dashboard": {
            "port": dashboard_port,
            "host": "0.0.0.0",
        },
        "platform_settings": {
            "unique_session": False,
            "rate_limit": {"time": 60, "count": 30, "strategy": "stall"},
            "reply_prefix": "",
            "forward_threshold": 1500,
            "enable_id_white_list": True,
            "id_whitelist": [u.strip() for u in allowed.split(",") if u.strip()],
            "id_whitelist_log": True,
            "reply_with_mention": False,
            "reply_with_quote": False,
        },
        "provider_sources": [],
        "provider": [],
        "provider_settings": {
            "enable": True,
            "default_provider_id": "",
            "wake_prefix": "",
            "web_search": False,
            "streaming_response": True,
        },
        "platform": [],
        "admins_id": [u.strip() for u in allowed.split(",") if u.strip()],
        "content_safety": {"enable": False},
    }

    # Add NVIDIA NIM provider
    if nvidia_key:
        config["provider_sources"].append({
            "id": "nvidia-nim",
            "type": "openai_chat_completion",
            "name": "NVIDIA NIM",
            "base_url": "https://integrate.api.nvidia.com/v1",
            "api_key": nvidia_key,
            "model_configs": [
                {
                    "model": model,
                    "alias": model.split("/")[-1],
                    "max_context": 131072,
                    "vision_support": False,
                }
            ],
        })
        config["provider_settings"]["default_provider_id"] = "nvidia-nim"
        print(f"Provider: NVIDIA NIM — {model}")

    # Add Telegram platform
    if telegram_token:
        config["platform"].append({
            "id": "telegram",
            "type": "telegram",
            "enable": True,
            "telegram_token": telegram_token,
            "telegram_proxy": "",
        })
        print(f"Platform: Telegram enabled")

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Config saved to {CONFIG_PATH}")

if __name__ == "__main__":
    create_config()
