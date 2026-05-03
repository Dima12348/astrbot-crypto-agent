#!/usr/bin/env python3
"""Search X/Twitter for crypto token mentions — sentiment analysis & report.

Two modes of operation:
  1. Agent mode (recommended): agent gathers data via web_search/web_extract,
     saves to JSON, then feeds it to this script for parsing & analysis.
  2. Standalone mode: direct scraping of search engines + Nitter instances
     (may fail from VPS/cloud IPs due to CAPTCHAs).

No API keys required — uses only Python stdlib.

Usage (agent mode):
    python twitter_search.py "PEPE" --input results.json
    echo '{"web_results":[...]}' | python twitter_search.py "PEPE" --stdin

Usage (standalone mode):
    python twitter_search.py "PEPE"
    python twitter_search.py "PEPE" --top 10

Input JSON format:
    {
        "web_results": [
            {"title": "...", "url": "https://x.com/user/status/123", "snippet": "..."}
        ],
        "nitter_html": "<raw html from nitter fetch>",
        "nitter_instance": "https://nitter.tiekoetter.com"
    }
"""
import sys
import json
import re
import urllib.request
import urllib.error
import urllib.parse
import time
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

NITTER_INSTANCES = [
    "https://nitter.tiekoetter.com",
    "https://nitter.cz",
    "https://xcancel.com",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.space",
    "https://nitter.catsarch.com",
    "https://nitter.kareem.one",
    "https://lightbrd.com",
    "https://nitter.net",
]

CRYPTO_NEWS_DOMAINS = [
    "coindesk.com", "cointelegraph.com", "decrypt.co", "theblock.co",
    "beincrypto.com", "cryptoslate.com", "dlnews.com", "bitcoinmagazine.com",
]


# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def http_get(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace"), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, str(e.reason)
    except Exception as e:
        return None, str(e)


def unwrap_ddg_url(url):
    if "uddg=" in url:
        m = re.search(r'uddg=([^&]+)', url)
        if m:
            return urllib.parse.unquote(m.group(1))
    return url


def extract_username(url):
    m = re.search(r"(?:x\.com|twitter\.com)/(\w+)(?:/status/\d+)?", url)
    return f"@{m.group(1)}" if m else None


def is_twitter_url(url):
    return any(d in url.lower() for d in ["x.com", "twitter.com"])


def is_crypto_news_url(url):
    return any(d in url.lower() for d in CRYPTO_NEWS_DOMAINS)


# ═══════════════════════════════════════════════════════════════════════
#  Web Search (standalone — tries DDG, Google, Bing)
# ═══════════════════════════════════════════════════════════════════════

def _search_ddg(query, max_results=10):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
    html, err = http_get(url, timeout=20)
    if err:
        return [], [], f"DDG: {err}"
    if "anomaly-modal" in html or "challenge-form" in html:
        return [], [], "DDG: CAPTCHA"

    results = []
    for href, title in re.findall(
        r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL
    ):
        title = re.sub(r'<[^>]+>', '', title).strip()
        if title:
            results.append({"title": title, "url": unwrap_ddg_url(href), "snippet": ""})

    if not results:
        for href, text in re.findall(
            r'<a[^>]*rel="nofollow"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL
        ):
            text = re.sub(r'<[^>]+>', '', text).strip()
            if text and len(text) > 5:
                results.append({"title": text, "url": unwrap_ddg_url(href), "snippet": ""})

    return _split_twitter(results, max_results), None


def _search_google(query, max_results=10):
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}&num={max_results}"
    html, err = http_get(url, timeout=15)
    if err:
        return [], [], f"Google: {err}"
    if "unusual traffic" in html.lower():
        return [], [], "Google: CAPTCHA"

    results = []
    for href, text in re.findall(
        r'<a[^>]*href="/url\?q=([^&"]+)[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL
    ):
        href = urllib.parse.unquote(href)
        text = re.sub(r'<[^>]+>', '', text).strip()
        if text and len(text) > 5 and not href.startswith("/"):
            results.append({"title": text, "url": href, "snippet": ""})

    return _split_twitter(results, max_results), None


def _search_bing(query, max_results=10):
    url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}&count={max_results}"
    html, err = http_get(url, timeout=15)
    if err:
        return [], [], f"Bing: {err}"
    if "captcha" in html.lower():
        return [], [], "Bing: CAPTCHA"

    results = []
    for href, title, snippet in re.findall(
        r'<li class="b_algo"[^>]*>.*?<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>.*?<p[^>]*>(.*?)</p>',
        html, re.DOTALL
    ):
        title = re.sub(r'<[^>]+>', '', title).strip()
        snippet = re.sub(r'<[^>]+>', '', snippet).strip()
        if title:
            results.append({"title": title, "url": href, "snippet": snippet})

    return _split_twitter(results, max_results), None


def _split_twitter(results, max_results):
    seen = set()
    twitter = []
    other = []
    for r in results:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        if is_twitter_url(r["url"]):
            twitter.append(r)
        elif is_crypto_news_url(r["url"]):
            other.append(r)
    return twitter[:max_results], other[:3]


def standalone_web_search(query, max_results=10):
    """Try DDG → Google → Bing. Returns (twitter_results, other_results, engine)."""
    for name, fn in [("DuckDuckGo", _search_ddg), ("Google", _search_google), ("Bing", _search_bing)]:
        try:
            (twitter, other), err = fn(query, max_results)
            if err:
                continue
            if twitter or other:
                return twitter, other, name
        except Exception:
            continue
    return [], [], None


# ═══════════════════════════════════════════════════════════════════════
#  Nitter Parsing
# ═══════════════════════════════════════════════════════════════════════

def parse_nitter_html(html, instance_url=""):
    """Parse Nitter HTML into tweet dicts using regex."""
    tweets = []
    items = re.split(r'<div class="timeline-item\s*[^"]*">', html)

    for item in items[1:]:
        tweet = {
            "username": "", "display_name": "", "text": "",
            "timestamp": "", "likes": 0, "retweets": 0, "replies": 0, "url": "",
        }

        m = re.search(r'<a[^>]*class="username"[^>]*href="/([^"]+)"[^>]*>@(\w+)</a>', item)
        if m:
            tweet["username"] = "@" + m.group(2)

        m = re.search(r'<a[^>]*class="fullname"[^>]*>([^<]+)</a>', item)
        if m:
            tweet["display_name"] = m.group(1).strip()

        m = re.search(r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>', item, re.DOTALL)
        if m:
            text = m.group(1)
            for old, new in [('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'")]:
                text = text.replace(old, new)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            tweet["text"] = text

        m = re.search(r'<span[^>]*class="tweet-date"[^>]*title="([^"]*)"', item)
        if m:
            tweet["timestamp"] = m.group(1)

        m = re.search(r'<a[^>]*href="(/[^"]*?/status/\d+)"', item)
        if m:
            tweet["url"] = instance_url.rstrip('/') + m.group(1)

        for pattern, field in [
            (r'icon-comment.*?<span[^>]*>([^<]*)</span>', "replies"),
            (r'icon-retweet.*?<span[^>]*>([^<]*)</span>', "retweets"),
            (r'icon-heart.*?<span[^>]*>([^<]*)</span>', "likes"),
        ]:
            m = re.search(pattern, item, re.DOTALL)
            if m:
                num = re.sub(r'[^\d]', '', m.group(1))
                if num:
                    tweet[field] = int(num)

        if tweet["text"] or tweet["username"]:
            tweets.append(tweet)

    return tweets


def standalone_nitter_search(query, max_tweets=15):
    """Try multiple Nitter instances. Returns (tweets, instance_url)."""
    for instance in NITTER_INSTANCES:
        html, err = http_get(f"{instance}/search?f=tweets&q={urllib.parse.quote_plus(query)}", timeout=15)
        if not html or len(html) < 2000:
            continue
        if "Making sure you" in html or "anubis" in html.lower():
            continue
        tweets = parse_nitter_html(html, instance)
        if tweets:
            return tweets[:max_tweets], instance
    return [], None


# ═══════════════════════════════════════════════════════════════════════
#  Sentiment Analysis
# ═══════════════════════════════════════════════════════════════════════

POSITIVE_KW = [
    "pump", "moon", "bullish", "breakout", "surge", "rally", "all-time high",
    "ath", "buy", "accumulate", "listing", "partnership", "upgrade", "adoption",
    "institutional", "etf", "whale buy", "growth", "undervalued", "gem",
    "bull run", "massive gains", "to the moon", "hodl", "diamond hands",
]

NEGATIVE_KW = [
    "dump", "crash", "rug", "scam", "hack", "exploit", "bearish", "sell",
    "fear", "fud", "ponzi", "fraud", "lawsuit", "sec", "ban", "warning",
    "whale sell", "liquidat", "overvalued", "dead", "rugpull", "honeypot",
    "fake", "shill", "bot", "wash trading", "exit scam",
]


def detect_sentiment(items):
    pos = neg = 0
    pos_kw = set()
    neg_kw = set()

    for item in items:
        text = " ".join([
            item.get("text", ""), item.get("snippet", ""), item.get("title", ""),
        ]).lower()
        for kw in POSITIVE_KW:
            if kw in text:
                pos += 1
                pos_kw.add(kw)
        for kw in NEGATIVE_KW:
            if kw in text:
                neg += 1
                neg_kw.add(kw)

    return {
        "positive": pos, "negative": neg,
        "pos_keywords": sorted(pos_kw), "neg_keywords": sorted(neg_kw),
    }


# ═══════════════════════════════════════════════════════════════════════
#  High-Level API
# ═══════════════════════════════════════════════════════════════════════

def search_twitter(query, max_results=10, web=True, nitter=True, input_data=None):
    """Search X/Twitter for a query. Returns structured results dict.

    Args:
        query: Search term (e.g. "PEPE crypto")
        max_results: Max results per source
        web: Enable standalone web search
        nitter: Enable standalone Nitter scraping
        input_data: Pre-fetched data from agent (overrides standalone):
            {"web_results": [...], "nitter_html": "...", "nitter_instance": "..."}

    Returns:
        dict with all results and sentiment analysis.
    """
    result = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "web_results": [],
        "other_results": [],
        "nitter_tweets": [],
        "nitter_instance": None,
        "engine": None,
        "sentiment": None,
        "source": "standalone",
    }

    if input_data:
        result["source"] = "agent"
        result["web_results"] = input_data.get("web_results", [])
        result["other_results"] = input_data.get("other_results", [])

        nitter_html = input_data.get("nitter_html", "")
        nitter_instance = input_data.get("nitter_instance", "")
        if nitter_html:
            result["nitter_tweets"] = parse_nitter_html(nitter_html, nitter_instance)
            result["nitter_instance"] = nitter_instance
    else:
        if web:
            search_q = f"{query} crypto site:x.com OR site:twitter.com"
            twitter_r, other_r, engine = standalone_web_search(search_q, max_results)
            result["web_results"] = twitter_r
            result["other_results"] = other_r
            result["engine"] = engine

        if nitter:
            symbol = query.split()[0].upper().replace("$", "")
            for term in [f"${symbol} crypto", f"{query} crypto", f"${symbol}"]:
                tweets, instance = standalone_nitter_search(term, max_results)
                if tweets:
                    result["nitter_tweets"] = tweets
                    result["nitter_instance"] = instance
                    break

    all_items = result["web_results"] + result["nitter_tweets"]
    if all_items:
        result["sentiment"] = detect_sentiment(all_items)

    return result


# ═══════════════════════════════════════════════════════════════════════
#  Display
# ═══════════════════════════════════════════════════════════════════════

def fmt_eng(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)


def display_report(result):
    query = result["query"]
    web_results = result["web_results"]
    other_results = result.get("other_results", [])
    nitter_tweets = result["nitter_tweets"]
    nitter_instance = result["nitter_instance"]
    engine = result.get("engine")
    source = result.get("source", "unknown")

    print(f"🐦 X/Twitter Search: {query}")
    print(f"{'='*60}")
    print(f"  Source: {source}" + (f" ({engine})" if engine else ""))

    if web_results:
        print(f"  Web results: {len(web_results)} from X/Twitter")
    if other_results:
        print(f"  News results: {len(other_results)}")
    if nitter_tweets:
        print(f"  Nitter tweets: {len(nitter_tweets)} from {nitter_instance}")
    if not web_results and not nitter_tweets:
        print(f"  ⚪ No X/Twitter data found")

    if web_results:
        print(f"\n  🔍 X/Twitter Results ({len(web_results)}):")
        print(f"  {'─'*50}")
        for i, r in enumerate(web_results, 1):
            title = r.get("title", "")
            url = r.get("url", "")
            snippet = r.get("snippet", "")
            user = extract_username(url)
            tag = f" ({user})" if user else ""
            print(f"  [{i}] {title}{tag}")
            if snippet:
                if len(snippet) > 200:
                    snippet = snippet[:197] + "..."
                print(f"       {snippet}")
            print(f"       🔗 {url[:100]}")
            print()

    if other_results:
        print(f"\n  📰 Crypto News ({len(other_results)}):")
        print(f"  {'─'*50}")
        for i, r in enumerate(other_results, 1):
            print(f"  [{i}] {r.get('title', '')}")
            if r.get("snippet"):
                s = r["snippet"][:200] + "..." if len(r["snippet"]) > 200 else r["snippet"]
                print(f"       {s}")
            print(f"       🔗 {r.get('url', '')[:100]}")
            print()

    if nitter_tweets:
        print(f"\n  🐦 Tweets ({len(nitter_tweets)}):")
        print(f"  {'─'*50}")
        for i, t in enumerate(nitter_tweets, 1):
            name = t.get("display_name", "") or t.get("username", "?")
            user = t.get("username", "")
            text = t.get("text", "")
            if len(text) > 280:
                text = text[:277] + "..."
            print(f"  [{i}] {name} {user}")
            print(f"       {text}")
            print(f"       ❤️ {fmt_eng(t.get('likes',0))}  🔁 {fmt_eng(t.get('retweets',0))}  "
                  f"💬 {fmt_eng(t.get('replies',0))}  🕐 {t.get('timestamp','')}")
            if t.get("url"):
                print(f"       🔗 {t['url'][:100]}")
            print()

    sentiment = result.get("sentiment")
    if sentiment:
        total = sentiment["positive"] + sentiment["negative"]
        print(f"\n  📊 SENTIMENT SNAPSHOT")
        print(f"  {'─'*50}")
        if total > 0:
            pos_pct = sentiment["positive"] / total * 100
            neg_pct = sentiment["negative"] / total * 100
            bar_len = 30
            pos_bar = int(pos_pct / 100 * bar_len)
            print(f"  {'🟢' * pos_bar}{'🔴' * (bar_len - pos_bar)}")
            print(f"  Positive: {sentiment['positive']} ({pos_pct:.0f}%) | "
                  f"Negative: {sentiment['negative']} ({neg_pct:.0f}%)")
            if sentiment["pos_keywords"]:
                print(f"  Bullish: {', '.join(sentiment['pos_keywords'])}")
            if sentiment["neg_keywords"]:
                print(f"  Bearish: {', '.join(sentiment['neg_keywords'])}")
            label = "🟢 BULLISH" if pos_pct > 70 else ("🔴 BEARISH" if neg_pct > 70 else "🟡 MIXED")
            print(f"  Overall: {label}")
        else:
            print(f"  No clear sentiment signals")

        if nitter_tweets:
            likes = sum(t.get("likes", 0) for t in nitter_tweets)
            rts = sum(t.get("retweets", 0) for t in nitter_tweets)
            print(f"\n  Engagement: ❤️ {fmt_eng(likes)} likes | 🔁 {fmt_eng(rts)} RTs")
            top = max(nitter_tweets, key=lambda t: t.get("likes", 0) + t.get("retweets", 0))
            if top.get("likes", 0) > 0:
                print(f"  Top tweet: {top.get('display_name', '?')} — ❤️ {fmt_eng(top['likes'])}")

    print(f"\n  ⚠️  Sentiment is keyword-based. Verify manually.")
    print(f"{'='*60}")


# ═══════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    nitter_only = "--nitter-only" in args
    web_only = "--web-only" in args
    json_only = "--json" in args
    read_stdin = "--stdin" in args
    input_file = None
    top = 10

    if "--top" in args:
        idx = args.index("--top")
        top = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]
    if "--input" in args:
        idx = args.index("--input")
        input_file = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    args = [a for a in args if a not in ("--nitter-only", "--web-only", "--json", "--stdin")]
    query = " ".join(args)

    input_data = None
    if input_file:
        with open(input_file) as f:
            input_data = json.load(f)
    elif read_stdin and not sys.stdin.isatty():
        input_data = json.load(sys.stdin)

    result = search_twitter(
        query, max_results=top,
        web=not nitter_only and not input_data,
        nitter=not web_only and not input_data,
        input_data=input_data,
    )

    if json_only:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        display_report(result)
        print(f"\n__JSON_START__")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"__JSON_END__")


if __name__ == "__main__":
    main()
