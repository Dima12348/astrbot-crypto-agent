# AstrBot Crypto Agent

AI agent with crypto research skills, based on [AstrBot](https://github.com/AstrBotDevs/AstrBot).

## What is this?

A self-hosted AI agent that can investigate crypto token pumps, track whale wallets, and compile on-chain intelligence reports. Connect it to **Telegram** (or other supported platforms) and any **OpenAI-compatible AI provider** — all configured via web dashboard.

## Features

- **Crypto Research Skill** — investigate tokens via CoinGecko, DEXScreener, Binance, Hyperliquid APIs
- **Multi-platform** — Telegram, Slack, QQ, Lark, DingTalk, and [more](https://github.com/AstrBotDevs/AstrBot#supported-messaging-platforms)
- **Web Dashboard** — configure providers, platforms, and skills via web UI
- **Agent Framework** — MCP support, knowledge base, persona settings, auto context compression

## Deploy on Render.com

1. Fork this repo
2. Create a new **Web Service** on [render.com](https://render.com)
3. Connect your forked repo
4. Settings:
   - **Environment**: Docker
   - **Port**: `6185`
5. Deploy

After deployment, open the dashboard URL and configure:

### Step 1 — Add AI Provider
Go to **Providers** → **Add Provider** → choose your provider:
- **OpenAI-compatible** (NVIDIA NIM, OpenRouter, local models, etc.)
- **Anthropic**, **Google Gemini**, **Dashscope**, etc.

### Step 2 — Add Platform
Go to **Platforms** → **Add Platform**:
- **Telegram** — enter your bot token from [@BotFather](https://t.me/BotFather)
- **Other platforms** — follow the in-dashboard instructions

### Step 3 — Use the Agent
Message your bot on Telegram. Ask about any crypto token:
> "Why did PEPE pump today?"
> "Research token 0x1234... on Ethereum"

The crypto-research skill will automatically activate and compile a full report.

## Crypto Research Skill

The `crypto-research` skill auto-installs on first start. It provides:

1. **Price & Volume Snapshot** — CoinGecko + DEXScreener
2. **X/Twitter Sentiment** — social buzz analysis
3. **Exchange & DEX Activity** — Binance, Hyperliquid, DEX pairs
4. **Whale & Wallet Tracking** — Arkham Intelligence, Etherscan, Solscan
5. **Structured Report** — risk assessment with red flags

## Environment Variables (optional)

You can pre-configure via env vars, but **everything can also be set via the web dashboard**:

| Variable | Description |
|----------|-------------|
| `PORT` | Dashboard port (default: `6185`, Render sets this automatically) |

## Manual Setup (local)

```bash
pip install -r requirements.txt
python main.py
```

Open `http://localhost:6185` to configure.

## Based On

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) v4.23.6 — Multi-platform LLM chatbot framework
- [crypto-research skill](https://github.com/Dima12348/astrbot-crypto) — On-chain research agent

## License

AGPL-3.0-or-later (same as AstrBot)
