"""
Pre-Market Scanner — Curl if Flow System
Runs 4:00am–9:25am EST daily to build the watchlist before RTH open.

Finds top NASDAQ gainers matching W118's stock universe:
  - Price $0.10–$15
  - Float < 20M shares
  - Volume surge (already moving)
  - NASDAQ listed
  - Catalyst tier assigned based on available signals

Output: watchlist.json for signal_monitor.py to watch

Usage:
    pip install finviz yfinance pandas requests
    python pre_market_scanner.py
    python pre_market_scanner.py --min-gain 10 --max-float 15 --top 20
"""

import argparse
import json
import os
import sys
from datetime import datetime, date

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("Run: pip install finviz yfinance pandas requests")
    sys.exit(1)

WATCHLIST_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "watchlist.json")

# ── FINVIZ SCREENER ───────────────────────────────────────────────────────────

def screen_yahoo_top_movers(min_gain_pct: float = 5.0, max_price: float = 15.0,
                             min_price: float = 0.10) -> list[dict]:
    """
    Pull Yahoo Finance day gainers — same list Webull shows as 'Top Movers'.
    This is the source W118 likely uses for his pre-market watchlist.
    """
    try:
        import urllib.request
        url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=day_gainers&count=50"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        quotes = data["finance"]["result"][0]["quotes"]
        results = []
        for q in quotes:
            price  = q.get("regularMarketPrice", 0) or 0
            change = q.get("regularMarketChangePercent", 0) or 0
            exch   = (q.get("exchange", "") or "").upper()
            if not (min_price <= price <= max_price):
                continue
            if change < min_gain_pct:
                continue
            results.append({
                "ticker":     q.get("symbol", ""),
                "name":       q.get("shortName", ""),
                "price":      round(price, 4),
                "change_pct": round(change, 2),
                "volume":     str(q.get("regularMarketVolume", 0)),
                "float_m":    0,   # enriched below via yfinance
                "exchange":   exch,
                "source":     "yahoo_top_movers",
            })
        print(f"[scanner] Yahoo Top Movers: {len(results)} candidates (price/gain filtered)")
        return results
    except Exception as e:
        print(f"[scanner] Yahoo Top Movers failed: {e}")
        return []


def screen_finviz(min_gain_pct: float = 5.0, max_float_m: float = 20.0,
                  max_price: float = 15.0, min_price: float = 0.10) -> list[dict]:
    """
    Pull top NASDAQ gainers from Finviz screener matching W118's universe.
    Falls back to yfinance-based approach if finviz is unavailable.
    """
    try:
        from finviz.screener import Screener
        filters = [
            "exch_nasd",                          # NASDAQ only
            f"sh_price_{int(min_price*10)}to{int(max_price)}",  # price range
            "sh_float_u20",                        # float under 20M
            "ta_change_u10",                       # up 10%+ today
        ]
        stock_list = Screener(filters=filters, table="Overview", order="-change")
        results = []
        for stock in stock_list:
            try:
                results.append({
                    "ticker":   stock["Ticker"],
                    "price":    float(stock.get("Price", 0)),
                    "change_pct": float(stock.get("Change", "0%").replace("%", "")),
                    "volume":   stock.get("Volume", "0").replace(",", ""),
                    "float_m":  _parse_float(stock.get("Float", "0")),
                    "sector":   stock.get("Sector", ""),
                    "industry": stock.get("Industry", ""),
                    "source":   "finviz",
                })
            except Exception:
                continue
        return results

    except ImportError:
        print("[scanner] finviz not installed — using yfinance fallback")
        return _yfinance_fallback(min_gain_pct, max_price, min_price)
    except Exception as e:
        print(f"[scanner] Finviz error: {e} — using yfinance fallback")
        return _yfinance_fallback(min_gain_pct, max_price, min_price)


def _parse_float(val: str) -> float:
    """Parse '5.2M' or '18.4M' → float in millions."""
    val = str(val).upper().strip()
    try:
        if "M" in val:
            return float(val.replace("M", "").replace(",", ""))
        if "B" in val:
            return float(val.replace("B", "").replace(",", "")) * 1000
        return float(val.replace(",", "")) / 1_000_000
    except Exception:
        return 0.0


def _yfinance_fallback(min_gain_pct: float, max_price: float, min_price: float) -> list[dict]:
    """
    Fallback: pull known small-cap NASDAQ candidates from Yahoo Finance trending.
    In a real setup, replace with a proper data feed (Alpaca, Polygon, etc.).
    """
    print("[scanner] NOTE: yfinance fallback has no real-time screener.")
    print("          For live scanning, install finviz or use Alpaca/Polygon API.")
    print("          Returning empty watchlist — add tickers manually to watchlist.json")
    return []


# ── CATALYST TIER ASSIGNMENT ──────────────────────────────────────────────────

def assign_catalyst_tier(ticker: str, info: dict) -> tuple[int, str]:
    """
    Assign W118 catalyst tier based on available signals.
    Tier 1: FDA, merger, earnings beat, major news
    Tier 2: halt-resume, sympathy play, day 2-3 runner
    Tier 3: China momentum stock, technical setup only

    Returns (tier, reason)
    """
    try:
        yf_ticker = yf.Ticker(ticker)
        news = yf_ticker.news or []
        news_headlines = " ".join(
            n.get("content", {}).get("title", "") if isinstance(n.get("content"), dict)
            else n.get("title", "")
            for n in news[:5]
        ).upper()
    except Exception:
        news_headlines = ""

    # Tier 1 keywords
    t1_keywords = ["FDA", "APPROVAL", "MERGER", "ACQUISITION", "EARNINGS", "BEAT",
                   "GUIDANCE", "CONTRACT", "PARTNERSHIP", "NDA", "CLINICAL", "PHASE 3"]
    if any(k in news_headlines for k in t1_keywords):
        matched = next(k for k in t1_keywords if k in news_headlines)
        return 1, f"Tier 1: {matched} in recent news"

    # Tier 2 keywords
    t2_keywords = ["HALT", "RESUME", "CONTINUATION", "FOLLOW", "DAY 2", "DAY 3"]
    if any(k in news_headlines for k in t2_keywords):
        return 2, "Tier 2: halt-resume or continuation pattern"

    # Check if China-related (Tier 3)
    china_keywords = ["CHINA", "CHINESE", "HONG KONG", "BEIJING", "SHANGHAI",
                      "SINO", "HAN", "CAYMAN"]
    ticker_industry = str(info.get("industry", "")).upper()
    if any(k in news_headlines or k in ticker_industry for k in china_keywords):
        return 3, "Tier 3: China momentum stock"

    # Default Tier 3 — technical only
    return 3, "Tier 3: technical setup, no clear catalyst found"


# ── ENRICH WITH YFINANCE ──────────────────────────────────────────────────────

def enrich_with_yfinance(candidates: list[dict]) -> list[dict]:
    """Add float, premarket change, and catalyst tier via yfinance."""
    enriched = []
    for c in candidates:
        ticker = c["ticker"]
        try:
            yf_t = yf.Ticker(ticker)
            info = yf_t.info or {}

            # Fill in missing float
            if not c.get("float_m"):
                shares_float = info.get("floatShares", 0) or 0
                c["float_m"] = round(shares_float / 1_000_000, 2)

            # Add company name
            c["name"] = info.get("shortName", ticker)

            # Catalyst tier
            tier, reason = assign_catalyst_tier(ticker, info)
            c["catalyst_tier"] = tier
            c["catalyst_reason"] = reason

            # Mark if price in range
            price = c.get("price", 0)
            c["price_ok"] = 0.10 <= price <= 15.0
            c["float_ok"] = 0 < c["float_m"] < 20.0

            enriched.append(c)
        except Exception as e:
            c["catalyst_tier"] = 3
            c["catalyst_reason"] = f"enrichment error: {e}"
            enriched.append(c)

    return enriched


# ── RANK AND FILTER ───────────────────────────────────────────────────────────

def rank_watchlist(candidates: list[dict], min_gain_pct: float) -> list[dict]:
    """Filter and rank by: catalyst tier > % gain > float (smaller = better)."""
    filtered = [
        c for c in candidates
        if c.get("price_ok", True)
        and c.get("float_ok", True)
        and c.get("change_pct", 0) >= min_gain_pct
    ]

    filtered.sort(key=lambda c: (
        c.get("catalyst_tier", 3),            # lower tier = higher priority
        -c.get("change_pct", 0),              # higher % gain = higher priority
        c.get("float_m", 20),                 # smaller float = higher priority
    ))

    return filtered


# ── SAVE WATCHLIST ────────────────────────────────────────────────────────────

def save_watchlist(watchlist: list[dict], path: str = WATCHLIST_PATH) -> None:
    output = {
        "date": date.today().isoformat(),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(watchlist),
        "stocks": watchlist,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"[scanner] Saved {len(watchlist)} stocks → {path}")


def print_watchlist(watchlist: list[dict]) -> None:
    if not watchlist:
        print("\n[scanner] No candidates found matching criteria.")
        return
    print(f"\n{'═'*65}")
    print(f"{'CURL IF FLOW — PRE-MARKET WATCHLIST':^65}")
    print(f"{'═'*65}")
    print(f"{'#':<3} {'TICKER':<7} {'PRICE':>6} {'GAIN%':>7} {'FLOAT':>7} {'TIER':<5} CATALYST")
    print(f"{'─'*65}")
    for i, s in enumerate(watchlist, 1):
        tier_emoji = "🔥" if s["catalyst_tier"] == 1 else ("⚡" if s["catalyst_tier"] == 2 else "📊")
        print(
            f"{i:<3} {s['ticker']:<7} ${s.get('price',0):>5.2f} "
            f"{s.get('change_pct',0):>+6.1f}% "
            f"{s.get('float_m',0):>5.1f}M  "
            f"T{s['catalyst_tier']} {tier_emoji}  {s.get('catalyst_reason','')[:35]}"
        )
    print(f"{'═'*65}\n")


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Curl if Flow — Pre-Market Scanner")
    parser.add_argument("--min-gain", type=float, default=10.0, help="Min % gain to consider")
    parser.add_argument("--max-float", type=float, default=20.0, help="Max float in millions")
    parser.add_argument("--max-price", type=float, default=15.0, help="Max stock price")
    parser.add_argument("--min-price", type=float, default=0.10, help="Min stock price")
    parser.add_argument("--top", type=int, default=15, help="Max stocks on watchlist")
    parser.add_argument("--no-enrich", action="store_true", help="Skip yfinance enrichment")
    parser.add_argument("--tickers", nargs="+", help="Manually specify tickers to analyze")
    args = parser.parse_args()

    print(f"\n[scanner] Curl if Flow Pre-Market Scanner — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"[scanner] Criteria: NASDAQ | ${args.min_price}–${args.max_price} | "
          f"Float <{args.max_float}M | >{args.min_gain}% gain\n")

    # Manual override
    if args.tickers:
        candidates = [{"ticker": t.upper(), "price": 0, "change_pct": 0,
                       "volume": "0", "float_m": 0, "source": "manual"}
                      for t in args.tickers]
    else:
        # Try Yahoo Top Movers first (same list as Webull "Top Stocks"), fall back to Finviz
        candidates = screen_yahoo_top_movers(args.min_gain, args.max_price, args.min_price)
        if not candidates:
            candidates = screen_finviz(args.min_gain, args.max_float, args.max_price, args.min_price)
        print(f"[scanner] Found {len(candidates)} raw candidates from screener")

    if not args.no_enrich:
        print("[scanner] Enriching with yfinance (catalyst tier, float verification)...")
        candidates = enrich_with_yfinance(candidates)

    watchlist = rank_watchlist(candidates, args.min_gain)[: args.top]
    print_watchlist(watchlist)
    save_watchlist(watchlist)

    print(f"[scanner] Done. Feed watchlist.json to signal_monitor.py")
    print(f"[scanner] Run: python signal_monitor.py --watchlist data/watchlist.json\n")


if __name__ == "__main__":
    main()
