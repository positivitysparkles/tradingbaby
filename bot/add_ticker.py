"""
Add tickers to today's watchlist for the bot to prioritize.
Usage: python bot/add_ticker.py AHMA JRSH CAST
The bot checks these FIRST before auto-discovery.
Resets automatically each day (date-gated).
"""
import json
import sys
from datetime import date
from pathlib import Path

WATCHLIST = Path(__file__).parent.parent / "data" / "watchlist.json"

def main():
    tickers = [t.upper() for t in sys.argv[1:] if t.strip()]
    if not tickers:
        print("Usage: python bot/add_ticker.py TICKER1 TICKER2 ...")
        sys.exit(1)

    WATCHLIST.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    if WATCHLIST.exists():
        try:
            data = json.loads(WATCHLIST.read_text())
            if data.get("date") != today:
                data = {"date": today, "stocks": []}
        except Exception:
            data = {"date": today, "stocks": []}
    else:
        data = {"date": today, "stocks": []}

    existing = {s["ticker"] for s in data["stocks"]}
    added = []
    for t in tickers:
        if t not in existing:
            data["stocks"].append({"ticker": t})
            added.append(t)

    WATCHLIST.write_text(json.dumps(data, indent=2))
    print(f"✅ Added: {added}")
    print(f"   Today's watchlist ({today}): {[s['ticker'] for s in data['stocks']]}")

if __name__ == "__main__":
    main()
