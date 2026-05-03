#!/usr/bin/env python3
"""Query meme token platforms for safety, DEX data, and social info.

Covers: RugCheck, DEXScreener, CoinGecko, DexScreener trending.
For GMGN/Pump.fun/DexTools — use web_search (APIs behind Cloudflare).

Usage:
    python meme_platforms.py "PEPE"
    python meme_platforms.py DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
    python meme_platforms.py "WIF" --chain solana
"""
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import time

HEADERS = {"User-Agent": "CryptoResearch/1.0", "Accept": "application/json"}
TIMEOUT = 12


def api_get(url, timeout=TIMEOUT, extra_headers=None):
    h = {**HEADERS, **(extra_headers or {})}
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def fmt_price(n):
    if n is None or n == 0:
        return "N/A"
    n = float(n)
    if n < 0.000001:
        return f"${n:.10f}"
    if n < 0.001:
        return f"${n:.8f}"
    if n < 1:
        return f"${n:.6f}"
    return f"${n:,.4f}"


def fmt_num(n):
    if n is None or n == 0:
        return "N/A"
    n = float(n)
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    if n >= 1e3:
        return f"${n/1e3:.1f}K"
    return f"${n:.0f}"


# ─── RugCheck (Solana token safety) ───────────────────────────────────

def rugcheck_summary(contract_address):
    """Get RugCheck safety summary for a Solana token."""
    print("  [RugCheck] Token safety report...")
    url = f"https://api.rugcheck.xyz/v1/tokens/{contract_address}/report/summary"
    data = api_get(url)
    if "error" in data:
        print(f"    Not found or error")
        return None
    return data


def rugcheck_full(contract_address):
    """Get full RugCheck report."""
    url = f"https://api.rugcheck.xyz/v1/tokens/{contract_address}/report"
    data = api_get(url)
    if "error" in data:
        return None
    return data


# ─── DEXScreener (meme token DEX data) ───────────────────────────────

def dexscreener_token(contract_address):
    """Get DEXScreener data for a specific token contract."""
    print("  [DEXScreener] Token pairs & liquidity...")
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    data = api_get(url)
    pairs = data.get("pairs", [])
    if not pairs:
        # Try as search query
        url2 = f"https://api.dexscreener.com/latest/dex/search?q={urllib.parse.quote(contract_address)}"
        data2 = api_get(url2)
        pairs = data2.get("pairs", [])
    pairs.sort(key=lambda p: float(p.get("volume", {}).get("h24", 0) or 0), reverse=True)
    print(f"    Found {len(pairs)} pairs")
    return pairs[:10]


def dexscreener_search(query, chain_filter=None):
    """Search DEXScreener for token by name/symbol."""
    print("  [DEXScreener] Searching for token...")
    url = f"https://api.dexscreener.com/latest/dex/search?q={urllib.parse.quote(query)}"
    data = api_get(url)
    pairs = data.get("pairs", [])
    if chain_filter:
        pairs = [p for p in pairs if p.get("chainId", "").lower() == chain_filter.lower()]
    pairs.sort(key=lambda p: float(p.get("volume", {}).get("h24", 0) or 0), reverse=True)
    print(f"    Found {len(pairs)} pairs")
    return pairs[:10]


def dexscreener_trending():
    """Get DEXScreener trending tokens (boosted)."""
    print("  [DEXScreener] Trending/boosted tokens...")
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    data = api_get(url)
    if isinstance(data, list):
        print(f"    Found {len(data)} boosted tokens")
        return data[:20]
    return []


# ─── CoinGecko (aggregated data) ─────────────────────────────────────

def coingecko_search(query):
    """Search CoinGecko for token."""
    print("  [CoinGecko] Token data...")
    url = f"https://api.coingecko.com/api/v3/search?query={urllib.parse.quote(query)}"
    data = api_get(url)
    coins = data.get("coins", [])
    if not coins:
        return None
    coin = coins[0]
    coin_id = coin["id"]
    time.sleep(1.5)  # Rate limit
    url2 = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}&sparkline=false"
    market = api_get(url2)
    if market and isinstance(market, list) and market:
        return market[0]
    return {"name": coin["name"], "symbol": coin["symbol"], "id": coin_id}


# ─── Report ───────────────────────────────────────────────────────────

def print_rugcheck(rc_data):
    if not rc_data:
        print("  No RugCheck data available")
        return

    score = rc_data.get("score_normalised", rc_data.get("score", "?"))
    risks = rc_data.get("risks", [])
    lp_locked = rc_data.get("lpLockedPct", 0)

    # Score interpretation: lower = safer on RugCheck
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
        for r in risks[:8]:
            level = r.get("level", "?")
            name = r.get("name", "?")
            desc = r.get("description", "")
            icon = "🔴" if level == "danger" else ("🟡" if level == "warn" else "ℹ️")
            print(f"    {icon} {name}: {desc}")
    else:
        print(f"  No risks detected ✅")


def print_dex_pairs(pairs, max_show=7):
    if not pairs:
        print("  No DEX pairs found")
        return

    total_liq = 0
    total_vol = 0
    for i, p in enumerate(pairs[:max_show], 1):
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
        h6_ch = ch.get("h6", 0)
        h1_ch = ch.get("h1", 0)

        created = p.get("pairCreatedAt")
        age = ""
        if created:
            age_days = (time.time() * 1000 - created) / 86400000
            if age_days < 1:
                age = f" [NEW: {age_days*24:.0f}h]"
            elif age_days < 30:
                age = f" [{age_days:.0f}d old]"
            else:
                age = f" [{age_days/30:.0f}mo old]"

        print(f"  {i}. {base}/{quote} on {dex} ({chain}){age}")
        print(f"     Price: {fmt_price(price)} | 1h: {h1_ch:+.1f}% | 6h: {h6_ch:+.1f}% | 24h: {h24_ch:+.1f}%")
        print(f"     Vol: {fmt_num(vol24)} | Liq: {fmt_num(liq)}")

        txns = p.get("txns", {}).get("h24", {})
        buys = txns.get("buys", 0)
        sells = txns.get("sells", 0)
        if buys + sells > 0:
            buy_pct = buys / (buys + sells) * 100
            print(f"     Txns: {buys + sells} (buy {buy_pct:.0f}% / sell {100 - buy_pct:.0f}%)")

        # Social links
        info = p.get("info", {})
        websites = info.get("websites", [])
        socials = info.get("socials", [])
        if websites or socials:
            links = []
            for w in websites[:2]:
                links.append(w.get("url", ""))
            for s in socials[:3]:
                label = s.get("type", "")
                handle = s.get("url", "")
                if label and handle:
                    links.append(f"{label}: {handle}")
            if links:
                print(f"     Links: {' | '.join(links[:4])}")

    print(f"\n  Total DEX Liquidity: {fmt_num(total_liq)}")
    print(f"  Total DEX 24h Vol:   {fmt_num(total_vol)}")
    if total_liq > 0:
        ratio = total_vol / total_liq
        flag = " ⚠️ HIGH" if ratio > 10 else (" 📈 ELEVATED" if ratio > 5 else " ✅")
        print(f"  Vol/Liq Ratio:       {ratio:.1f}x{flag}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    chain_filter = None
    if "--chain" in args:
        idx = args.index("--chain")
        chain_filter = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    query = " ".join(args)
    is_contract = len(query) > 20 and any(c in query for c in "0123456789")

    print(f"🔍 Meme token research: {query}")
    if chain_filter:
        print(f"   Chain filter: {chain_filter}")
    print()

    # ── DEXScreener ──
    if is_contract:
        pairs = dexscreener_token(query)
    else:
        pairs = dexscreener_search(query, chain_filter)

    # ── RugCheck (Solana only) ──
    rc_data = None
    if pairs:
        # Try RugCheck for the top pair's base token on Solana
        sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
        if sol_pairs:
            contract = sol_pairs[0].get("baseToken", {}).get("address", "")
            if contract:
                rc_data = rugcheck_summary(contract)
        elif is_contract and chain_filter == "solana":
            rc_data = rugcheck_summary(query)

    # ── CoinGecko ──
    cg_data = None
    if not is_contract:
        cg_data = coingecko_search(query)

    # ── DEXScreener Trending ──
    trending = dexscreener_trending()

    # ── Print Report ──
    print(f"\n{'='*65}")
    print(f"  🐸 MEME TOKEN REPORT: {query.upper()}")
    print(f"{'='*65}")

    # CoinGecko data
    if cg_data and "current_price" in cg_data:
        print(f"\n  📊 MARKET DATA (CoinGecko)")
        print(f"  {'─'*40}")
        print(f"  Name:        {cg_data.get('name', '?')} ({cg_data.get('symbol', '?').upper()})")
        print(f"  Price:       {fmt_price(cg_data.get('current_price'))}")
        print(f"  Market Cap:  {fmt_num(cg_data.get('market_cap'))}")
        print(f"  24h Vol:     {fmt_num(cg_data.get('total_volume'))}")
        print(f"  Rank:        #{cg_data.get('market_cap_rank', 'N/A')}")
        print(f"  24h Change:  {cg_data.get('price_change_percentage_24h', 0):+.2f}%")

    # DEX pairs
    print(f"\n  🔄 DEX PAIRS")
    print(f"  {'─'*40}")
    print_dex_pairs(pairs)

    # RugCheck
    if rc_data:
        print(f"\n  🛡️  RUGCHECK SAFETY (Solana)")
        print(f"  {'─'*40}")
        print_rugcheck(rc_data)

    # Trending
    if trending:
        print(f"\n  🔥 DEXSCREENER TRENDING (Top Boosted)")
        print(f"  {'─'*40}")
        for i, t in enumerate(trending[:10], 1):
            addr = t.get("tokenAddress", t.get("address", "?"))
            chain = t.get("chainId", "?")
            desc = t.get("description", "")[:60]
            print(f"  {i}. {addr[:12]}... ({chain}) {desc}")

    # Web search instructions
    print(f"\n  🌐 WEB SEARCH NEEDED (APIs behind Cloudflare)")
    print(f"  {'─'*40}")
    print(f"  For deeper analysis, use web_search / web_extract:")
    print(f"  • GMGN:       web_search(query=\"{query.upper()} site:gmgn.ai\")")
    print(f"  • DexTools:    web_search(query=\"{query.upper()} site:dextools.io\")")
    print(f"  • Pump.fun:    web_search(query=\"{query.upper()} site:pump.fun\")")
    print(f"  • Birdeye:     web_search(query=\"{query.upper()} site:birdeye.so\")")
    print(f"  • X/Twitter:   web_search(query=\"{query.upper()} crypto site:x.com\")")

    print(f"\n{'='*65}")


if __name__ == "__main__":
    main()
