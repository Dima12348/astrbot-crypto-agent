# AstrBot Crypto Agent

AI agent with crypto research skills, based on [AstrBot](https://github.com/AstrBotDevs/AstrBot).

## What is this?

A self-hosted AI agent that can investigate crypto token pumps, track whale wallets, and compile on-chain intelligence reports. Connect it to **Telegram** (or other supported platforms) and any **OpenAI-compatible AI provider**.

## Features

- **Crypto Research Skill** — investigate tokens via CoinGecko, DEXScreener, Binance, Hyperliquid APIs
- **Multi-platform** — Telegram, Slack, QQ, Lark, DingTalk, and [more](https://github.com/AstrBotDevs/AstrBot#supported-messaging-platforms)
- **Web Dashboard** — configure providers, platforms, and skills via web UI (port 6185)
- **Agent Framework** — MCP support, knowledge base, persona settings, auto context compression

## Quick Start

### Docker (recommended)

```bash
docker build -t astrbot-crypto .
docker run -p 6185:6185 \
  -e TELEGRAM_BOT_TOKEN="your-telegram-token" \
  -e TELEGRAM_ALLOWED_USERS="your-user-id" \
  -e NVIDIA_API_KEY="your-nvidia-nim-key" \
  -v $(pwd)/data:/AstrBot/data \
  astrbot-crypto
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (optional — can configure via UI) |
| `TELEGRAM_ALLOWED_USERS` | Comma-separated Telegram user IDs |
| `NVIDIA_API_KEY` | NVIDIA NIM API key (optional — can configure via UI) |
| `DEFAULT_MODEL` | LLM model ID (default: `deepseek-ai/deepseek-v4-pro`) |
| `PORT` | Dashboard port (default: `6185`) |

### Manual Setup

```bash
pip install -r requirements.txt
python main.py
```

Then open `http://localhost:6185` to configure your AI provider and platform.

## Crypto Research Skill

The `crypto-research` skill automatically installs on first start. It provides:

1. **Price & Volume Snapshot** — CoinGecko + DEXScreener
2. **X/Twitter Sentiment** — social buzz analysis
3. **Exchange & DEX Activity** — Binance, Hyperliquid, DEX pairs
4. **Whale & Wallet Tracking** — Arkham Intelligence, Etherscan, Solscan
5. **Structured Report** — risk assessment with red flags

## Based On

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) v4.23.6 — Multi-platform LLM chatbot framework
- [crypto-research skill](https://github.com/Dima12348/astrbot-crypto) — On-chain research agent

## License

AGPL-3.0-or-later (same as AstrBot)
