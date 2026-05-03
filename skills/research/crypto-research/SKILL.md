---
name: crypto-research
description: "Use when investigating a crypto token pump, tracking whale wallets, or analyzing on-chain activity. Searches 9 CEX exchanges, DEXScreener, RugCheck, meme platforms (GMGN, DexTools, Pump.fun, Birdeye), X/Twitter, and Arkham for comprehensive token intelligence."
version: 2.0.0
author: User
license: MIT
metadata:
  hermes:
    tags: [Crypto, Research, Trading, DeFi, OnChain, Whales, X, Twitter, Arkham, Hyperliquid, Meme, GMGN, PumpFun, RugCheck]
    related_skills: [polymarket]
---

# Crypto Research Agent

Investigate crypto token pumps, track whale wallets, and compile on-chain intelligence reports. Designed for answering "why did this coin pump?" with data from multiple sources.

## When to Use

- A coin pumped/dumped and you want to know why
- You need to check if a pump is organic or manipulated
- Tracking whale wallets and large fund movements
- Monitoring DEX/CEX volume and liquidity for a token
- Quick due diligence before entering a position
- Checking per-exchange prices (prices differ between exchanges!)
- Analyzing meme tokens (safety, rug pull risk, social buzz)

## Don't Use For

- Automated trading execution (this is research only)
- Portfolio tracking (use a portfolio app)
- Price alerts (use dedicated alert services)

## Research Workflow

When asked to research a token, follow this sequence:

### Phase 1 — Price & Volume Snapshot (1-2 min)

Get current market data to establish the baseline.

```bash
# CoinGecko — price, volume, market cap, 24h change
python3 ${HERMES_SKILL_DIR}/scripts/coingecko_search.py "TOKEN_NAME_OR_SYMBOL"

# DEXScreener — DEX pairs, liquidity, price changes across timeframes
python3 ${HERMES_SKILL_DIR}/scripts/dexscreener_search.py "TOKEN_SYMBOL"
```

Or use web_extract for quick lookups:
```
web_extract(urls=["https://api.coingecko.com/api/v3/search?query=TOKEN_SYMBOL"])
web_extract(urls=["https://api.dexscreener.com/latest/dex/search?q=TOKEN_SYMBOL"])
```

### Phase 2 — Exchange Price Comparison (2-3 min)

**Prices differ between exchanges!** This is critical for:
- Finding arbitrage opportunities
- Verifying real market price
- Spotting wash trading on specific exchanges

```bash
# Query ALL 9 exchanges at once
python3 ${HERMES_SKILL_DIR}/scripts/exchange_prices.py "TOKEN_SYMBOL"
```

Exchanges covered (all free, no auth needed):

| Exchange | API | Notes |
|----------|-----|-------|
| Binance | `api.binance.com/api/v3/ticker/24hr` | Largest volume |
| Bybit | `api.bybit.com/v5/market/tickers` | Derivatives leader |
| OKX | `okx.com/api/v5/market/ticker` | Major global exchange |
| KuCoin | `api.kucoin.com/api/v1/market/orderbook` | Altcoin hub |
| Gate.io | `api.gateio.ws/api/v4/spot/tickers` | Wide token selection |
| MEXC | `api.mexc.com/api/v3/ticker/24hr` | Many new listings |
| Bitget | `api.bitget.com/api/v2/spot/market/tickers` | Copy trading |
| HTX (Huobi) | `api.huobi.pro/market/detail/merged` | Asian markets |
| Hyperliquid | `api.hyperliquid.xyz/info` | Perps DEX, mid prices |

The script outputs a price table with spread analysis — if spread > 1%, flag as arbitrage opportunity.

### Phase 3 — X/Twitter Sentiment (2-5 min)

Search for social buzz around the token. The `twitter_search.py` script analyzes X/Twitter mentions and provides sentiment analysis.

```bash
# Standalone mode — direct web search + Nitter scraping
python3 ${HERMES_SKILL_DIR}/scripts/twitter_search.py "PEPE crypto"

# Agent mode (recommended) — feed pre-fetched data for analysis
# 1. Agent gathers data via web_search/web_extract
# 2. Saves to JSON file
# 3. Feeds to script for parsing & sentiment
python3 ${HERMES_SKILL_DIR}/scripts/twitter_search.py "PEPE" --input results.json

# Or via stdin
echo '{"web_results":[...]}' | python3 ${HERMES_SKILL_DIR}/scripts/twitter_search.py "PEPE" --stdin

# JSON-only output (for piping/processing)
python3 ${HERMES_SKILL_DIR}/scripts/twitter_search.py "PEPE" --json
```

**Agent workflow (recommended):**

When standalone scraping fails (VPS IPs blocked by search engines/CAPTCHAs), the agent should use its own `web_search` and `web_extract` tools:

```
# Step 1: Agent gathers data
web_search(query="TOKEN_SYMBOL crypto pump site:x.com OR site:twitter.com")
web_search(query="TOKEN_SYMBOL crypto news today")
web_search(query="TOKEN_SYMBOL listing announcement")
web_extract(urls=["https://nitter.tiekoetter.com/search?f=tweets&q=TOKEN_SYMBOL+crypto"])

# Step 2: Save results to JSON
# Format: {"web_results": [{"title":"...", "url":"...", "snippet":"..."}],
#          "nitter_html": "<raw html>", "nitter_instance": "https://nitter.tiekoetter.com"}

# Step 3: Feed to script
python3 ${HERMES_SKILL_DIR}/scripts/twitter_search.py "TOKEN_SYMBOL" --input results.json
```

The script provides:
- X/Twitter web search results (links, snippets)
- Nitter tweet parsing (text, likes, retweets, replies)
- Keyword-based sentiment analysis (bullish/bearish signals)
- Structured report with engagement metrics

**Look for:**
- Influencer mentions (KOLs with 50k+ followers)
- Listing announcements from exchanges
- Partnership news
- Coordinated shill campaigns (multiple accounts posting same text)
- FUD or scam allegations

**Note:** AstrBot has no native X/Twitter platform adapter. All X/Twitter research is done via web_search, Nitter scraping, and the `twitter_search.py` script.

### Phase 4 — Meme Token Platforms (2-3 min)

For meme tokens (Solana memes, new tokens, pump.fun launches), use the dedicated script:

```bash
# Meme platform research — RugCheck safety + DEXScreener data
python3 ${HERMES_SKILL_DIR}/scripts/meme_platforms.py "TOKEN_SYMBOL"
python3 ${HERMES_SKILL_DIR}/scripts/meme_platforms.py "CONTRACT_ADDRESS" --chain solana
```

This queries:
- **RugCheck** (api.rugcheck.xyz) — token safety score, risk flags, LP lock %
- **DEXScreener** — all DEX pairs, liquidity, buy/sell ratios, social links
- **DEXScreener Trending** — top boosted tokens right now

For platforms behind Cloudflare (APIs blocked), use web_search:

```
# GMGN — Solana meme token analytics, smart money tracking
web_search(query="TOKEN_SYMBOL site:gmgn.ai")
web_extract(urls=["https://gmgn.ai/token/CHAIN/TOKEN_ADDRESS"])

# DexTools — DEX analytics, pair explorer, charts
web_search(query="TOKEN_SYMBOL site:dextools.io")
web_extract(urls=["https://www.dextools.io/app/en/pair-explorer/TOKEN_ADDRESS"])

# Pump.fun — Solana token launcher, bonding curve data
web_search(query="TOKEN_SYMBOL site:pump.fun")

# Birdeye — Solana/ETH token analytics, wallet tracking
web_search(query="TOKEN_SYMBOL site:birdeye.so")
web_extract(urls=["https://birdeye.so/token/TOKEN_ADDRESS?chain=solana"])
```

### Phase 5 — Whale & Wallet Tracking (3-5 min)

**Arkham Intelligence (primary source for wallet tracking):**

Use web_search to find Arkham entity pages:
```
web_search(query="TOKEN_SYMBOL site:platform.arkhamintelligence.com")
web_search(query="TOKEN_SYMBOL whale wallet arkham")
```

Then extract data:
```
web_extract(urls=["https://platform.arkhamintelligence.com/token/TOKEN_SYMBOL"])
```

**Alternative on-chain explorers:**
```
# Etherscan (ERC-20 tokens)
web_search(query="TOKEN_SYMBOL etherscan token tracker")

# Solscan (Solana tokens)
web_search(query="TOKEN_SYMBOL solscan holders")

# DexScreener top holders
web_extract(urls=["https://api.dexscreener.com/latest/dex/tokens/CONTRACT_ADDRESS"])
```

Look for:
- Top holder concentration (>50% in top 10 wallets = red flag)
- Recent large transfers to/from exchanges
- New wallets created in last 24h holding significant amounts
- Known whale wallets accumulating

### Phase 6 — Compile Report (1-2 min)

After gathering all data, compile a structured report:

```
## 🔍 Crypto Research Report: [TOKEN_NAME] ($SYMBOL)

### 📊 Price & Volume
- Current Price: $X.XX (CoinGecko aggregated)
- 24h Change: +XX%
- 24h Volume: $XXM
- Market Cap: $XXM
- Liquidity: $XXM (DEX) / $XXM (CEX)

### 🏦 Exchange Prices
| Exchange | Price | 24h Change | Volume |
|----------|-------|------------|--------|
| Binance  | $X.XX | +X%        | $XXM   |
| OKX      | $X.XX | +X%        | $XXM   |
| Bybit    | $X.XX | +X%        | $XXM   |
| ...      | ...   | ...        | ...    |
- Price Spread: X.XX% (Low: $X on EX1 / High: $X on EX2)

### 🐦 Social Sentiment (X/Twitter)
- Buzz level: HIGH / MEDIUM / LOW
- Key mentions: [list influencers/news]
- Sentiment: POSITIVE / NEGATIVE / MIXED
- Red flags: [coordinated shills? bot activity?]

### 🔄 DEX Activity
- Where trading: [list DEX pairs/chains]
- Volume distribution: CEX vs DEX split
- Notable: [new listings? volume spikes?]

### 🐸 Meme Platform Data
- RugCheck Score: X (GOOD / CAUTION / DANGEROUS)
- LP Locked: XX%
- Risks: [list RugCheck warnings]
- GMGN Smart Money: [if available]
- DexTools: [pair explorer link]

### 🐋 Whale Activity
- Top 10 holder concentration: XX%
- Recent large moves: [describe]
- Wallet patterns: [accumulation / distribution / neutral]

### ⚠️ Risk Assessment
- Rug pull risk: LOW / MEDIUM / HIGH
- Manipulation indicators: [list]
- Organic growth indicators: [list]

### 💡 Verdict
[2-3 sentence summary: is this pump justified by news/fundamentals,
or does it look like manipulation/paid promotion?]
```

## Quick Reference

| Data Source | What It Provides | How to Access |
|-------------|-----------------|---------------|
| CoinGecko | Price, volume, market cap, metadata | `scripts/coingecko_search.py` (free API) |
| DEXScreener | DEX pairs, liquidity, txns, trending | `scripts/dexscreener_search.py` (free API) |
| Binance | Spot ticker, 24h stats | `scripts/exchange_prices.py` (free, no auth) |
| Bybit | Spot/derivatives ticker | `scripts/exchange_prices.py` (free, no auth) |
| OKX | Spot ticker, 24h stats | `scripts/exchange_prices.py` (free, no auth) |
| KuCoin | Spot orderbook L1 | `scripts/exchange_prices.py` (free, no auth) |
| Gate.io | Spot ticker, 24h stats | `scripts/exchange_prices.py` (free, no auth) |
| MEXC | Spot ticker, 24h stats | `scripts/exchange_prices.py` (free, no auth) |
| Bitget | Spot ticker, 24h stats | `scripts/exchange_prices.py` (free, no auth) |
| HTX (Huobi) | Spot merged ticker | `scripts/exchange_prices.py` (free, no auth) |
| Hyperliquid | Perps markets, mid prices | `scripts/exchange_prices.py` (free, no auth) |
| RugCheck | Token safety, risks, LP lock % | `scripts/meme_platforms.py` (free API) |
| DEXScreener Trending | Top boosted tokens | `scripts/meme_platforms.py` (free API) |
| GMGN | Meme analytics, smart money | `web_search` (API behind Cloudflare) |
| DexTools | DEX pair explorer, charts | `web_search` (API behind Cloudflare) |
| Pump.fun | Solana token launcher data | `web_search` (API behind Cloudflare) |
| Birdeye | Solana token analytics | `web_search` (API behind Cloudflare) |
| X/Twitter | Social sentiment, news, KOL mentions | `scripts/twitter_search.py` + `web_search` / Nitter |
| Arkham | Whale wallets, entity tracking, fund flows | `web_search` + `web_extract` |
| Etherscan | ERC-20 transfers, holders, contracts | `web_extract` (free tier) |

## Red Flags Checklist

When analyzing a pump, check for these warning signs:

- [ ] Volume spike without news catalyst
- [ ] Concentrated top holders (>60% in top 10)
- [ ] Token contract verified? (Etherscan)
- [ ] Liquidity locked? (check RugCheck / DEXScreener)
- [ ] Social mentions from accounts created recently
- [ ] Same text posted by multiple accounts (coordinated shill)
- [ ] No GitHub / dev activity / audit
- [ ] Token age < 7 days
- [ ] Sudden volume from 1-2 exchanges only
- [ ] Large transfers to CEX (whales preparing to dump)
- [ ] Price spread > 1% between exchanges (possible manipulation)
- [ ] RugCheck score > 20 (high risk)
- [ ] LP locked < 50% (dev can drain liquidity)
- [ ] Only on DEX, not on any CEX (lower credibility)

## Common Pitfalls

1. **Symbol collisions** — Many tokens share the same ticker (e.g., multiple "PEPE"). Always verify by checking contract address or chain.
2. **Stale Nitter instances** — Public Nitter hosts go down frequently. If one fails, try another or fall back to web_search.
3. **CoinGecko rate limits** — Free tier: ~30 req/min. Add delays between requests.
4. **Chain-specific tokens** — A token on Solana won't appear on Etherscan. Identify the chain first (DEXScreener shows chain info).
5. **Wash trading** — High volume on low-liquidity DEX pairs can be faked. Cross-reference CEX volume.
6. **Price differences** — Prices CAN and DO differ between exchanges. Don't rely on a single source. Use `exchange_prices.py` to compare.
7. **Meme token safety** — Always run RugCheck for Solana tokens. A token can pump 1000% and still be a rug pull.
8. **Cloudflare blocks** — GMGN, Pump.fun APIs are behind Cloudflare. Use web_search/web_extract as fallback.

## Helper Scripts

All scripts use only Python stdlib (no pip install needed).

```bash
# Search CoinGecko for a token
python3 ${HERMES_SKILL_DIR}/scripts/coingecko_search.py "PEPE"

# Search DEXScreener for DEX pairs
python3 ${HERMES_SKILL_DIR}/scripts/dexscreener_search.py "PEPE"

# Compare prices across 9 exchanges
python3 ${HERMES_SKILL_DIR}/scripts/exchange_prices.py "PEPE"

# Meme token research (RugCheck + DEXScreener trending)
python3 ${HERMES_SKILL_DIR}/scripts/meme_platforms.py "WIF"
python3 ${HERMES_SKILL_DIR}/scripts/meme_platforms.py "DEZ...263" --chain solana

# X/Twitter sentiment search (standalone + agent modes)
python3 ${HERMES_SKILL_DIR}/scripts/twitter_search.py "PEPE crypto"
python3 ${HERMES_SKILL_DIR}/scripts/twitter_search.py "PEPE" --input results.json
python3 ${HERMES_SKILL_DIR}/scripts/twitter_search.py "PEPE" --json

# Full research pipeline (runs all 6 phases, outputs report)
python3 ${HERMES_SKILL_DIR}/scripts/full_research.py "PEPE"
python3 ${HERMES_SKILL_DIR}/scripts/full_research.py "VIRTUAL" --chain base
python3 ${HERMES_SKILL_DIR}/scripts/full_research.py "PEPE" --twitter-input twitter_data.json
```

## X/Twitter Integration Note

AstrBot has **no native X/Twitter platform adapter**. The crypto research skill uses:
- `twitter_search.py` — dedicated script with standalone web search + Nitter scraping + sentiment analysis
- Agent `web_search` / `web_extract` tools — primary method for gathering X/Twitter data from VPS
- Nitter instances (e.g., `nitter.tiekoetter.com`) — public X/Twitter frontends, no auth needed

The recommended agent workflow:
1. Use `web_search` to find X/Twitter mentions
2. Use `web_extract` to scrape Nitter pages
3. Save results to JSON and feed to `twitter_search.py --input` for parsing + sentiment analysis

For deeper X/Twitter integration:
- Add a Twitter MCP server to AstrBot's MCP configuration (dashboard → Extensions → MCP Servers)
- Consider adding a custom platform adapter for X/Twitter

## Notes

- All APIs used are free and require no authentication
- For deeper Arkham data, consider their paid API if you need it regularly
- X/Twitter data quality depends on web_search coverage
- GMGN/Pump.fun/DexTools/Birdeye require web_search (APIs behind Cloudflare)
- This skill is for RESEARCH only — never financial advice
