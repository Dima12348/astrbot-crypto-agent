#!/usr/bin/env python3
"""Search CoinGecko for crypto token data (price, volume, market cap).

Free API — no key needed. ~30 req/min rate limit.

Usage:
    python coingecko_search.py "PEPE"
    python coingecko_search.py "BTC"
    python coingecko_search.py "VIRTUAL" --top 3
"""
import sys
import json
import urllib.request
import urllib.error
import time

BASE = "https://api.coingecko.com/api/v3"
HEADERS = {"User-Agent": "HermesCryptoResearch/1.0", "Accept": "application/json"}


def api_get(path, params=None):
    """Make a GET request to CoinGecko API."""
    url = BASE + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("Rate limited, waiting 30s...")
            time.sleep(30)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        raise


def search_token(query):
    """Search for tokens by name/symbol."""
    data = api_get("/search", {"query": query})
    coins = data.get("coins", [])
    if not coins:
        print(f"No results for '{query}'")
        return []
    return coins


def get_market_data(coin_ids):
    """Get detailed market data for a list of coin IDs."""
    ids_str = ",".join(coin_ids)
    return api_get("/coins/markets", {
        "vs_currency": "usd",
        "ids": ids_str,
        "order": "market_cap_desc",
        "per_page": str(len(coin_ids)),
        "page": "1",
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d,30d"
    })


def format_number(n):
    """Format large numbers with suffixes."""
    if n is None:
        return "N/A"
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    if n >= 1e3:
        return f"${n/1e3:.2f}K"
    return f"${n:.2f}"


def format_pct(n):
    """Format percentage."""
    if n is None:
        return "N/A"
    sign = "+" if n >= 0 else ""
    return f"{sign}{n:.2f}%"


def print_token_data(token):
    """Print formatted token data."""
    name = token.get("name", "Unknown")
    symbol = token.get("symbol", "?").upper()
    rank = token.get("market_cap_rank", "N/A")

    print(f"{'='*60}")
    print(f"  {name} ({symbol}) — Rank #{rank}")
    print(f"{'='*60}")

    price = token.get("current_price")
    if price is not None:
        if price < 0.001:
            price_str = f"${price:.8f}"
        elif price < 1:
            price_str = f"${price:.6f}"
        else:
            price_str = f"${price:,.2f}"
    else:
        price_str = "N/A"
    print(f"  Price:          {price_str}")

    ath = token.get("ath")
    ath_change = token.get("ath_change_percentage")
    if ath is not None:
        print(f"  ATH:            ${ath:,.6f} ({format_pct(ath_change)})")

    print(f"  Market Cap:     {format_number(token.get('market_cap'))}")
    print(f"  24h Volume:     {format_number(token.get('total_volume'))}")

    mc = token.get("market_cap")
    vol = token.get("total_volume")
    if mc and vol and mc > 0:
        ratio = vol / mc * 100
        print(f"  Vol/MC Ratio:   {ratio:.1f}%", end="")
        if ratio > 50:
            print(" ⚠️  HIGH (possible wash trading)")
        elif ratio > 20:
            print(" 📈 ELEVATED")
        else:
            print(" ✅ NORMAL")

    print(f"\n  Price Changes:")
    print(f"    1h:   {format_pct(token.get('price_change_percentage_1h_in_currency'))}")
    print(f"    24h:  {format_pct(token.get('price_change_percentage_24h_in_currency'))}")
    print(f"    7d:   {format_pct(token.get('price_change_percentage_7d_in_currency'))}")
    print(f"    30d:  {format_pct(token.get('price_change_percentage_30d_in_currency'))}")

    supply = token.get("circulating_supply")
    total = token.get("total_supply")
    max_s = token.get("max_supply")
    if supply:
        print(f"\n  Supply:")
        print(f"    Circulating: {format_number(supply).replace('$','')}")
        if total:
            print(f"    Total:       {format_number(total).replace('$','')}")
        if max_s:
            print(f"    Max:         {format_number(max_s).replace('$','')}")
            if supply and max_s:
                pct = supply / max_s * 100
                print(f"    In circulation: {pct:.1f}%")

    # Red flags
    flags = []
    if vol and mc and vol / mc > 50:
        flags.append("Volume/MarketCap ratio > 50% — possible wash trading")
    if ath_change and ath_change < -90:
        flags.append(f"Down {abs(ath_change):.0f}% from ATH — deep drawdown")
    if token.get("price_change_percentage_24h_in_currency", 0) > 100:
        flags.append("24h change > 100% — extreme volatility, verify legitimacy")

    if flags:
        print(f"\n  ⚠️  Red Flags:")
        for f in flags:
            print(f"    • {f}")

    print()


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    top = 3
    if "--top" in args:
        idx = args.index("--top")
        top = int(args[idx + 1])
        args = args[:idx] + args[idx+2:]

    query = " ".join(args)
    print(f"Searching CoinGecko for: {query}\n")

    coins = search_token(query)
    if not coins:
        sys.exit(1)

    # Get top N results
    selected = coins[:top]
    print(f"Found {len(coins)} results, showing top {len(selected)}:\n")

    for i, coin in enumerate(selected):
        print(f"  {i+1}. {coin['name']} ({coin['symbol'].upper()}) — "
              f"Rank #{coin.get('market_cap_rank', '?')} — ID: {coin['id']}")

    print()

    # Fetch detailed market data
    ids = [c["id"] for c in selected]
    print("Fetching market data...\n")
    time.sleep(1)  # Rate limit courtesy

    try:
        market_data = get_market_data(ids)
        for token in market_data:
            print_token_data(token)
    except Exception as e:
        print(f"Error fetching market data: {e}")
        # Fallback: print what we have from search
        for coin in selected:
            print(f"  {coin['name']} ({coin['symbol'].upper()})")
            print(f"    Market Cap Rank: #{coin.get('market_cap_rank', '?')}")
            print(f"    ID: {coin['id']}")
            print()


if __name__ == "__main__":
    main()
