"""
analyze_trades.py — Pull ALL live bot trades from Supabase + summarize.

Usage:
    python bot/analyze_trades.py
    python bot/analyze_trades.py --ticker AIIO   # filter one stock
    python bot/analyze_trades.py --days 7        # last N days only

Reads from Supabase w118_trades table using the public anon key (read-only).
No config.py needed — the anon key is hardcoded (it's public/safe by design).
"""
import requests
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

# Public anon key — read-only, safe to commit (RLS enforced in Supabase)
SUPABASE_URL = "https://lgzzuppprbokfobhycov.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_qIqnOFvjWSVquqlCpDIj2Q_t468MohI"

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
}

def fetch_all_trades(days: int | None = None, ticker: str | None = None) -> list[dict]:
    """Pull all rows from w118_trades, newest first."""
    url = f"{SUPABASE_URL}/rest/v1/w118_trades"
    params = {
        "select": "*",
        "order": "date.desc,time_et.desc",
        "limit": 5000,
    }
    if ticker:
        params["ticker"] = f"eq.{ticker.upper()}"
    if days:
        from datetime import timedelta, date as date_
        cutoff = (date_.today() - timedelta(days=days)).isoformat()
        params["date"] = f"gte.{cutoff}"

    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def _pct(val: float | None) -> str:
    if val is None:
        return "—"
    return f"{val:+.1f}%"


def _grade_order(g: str) -> int:
    return {"A+": 0, "A": 1, "B": 2, "C": 3}.get(g, 9)


def summarize(trades: list[dict]) -> None:
    if not trades:
        print("No trades found.")
        return

    print(f"\n{'='*60}")
    print(f"  LIVE BOT TRADE REPORT  ({len(trades)} entries)")
    print(f"{'='*60}\n")

    # ── Ticker counts ────────────────────────────────────────────
    ticker_count = Counter(t["ticker"] for t in trades)
    print("── Top tickers (by entry count) ──")
    for tk, cnt in ticker_count.most_common(20):
        sub = [t for t in trades if t["ticker"] == tk]
        grades = [t.get("grade") or "?" for t in sub]
        prices = [t.get("price") for t in sub if t.get("price")]
        price_range = f"${min(prices):.2f}–${max(prices):.2f}" if prices else "—"
        print(f"  {tk:8s}  {cnt:3d}x  grades: {', '.join(sorted(grades))}  prices: {price_range}")

    # ── Session distribution ─────────────────────────────────────
    sessions = Counter(t.get("session") or "unknown" for t in trades)
    print(f"\n── Session breakdown ──")
    for sess, cnt in sorted(sessions.items(), key=lambda x: -x[1]):
        print(f"  {sess:15s}  {cnt:3d} trades  ({cnt/len(trades)*100:.0f}%)")

    # ── Grade distribution ────────────────────────────────────────
    grades = Counter(t.get("grade") or "?" for t in trades)
    print(f"\n── Grade distribution ──")
    for g in ["A+", "A", "B", "C", "?"]:
        cnt = grades.get(g, 0)
        if cnt:
            print(f"  Grade {g:3s}  {cnt:3d} ({cnt/len(trades)*100:.0f}%)")

    # ── Deep curl ────────────────────────────────────────────────
    deep_curls = sum(1 for t in trades if t.get("deep_curl"))
    print(f"\n── Deep curl (⭐) ──")
    print(f"  {deep_curls} / {len(trades)} entries had deep-curl flag ({deep_curls/len(trades)*100:.0f}%)")

    # ── VWAP tag distribution ────────────────────────────────────
    vwap_tags = Counter(t.get("vwap_tag") or "—" for t in trades)
    print(f"\n── VWAP tag distribution ──")
    for tag, cnt in sorted(vwap_tags.items(), key=lambda x: -x[1])[:8]:
        print(f"  {tag:20s}  {cnt:3d}")

    # ── Volume ratio ─────────────────────────────────────────────
    vol_ratios = [t.get("vol_ratio") for t in trades if t.get("vol_ratio") is not None]
    if vol_ratios:
        avg_vol = sum(vol_ratios) / len(vol_ratios)
        print(f"\n── Volume at entry ──")
        print(f"  Avg rel vol: {avg_vol:.1f}x   Min: {min(vol_ratios):.1f}x   Max: {max(vol_ratios):.1f}x")
        under_1_5 = sum(1 for v in vol_ratios if v < 1.5)
        print(f"  Entries below 1.5x: {under_1_5} ({under_1_5/len(vol_ratios)*100:.0f}%) — passed as soft condition")

    # ── K / D at entry ────────────────────────────────────────────
    k_vals = [t.get("k_value") for t in trades if t.get("k_value") is not None]
    if k_vals:
        print(f"\n── StochRSI K at entry ──")
        print(f"  Avg K: {sum(k_vals)/len(k_vals):.1f}   Min: {min(k_vals):.1f}   Max: {max(k_vals):.1f}")
        reset_zone = sum(1 for k in k_vals if k <= 30)
        print(f"  K ≤ 30 (deep-curl reset zone): {reset_zone} ({reset_zone/len(k_vals)*100:.0f}%)")
        overbought = sum(1 for k in k_vals if k >= 85)
        print(f"  K ≥ 85 (overbought, would be blocked): {overbought}")

    # ── Price distribution ────────────────────────────────────────
    prices = [t.get("price") for t in trades if t.get("price")]
    if prices:
        buckets = {"<$1": 0, "$1-2": 0, "$2-5": 0, "$5-10": 0, "$10-15": 0}
        for p in prices:
            if   p < 1:   buckets["<$1"] += 1
            elif p < 2:   buckets["$1-2"] += 1
            elif p < 5:   buckets["$2-5"] += 1
            elif p < 10:  buckets["$5-10"] += 1
            else:         buckets["$10-15"] += 1
        print(f"\n── Entry price distribution ──")
        for bucket, cnt in buckets.items():
            if cnt:
                print(f"  {bucket:8s}  {cnt:3d} ({cnt/len(prices)*100:.0f}%)")

    # ── Recent entries (last 20) ──────────────────────────────────
    print(f"\n── Most recent 20 entries ──")
    for t in trades[:20]:
        ts = f"{t.get('date','?')} {t.get('time_et','?')}"
        grade = t.get("grade") or "?"
        star = "⭐" if t.get("deep_curl") else "  "
        price = t.get("entry_price") or t.get("price") or 0
        k = t.get("k_value") or 0
        vol = t.get("vol_ratio") or 0
        print(f"  {ts}  {t['ticker']:8s}  [{grade}]{star}  ${price:.3f}  K={k:.0f}  Vol={vol:.1f}x")

    # ── Repeated stocks (daily re-entries) ────────────────────────
    repeats = {tk: cnt for tk, cnt in ticker_count.items() if cnt >= 3}
    if repeats:
        print(f"\n── Stocks entered 3+ times (daily re-entry pattern) ──")
        for tk, cnt in sorted(repeats.items(), key=lambda x: -x[1]):
            sub = sorted([t for t in trades if t["ticker"] == tk],
                         key=lambda x: x.get("ts") or "")
            dates = list(dict.fromkeys([(t.get("ts") or "")[:10] for t in sub]))
            print(f"  {tk:8s}  {cnt}x  across days: {', '.join(dates)}")

    print(f"\n{'='*60}")
    print("NOTE: P&L % is NOT in the Supabase log (only entry data is stored).")
    print("For exit P&L, cross-reference with Alpaca paper account Activities page.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze bot trades from Supabase")
    parser.add_argument("--ticker", help="Filter to one ticker")
    parser.add_argument("--days", type=int, help="Last N days only")
    parser.add_argument("--json", action="store_true", help="Dump raw JSON")
    args = parser.parse_args()

    print(f"Fetching trades from Supabase...")
    try:
        trades = fetch_all_trades(days=args.days, ticker=args.ticker)
    except Exception as e:
        print(f"ERROR: {e}")
        print("Check network connection. Supabase URL and anon key are hardcoded in this script.")
        sys.exit(1)

    if args.json:
        print(json.dumps(trades, indent=2))
    else:
        summarize(trades)
