# 🤖 AstrBot Crypto Agent

A fork of [AstrBot](https://github.com/Soulter/AstrBot) — an open-source multi-platform AI chatbot — extended with a **crypto research skill** for token analysis, exchange price comparison, and X/Twitter sentiment tracking.

> 📌 **AstrBot** is created and maintained by [Soulter](https://github.com/Soulter). This fork is the work of an enthusiast who adapted the agent for personal crypto research needs. All rights to the original AstrBot belong to its author.

## ✨ Features

### 🧠 AI Chatbot (AstrBot Core)
- **18+ messaging platforms**: Telegram, Discord, Slack, QQ, WeChat, LINE, Feishu, DingTalk, KOOK, and more
- **30+ LLM providers**: OpenAI, Anthropic, Gemini, Groq, xAI, DashScope, vLLM, and any OpenAI-compatible API
- **TTS/STT**: OpenAI Whisper, Edge TTS, Azure TTS, FishAudio, GPT-SoVITS, MiMo
- **Web Dashboard** (Vue 3 + Vuetify) for configuration at `http://localhost:6185`
- **Plugin system** ("Stars") with 1000+ community plugins
- **RAG Knowledge Base** with FAISS vector search
- **MCP (Model Context Protocol)** support for tool integration
- **Sandboxed code execution** via Shipyard

### 🔍 Crypto Research Skill
A dedicated skill for investigating crypto token pumps, tracking whale wallets, and analyzing market data:

| Phase | Source | What It Does |
|-------|--------|-------------|
| 1 | **CoinGecko** | Price, volume, market cap, ATH, 1h/24h/7d/30d changes |
| 2 | **DEXScreener** | DEX pairs, liquidity, buy/sell ratios, trending tokens |
| 3 | **9 CEX Exchanges** | Price comparison across Binance, Bybit, OKX, KuCoin, Gate.io, MEXC, Bitget, HTX, Hyperliquid |
| 4 | **X/Twitter** | Social sentiment analysis via web search + Nitter scraping |
| 5 | **Meme Platforms** | RugCheck safety scores, GMGN, DexTools, Pump.fun, Birdeye |
| 6 | **Whale Tracking** | Arkham Intelligence, Etherscan, Solscan wallet analysis |

**Key scripts** (all Python stdlib, no pip install needed):

```bash
# Full research pipeline (all 6 phases)
python3 scripts/full_research.py "PEPE"

# Individual scripts
python3 scripts/coingecko_search.py "BTC"          # Price & market data
python3 scripts/dexscreener_search.py "PEPE"        # DEX pairs & liquidity
python3 scripts/exchange_prices.py "ETH"            # 9 exchange price comparison
python3 scripts/twitter_search.py "SOL crypto"      # X/Twitter sentiment
python3 scripts/meme_platforms.py "WIF"             # Meme token safety
```

## 🚀 Installation

### Option 1: Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/Dima12348/astrbot-crypto-agent.git
cd astrbot-crypto-agent

# Start with Docker Compose
docker compose up -d

# Dashboard available at http://localhost:6185
```

The crypto-research skill is automatically copied to `data/skills/` on first start.

### Option 2: Python (Local)

**Requirements:** Python 3.12+, pip/uv

```bash
# Clone the repo
git clone https://github.com/Dima12348/astrbot-crypto-agent.git
cd astrbot-crypto-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Start the bot
python main.py

# Dashboard available at http://localhost:6185
```

### Option 3: CLI

```bash
pip install astrbot
astrbot init
astrbot run
```

### Option 4: One-Click Cloud

[![Deploy on RainYun](https://store.rainyun.com/img/badge.svg)](https://app.rainyun.com/apps/?type=docker&id=astrbot)

## ⚙️ Configuration

After starting, open the **Web Dashboard** at `http://localhost:6185` to configure:

### 1. Add an LLM Provider
Go to **Settings → Providers** and add your API key:
- OpenAI / Anthropic / Gemini / Groq / xAI
- Or any OpenAI-compatible endpoint (local models, proxies)

### 2. Connect a Messaging Platform
Go to **Settings → Platforms** and add:
- **Telegram**: Get bot token from [@BotFather](https://t.me/BotFather)
- **Discord**: Create bot at [Discord Developer Portal](https://discord.com/developers)
- **Slack**: Create app at [Slack API](https://api.slack.com/apps)
- **QQ**: Use NapCat or go-cqhttp
- Others: See [AstrBot documentation](https://astrbot.soulter.top)

### 3. Enable Crypto Research Skill
The skill is auto-loaded from `data/skills/research/crypto-research/`. No extra configuration needed — just ask the bot to research a token:

```
"Research PEPE for me"
"Why did VIRTUAL pump today?"
"Check exchange prices for ETH"
"Analyze meme token WIF on Solana"
```

## 📁 Project Structure

```
astrbot-crypto-agent/
├── main.py                    # Entry point
├── compose.yml                # Docker Compose
├── Dockerfile                 # Docker build
├── requirements.txt           # Python dependencies
├── setup_config.py            # Render.com config generator
├── start.sh                   # Docker startup script
│
├── astrbot/                   # Core bot engine
│   ├── core/
│   │   ├── agent/             # Agent framework + MCP
│   │   ├── platform/          # 18 platform adapters
│   │   ├── provider/          # 35 LLM/TTS/STT providers
│   │   ├── pipeline/          # Message processing pipeline
│   │   ├── knowledge_base/    # RAG with FAISS
│   │   ├── star/              # Plugin system
│   │   └── tools/             # Built-in tools
│   └── cli/                   # CLI commands
│
├── dashboard/                 # Vue 3 WebUI (source)
├── skills/                    # Custom skills
│   └── research/
│       └── crypto-research/   # 🔍 Crypto research skill
│           ├── SKILL.md
│           └── scripts/
│               ├── full_research.py       # Full 6-phase pipeline
│               ├── coingecko_search.py    # CoinGecko API
│               ├── dexscreener_search.py  # DEXScreener API
│               ├── exchange_prices.py     # 9 CEX exchanges
│               ├── twitter_search.py      # X/Twitter + sentiment
│               └── meme_platforms.py      # RugCheck + meme platforms
│
├── docs/                      # Documentation site
├── k8s/                       # Kubernetes manifests
└── tests/                     # Test suite
```

## 🔧 Deployment

### Docker + Shipyard Sandbox (Code Execution)

```bash
docker compose -f compose-with-shipyard.yml up -d
```

### Render.com

1. Fork this repo
2. Create a new **Web Service** on [Render](https://render.com)
3. Set build command: `docker build -t astrbot .`
4. Set start command: `python3 main.py`
5. Environment variable: `PORT=10000`

### Kubernetes

```bash
kubectl apply -f k8s/astrbot/
```

### systemd (Linux)

```bash
sudo cp scripts/astrbot.service /etc/systemd/system/
sudo systemctl enable astrbot
sudo systemctl start astrbot
```

## 📊 Crypto Research Examples

### Full Pipeline
```bash
python3 skills/research/crypto-research/scripts/full_research.py "PEPE"
python3 skills/research/crypto-research/scripts/full_research.py "VIRTUAL" --chain base
```

Output includes:
- 📊 Price & volume (CoinGecko)
- 🔄 DEX pairs & liquidity (DEXScreener)
- 🏦 Prices across 9 exchanges with spread analysis
- 🐦 X/Twitter sentiment with bullish/bearish signals
- 🛡️ RugCheck safety score (Solana tokens)
- 🔥 Trending tokens
- ⚠️ Automated risk assessment

### X/Twitter Search (Agent Mode)
```bash
# Agent gathers data via web_search, saves to JSON, feeds to script
python3 skills/research/crypto-research/scripts/twitter_search.py "PEPE" --input results.json
python3 skills/research/crypto-research/scripts/twitter_search.py "PEPE" --json
```

### Exchange Price Comparison
```bash
python3 skills/research/crypto-research/scripts/exchange_prices.py "BTC"
```
```
Exchange              Price    24h Chg    24h Volume
Binance          $67,432.10    +2.34%      $1.2B
Bybit            $67,428.50    +2.31%      $890M
OKX              $67,435.20    +2.36%      $456M
...
Price Spread: 0.012% ✅ Normal
```

## 🛡️ Security

- All crypto research scripts use **only Python stdlib** (no third-party packages)
- No API keys stored in code — configure via dashboard
- Branch protection enabled on `main` (no force push, no deletion)
- AGPL-3.0 license ensures modifications stay open source

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under [AGPL-3.0-or-later](LICENSE).

The crypto research skill (`skills/research/crypto-research/`) is licensed under MIT.

## 🔗 Links

- [AstrBot Documentation](https://astrbot.soulter.top)
- [AstrBot GitHub](https://github.com/Soulter/AstrBot)
- [Plugin Marketplace](https://astrbot.soulter.top/store/plugins)
- [Telegram Bot](https://t.me) — Create your bot with @BotFather

## 💡 Support

- [GitHub Issues](https://github.com/Dima12348/astrbot-crypto-agent/issues)
- [AstrBot Discord](https://discord.gg/astrbot)
