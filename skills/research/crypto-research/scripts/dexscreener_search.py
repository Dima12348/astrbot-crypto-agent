#!/usr/bin/env python3
"""Search DEXScreener for DEX trading pairs, liquidity, and transaction data.

Free API — no key needed, no rate limits (reasonable use).

Usage:
    python dexscreener_search.py "PEPE"
    python dexscreener_search.py "0xdAC17F958D2ee523a2206206994597C13D831ec7"  # by contract
    python dexscreener_search.py "VIRTUAL" --chain base
"""
import sys
import json
import urllib.request
import urllib.error

BASE = "https://api.dexscreener.com"
HEADERS = {"User-Agent": "HermesCryptoResearch/1.0", "Accept": "application/json"}


def api_get(path):
    """Make a GET request to DEXScreener API."""
    url = BASE + path
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def search_pairs(query):
    """Search for trading pairs by symbol, name, or contract address."""
    return api_get(f"/latest/dex/search?q={urllib.request.quote(query)}")


def get_pairs_by_token(address):
    """Get pairs by token contract address."""
    return api_get(f"/tokens/v1/token-profiles/latest/{address}")


def format_number(n):
    """Format large numbers."""
    if n is None:
        return "N/A"
    n = float(n)
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    if n >= 1e3:
        return f"${n/1e3:.2f}K"
    return f"${n:.2f}"


def format_price(n):
    """Format price with appropriate decimal places."""
    if n is None:
        return "N/A"
    n = float(n)
    if n < 0.000001:
        return f"${n:.10f}"
    if n < 0.001:
        return f"${n:.8f}"
    if n < 1:
        return f"${n:.6f}"
    return f"${n:,.2f}"


def print_pair(pair, index=None):
    """Print formatted pair data."""
    dex = pair.get("dexId", "unknown")
    chain = pair.get("chainId", "unknown").upper()
    base = pair.get("baseToken", {})
    quote = pair.get("quoteToken", {})
    base_sym = base.get("symbol", "?")
    quote_sym = quote.get("symbol", "?")
    pair_addr = pair.get("pairAddress", "")

    prefix = f"  [{index}]" if index else ""
    print(f"{prefix} {base_sym}/{quote_sym} on {dex} ({chain})")
    print(f"       Pair: {pair_addr[:20]}...")

    price = pair.get("priceUsd")
    print(f"       Price: {format_price(price)}")

    # Price changes
    changes = pair.get("priceChange", {})
    if changes:
        h1 = changes.get("h1", 0)
        h6 = changes.get("h6", 0)
        h24 = changes.get("h24", 0)
        print(f"       Changes: 1h: {h1:+.1f}% | 6h: {h6:+.1f}% | 24h: {h24:+.1f}%")

    # Volume
    volume = pair.get("volume", {})
    if volume:
        vol_h24 = volume.get("h24", 0)
        vol_h6 = volume.get("h6", 0)
        vol_h1 = volume.get("h1", 0)
        print(f"       Volume: 1h: {format_number(vol_h1)} | 6h: {format_number(vol_h6)} | 24h: {format_number(vol_h24)}")

    # Liquidity
    liquidity = pair.get("liquidity", {})
    if liquidity:
        liq_usd = liquidity.get("usd", 0)
        liq_base = liquidity.get("base", 0)
        liq_quote = liquidity.get("quote", 0)
        liq_str = format_number(liq_usd) if liq_usd else "N/A"
        print(f"       Liquidity: {liq_str}", end="")
        if liq_usd and liq_usd < 10000:
            print(" ⚠️  VERY LOW", end="")
        elif liq_usd and liq_usd < 100000:
            print(" 📉 LOW", end="")
        else:
            print(" ✅", end="")
        print()

    # Transactions
    txns = pair.get("txns", {})
    if txns:
        h24 = txns.get("h24", {})
        buys = h24.get("buys", 0)
        sells = h24.get("sells", 0)
        total = buys + sells
        if total > 0:
            buy_pct = buys / total * 100
            print(f"       Txns 24h: {total} (buys: {buys} [{buy_pct:.0f}%] | sells: {sells})")
            if buy_pct > 80:
                print(f"       📈 Strong buy pressure")
            elif buy_pct < 20:
                print(f"       📉 Heavy selling")

    # FDV & Market Cap
    fdv = pair.get("fdv")
    mc = pair.get("marketCap")
    if fdv:
        print(f"       FDV: {format_number(fdv)}")
    if mc:
        print(f"       Market Cap: {format_number(mc)}")

    # Created at
    created = pair.get("pairCreatedAt")
    if created:
        from datetime import datetime
        dt = datetime.fromtimestamp(created / 1000)
        age_days = (datetime.now() - dt).days
        print(f"       Created: {dt.strftime('%Y-%m-%d')} ({age_days}d ago)", end="")
        if age_days < 1:
            print(" ⚠️  NEW (< 24h)", end="")
        elif age_days < 7:
            print(" 🆕 NEW (< 7d)", end="")
        print()

    # Info links
    info = pair.get("info", {})
    websites = info.get("websites", [])
    socials = info.get("socials", [])
    if websites:
        print(f"       Website: {websites[0].get('url', 'N/A')}")
    if socials:
        social_links = [f"{s['type']}: {s.get('url', '')}" for s in socials[:3]]
        print(f"       Socials: {' | '.join(social_links)}")

    print()


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    chain_filter = None
    if "--chain" in args:
        idx = args.index("--chain")
        chain_filter = args[idx + 1].lower()
        args = args[:idx] + args[idx+2:]

    query = " ".join(args)
    print(f"Searching DEXScreener for: {query}")
    if chain_filter:
        print(f"Chain filter: {chain_filter}")
    print()

    try:
        data = search_pairs(query)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    pairs = data.get("pairs", [])
    if not pairs:
        print("No pairs found.")
        sys.exit(0)

    # Apply chain filter
    if chain_filter:
        pairs = [p for p in pairs if p.get("chainId", "").lower() == chain_filter]

    if not pairs:
        print(f"No pairs found on chain '{chain_filter}'.")
        sys.exit(0)

    # Sort by volume (descending)
    pairs.sort(key=lambda p: float(p.get("volume", {}).get("h24", 0) or 0), reverse=True)

    # Show top 10
    show = min(10, len(pairs))
    print(f"Found {len(pairs)} pairs, showing top {show} by 24h volume:\n")

    for i, pair in enumerate(pairs[:show], 1):
        print_pair(pair, index=i)

    # Summary
    total_liq = sum(float(p.get("liquidity", {}).get("usd", 0) or 0) for p in pairs)
    total_vol = sum(float(p.get("volume", {}).get("h24", 0) or 0) for p in pairs)
    chains = set(p.get("chainId", "?") for p in pairs)
    dexes = set(p.get("dexId", "?") for p in pairs)

    print(f"{'='*50}")
    print(f"  Summary:")
    print(f"    Total pairs:      {len(pairs)}")
    print(f"    Chains:           {', '.join(chains)}")
    print(f"    DEXes:            {', '.join(dexes)}")
    print(f"    Total Liquidity:  {format_number(total_liq)}")
    print(f"    Total 24h Volume: {format_number(total_vol)}")
    if total_liq > 0:
        print(f"    Vol/Liq Ratio:    {total_vol/total_liq:.1f}x")
    print()


if __name__ == "__main__":
    main()
