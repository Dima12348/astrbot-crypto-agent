#!/usr/bin/env python3
"""Full crypto research pipeline — gathers data from multiple sources and compiles a report.

Runs all research phases:
  1. Price & Volume (CoinGecko)
  2. DEX Pairs & Liquidity (DEXScreener)
  3. Exchange prices across 9 CEX (Binance, Bybit, OKX, KuCoin, Gate.io, MEXC, Bitget, HTX, Hyperliquid)
  4. X/Twitter Sentiment (web search + Nitter)
  5. Meme platforms (RugCheck safety, DEXScreener trending)
  6. Compiles a structured report

Usage:
    python full_research.py "PEPE"
    python full_research.py "VIRTUAL" --chain base
    python full_research.py "PEPE" --twitter-input twitter_data.json
    python full_research.py "0xdAC17F958D2ee523a2206206994597C13D831ec7"  # by contract
"""
import sys
import os
import json
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import time
from datetime import datetime

HEADERS = {"User-Agent": "HermesCryptoResearch/1.0", "Accept": "application/json"}


def api_get(url, timeout=15):
    """Generic GET request."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, Exception) as e:
        return {"error": str(e)}


def fmt_num(n):
    if n is None:
        return "N/A"
    n = float(n)
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    if n >= 1e3:
        return f"${n/1e3:.1f}K"
    return f"${n:.6f}"


def fmt_pct(n):
    if n is None:
        return "N/A"
    return f"{'+'if n>=0 else ''}{n:.2f}%"


def fmt_price(n):
    if n is None:
        return "N/A"
    n = float(n)
    if n < 0.000001:
        return f"${n:.10f}"
    if n < 0.001:
        return f"${n:.8f}"
    if n < 1:
        return f"${n:.6f}"
    return f"${n:,.4f}"


# ─── Phase 1: CoinGecko ───────────────────────────────────────────────

def coingecko_search(query):
    """Search CoinGecko and return top token data."""
    print("  [1/5] CoinGecko — price & market data...")
    url = f"https://api.coingecko.com/api/v3/search?query={urllib.parse.quote(query)}"
    data = api_get(url)
    coins = data.get("coins", [])
    if not coins:
        print(f"    No results for '{query}'")
        return None

    coin = coins[0]
    coin_id = coin["id"]
    print(f"    Found: {coin['name']} ({coin['symbol'].upper()}) — Rank #{coin.get('market_cap_rank', '?')}")

    time.sleep(1.5)  # Rate limit
    url2 = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}&price_change_percentage=1h,24h,7d,30d&sparkline=false"
    market = api_get(url2)
    if market and isinstance(market, list) and len(market) > 0:
        return market[0]
    return {"name": coin["name"], "symbol": coin["symbol"], "id": coin_id}


# ─── Phase 2: DEXScreener ─────────────────────────────────────────────

def dexscreener_search(query, chain_filter=None):
    """Search DEXScreener for DEX pairs."""
    print("  [2/5] DEXScreener — DEX pairs & liquidity...")
    url = f"https://api.dexscreener.com/latest/dex/search?q={urllib.parse.quote(query)}"
    data = api_get(url)
    pairs = data.get("pairs", [])
    if chain_filter:
        pairs = [p for p in pairs if p.get("chainId", "").lower() == chain_filter.lower()]
    pairs.sort(key=lambda p: float(p.get("volume", {}).get("h24", 0) or 0), reverse=True)
    print(f"    Found {len(pairs)} pairs")
    return pairs[:5]


# ─── Phase 3: All Exchange Prices ─────────────────────────────────────

def query_binance(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
    data = api_get(url)
    if data and "lastPrice" in data:
        return {"exchange": "Binance", "price": float(data["lastPrice"]),
                "volume": float(data.get("quoteVolume", 0)),
                "high": float(data.get("highPrice", 0)),
                "low": float(data.get("lowPrice", 0)),
                "change_24h": float(data.get("priceChangePercent", 0))}
    return None


def query_bybit(symbol):
    url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}USDT"
    data = api_get(url)
    if data and data.get("result", {}).get("list"):
        item = data["result"]["list"][0]
        return {"exchange": "Bybit", "price": float(item.get("lastPrice", 0)),
                "volume": float(item.get("turnover24h", 0)),
                "high": float(item.get("highPrice24h", 0)),
                "low": float(item.get("lowPrice24h", 0)),
                "change_24h": float(item.get("price24hPcnt", 0)) * 100}
    return None


def query_okx(symbol):
    url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT"
    data = api_get(url)
    if data and data.get("data"):
        item = data["data"][0]
        last = float(item.get("last", 0))
        open_ = float(item.get("open24h", 0))
        change = ((last - open_) / open_ * 100) if open_ else 0
        return {"exchange": "OKX", "price": last,
                "volume": float(item.get("volCcy24h", 0)),
                "high": float(item.get("high24h", 0)),
                "low": float(item.get("low24h", 0)),
                "change_24h": change}
    return None


def query_kucoin(symbol):
    url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}-USDT"
    data = api_get(url)
    if data and data.get("data"):
        item = data["data"]
        return {"exchange": "KuCoin", "price": float(item.get("price", 0)),
                "volume": 0, "high": 0, "low": 0, "change_24h": 0}
    return None


def query_gateio(symbol):
    url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}_USDT"
    data = api_get(url)
    if data and isinstance(data, list) and data:
        item = data[0]
        return {"exchange": "Gate.io", "price": float(item.get("last", 0)),
                "volume": float(item.get("quote_volume", 0)),
                "high": float(item.get("high_24h", 0)),
                "low": float(item.get("low_24h", 0)),
                "change_24h": float(item.get("change_percentage", 0))}
    return None


def query_mexc(symbol):
    url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={symbol}USDT"
    data = api_get(url)
    if data and "lastPrice" in data:
        return {"exchange": "MEXC", "price": float(data["lastPrice"]),
                "volume": float(data.get("quoteVolume", 0)),
                "high": float(data.get("highPrice", 0)),
                "low": float(data.get("lowPrice", 0)),
                "change_24h": float(data.get("priceChangePercent", 0))}
    return None


def query_bitget(symbol):
    url = f"https://api.bitget.com/api/v2/spot/market/tickers?symbol={symbol}USDT"
    data = api_get(url)
    if data and data.get("data"):
        item = data["data"][0] if isinstance(data["data"], list) else data["data"]
        chg = float(item.get("change24h", 0))
        if abs(chg) < 1:
            chg *= 100
        return {"exchange": "Bitget", "price": float(item.get("lastPr", 0)),
                "volume": float(item.get("quoteVolume", 0)),
                "high": float(item.get("high24h", 0)),
                "low": float(item.get("low24h", 0)),
                "change_24h": chg}
    return None


def query_htx(symbol):
    url = f"https://api.huobi.pro/market/detail/merged?symbol={symbol.lower()}usdt"
    data = api_get(url)
    if data and data.get("tick"):
        tick = data["tick"]
        open_ = tick.get("open", 0)
        last = tick.get("close", 0)
        change = ((last - open_) / open_ * 100) if open_ else 0
        return {"exchange": "HTX (Huobi)", "price": last,
                "volume": float(tick.get("amount", 0)),
                "high": float(tick.get("high", 0)),
                "low": float(tick.get("low", 0)),
                "change_24h": change}
    return None


def query_hyperliquid(symbol):
    url = "https://api.hyperliquid.xyz/info"
    req = urllib.request.Request(url, headers={**HEADERS, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10, data=json.dumps({"type": "meta"}).encode()) as resp:
            meta = json.loads(resp.read())
    except Exception:
        return None
    for asset in meta.get("universe", []):
        if asset.get("name", "").upper() == symbol.upper():
            try:
                with urllib.request.urlopen(req, timeout=10, data=json.dumps({"type": "allMids"}).encode()) as resp:
                    mids = json.loads(resp.read())
                mid = mids.get(symbol.upper())
                if mid:
                    return {"exchange": "Hyperliquid (perps)", "price": float(mid),
                            "volume": 0, "high": 0, "low": 0, "change_24h": 0}
            except Exception:
                pass
    return None


def query_all_exchanges(symbol):
    """Query all 9 exchanges and return results sorted by volume."""
    print(f"  [3/5] Exchanges — querying 9 CEX...")
    EXCHANGES = [
        ("Binance", query_binance),
        ("Bybit", query_bybit),
        ("OKX", query_okx),
        ("KuCoin", query_kucoin),
        ("Gate.io", query_gateio),
        ("MEXC", query_mexc),
        ("Bitget", query_bitget),
        ("HTX", query_htx),
        ("Hyperliquid", query_hyperliquid),
    ]
    results = []
    for name, func in EXCHANGES:
        print(f"    {name}...", end=" ", flush=True)
        r = func(symbol)
        if r:
            print(f"✅ {fmt_price(r['price'])}")
            results.append(r)
        else:
            print("❌")
        time.sleep(0.2)
    results.sort(key=lambda r: r["volume"], reverse=True)
    print(f"    Found on {len(results)}/{len(EXCHANGES)} exchanges")
    return results


# ─── Phase 4: X/Twitter Sentiment ─────────────────────────────────────

def twitter_search(query, twitter_input=None):
    """Run twitter_search.py and return parsed results."""
    print("  [4/6] X/Twitter — sentiment analysis...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(script_dir, "twitter_search.py")
    cmd = [sys.executable, script, query, "--json", "--top", "10"]
    if twitter_input:
        cmd.extend(["--input", twitter_input])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout.strip())
            tw = len(data.get("web_results", []))
            nt = len(data.get("nitter_tweets", []))
            eng = data.get("engine", "?")
            src = data.get("source", "?")
            print(f"    Found {tw} web + {nt} Nitter tweets ({src}, {eng})")
            return data
        else:
            err = proc.stderr.strip()[:120] if proc.stderr else "no output"
            print(f"    No data ({err})")
            return None
    except subprocess.TimeoutExpired:
        print("    Timeout (60s)")
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


# ─── Phase 5: Meme Platforms (RugCheck) ───────────────────────────────

def rugcheck_summary(contract_address):
    """Get RugCheck safety summary for a Solana token."""
    print("  [5/6] RugCheck — token safety (Solana)...")
    url = f"https://api.rugcheck.xyz/v1/tokens/{contract_address}/report/summary"
    data = api_get(url)
    if "error" in data:
        print(f"    Not applicable (not Solana or not found)")
        return None
    score = data.get("score_normalised", data.get("score", "?"))
    risks = data.get("risks", [])
    print(f"    Score: {score} | Risks: {len(risks)}")
    return data


# ─── Phase 5: DEXScreener Trending ────────────────────────────────────

def dexscreener_trending():
    """Get DEXScreener trending/boosted tokens."""
    print("  [6/6] DEXScreener — trending tokens...")
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    data = api_get(url)
    if isinstance(data, list):
        print(f"    Found {len(data)} boosted tokens")
        return data[:15]
    return []


# ─── Report Compilation ───────────────────────────────────────────────

def compile_report(query, cg_data, dex_pairs, exchange_results, twitter_data, rugcheck_data, trending):
    """Compile all data into a structured report."""
    symbol = query.upper()
    name = symbol

    if cg_data:
        name = cg_data.get("name", symbol)
        symbol = cg_data.get("symbol", symbol).upper()

    print()
    print(f"{'='*70}")
    print(f"  🔍 CRYPTO RESEARCH REPORT: {name} (${symbol})")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")

    # ── Price & Volume (CoinGecko) ──
    print(f"\n  📊 PRICE & VOLUME (CoinGecko)")
    print(f"  {'─'*45}")
    if cg_data and "current_price" in cg_data:
        print(f"  Price:         {fmt_price(cg_data['current_price'])}")
        print(f"  Market Cap:    {fmt_num(cg_data.get('market_cap'))}")
        print(f"  24h Volume:    {fmt_num(cg_data.get('total_volume'))}")
        print(f"  Rank:          #{cg_data.get('market_cap_rank', 'N/A')}")

        mc = cg_data.get("market_cap")
        vol = cg_data.get("total_volume")
        if mc and vol and mc > 0:
            ratio = vol / mc * 100
            flag = " ⚠️ HIGH" if ratio > 50 else (" 📈 ELEVATED" if ratio > 20 else " ✅")
            print(f"  Vol/MC Ratio:  {ratio:.1f}%{flag}")

        print(f"\n  Changes: 1h: {fmt_pct(cg_data.get('price_change_percentage_1h_in_currency'))}"
              f" | 24h: {fmt_pct(cg_data.get('price_change_percentage_24h_in_currency'))}"
              f" | 7d: {fmt_pct(cg_data.get('price_change_percentage_7d_in_currency'))}"
              f" | 30d: {fmt_pct(cg_data.get('price_change_percentage_30d_in_currency'))}")

        ath = cg_data.get("ath")
        ath_pct = cg_data.get("ath_change_percentage")
        if ath:
            print(f"  ATH:           {fmt_price(ath)} ({fmt_pct(ath_pct)})")
    else:
        print(f"  No CoinGecko data available")

    # ── DEX Pairs ──
    print(f"\n  🔄 DEX PAIRS & LIQUIDITY")
    print(f"  {'─'*45}")
    if dex_pairs:
        total_liq = 0
        total_vol = 0
        for i, p in enumerate(dex_pairs[:5], 1):
            base = p.get("baseToken", {}).get("symbol", "?")
            quote = p.get("quoteToken", {}).get("symbol", "?")
            dex = p.get("dexId", "?")
            chain = p.get("chainId", "?").upper()
            price = p.get("priceUsd")
            vol24 = float(p.get("volume", {}).get("h24", 0) or 0)
            liq = float(p.get("liquidity", {}).get("usd", 0) or 0)
            total_liq += liq
            total_vol += vol24

            ch = p.get("priceChange", {})
            h24_ch = ch.get("h24", 0)

            print(f"  {i}. {base}/{quote} on {dex} ({chain})")
            print(f"     Price: {fmt_price(price)} | 24h: {h24_ch:+.1f}% | "
                  f"Vol: {fmt_num(vol24)} | Liq: {fmt_num(liq)}")

            txns = p.get("txns", {}).get("h24", {})
            buys = txns.get("buys", 0)
            sells = txns.get("sells", 0)
            if buys + sells > 0:
                buy_pct = buys / (buys + sells) * 100
                print(f"     Txns: {buys+sells} (buy {buy_pct:.0f}% / sell {100-buy_pct:.0f}%)")

        print(f"\n  Total DEX Liquidity: {fmt_num(total_liq)}")
        print(f"  Total DEX 24h Vol:   {fmt_num(total_vol)}")
        if total_liq > 0:
            print(f"  Vol/Liq Ratio:       {total_vol/total_liq:.1f}x")
    else:
        print(f"  No DEX pairs found")

    # ── Exchange Prices ──
    print(f"\n  🏦 EXCHANGE PRICES (9 CEX)")
    print(f"  {'─'*45}")
    if exchange_results:
        print(f"  {'Exchange':<22} {'Price':>14} {'24h Chg':>9} {'24h Volume':>12}")
        print(f"  {'─'*22} {'─'*14} {'─'*9} {'─'*12}")
        prices = []
        for r in exchange_results:
            price = r["price"]
            if price > 0:
                prices.append(price)
            chg = f"{r['change_24h']:+.2f}%" if r['change_24h'] else "N/A"
            vol = fmt_num(r['volume']) if r['volume'] else "N/A"
            print(f"  {r['exchange']:<22} {fmt_price(price):>14} {chg:>9} {vol:>12}")

        if len(prices) >= 2:
            min_p = min(prices)
            max_p = max(prices)
            spread = (max_p - min_p) / min_p * 100
            print(f"\n  Price Spread: {spread:.3f}%", end="")
            if spread > 1:
                print(f"  ⚠️  Significant — arbitrage opportunity")
            elif spread > 0.5:
                print(f"  📈 Notable")
            else:
                print(f"  ✅ Normal")
    else:
        print(f"  Not found on any exchange")

    # ── X/Twitter Sentiment ──
    if twitter_data:
        tw_results = twitter_data.get("web_results", [])
        nt_tweets = twitter_data.get("nitter_tweets", [])
        sentiment = twitter_data.get("sentiment")
        source = twitter_data.get("source", "unknown")

        print(f"\n  🐦 X/TWITTER SENTIMENT")
        print(f"  {'─'*45}")
        print(f"  Source: {source} | Web: {len(tw_results)} | Nitter: {len(nt_tweets)}")

        if tw_results:
            print(f"\n  Top X/Twitter mentions:")
            for i, r in enumerate(tw_results[:5], 1):
                title = r.get("title", "")[:70]
                print(f"    [{i}] {title}")

        if nt_tweets:
            print(f"\n  Top Nitter tweets:")
            for i, t in enumerate(nt_tweets[:5], 1):
                name = t.get("display_name", "") or t.get("username", "?")
                text = t.get("text", "")
                if len(text) > 100:
                    text = text[:97] + "..."
                likes = t.get("likes", 0)
                rts = t.get("retweets", 0)
                print(f"    [{i}] {name}: {text}")
                print(f"         ❤️ {likes} 🔁 {rts}")

        if sentiment:
            total = sentiment["positive"] + sentiment["negative"]
            if total > 0:
                pos_pct = sentiment["positive"] / total * 100
                neg_pct = sentiment["negative"] / total * 100
                label = "🟢 BULLISH" if pos_pct > 70 else ("🔴 BEARISH" if neg_pct > 70 else "🟡 MIXED")
                print(f"\n  Sentiment: {label} "
                      f"(+{sentiment['positive']} / -{sentiment['negative']})")
                if sentiment["pos_keywords"]:
                    print(f"  Bullish signals: {', '.join(sentiment['pos_keywords'][:6])}")
                if sentiment["neg_keywords"]:
                    print(f"  Bearish signals: {', '.join(sentiment['neg_keywords'][:6])}")
            else:
                print(f"\n  Sentiment: ⚪ No clear signals")
        else:
            print(f"\n  Sentiment: ⚪ No data available")
    else:
        print(f"\n  🐦 X/TWITTER SENTIMENT")
        print(f"  {'─'*45}")
        print(f"  ⚪ No X/Twitter data (web search may be blocked from server)")
        print(f"  Agent should use web_search to gather X/Twitter data")
        print(f"     web_search(query=\"{symbol} crypto pump site:x.com\")")
        print(f"     web_search(query=\"{symbol} crypto news today\")")

    # ── RugCheck (Solana) ──
    if rugcheck_data:
        print(f"\n  🛡️  RUGCHECK SAFETY (Solana)")
        print(f"  {'─'*45}")
        score = rugcheck_data.get("score_normalised", rugcheck_data.get("score", "?"))
        risks = rugcheck_data.get("risks", [])
        lp_locked = rugcheck_data.get("lpLockedPct", 0)

        if isinstance(score, (int, float)):
            if score <= 5:
                status = "🟢 GOOD"
            elif score <= 20:
                status = "🟡 CAUTION"
            else:
                status = "🔴 DANGEROUS"
        else:
            status = "⚪ Unknown"

        print(f"  Safety Score: {score} {status}")
        print(f"  LP Locked: {lp_locked:.1f}%")

        if risks:
            print(f"  Risks found: {len(risks)}")
            for r in risks[:6]:
                level = r.get("level", "?")
                name = r.get("name", "?")
                desc = r.get("description", "")
                icon = "🔴" if level == "danger" else ("🟡" if level == "warn" else "ℹ️")
                print(f"    {icon} {name}: {desc}")
        else:
            print(f"  No risks detected ✅")

    # ── Trending ──
    if trending:
        print(f"\n  🔥 DEXSCREENER TRENDING (Top Boosted)")
        print(f"  {'─'*45}")
        for i, t in enumerate(trending[:8], 1):
            addr = t.get("tokenAddress", t.get("address", "?"))
            chain = t.get("chainId", "?")
            desc = t.get("description", "")[:50]
            print(f"  {i}. {addr[:16]}... ({chain}) {desc}")

    # ── Risk Assessment ──
    print(f"\n  ⚠️  RISK ASSESSMENT")
    print(f"  {'─'*45}")
    risks = []
    positives = []

    if cg_data:
        vol = cg_data.get("total_volume", 0)
        mc = cg_data.get("market_cap", 0)
        if vol and mc and mc > 0:
            if vol / mc > 50:
                risks.append("Volume/MarketCap > 50% — possible wash trading")
            elif vol / mc > 20:
                risks.append("Elevated Vol/MC ratio — verify volume authenticity")
            else:
                positives.append("Normal Vol/MC ratio")

        ch24 = cg_data.get("price_change_percentage_24h", 0)
        if ch24 and ch24 > 100:
            risks.append(f"24h change {ch24:+.0f}% — extreme volatility, verify legitimacy")
        elif ch24 and ch24 > 30:
            risks.append(f"24h change {ch24:+.0f}% — significant move, check for catalyst")

        ath_pct = cg_data.get("ath_change_percentage")
        if ath_pct and ath_pct < -95:
            risks.append(f"Down {abs(ath_pct):.0f}% from ATH — deep drawdown territory")

    if dex_pairs:
        top_liq = float(dex_pairs[0].get("liquidity", {}).get("usd", 0) or 0)
        if top_liq < 10000:
            risks.append("DEX liquidity < $10K — extremely thin, high slippage risk")
        elif top_liq < 100000:
            risks.append("DEX liquidity < $100K — thin liquidity")

        created = dex_pairs[0].get("pairCreatedAt")
        if created:
            age_days = (datetime.now().timestamp() * 1000 - created) / 86400000
            if age_days < 1:
                risks.append("Token pair < 24h old — very new, high risk")
            elif age_days < 7:
                risks.append("Token pair < 7 days old — new token")
            elif age_days > 365:
                positives.append(f"Token pair is {age_days:.0f} days old — established")

        txns = dex_pairs[0].get("txns", {}).get("h24", {})
        buys = txns.get("buys", 0)
        sells = txns.get("sells", 0)
        if buys + sells > 0:
            buy_pct = buys / (buys + sells) * 100
            if buy_pct > 80:
                risks.append(f"Buy pressure {buy_pct:.0f}% — could be coordinated buying")
            elif buy_pct < 20:
                risks.append(f"Sell pressure {100-buy_pct:.0f}% — heavy selling")

    if not exchange_results:
        risks.append("Not listed on any major CEX — lower credibility")
    else:
        if len(exchange_results) >= 3:
            positives.append(f"Listed on {len(exchange_results)} exchanges")
        if any(r["exchange"] == "Binance" for r in exchange_results):
            positives.append("Listed on Binance")
        if any(r["exchange"] == "Hyperliquid (perps)" for r in exchange_results):
            positives.append("Has Hyperliquid perps market")

    if twitter_data:
        sentiment = twitter_data.get("sentiment")
        if sentiment:
            total = sentiment["positive"] + sentiment["negative"]
            if total > 0:
                pos_pct = sentiment["positive"] / total * 100
                if pos_pct > 70:
                    positives.append(f"X/Twitter sentiment BULLISH ({pos_pct:.0f}% positive)")
                elif pos_pct < 30:
                    risks.append(f"X/Twitter sentiment BEARISH ({100-pos_pct:.0f}% negative)")
            neg_kw = sentiment.get("neg_keywords", [])
            if "scam" in neg_kw or "rug" in neg_kw or "rugpull" in neg_kw:
                risks.append("X/Twitter mentions scam/rug — verify legitimacy")
            if "shill" in neg_kw or "bot" in neg_kw:
                risks.append("X/Twitter reports coordinated shilling/bot activity")

    if rugcheck_data:
        rc_score = rugcheck_data.get("score_normalised", 0)
        if isinstance(rc_score, (int, float)):
            if rc_score > 20:
                risks.append(f"RugCheck score {rc_score} — high risk token")
            elif rc_score <= 5:
                positives.append(f"RugCheck score {rc_score} — safe")

    if risks:
        for r in risks:
            print(f"  🔴 {r}")
    if positives:
        for p in positives:
            print(f"  🟢 {p}")
    if not risks and not positives:
        print(f"  ⚪ Insufficient data for assessment")

    # ── Summary ──
    print(f"\n  💡 SUMMARY")
    print(f"  {'─'*45}")
    risk_score = len(risks)
    if risk_score == 0:
        print(f"  Risk level: LOW — No major red flags detected")
    elif risk_score <= 2:
        print(f"  Risk level: MEDIUM — Some concerns, do additional research")
    else:
        print(f"  Risk level: HIGH — Multiple red flags detected")

    sources = ["CoinGecko", "DEXScreener"]
    if exchange_results:
        ex_names = [r["exchange"] for r in exchange_results]
        sources.extend(ex_names)
    if rugcheck_data:
        sources.append("RugCheck")
    print(f"\n  Data sources: {', '.join(sources)}")

    print(f"\n  🔗 For deeper X/Twitter analysis, use web_search:")
    print(f"     web_search(query=\"{symbol} crypto pump site:x.com\")")
    print(f"     web_search(query=\"{symbol} crypto news today\")")
    print(f"     Save results to JSON, then: python3 twitter_search.py \"{symbol}\" --input results.json")

    print(f"\n  🔗 For meme platforms, use web_search:")
    print(f"     web_search(query=\"{symbol} site:gmgn.ai\")")
    print(f"     web_search(query=\"{symbol} site:dextools.io\")")
    print(f"     web_search(query=\"{symbol} site:pump.fun\")")
    print(f"     web_search(query=\"{symbol} site:birdeye.so\")")

    print(f"\n  ⚠️  This is NOT financial advice. Always DYOR.")
    print(f"{'='*70}")


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    chain_filter = None
    twitter_input = None
    if "--chain" in args:
        idx = args.index("--chain")
        chain_filter = args[idx + 1]
        args = args[:idx] + args[idx+2:]
    if "--twitter-input" in args:
        idx = args.index("--twitter-input")
        twitter_input = args[idx + 1]
        args = args[:idx] + args[idx+2:]

    query = " ".join(args)
    symbol_guess = query.upper().replace(" ", "")

    print(f"🔍 Starting crypto research for: {query}")
    print(f"   Chain filter: {chain_filter or 'all'}")
    if twitter_input:
        print(f"   Twitter input: {twitter_input}")
    print()

    # Phase 1: CoinGecko
    cg_data = coingecko_search(query)
    if cg_data and "symbol" in cg_data:
        symbol_guess = cg_data["symbol"].upper()

    # Phase 2: DEXScreener
    dex_pairs = dexscreener_search(query, chain_filter)

    # Phase 3: All Exchange Prices
    exchange_results = query_all_exchanges(symbol_guess)

    # Phase 4: X/Twitter Sentiment
    tw_query = f"{symbol_guess} crypto"
    tw_data = twitter_search(tw_query, twitter_input)

    # Phase 5: RugCheck (Solana tokens)
    rugcheck_data = None
    if dex_pairs:
        sol_pairs = [p for p in dex_pairs if p.get("chainId") == "solana"]
        if sol_pairs:
            contract = sol_pairs[0].get("baseToken", {}).get("address", "")
            if contract:
                rugcheck_data = rugcheck_summary(contract)

    # Phase 6: DEXScreener Trending
    trending = dexscreener_trending()

    # Compile report
    compile_report(query, cg_data, dex_pairs, exchange_results, tw_data, rugcheck_data, trending)


if __name__ == "__main__":
    main()
