#!/usr/bin/env python3
"""
discord_parser.py — Weatherman118 Discord recap parser
Parses: $TICKER\nEntry X.XX PM → High X.XX = +XX%
CLI: python discord_parser.py input.txt [--output trades.json] [--dump-historical]
"""
import re
import json
import sys
import argparse
from datetime import date

HISTORICAL_TRADES = [
    {"date":"2026-04-27","ticker":"YAAS","entry_price":1.20,"session":"PM","high":1.59,"pct_gain":33.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-27","ticker":"YAAS","entry_price":1.37,"session":"RTH","high":2.57,"pct_gain":87.6,"result":"win","is_re_entry":True,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-27","ticker":"SGMT","entry_price":8.13,"session":"PM","high":9.00,"pct_gain":10.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-27","ticker":"SGMT","entry_price":7.60,"session":"RTH","high":9.37,"pct_gain":25.0,"result":"win","is_re_entry":True,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-27","ticker":"USEG","entry_price":1.32,"session":"PM","high":1.65,"pct_gain":25.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-27","ticker":"CYCU","entry_price":1.20,"session":"PM","high":1.40,"pct_gain":16.0,"result":"loss","is_re_entry":False,"multi_entry":False,"source":"recap","note":"Closed with minor loss"},
    {"date":"2026-04-27","ticker":"ASBP","entry_price":0.25,"session":"RTH","high":0.309,"pct_gain":23.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-27","ticker":"ELPW","entry_price":3.85,"session":"RTH","high":4.89,"pct_gain":27.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-27","ticker":"SKLZ","entry_price":8.25,"session":"RTH","high":9.06,"pct_gain":10.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-27","ticker":"PAPL","entry_price":1.25,"session":"RTH","high":1.53,"pct_gain":22.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"BBBY","entry_price":6.45,"session":"PM","high":7.70,"pct_gain":20.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"KIDZ","entry_price":1.10,"session":"PM","high":1.44,"pct_gain":30.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"SKYQ","entry_price":7.00,"session":"PM","high":7.73,"pct_gain":10.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"SAFX","entry_price":0.45,"session":"PM","high":0.53,"pct_gain":18.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"NEXR","entry_price":3.50,"session":"PM","high":4.06,"pct_gain":16.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"SNBR","entry_price":2.70,"session":"PM","high":3.25,"pct_gain":20.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"SNBR","entry_price":2.80,"session":"RTH","high":4.24,"pct_gain":51.0,"result":"win","is_re_entry":True,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"BIYA","entry_price":1.28,"session":"PM","high":1.44,"pct_gain":12.5,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"BIYA","entry_price":1.28,"session":"RTH","high":2.19,"pct_gain":72.0,"result":"win","is_re_entry":True,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"SBLX","entry_price":3.60,"session":"PM","high":5.06,"pct_gain":40.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-28","ticker":"AKAN","entry_price":5.60,"session":"PM","high":29.50,"pct_gain":426.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap","note":"initial alert, multiday runner"},
    {"date":"2026-04-28","ticker":"ATER","entry_price":1.00,"session":"RTH","high":1.87,"pct_gain":87.0,"result":"win","is_re_entry":False,"multi_entry":True,"source":"recap"},
    {"date":"2026-04-28","ticker":"SEGG","entry_price":1.30,"session":"RTH","high":1.56,"pct_gain":20.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-29","ticker":"INHD","entry_price":0.10,"session":"PM","high":0.1599,"pct_gain":60.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-29","ticker":"GCTK","entry_price":1.14,"session":"PM","high":1.26,"pct_gain":10.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-29","ticker":"GCTK","entry_price":1.07,"session":"PM","high":1.28,"pct_gain":20.0,"result":"win","is_re_entry":True,"multi_entry":True,"source":"recap"},
    {"date":"2026-04-29","ticker":"SAGT","entry_price":2.06,"session":"PM","high":3.36,"pct_gain":63.0,"result":"win","is_re_entry":False,"multi_entry":True,"source":"recap"},
    {"date":"2026-04-29","ticker":"PAPL","entry_price":1.70,"session":"RTH","high":2.06,"pct_gain":21.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-29","ticker":"SEGG","entry_price":1.30,"session":"RTH","high":1.63,"pct_gain":25.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-29","ticker":"AIXI","entry_price":0.90,"session":"PM","high":1.15,"pct_gain":28.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-29","ticker":"AKAN","entry_price":21.85,"session":"RTH","high":31.70,"pct_gain":45.0,"result":"win","is_re_entry":True,"multi_entry":False,"source":"recap","note":"multiday runner"},
    {"date":"2026-04-29","ticker":"XTLB","entry_price":4.00,"session":"RTH","high":4.52,"pct_gain":12.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-29","ticker":"XTLB","entry_price":3.48,"session":"RTH","high":4.24,"pct_gain":21.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-29","ticker":"XTLB","entry_price":3.48,"session":"RTH","high":4.87,"pct_gain":40.0,"result":"win","is_re_entry":True,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-30","ticker":"ABTS","entry_price":1.60,"session":"PM","high":1.78,"pct_gain":11.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-30","ticker":"OSRH","entry_price":0.50,"session":"PM","high":0.58,"pct_gain":16.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-30","ticker":"AKAN","entry_price":23.95,"session":"PM","high":39.10,"pct_gain":63.0,"result":"win","is_re_entry":True,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-30","ticker":"BIYA","entry_price":2.07,"session":"PM","high":2.42,"pct_gain":17.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-30","ticker":"FATN","entry_price":2.75,"session":"PM","high":3.76,"pct_gain":36.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-30","ticker":"HCAI","entry_price":10.90,"session":"PM","high":14.45,"pct_gain":32.0,"result":"win","is_re_entry":False,"multi_entry":True,"source":"recap"},
    {"date":"2026-04-30","ticker":"CANF","entry_price":3.65,"session":"RTH","high":4.08,"pct_gain":11.0,"result":"loss","is_re_entry":False,"multi_entry":True,"source":"recap","note":"Closed little under BE"},
    {"date":"2026-04-30","ticker":"BIYA","entry_price":2.07,"session":"PM","high":2.50,"pct_gain":20.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-30","ticker":"OSRH","entry_price":0.59,"session":"RTH","high":0.8414,"pct_gain":42.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-04-30","ticker":"AKAN","entry_price":36.17,"session":"RTH","high":64.00,"pct_gain":77.0,"result":"win","is_re_entry":True,"multi_entry":False,"source":"recap","note":"up 1667% from PM entry, 1063% from initial 5.50"},
    {"date":"2026-03-23","ticker":"BCG","entry_price":2.95,"session":"PM","high":3.83,"pct_gain":30.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-03-23","ticker":"CYCN","entry_price":2.10,"session":"PM","high":8.48,"pct_gain":304.0,"result":"win","is_re_entry":False,"multi_entry":True,"source":"recap","note":"initial 2.10/2.35, adds at 5.65"},
    {"date":"2026-03-23","ticker":"UCAR","entry_price":0.65,"session":"RTH","high":0.88,"pct_gain":35.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-03-23","ticker":"RENX","entry_price":2.60,"session":"RTH","high":3.48,"pct_gain":35.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-03-24","ticker":"MASK","entry_price":1.80,"session":"RTH","high":3.32,"pct_gain":85.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap"},
    {"date":"2026-03-24","ticker":"POLA","entry_price":2.10,"session":"RTH","high":2.89,"pct_gain":37.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap","note":"guidance for team"},
    {"date":"2026-03-24","ticker":"OXBR","entry_price":1.05,"session":"PM","high":1.41,"pct_gain":34.0,"result":"win","is_re_entry":False,"multi_entry":False,"source":"recap","note":"guidance for team"},
    {"date":"2026-03-24","ticker":"ELAB","entry_price":2.90,"session":"PM","high":8.57,"pct_gain":195.0,"result":"win","is_re_entry":True,"multi_entry":True,"source":"recap","note":"initial 2.90, adds at 4.00"},
]

TICKER_RE   = re.compile(r'^\$([A-Z]{1,6})\s*$', re.MULTILINE)
ENTRY_RE    = re.compile(
    r'[Ee]ntr(?:y|ies)\s+([\d.]+)\s+'
    r'(PM|RTH|AH|Premarket|Power\s*Hr|Power\s*Hour)\s*'
    r'(?:[-–→]+\s*)?'
    r'(?:[Hh]igh\s*)?([\d.]+)\s*=\s*\+?([\d.]+)%',
    re.IGNORECASE
)
REENTRY_RE  = re.compile(r're.?entr', re.IGNORECASE)
DATE_RE     = re.compile(r'(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})')


def normalise_session(raw: str) -> str:
    raw = raw.strip().upper().replace(" ", "")
    if raw in ("PM", "PREMARKET"):
        return "PM"
    if raw in ("POWERHOUR", "POWERHR"):
        return "Power Hr"
    return "RTH"


def parse_date(text: str) -> str:
    m = DATE_RE.search(text)
    if not m:
        return str(date.today())
    d = m.group(1)
    if "-" in d:
        return d
    parts = d.replace("/", "-").split("-")
    if len(parts[2]) == 2:
        parts[2] = "20" + parts[2]
    return f"{parts[2]}-{int(parts[0]):02d}-{int(parts[1]):02d}"


def parse_text(text: str, trade_date: str | None = None) -> list[dict]:
    trades = []
    blocks = re.split(r'\n{2,}', text.strip())
    for block in blocks:
        ticker_m = TICKER_RE.search(block)
        if not ticker_m:
            continue
        ticker = ticker_m.group(1)
        block_date = trade_date or parse_date(block)
        is_re = bool(REENTRY_RE.search(block))
        for entry_m in ENTRY_RE.finditer(block):
            trade = {
                "date":        block_date,
                "ticker":      ticker,
                "entry_price": float(entry_m.group(1)),
                "session":     normalise_session(entry_m.group(2)),
                "high":        float(entry_m.group(3)),
                "pct_gain":    float(entry_m.group(4)),
                "result":      "win" if float(entry_m.group(4)) > 0 else "loss",
                "is_re_entry": is_re,
                "multi_entry": False,
                "source":      "recap",
            }
            trades.append(trade)
    return trades


def compute_stats(trades: list[dict]) -> dict:
    wins   = [t for t in trades if t["result"] == "win"]
    losses = [t for t in trades if t["result"] == "loss"]
    pm     = [t for t in wins   if t["session"] == "PM"]
    rth    = [t for t in wins   if t["session"] == "RTH"]
    best   = max(trades, key=lambda t: t["pct_gain"], default=None)
    return {
        "total_trades":   len(trades),
        "wins":           len(wins),
        "losses":         len(losses),
        "win_rate_pct":   round(len(wins) / len(trades) * 100, 1) if trades else 0,
        "avg_winner_pct": round(sum(t["pct_gain"] for t in wins)   / len(wins),   1) if wins   else 0,
        "avg_loser_pct":  round(sum(t["pct_gain"] for t in losses) / len(losses), 1) if losses else 0,
        "pm_wins":        len(pm),
        "rth_wins":       len(rth),
        "pm_win_pct":     round(len(pm) / len(wins) * 100, 1) if wins else 0,
        "best_trade":     f"{best['ticker']} +{best['pct_gain']}%" if best else "n/a",
    }


def main():
    parser = argparse.ArgumentParser(description="Parse W118 Discord recaps into JSON")
    parser.add_argument("input", nargs="?", help="Input text file (omit for stdin)")
    parser.add_argument("--output", "-o", default="-", help="Output JSON file (default: stdout)")
    parser.add_argument("--date",   "-d", help="Trade date override YYYY-MM-DD")
    parser.add_argument("--append", "-a", help="Existing JSON file to append new trades into")
    parser.add_argument("--dump-historical", action="store_true",
                        help="Dump the 52 embedded historical trades to output and exit")
    args = parser.parse_args()

    if args.dump_historical:
        out = {"trades": HISTORICAL_TRADES, "stats": compute_stats(HISTORICAL_TRADES)}
        _write(args.output, out)
        return

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    new_trades = parse_text(text, args.date)

    if args.append:
        try:
            with open(args.append, encoding="utf-8") as f:
                existing = json.load(f)
            all_trades = existing.get("trades", []) + new_trades
        except (FileNotFoundError, json.JSONDecodeError):
            all_trades = new_trades
    else:
        all_trades = new_trades

    out = {"trades": all_trades, "stats": compute_stats(all_trades)}
    _write(args.output, out)
    print(f"Parsed {len(new_trades)} new trade(s). Total: {len(all_trades)}.", file=sys.stderr)


def _write(path: str, data: dict):
    text = json.dumps(data, indent=2)
    if path == "-":
        print(text)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()
