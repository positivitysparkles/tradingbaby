"""
audit_alpaca.py — Full trade audit: Alpaca fills × Supabase entries → improvement log.

Pulls every paper-account FILL from Alpaca, matches buy→sell pairs to compute
realized P&L, cross-references with Supabase entry data (grade, K, vol, session,
deep-curl), computes win-rate breakdowns, and writes dated recommendations to
data/improvement_log.json so improvements are never lost or repeated.

Usage (run on VPS or MacBook where bot/config.py has real keys):
    python bot/audit_alpaca.py             # full report
    python bot/audit_alpaca.py --apply     # also apply safe auto-fixes to config.py
    python bot/audit_alpaca.py --history   # print past improvement log entries
    python bot/audit_alpaca.py --json      # dump raw Alpaca fills as JSON
"""

import sys
import json
import requests
import argparse
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Locate config ────────────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    import config as _cfg
    ALPACA_KEY_ID     = getattr(_cfg, "ALPACA_KEY_ID", "")
    ALPACA_SECRET_KEY = getattr(_cfg, "ALPACA_SECRET_KEY", "")
    ALPACA_BASE_URL   = getattr(_cfg, "ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    ALPACA_DATA_URL   = getattr(_cfg, "ALPACA_DATA_URL", "https://data.alpaca.markets")
except ImportError:
    ALPACA_KEY_ID     = ""
    ALPACA_SECRET_KEY = ""
    ALPACA_BASE_URL   = "https://paper-api.alpaca.markets"

# Supabase public anon key (read-only — safe to commit)
SUPABASE_URL      = "https://lgzzuppprbokfobhycov.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_qIqnOFvjWSVquqlCpDIj2Q_t468MohI"

IMPROVEMENT_LOG   = Path(__file__).parent.parent / "data" / "improvement_log.json"

ALPACA_HEADERS = {
    "APCA-API-KEY-ID":     ALPACA_KEY_ID,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
}
SUPABASE_HEADERS = {
    "apikey":        SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
}


# ── Alpaca fetch ─────────────────────────────────────────────────────────────

def fetch_fills() -> list[dict]:
    """Pull ALL FILL activities from Alpaca paper account (paginated)."""
    fills, page_token = [], None
    while True:
        params = {"activity_type": "FILL", "page_size": 100, "direction": "asc"}
        if page_token:
            params["page_token"] = page_token
        r = requests.get(
            f"{ALPACA_BASE_URL}/v2/account/activities",
            headers=ALPACA_HEADERS, params=params, timeout=15
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        fills.extend(batch)
        if len(batch) < 100:
            break
        page_token = batch[-1]["id"]
    return fills


def fetch_account() -> dict:
    r = requests.get(f"{ALPACA_BASE_URL}/v2/account", headers=ALPACA_HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


# ── Supabase fetch ────────────────────────────────────────────────────────────

def fetch_supabase_entries() -> list[dict]:
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/w118_trades",
        headers=SUPABASE_HEADERS,
        params={"select": "*", "order": "ts.asc", "limit": 5000},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


# ── Match buy→sell pairs ──────────────────────────────────────────────────────

def pair_trades(fills: list[dict]) -> list[dict]:
    """
    Match each BUY fill with subsequent SELL fills for the same ticker.
    Uses FIFO: oldest buy shares matched against oldest sell shares.
    Returns a list of closed-trade dicts with realized P&L.
    """
    # Group fills by ticker
    by_ticker: dict[str, list] = defaultdict(list)
    for f in fills:
        by_ticker[f["symbol"]].append(f)

    closed: list[dict] = []

    for ticker, events in by_ticker.items():
        buy_queue: list[dict] = []  # each entry: {"price": float, "qty": int, "ts": str}

        for ev in events:
            qty   = int(float(ev.get("qty") or ev.get("shares", 0)))
            price = float(ev.get("price") or 0)
            side  = ev.get("side", "").lower()
            ts    = ev.get("transaction_time") or ev.get("timestamp") or ""

            if side in ("buy", "long"):
                buy_queue.append({"price": price, "qty": qty, "ts": ts})

            elif side in ("sell", "short") and qty > 0:
                remaining = qty
                while remaining > 0 and buy_queue:
                    buy = buy_queue[0]
                    matched = min(remaining, buy["qty"])
                    pnl_pct = (price - buy["price"]) / buy["price"] * 100 if buy["price"] else 0
                    pnl_usd = (price - buy["price"]) * matched

                    closed.append({
                        "ticker":   ticker,
                        "entry_price": buy["price"],
                        "exit_price":  price,
                        "qty":      matched,
                        "pnl_pct":  round(pnl_pct, 2),
                        "pnl_usd":  round(pnl_usd, 2),
                        "win":      pnl_pct >= 0,
                        "entry_ts": buy["ts"],
                        "exit_ts":  ts,
                    })

                    buy["qty"] -= matched
                    remaining -= matched
                    if buy["qty"] <= 0:
                        buy_queue.pop(0)

    return sorted(closed, key=lambda x: x["entry_ts"])


# ── Cross-reference with Supabase ─────────────────────────────────────────────

def enrich_with_supabase(trades: list[dict], entries: list[dict]) -> list[dict]:
    """
    For each closed trade, find the matching Supabase entry (same ticker,
    entry price within 2%, entry time within 30 min) and attach grade/K/vol/session.
    """
    def ts_epoch(s: str) -> float:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0.0

    sb_by_ticker: dict[str, list] = defaultdict(list)
    for e in entries:
        sb_by_ticker[e["ticker"]].append(e)

    for t in trades:
        candidates = sb_by_ticker.get(t["ticker"], [])
        best = None
        for c in candidates:
            price_match = (abs(float(c.get("price") or 0) - t["entry_price"]) / max(t["entry_price"], 0.01)) < 0.02
            time_diff = abs(ts_epoch(c.get("ts", "")) - ts_epoch(t["entry_ts"]))
            if price_match and time_diff < 1800:  # within 30 min
                if best is None or time_diff < abs(ts_epoch(best.get("ts", "")) - ts_epoch(t["entry_ts"])):
                    best = c
        if best:
            t["grade"]      = best.get("grade")
            t["k"]          = best.get("k")
            t["vol_ratio"]  = best.get("vol_ratio")
            t["session"]    = best.get("session")
            t["deep_curl"]  = best.get("deep_curl", False)
            t["vwap_tag"]   = best.get("vwap_tag")
            t["macd_hist"]  = best.get("macd_hist")
        else:
            t["grade"] = t["k"] = t["vol_ratio"] = t["session"] = t["deep_curl"] = t["vwap_tag"] = t["macd_hist"] = None

    return trades


# ── Stats helpers ─────────────────────────────────────────────────────────────

def _winrate(trades: list[dict]) -> tuple[float, int, int]:
    wins = sum(1 for t in trades if t["win"])
    return (wins / len(trades) * 100 if trades else 0.0, wins, len(trades))


def _avg_pnl(trades: list[dict]) -> float:
    return sum(t["pnl_pct"] for t in trades) / len(trades) if trades else 0.0


def _bucket(val: float | None, boundaries: list[float], labels: list[str]) -> str:
    if val is None:
        return "unknown"
    for b, label in zip(boundaries, labels):
        if val <= b:
            return label
    return labels[-1]


# ── Generate improvement recommendations ─────────────────────────────────────

def generate_recommendations(trades: list[dict]) -> list[dict]:
    """
    Analyse what's winning vs losing and return a list of recommendations.
    Each recommendation has: category, finding, suggestion, confidence, data_points.
    """
    recs: list[dict] = []
    enriched = [t for t in trades if t.get("grade") is not None]

    # ── Grade analysis ──
    for grade in ["A+", "A", "B", "C"]:
        g_trades = [t for t in enriched if t.get("grade") == grade]
        if len(g_trades) >= 3:
            wr, wins, total = _winrate(g_trades)
            avg = _avg_pnl(g_trades)
            if wr < 60 and total >= 5:
                recs.append({
                    "category": "grade_gate",
                    "finding":  f"Grade {grade}: {wr:.0f}% WR over {total} trades (avg {avg:+.1f}%)",
                    "suggestion": f"Consider disabling auto-buy for grade {grade} "
                                  f"(add '{grade}' to EDGE_BLOCKED_GRADES in config)",
                    "confidence": "high" if total >= 10 else "medium",
                    "data_points": total,
                })
            elif wr >= 80 and avg >= 20:
                recs.append({
                    "category": "grade_strength",
                    "finding":  f"Grade {grade}: {wr:.0f}% WR over {total} trades (avg {avg:+.1f}%)",
                    "suggestion": f"Grade {grade} is strongest — consider increasing DOLLARS_BY_GRADE['{grade}'] slightly",
                    "confidence": "medium",
                    "data_points": total,
                })

    # ── Session analysis ──
    for sess in ["premarket", "open", "midday", "power hour", "after-hours"]:
        s_trades = [t for t in enriched if t.get("session") == sess]
        if len(s_trades) >= 3:
            wr, wins, total = _winrate(s_trades)
            avg = _avg_pnl(s_trades)
            if wr < 55 and total >= 5:
                recs.append({
                    "category": "session_gate",
                    "finding":  f"{sess}: {wr:.0f}% WR over {total} trades (avg {avg:+.1f}%)",
                    "suggestion": f"Session '{sess}' underperforming — "
                                  f"consider tightening entry criteria or avoiding it",
                    "confidence": "high" if total >= 10 else "medium",
                    "data_points": total,
                })

    # ── Deep curl analysis ──
    dc_trades  = [t for t in enriched if t.get("deep_curl")]
    ndc_trades = [t for t in enriched if not t.get("deep_curl")]
    if len(dc_trades) >= 3 and len(ndc_trades) >= 3:
        dc_wr  = _winrate(dc_trades)[0]
        ndc_wr = _winrate(ndc_trades)[0]
        if dc_wr > ndc_wr + 15:
            recs.append({
                "category": "deep_curl",
                "finding":  f"Deep-curl entries: {dc_wr:.0f}% WR vs non-deep-curl: {ndc_wr:.0f}% WR",
                "suggestion": "Deep-curl is clearly stronger — consider increasing A+ grade sizing or requiring deep-curl for lower grades",
                "confidence": "high",
                "data_points": len(dc_trades) + len(ndc_trades),
            })

    # ── StochRSI K at entry ──
    k_vals = [(t.get("k"), t["win"]) for t in enriched if t.get("k") is not None]
    if len(k_vals) >= 10:
        low_k  = [(k, w) for k, w in k_vals if k <= 30]
        high_k = [(k, w) for k, w in k_vals if k > 30]
        if low_k and high_k:
            low_wr  = sum(w for _, w in low_k)  / len(low_k)  * 100
            high_wr = sum(w for _, w in high_k) / len(high_k) * 100
            if low_wr > high_wr + 10 and len(low_k) >= 5:
                recs.append({
                    "category": "k_threshold",
                    "finding":  f"K≤30 at entry: {low_wr:.0f}% WR ({len(low_k)} trades) vs K>30: {high_wr:.0f}% WR ({len(high_k)} trades)",
                    "suggestion": "Entries with deep-reset StochRSI (K≤30) win more — DEEP_CURL_RESET=30 is correct; consider preferring these in sizing",
                    "confidence": "medium",
                    "data_points": len(k_vals),
                })

    # ── Volume ratio ──
    vol_vals = [(t.get("vol_ratio"), t["win"]) for t in enriched if t.get("vol_ratio") is not None]
    if len(vol_vals) >= 10:
        high_vol = [(v, w) for v, w in vol_vals if v >= 2.0]
        low_vol  = [(v, w) for v, w in vol_vals if v < 2.0]
        if high_vol and low_vol:
            hv_wr = sum(w for _, w in high_vol) / len(high_vol) * 100
            lv_wr = sum(w for _, w in low_vol)  / len(low_vol)  * 100
            if hv_wr > lv_wr + 15 and len(high_vol) >= 5:
                recs.append({
                    "category": "volume_threshold",
                    "finding":  f"Vol≥2.0x: {hv_wr:.0f}% WR ({len(high_vol)} trades) vs Vol<2.0x: {lv_wr:.0f}% WR ({len(low_vol)} trades)",
                    "suggestion": "Higher volume at entry wins more — consider raising REL_VOL_MIN from 1.5 to 2.0 for non-A+ grades",
                    "confidence": "medium",
                    "data_points": len(vol_vals),
                })

    # ── Price range ──
    price_data = [(t["entry_price"], t["win"]) for t in trades]
    buckets = {
        "under_$1":   [(p, w) for p, w in price_data if p < 1.0],
        "$1–$5":      [(p, w) for p, w in price_data if 1.0 <= p < 5.0],
        "$5–$10":     [(p, w) for p, w in price_data if 5.0 <= p < 10.0],
        "$10–$15":    [(p, w) for p, w in price_data if 10.0 <= p < 15.0],
    }
    for label, items in buckets.items():
        if len(items) >= 5:
            wr = sum(w for _, w in items) / len(items) * 100
            if wr < 50:
                recs.append({
                    "category": "price_range",
                    "finding":  f"Price range {label}: {wr:.0f}% WR over {len(items)} trades",
                    "suggestion": f"Consider tightening {label} universe or requiring higher grade in that range",
                    "confidence": "medium",
                    "data_points": len(items),
                })

    return recs


# ── Print report ──────────────────────────────────────────────────────────────

def print_report(fills: list[dict], closed: list[dict], account: dict) -> None:
    equity   = float(account.get("equity") or 0)
    cash     = float(account.get("cash") or 0)
    day_pnl  = float(account.get("unrealized_intraday_pl") or 0)
    total_pnl= float(account.get("last_equity") or equity) - float(account.get("initial_equity") or equity)

    print(f"\n{'='*65}")
    print(f"  ALPACA PAPER ACCOUNT — FULL TRADE AUDIT")
    print(f"{'='*65}")
    print(f"  Equity: ${equity:,.2f}   Cash: ${cash:,.2f}   Day P&L: ${day_pnl:+,.2f}")
    print(f"  Total fills fetched: {len(fills)}")

    if not closed:
        print("\n  No completed round-trip trades found yet.")
        return

    wins = [t for t in closed if t["win"]]
    losses = [t for t in closed if not t["win"]]
    wr = len(wins) / len(closed) * 100
    avg_win  = sum(t["pnl_pct"] for t in wins)  / len(wins)  if wins   else 0
    avg_loss = sum(t["pnl_pct"] for t in losses) / len(losses) if losses else 0
    best = max(closed, key=lambda t: t["pnl_pct"])
    worst = min(closed, key=lambda t: t["pnl_pct"])
    total_usd = sum(t["pnl_usd"] for t in closed)

    print(f"\n── Overall stats ({len(closed)} closed positions) ──")
    print(f"  Win rate:  {wr:.1f}%  ({len(wins)}W / {len(losses)}L)")
    print(f"  Avg win:   {avg_win:+.1f}%   Avg loss: {avg_loss:+.1f}%")
    print(f"  Best:  {best['ticker']} {best['pnl_pct']:+.1f}%  (${best['pnl_usd']:+,.0f})")
    print(f"  Worst: {worst['ticker']} {worst['pnl_pct']:+.1f}%  (${worst['pnl_usd']:+,.0f})")
    print(f"  Total realized P&L: ${total_usd:+,.2f}")

    # By ticker
    by_ticker: dict[str, list] = defaultdict(list)
    for t in closed:
        by_ticker[t["ticker"]].append(t)
    sorted_tickers = sorted(by_ticker.items(), key=lambda x: len(x[1]), reverse=True)

    print(f"\n── Top tickers (sorted by trade count) ──")
    print(f"  {'Ticker':<8} {'Trades':>6} {'Win%':>6} {'Avg%':>7} {'$P&L':>9} {'Grades'}")
    for tk, trades in sorted_tickers[:20]:
        tw, _, tt = _winrate(trades)
        ta = _avg_pnl(trades)
        tu = sum(t["pnl_usd"] for t in trades)
        gs = ", ".join(sorted(set(t.get("grade") or "?" for t in trades)))
        print(f"  {tk:<8} {tt:>6} {tw:>5.0f}% {ta:>+6.1f}% {tu:>+9,.0f}  {gs}")

    # By grade
    enriched = [t for t in closed if t.get("grade")]
    if enriched:
        print(f"\n── By grade ──")
        for grade in ["A+", "A", "B", "C"]:
            gt = [t for t in enriched if t.get("grade") == grade]
            if gt:
                gw, gwin, gtot = _winrate(gt)
                ga = _avg_pnl(gt)
                gu = sum(t["pnl_usd"] for t in gt)
                dc = sum(1 for t in gt if t.get("deep_curl"))
                print(f"  [{grade}]  {gtot:>3} trades  {gw:>5.0f}% WR  avg {ga:+.1f}%  ${gu:+,.0f}  deep-curl: {dc}/{gtot}")

    # By session
    sess_trades = [t for t in closed if t.get("session")]
    if sess_trades:
        print(f"\n── By session ──")
        for sess in ["premarket", "open", "midday", "power hour", "after-hours"]:
            st = [t for t in sess_trades if t.get("session") == sess]
            if st:
                sw, _, stot = _winrate(st)
                sa = _avg_pnl(st)
                print(f"  {sess:<15}  {stot:>3} trades  {sw:>5.0f}% WR  avg {sa:+.1f}%")

    # Recent 15
    print(f"\n── Most recent 15 closed trades ──")
    print(f"  {'Date':<12} {'Ticker':<8} {'Entry':>7} {'Exit':>7} {'%':>7} {'$':>8} {'Grade'}")
    for t in sorted(closed, key=lambda x: x["exit_ts"])[-15:]:
        dt = t["exit_ts"][:10] if t["exit_ts"] else "—"
        grade = t.get("grade") or "?"
        star = "⭐" if t.get("deep_curl") else ""
        print(f"  {dt:<12} {t['ticker']:<8} ${t['entry_price']:>6.3f} ${t['exit_price']:>6.3f} "
              f"{t['pnl_pct']:>+6.1f}% {t['pnl_usd']:>+8,.0f}  [{grade}]{star}")


def print_recommendations(recs: list[dict]) -> None:
    if not recs:
        print(f"\n── Recommendations: none (insufficient data or all metrics strong) ──")
        return
    print(f"\n── Improvement Recommendations ({len(recs)}) ──")
    for i, r in enumerate(recs, 1):
        conf = {"high": "🔴 HIGH", "medium": "🟡 MED ", "low": "🟢 LOW "}.get(r["confidence"], "?")
        print(f"\n  {i}. [{conf}] {r['category'].upper()}")
        print(f"     Finding:    {r['finding']}")
        print(f"     Suggestion: {r['suggestion']}")
        print(f"     Data pts:   {r['data_points']}")


# ── Improvement log ───────────────────────────────────────────────────────────

def load_improvement_log() -> list[dict]:
    if IMPROVEMENT_LOG.exists():
        try:
            return json.loads(IMPROVEMENT_LOG.read_text())
        except Exception:
            return []
    return []


def save_improvement_log(recs: list[dict], stats: dict) -> None:
    log = load_improvement_log()
    entry = {
        "ts":     datetime.now(timezone.utc).isoformat(),
        "stats":  stats,
        "recommendations": recs,
    }
    log.append(entry)
    IMPROVEMENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    IMPROVEMENT_LOG.write_text(json.dumps(log, indent=2))
    print(f"\n  ✅ Recommendations saved to {IMPROVEMENT_LOG}")
    print(f"     (Run with --history to review all past entries)")


def print_history() -> None:
    log = load_improvement_log()
    if not log:
        print("No improvement log entries yet.")
        return
    print(f"\n{'='*65}")
    print(f"  IMPROVEMENT LOG — {len(log)} audit(s) on record")
    print(f"{'='*65}")
    for entry in log:
        ts   = entry["ts"][:16].replace("T", " ")
        stat = entry.get("stats", {})
        recs = entry.get("recommendations", [])
        wr   = stat.get("win_rate", 0)
        tot  = stat.get("total_trades", 0)
        print(f"\n  {ts}  |  {tot} trades  |  {wr:.1f}% WR  |  {len(recs)} recommendation(s)")
        for r in recs:
            conf = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(r.get("confidence"), "?")
            print(f"    {conf} {r['category']}: {r['finding']}")
            print(f"       → {r['suggestion']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Alpaca × Supabase trade audit")
    parser.add_argument("--json",    action="store_true", help="Dump raw Alpaca fills as JSON")
    parser.add_argument("--history", action="store_true", help="Print past improvement log")
    parser.add_argument("--apply",   action="store_true", help="(future) Auto-apply safe config fixes")
    args = parser.parse_args()

    if args.history:
        print_history()
        return

    if not ALPACA_KEY_ID or ALPACA_KEY_ID == "PASTE_YOUR_KEY_ID":
        print("ERROR: No Alpaca API key found in bot/config.py.")
        print("Run this script on the VPS or MacBook where config.py has real keys.")
        sys.exit(1)

    print("Fetching Alpaca fills...")
    try:
        fills   = fetch_fills()
        account = fetch_account()
    except Exception as e:
        print(f"ERROR fetching Alpaca data: {e}")
        sys.exit(1)

    if args.json:
        print(json.dumps(fills, indent=2))
        return

    print(f"Fetching Supabase entry data...")
    try:
        entries = fetch_supabase_entries()
    except Exception as e:
        print(f"WARNING: Could not fetch Supabase data ({e}) — trade enrichment skipped")
        entries = []

    print(f"Matching {len(fills)} fills into closed positions...")
    closed  = pair_trades(fills)
    closed  = enrich_with_supabase(closed, entries)

    print_report(fills, closed, account)

    recs = generate_recommendations(closed)
    print_recommendations(recs)

    # Save to improvement log
    wins = sum(1 for t in closed if t["win"])
    stats = {
        "total_fills":   len(fills),
        "total_trades":  len(closed),
        "wins":          wins,
        "losses":        len(closed) - wins,
        "win_rate":      round(wins / len(closed) * 100, 1) if closed else 0,
        "total_pnl_usd": round(sum(t["pnl_usd"] for t in closed), 2),
        "avg_win_pct":   round(sum(t["pnl_pct"] for t in closed if t["win"]) / wins, 1) if wins else 0,
    }
    save_improvement_log(recs, stats)


if __name__ == "__main__":
    main()
