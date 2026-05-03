#!/usr/bin/env python3
"""Full crypto research pipeline — gathers data from multiple sources and compiles a report.

Runs all research phases:
  1. Price & Volume (CoinGecko)
  2. DEX Pairs & Liquidity (DEXScreener)
  3. Exchange data (Binance, Hyperliquid)
  4. Compiles a structured report

Usage:
    python full_research.py "PEPE"
    python full_research.py "VIRTUAL" --chain base
    python full_research.py "0xdAC17F958D2ee523a2206206994597C13D831ec7"  # by contract
"""
import sys
import json
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
    print("  [1/3] CoinGecko — price & market data...")
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
    print("  [2/3] DEXScreener — DEX pairs & liquidity...")
    url = f"https://api.dexscreener.com/latest/dex/search?q={urllib.parse.quote(query)}"
    data = api_get(url)
    pairs = data.get("pairs", [])
    if chain_filter:
        pairs = [p for p in pairs if p.get("chainId", "").lower() == chain_filter.lower()]
    pairs.sort(key=lambda p: float(p.get("volume", {}).get("h24", 0) or 0), reverse=True)
    print(f"    Found {len(pairs)} pairs")
    return pairs[:5]


# ─── Phase 3: Exchange Data ───────────────────────────────────────────

def binance_ticker(symbol):
    """Get Binance 24h ticker."""
    print("  [3/3] Binance — CEX data...")
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol.upper()}USDT"
    data = api_get(url)
    if "error" in data or data.get("code"):
        print(f"    Not found on Binance spot")
        return None
    print(f"    Found on Binance: {symbol}/USDT")
    return data


def hyperliquid_meta():
    """Get Hyperliquid meta (all markets)."""
    url = "https://api.hyperliquid.xyz/info"
    req = urllib.request.Request(url, headers={**HEADERS, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15, data=json.dumps({"type": "meta"}).encode()) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def hyperliquid_search(symbol):
    """Search for a symbol on Hyperliquid."""
    print("    Checking Hyperliquid perps...")
    meta = hyperliquid_meta()
    if not meta:
        return None
    for asset in meta.get("universe", []):
        if asset.get("name", "").upper() == symbol.upper():
            print(f"    Found on Hyperliquid: {symbol}-PERP")
            return asset
    print(f"    Not on Hyperliquid")
    return None


# ─── Report Compilation ───────────────────────────────────────────────

def compile_report(query, cg_data, dex_pairs, binance_data, hl_data):
    """Compile all data into a structured report."""
    symbol = query.upper()
    name = symbol

    if cg_data:
        name = cg_data.get("name", symbol)
        symbol = cg_data.get("symbol", symbol).upper()

    print()
    print(f"{'='*65}")
    print(f"  🔍 CRYPTO RESEARCH REPORT: {name} (${symbol})")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*65}")

    # ── Price & Volume ──
    print(f"\n  📊 PRICE & VOLUME")
    print(f"  {'─'*40}")
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
    print(f"  {'─'*40}")
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

    # ── CEX Data ──
    print(f"\n  🏦 CEX DATA")
    print(f"  {'─'*40}")
    if binance_data:
        print(f"  Binance {symbol}/USDT:")
        print(f"    Price:     {fmt_price(float(binance_data.get('lastPrice', 0)))}")
        print(f"    24h Vol:   {fmt_num(float(binance_data.get('quoteVolume', 0)))}")
        print(f"    24h High:  {fmt_price(float(binance_data.get('highPrice', 0)))}")
        print(f"    24h Low:   {fmt_price(float(binance_data.get('lowPrice', 0)))}")
        print(f"    Trades:    {binance_data.get('count', 'N/A')}")
    else:
        print(f"  Not on Binance spot")

    if hl_data:
        print(f"\n  Hyperliquid {symbol}-PERP:")
        print(f"    Available: ✅")
        sz_dec = hl_data.get("szDecimals", "?")
        print(f"    Size decimals: {sz_dec}")
    else:
        print(f"  Not on Hyperliquid perps")

    # ── Risk Assessment ──
    print(f"\n  ⚠️  RISK ASSESSMENT")
    print(f"  {'─'*40}")
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

        # Check pair age
        created = dex_pairs[0].get("pairCreatedAt")
        if created:
            age_days = (datetime.now() - datetime.fromtimestamp(created / 1000)).days
            if age_days < 1:
                risks.append("Token pair < 24h old — very new, high risk")
            elif age_days < 7:
                risks.append("Token pair < 7 days old — new token")
            elif age_days > 365:
                positives.append(f"Token pair is {age_days} days old — established")

        # Check buy/sell ratio
        txns = dex_pairs[0].get("txns", {}).get("h24", {})
        buys = txns.get("buys", 0)
        sells = txns.get("sells", 0)
        if buys + sells > 0:
            buy_pct = buys / (buys + sells) * 100
            if buy_pct > 80:
                risks.append(f"Buy pressure {buy_pct:.0f}% — could be coordinated buying")
            elif buy_pct < 20:
                risks.append(f"Sell pressure {100-buy_pct:.0f}% — heavy selling")

    if not binance_data and not hl_data:
        risks.append("Not listed on major CEX — lower credibility")
    else:
        if binance_data:
            positives.append("Listed on Binance")
        if hl_data:
            positives.append("Listed on Hyperliquid")

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
    print(f"  {'─'*40}")
    risk_score = len(risks)
    if risk_score == 0:
        print(f"  Risk level: LOW — No major red flags detected")
    elif risk_score <= 2:
        print(f"  Risk level: MEDIUM — Some concerns, do additional research")
    else:
        print(f"  Risk level: HIGH — Multiple red flags detected")

    print(f"\n  Data sources: CoinGecko, DEXScreener", end="")
    if binance_data:
        print(", Binance", end="")
    if hl_data:
        print(", Hyperliquid", end="")
    print()
    print(f"\n  ⚠️  This is NOT financial advice. Always DYOR.")
    print(f"{'='*65}")


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    chain_filter = None
    if "--chain" in args:
        idx = args.index("--chain")
        chain_filter = args[idx + 1]
        args = args[:idx] + args[idx+2:]

    query = " ".join(args)
    symbol_guess = query.upper().replace(" ", "")

    print(f"🔍 Starting crypto research for: {query}")
    print(f"   Chain filter: {chain_filter or 'all'}")
    print()

    # Phase 1
    cg_data = coingecko_search(query)
    if cg_data and "symbol" in cg_data:
        symbol_guess = cg_data["symbol"].upper()

    # Phase 2
    dex_pairs = dexscreener_search(query, chain_filter)

    # Phase 3
    binance_data = binance_ticker(symbol_guess)
    hl_data = hyperliquid_search(symbol_guess)

    # Compile
    compile_report(query, cg_data, dex_pairs, binance_data, hl_data)


if __name__ == "__main__":
    main()
