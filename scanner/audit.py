"""
Self-Audit Engine — Curl if Flow System
Grades paper trades, tracks win rate progression, identifies patterns.

Closes open paper trades based on current price (or manual input).
Produces a daily/cumulative report showing what's working and what isn't.

Usage:
    python audit.py                          # full report on all paper trades
    python audit.py --close TICKER PRICE     # manually close a trade
    python audit.py --report                 # print current stats + pattern analysis
    python audit.py --grade TRADE_ID A+      # manually grade a trade
"""

import argparse
import json
import os
import sys
from datetime import datetime

import pytz

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("Run: pip install yfinance pandas")
    sys.exit(1)

ET = pytz.timezone("America/New_York")
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER_LOG_PATH = os.path.join(BASE_DIR, "data", "paper_trades.json")
HISTORICAL_PATH = os.path.join(BASE_DIR, "data", "trades-parsed.json")


# ── GRADING ───────────────────────────────────────────────────────────────────

def grade_trade(trade: dict) -> str:
    """
    Auto-grade a closed trade using W118's A+/A/B/C scale.
    A+: all conditions confirmed, perfect exits
    A:  all conditions, minor exit error
    B:  5 of 6 conditions, decent exits
    C:  4 or fewer conditions, or broke a rule
    """
    conds = trade.get("conditions", {})
    n_confirmed = sum(1 for v in conds.values() if v is True)
    catalyst_present = conds.get("catalyst") is not None

    # Penalty checks
    t1_hit = trade.get("t1_hit", False)
    be_moved = trade.get("stop_moved_be", False)

    if n_confirmed >= 5 and catalyst_present and t1_hit and be_moved:
        return "A+"
    if n_confirmed >= 5 and catalyst_present:
        return "A"
    if n_confirmed >= 4:
        return "B"
    return "C"


# ── CLOSE TRADE ───────────────────────────────────────────────────────────────

def close_trade(trade_id: str, exit_price: float, reason: str = "manual") -> bool:
    if not os.path.exists(PAPER_LOG_PATH):
        print("No paper trades file found.")
        return False

    with open(PAPER_LOG_PATH) as f:
        paper = json.load(f)

    found = False
    for t in paper["trades"]:
        if t["id"] == trade_id or t["ticker"] == trade_id:
            if t["status"] != "open":
                print(f"Trade {trade_id} is already closed.")
                continue
            entry = t["entry_price"]
            pct   = round((exit_price - entry) / entry * 100, 2)
            pnl   = round((exit_price - entry) * t["shares"], 2)
            t["exit_price"] = exit_price
            t["exit_time"]  = datetime.now(ET).isoformat()
            t["pct_gain"]   = pct
            t["pnl_usd"]    = pnl
            t["status"]     = "closed"
            t["result"]     = "win" if pct > 0 else "loss"
            t["exit_reason"] = reason

            # Check if T1/T2 were hit
            if exit_price >= t.get("t1_price", float("inf")):
                t["t1_hit"] = True
            if exit_price >= t.get("t2_price", float("inf")):
                t["t2_hit"] = True

            t["grade"] = grade_trade(t)
            found = True
            print(f"Closed {t['ticker']} @ ${exit_price} | {pct:+.1f}% | ${pnl:+.2f} | Grade: {t['grade']}")

    if found:
        _update_paper_stats(paper)
        with open(PAPER_LOG_PATH, "w") as f:
            json.dump(paper, f, indent=2)

    return found


def _update_paper_stats(paper: dict) -> None:
    trades  = paper["trades"]
    closed  = [t for t in trades if t["status"] == "closed"]
    wins    = [t for t in closed if t.get("result") == "win"]
    losses  = [t for t in closed if t.get("result") == "loss"]
    open_ct = len([t for t in trades if t["status"] == "open"])

    paper["stats"] = {
        "total_closed":   len(closed),
        "wins":           len(wins),
        "losses":         len(losses),
        "open":           open_ct,
        "win_rate_pct":   round(len(wins) / len(closed) * 100, 1) if closed else 0,
        "avg_winner_pct": round(sum(t["pct_gain"] for t in wins) / len(wins), 1) if wins else 0,
        "avg_loser_pct":  round(sum(t["pct_gain"] for t in losses) / len(losses), 1) if losses else 0,
        "total_pnl_usd":  round(sum(t.get("pnl_usd", 0) or 0 for t in closed), 2),
        "updated_at":     datetime.utcnow().isoformat() + "Z",
    }


# ── AUTO-CLOSE VIA YFINANCE ───────────────────────────────────────────────────

def auto_close_open_trades() -> None:
    """Try to close open trades using current yfinance price."""
    if not os.path.exists(PAPER_LOG_PATH):
        return
    with open(PAPER_LOG_PATH) as f:
        paper = json.load(f)

    open_trades = [t for t in paper["trades"] if t["status"] == "open"]
    if not open_trades:
        return

    print(f"\n[audit] Checking {len(open_trades)} open trades against current prices...")
    for t in open_trades:
        try:
            info = yf.Ticker(t["ticker"]).fast_info
            price = info.last_price
            if price:
                entry = t["entry_price"]
                pct   = (price - entry) / entry * 100
                stop  = t["stop_price"]
                t1    = t["t1_price"]
                t2    = t["t2_price"]

                print(f"  {t['ticker']}: entry=${entry} | now=${price:.4f} ({pct:+.1f}%)")
                if price <= stop:
                    print(f"    → STOP HIT — closing at ${price:.4f}")
                    close_trade(t["id"], price, "stop")
                elif price >= t2:
                    t["t1_hit"] = True
                    t["t2_hit"] = True
                    print(f"    → T2 hit — still open (trailing stop active)")
                elif price >= t1:
                    t["t1_hit"] = True
                    print(f"    → T1 hit — monitoring for T2/T3")
        except Exception as e:
            print(f"  {t['ticker']}: price check failed ({e})")


# ── PATTERN ANALYSIS ──────────────────────────────────────────────────────────

def analyze_patterns(trades: list[dict]) -> None:
    closed = [t for t in trades if t["status"] == "closed"]
    if not closed:
        print("No closed trades to analyze yet.")
        return

    wins   = [t for t in closed if t.get("result") == "win"]
    losses = [t for t in closed if t.get("result") == "loss"]

    print(f"\n{'═'*60}")
    print(f"PATTERN ANALYSIS — {len(closed)} closed trades")
    print(f"{'─'*60}")

    # Condition correlation
    conditions = ["stoch_curl", "k_above_d", "sha_green", "above_zlsma", "vol_surge", "catalyst"]
    print("\nCondition → Win Rate:")
    for cond in conditions:
        with_cond  = [t for t in closed if t.get("conditions", {}).get(cond)]
        without    = [t for t in closed if not t.get("conditions", {}).get(cond)]
        if with_cond:
            wr = sum(1 for t in with_cond if t.get("result") == "win") / len(with_cond) * 100
            print(f"  {cond:<15} present:  {len(with_cond):>3} trades | {wr:.0f}% win rate")
        if without:
            wr = sum(1 for t in without if t.get("result") == "win") / len(without) * 100
            print(f"  {cond:<15} ABSENT:   {len(without):>3} trades | {wr:.0f}% win rate")

    # K value at entry analysis
    if wins:
        avg_k_wins   = sum(t.get("stoch_k", 20) for t in wins) / len(wins)
        avg_pre_wins = sum(t.get("pre_k", 0)    for t in wins) / len(wins)
        print(f"\nStoch RSI K at entry (winners):  avg={avg_k_wins:.1f} | pre-K avg={avg_pre_wins:.1f}")
    if losses:
        avg_k_loss   = sum(t.get("stoch_k", 20) for t in losses) / len(losses)
        avg_pre_loss = sum(t.get("pre_k", 0)    for t in losses) / len(losses)
        print(f"Stoch RSI K at entry (losers):   avg={avg_k_loss:.1f} | pre-K avg={avg_pre_loss:.1f}")

    # Session analysis
    for session in ["PM", "RTH", "AH"]:
        sess_trades = [t for t in closed if t.get("session") == session]
        if sess_trades:
            wr = sum(1 for t in sess_trades if t.get("result") == "win") / len(sess_trades) * 100
            avg_gain = sum(t.get("pct_gain", 0) for t in sess_trades) / len(sess_trades)
            print(f"\n  {session} session: {len(sess_trades)} trades | {wr:.0f}% win | avg gain {avg_gain:+.1f}%")

    # Vol ratio
    if wins and losses:
        avg_vol_win  = sum(t.get("vol_ratio", 1) for t in wins) / len(wins)
        avg_vol_loss = sum(t.get("vol_ratio", 1) for t in losses) / len(losses)
        print(f"\nAvg volume ratio — winners: {avg_vol_win:.1f}x | losers: {avg_vol_loss:.1f}x")

    # Grade distribution
    grades = {}
    for t in closed:
        g = t.get("grade", "?")
        grades[g] = grades.get(g, 0) + 1
    print(f"\nGrade distribution: {grades}")
    print(f"{'═'*60}\n")


# ── FULL REPORT ───────────────────────────────────────────────────────────────

def print_report(paper: dict) -> None:
    stats  = paper.get("stats", {})
    trades = paper.get("trades", [])
    closed = [t for t in trades if t["status"] == "closed"]
    open_t = [t for t in trades if t["status"] == "open"]

    print(f"\n{'═'*60}")
    print(f"{'CURL IF FLOW — PAPER TRADING REPORT':^60}")
    print(f"{'═'*60}")
    print(f"  Closed trades:  {stats.get('total_closed', 0)}")
    print(f"  Win rate:       {stats.get('win_rate_pct', 0)}%  ({stats.get('wins',0)}W / {stats.get('losses',0)}L)")
    print(f"  Avg winner:     +{stats.get('avg_winner_pct', 0)}%")
    print(f"  Avg loser:      {stats.get('avg_loser_pct', 0)}%")
    print(f"  Total P&L:      ${stats.get('total_pnl_usd', 0):+.2f}")
    print(f"  Open positions: {stats.get('open', 0)}")

    # W118 comparison
    print(f"\n  vs W118 historical: 98.0% win rate | avg winner +53.7%")
    our_wr = stats.get("win_rate_pct", 0)
    gap    = 98.0 - our_wr
    print(f"  Gap to close:   {gap:.1f}% win rate")

    if open_t:
        print(f"\n{'─'*60}")
        print(f"OPEN POSITIONS ({len(open_t)})")
        for t in open_t:
            print(f"  {t['ticker']:<6} entry=${t['entry_price']} | "
                  f"stop=${t['stop_price']} T1=${t['t1_price']} T2=${t['t2_price']}")

    if closed:
        print(f"\n{'─'*60}")
        print(f"RECENT CLOSED TRADES")
        for t in sorted(closed, key=lambda x: x.get("exit_time",""), reverse=True)[:10]:
            pct   = t.get("pct_gain", 0) or 0
            grade = t.get("grade", "?")
            print(f"  {t['ticker']:<6} {pct:>+6.1f}%  Grade:{grade}  [{t.get('session','?')}]  "
                  f"K={t.get('stoch_k','?')} pre-K={t.get('pre_k','?')}")

    analyze_patterns(trades)


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Curl if Flow — Self Audit")
    parser.add_argument("--close", nargs=2, metavar=("TICKER_OR_ID", "PRICE"),
                        help="Close a trade: --close TICKER EXIT_PRICE")
    parser.add_argument("--grade", nargs=2, metavar=("TRADE_ID", "GRADE"),
                        help="Manually set grade: --grade TRADE_ID A+")
    parser.add_argument("--auto-close", action="store_true",
                        help="Auto-close open trades using current yfinance price")
    parser.add_argument("--report", action="store_true", help="Print full report")
    args = parser.parse_args()

    if not os.path.exists(PAPER_LOG_PATH):
        print("No paper trades yet. Run signal_monitor.py to start logging trades.")
        sys.exit(0)

    with open(PAPER_LOG_PATH) as f:
        paper = json.load(f)

    if args.close:
        close_trade(args.close[0], float(args.close[1]))

    if args.grade:
        for t in paper["trades"]:
            if t["id"] == args.grade[0] or t["ticker"] == args.grade[0]:
                t["grade"] = args.grade[1]
                print(f"Graded {t['ticker']} as {args.grade[1]}")
        with open(PAPER_LOG_PATH, "w") as f:
            json.dump(paper, f, indent=2)

    if args.auto_close:
        auto_close_open_trades()
        with open(PAPER_LOG_PATH) as f:
            paper = json.load(f)

    # Always print report
    print_report(paper)


if __name__ == "__main__":
    main()
