---
name: crypto-research
description: "Use when investigating a crypto token pump, tracking whale wallets, or analyzing on-chain activity. Searches X/Twitter, exchanges, DEXScreener, and Arkham for comprehensive token intelligence."
version: 1.0.0
author: User
license: MIT
metadata:
  hermes:
    tags: [Crypto, Research, Trading, DeFi, OnChain, Whales, X, Twitter, Arkham, Hyperliquid]
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

### Phase 2 — X/Twitter Sentiment (2-5 min)

Search for social buzz around the token. Use multiple angles.

**Option A — Web search (fastest, use web_search):**
```
web_search(query="TOKEN_SYMBOL crypto pump today site:x.com OR site:twitter.com")
web_search(query="TOKEN_SYMBOL crypto news today")
web_search(query="TOKEN_SYMBOL listing announcement")
```

**Option B — Nitter instances (no auth needed):**
```
web_extract(urls=["https://nitter.privacydev.net/search?f=tweets&q=TOKEN_SYMBOL+crypto"])
web_extract(urls=["https://nitter.poast.org/search?f=tweets&q=TOKEN_SYMBOL+crypto"])
```

**Option C — Direct X search (if web_search covers it):**
```
web_search(query="TOKEN_SYMBOL from:coingecko OR from:binabory OR from:whale_alert")
```

Look for:
- Influencer mentions (KOLs with 50k+ followers)
- Listing announcements from exchanges
- Partnership news
- Coordinated shill campaigns (multiple accounts posting same text)
- FUD or scam allegations

### Phase 3 — Exchange & DEX Activity (2-3 min)

Check where the token is trading and liquidity depth.

**DEXScreener (best for DEX data):**
```bash
# Full pair data — liquidity, volume, price changes, txns
python3 ${HERMES_SKILL_DIR}/scripts/dexscreener_search.py "TOKEN_SYMBOL"
```

**Hyperliquid (perps DEX):**
```bash
# Check if token has perps market on Hyperliquid
curl -s "https://api.hyperliquid.xyz/info" \
  -H "Content-Type: application/json" \
  -d '{"type": "meta"}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
universe = data.get('universe', [])
for asset in universe:
    name = asset.get('name', '').upper()
    if 'TOKEN_SYMBOL' in name:
        print(json.dumps(asset, indent=2))
"
```

**Binance/Bybit spot data (via CCXT if installed, otherwise curl):**
```bash
# Binance ticker
curl -s "https://api.binance.com/api/v3/ticker/24hr?symbol=TOKEN_SYMBOLUSDT" | python3 -m json.tool

# Bybit ticker
curl -s "https://api.bybit.com/v5/market/tickers?category=spot&symbol=TOKEN_SYMBOLUSDT" | python3 -m json.tool
```

### Phase 4 — Whale & Wallet Tracking (3-5 min)

**Arkham Intelligence (primary source for wallet tracking):**

Use web_search to find Arkham entity pages:
```
web_search(query="TOKEN_SYMBOL site:platform.arkhamintelligence.com")
web_search(query="TOKEN_SYMBOL whale wallet arkham"
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

### Phase 5 — Compile Report (1-2 min)

After gathering all data, compile a structured report:

```
## 🔍 Crypto Research Report: [TOKEN_NAME] ($SYMBOL)

### 📊 Price & Volume
- Current Price: $X.XX
- 24h Change: +XX%
- 24h Volume: $XXM
- Market Cap: $XXM
- Liquidity: $XXM (DEX) / $XXM (CEX)

### 🐦 Social Sentiment (X/Twitter)
- Buzz level: HIGH / MEDIUM / LOW
- Key mentions: [list influencers/news]
- Sentiment: POSITIVE / NEGATIVE / MIXED
- Red flags: [coordinated shills? bot activity?]

### 📈 Exchange Activity
- Where trading: [list exchanges/pairs]
- Volume distribution: CEX vs DEX split
- Notable: [new listings? volume spikes?]

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
| DEXScreener | DEX pairs, liquidity, txns, price charts | `scripts/dexscreener_search.py` (free API) |
| Binance API | Spot/futures ticker, order book depth | `curl` (free, no auth) |
| Bybit API | Spot/derivatives ticker | `curl` (free, no auth) |
| Hyperliquid | Perps markets, open interest | `curl` (free, no auth) |
| X/Twitter | Social sentiment, news, KOL mentions | `web_search` / Nitter |
| Arkham | Whale wallets, entity tracking, fund flows | `web_search` + `web_extract` |
| Etherscan | ERC-20 transfers, holders, contracts | `web_extract` (free tier) |
| DexScreener | Token pairs across all chains | `curl` (free, no auth) |

## Red Flags Checklist

When analyzing a pump, check for these warning signs:

- [ ] Volume spike without news catalyst
- [ ] Concentrated top holders (>60% in top 10)
- [ ] Token contract verified? (Etherscan)
- [ ] Liquidity locked? (check DEXScreener)
- [ ] Social mentions from accounts created recently
- [ ] Same text posted by multiple accounts (coordinated shill)
- [ ] No GitHub / dev activity / audit
- [ ] Token age < 7 days
- [ ] Sudden volume from 1-2 exchanges only
- [ ] Large transfers to CEX (whales preparing to dump)

## Common Pitfalls

1. **Symbol collisions** — Many tokens share the same ticker (e.g., multiple "PEPE"). Always verify by checking contract address or chain.
2. **Stale Nitter instances** — Public Nitter hosts go down frequently. If one fails, try another or fall back to web_search.
3. **CoinGecko rate limits** — Free tier: ~30 req/min. Add delays between requests.
4. **Chain-specific tokens** — A token on Solana won't appear on Etherscan. Identify the chain first (DEXScreener shows chain info).
5. **Wash trading** — High volume on low-liquidity DEX pairs can be faked. Cross-reference CEX volume.

## Helper Scripts

All scripts use only Python stdlib (no pip install needed).

```bash
# Search CoinGecko for a token
python3 ${HERMES_SKILL_DIR}/scripts/coingecko_search.py "PEPE"

# Search DEXScreener for DEX pairs
python3 ${HERMES_SKILL_DIR}/scripts/dexscreener_search.py "PEPE"

# Full research pipeline (runs all phases, outputs report)
python3 ${HERMES_SKILL_DIR}/scripts/full_research.py "PEPE"
```

## Notes

- All APIs used are free and require no authentication
- For deeper Arkham data, consider their paid API if you need it regularly
- X/Twitter data quality depends on web_search coverage
- This skill is for RESEARCH only — never financial advice
