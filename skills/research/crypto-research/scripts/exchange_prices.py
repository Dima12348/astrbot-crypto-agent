#!/usr/bin/env python3
"""Query all major crypto exchanges for a token and show per-exchange prices.

Usage:
    python exchange_prices.py "BTC"
    python exchange_prices.py "PEPE"
    python exchange_prices.py "VIRTUAL"
"""
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import time

HEADERS = {"User-Agent": "CryptoResearch/1.0", "Accept": "application/json"}
TIMEOUT = 10


def api_get(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


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


def fmt_vol(n):
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


# ─── Exchange Query Functions ─────────────────────────────────────────

def query_binance(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
    data = api_get(url)
    if data and "lastPrice" in data:
        return {
            "exchange": "Binance",
            "price": float(data["lastPrice"]),
            "volume": float(data.get("quoteVolume", 0)),
            "high": float(data.get("highPrice", 0)),
            "low": float(data.get("lowPrice", 0)),
            "change_24h": float(data.get("priceChangePercent", 0)),
        }
    return None


def query_bybit(symbol):
    url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}USDT"
    data = api_get(url)
    if data and data.get("result", {}).get("list"):
        item = data["result"]["list"][0]
        return {
            "exchange": "Bybit",
            "price": float(item.get("lastPrice", 0)),
            "volume": float(item.get("turnover24h", 0)),
            "high": float(item.get("highPrice24h", 0)),
            "low": float(item.get("lowPrice24h", 0)),
            "change_24h": float(item.get("price24hPcnt", 0)) * 100,
        }
    return None


def query_okx(symbol):
    url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT"
    data = api_get(url)
    if data and data.get("data"):
        item = data["data"][0]
        last = float(item.get("last", 0))
        open_ = float(item.get("open24h", 0))
        change = ((last - open_) / open_ * 100) if open_ else 0
        return {
            "exchange": "OKX",
            "price": last,
            "volume": float(item.get("volCcy24h", 0)),
            "high": float(item.get("high24h", 0)),
            "low": float(item.get("low24h", 0)),
            "change_24h": change,
        }
    return None


def query_kucoin(symbol):
    url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}-USDT"
    data = api_get(url)
    if data and data.get("data"):
        item = data["data"]
        return {
            "exchange": "KuCoin",
            "price": float(item.get("price", 0)),
            "volume": 0,  # KuCoin L1 doesn't include volume
            "high": 0,
            "low": 0,
            "change_24h": 0,
        }
    return None


def query_gateio(symbol):
    url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}_USDT"
    data = api_get(url)
    if data and isinstance(data, list) and len(data) > 0:
        item = data[0]
        return {
            "exchange": "Gate.io",
            "price": float(item.get("last", 0)),
            "volume": float(item.get("quote_volume", 0)),
            "high": float(item.get("high_24h", 0)),
            "low": float(item.get("low_24h", 0)),
            "change_24h": float(item.get("change_percentage", 0)),
        }
    return None


def query_mexc(symbol):
    url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={symbol}USDT"
    data = api_get(url)
    if data and "lastPrice" in data:
        return {
            "exchange": "MEXC",
            "price": float(data["lastPrice"]),
            "volume": float(data.get("quoteVolume", 0)),
            "high": float(data.get("highPrice", 0)),
            "low": float(data.get("lowPrice", 0)),
            "change_24h": float(data.get("priceChangePercent", 0)),
        }
    return None


def query_bitget(symbol):
    url = f"https://api.bitget.com/api/v2/spot/market/tickers?symbol={symbol}USDT"
    data = api_get(url)
    if data and data.get("data"):
        item = data["data"][0] if isinstance(data["data"], list) else data["data"]
        return {
            "exchange": "Bitget",
            "price": float(item.get("lastPr", 0)),
            "volume": float(item.get("quoteVolume", 0)),
            "high": float(item.get("high24h", 0)),
            "low": float(item.get("low24h", 0)),
            "change_24h": float(item.get("change24h", 0)) * 100 if abs(float(item.get("change24h", 0))) < 1 else float(item.get("change24h", 0)),
        }
    return None


def query_htx(symbol):
    url = f"https://api.huobi.pro/market/detail/merged?symbol={symbol.lower()}usdt"
    data = api_get(url)
    if data and data.get("tick"):
        tick = data["tick"]
        open_ = tick.get("open", 0)
        last = tick.get("close", 0)
        change = ((last - open_) / open_ * 100) if open_ else 0
        return {
            "exchange": "HTX (Huobi)",
            "price": last,
            "volume": float(tick.get("amount", 0)),
            "high": float(tick.get("high", 0)),
            "low": float(tick.get("low", 0)),
            "change_24h": change,
        }
    return None


def query_hyperliquid(symbol):
    """Check Hyperliquid perps market and get mid price."""
    url = "https://api.hyperliquid.xyz/info"
    req = urllib.request.Request(url, headers={**HEADERS, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10, data=json.dumps({"type": "meta"}).encode()) as resp:
            meta = json.loads(resp.read())
    except Exception:
        return None

    for asset in meta.get("universe", []):
        if asset.get("name", "").upper() == symbol.upper():
            # Get current price via all mids
            try:
                with urllib.request.urlopen(req, timeout=10, data=json.dumps({"type": "allMids"}).encode()) as resp:
                    mids = json.loads(resp.read())
                mid_price = mids.get(symbol.upper())
                if mid_price:
                    return {
                        "exchange": "Hyperliquid (perps)",
                        "price": float(mid_price),
                        "volume": 0,
                        "high": 0,
                        "low": 0,
                        "change_24h": 0,
                    }
            except Exception:
                return {
                    "exchange": "Hyperliquid (perps)",
                    "price": 0,
                    "volume": 0,
                    "high": 0,
                    "low": 0,
                    "change_24h": 0,
                }
    return None


# ─── Main ─────────────────────────────────────────────────────────────

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


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    symbol = args[0].upper().strip()
    print(f"🔍 Fetching prices for ${symbol} across all exchanges...\n")

    results = []
    for name, func in EXCHANGES:
        print(f"  Checking {name}...", end=" ", flush=True)
        result = func(symbol)
        if result:
            print(f"✅ {fmt_price(result['price'])}")
            results.append(result)
        else:
            print("❌ not found")
        time.sleep(0.3)

    if not results:
        print(f"\n  ${symbol} not found on any exchange.")
        sys.exit(0)

    # Sort by volume (highest first)
    results.sort(key=lambda r: r["volume"], reverse=True)

    # ── Price Table ──
    print(f"\n{'='*70}")
    print(f"  💰 ${symbol} — EXCHANGE PRICE COMPARISON")
    print(f"{'='*70}")
    print(f"  {'Exchange':<20} {'Price':>14} {'24h Change':>10} {'24h Volume':>12} {'High':>14} {'Low':>14}")
    print(f"  {'─'*20} {'─'*14} {'─'*10} {'─'*12} {'─'*14} {'─'*14}")

    prices = []
    for r in results:
        price = r["price"]
        if price > 0:
            prices.append(price)
        chg = f"{r['change_24h']:+.2f}%" if r['change_24h'] else "N/A"
        vol = fmt_vol(r['volume']) if r['volume'] else "N/A"
        high = fmt_price(r['high']) if r['high'] else "N/A"
        low = fmt_price(r['low']) if r['low'] else "N/A"
        print(f"  {r['exchange']:<20} {fmt_price(price):>14} {chg:>10} {vol:>12} {high:>14} {low:>14}")

    # ── Price Spread Analysis ──
    if len(prices) >= 2:
        min_p = min(prices)
        max_p = max(prices)
        spread = (max_p - min_p) / min_p * 100
        print(f"\n  📊 PRICE SPREAD ANALYSIS")
        print(f"  {'─'*40}")
        print(f"  Lowest:  {fmt_price(min_p)}", end="")
        lowest_ex = [r['exchange'] for r in results if r['price'] == min_p]
        print(f"  ({', '.join(lowest_ex)})")
        print(f"  Highest: {fmt_price(max_p)}", end="")
        highest_ex = [r['exchange'] for r in results if r['price'] == max_p]
        print(f"  ({', '.join(highest_ex)})")
        print(f"  Spread:  {spread:.3f}%", end="")
        if spread > 1:
            print(f"  ⚠️  Significant — arbitrage opportunity possible")
        elif spread > 0.5:
            print(f"  📈 Notable")
        else:
            print(f"  ✅ Normal")

    print(f"\n  Exchanges found: {len(results)}/{len(EXCHANGES)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
