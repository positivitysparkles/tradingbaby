"""
Quick status check — shows current positions, today's trades, open orders.
Usage: python bot/status.py
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import ALPACA_KEY_ID, ALPACA_SECRET_KEY, ALPACA_BASE_URL, ALPACA_DATA_URL
import requests

_HDR = {
    "APCA-API-KEY-ID":     ALPACA_KEY_ID,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
}

def _get(path: str):
    base = ALPACA_DATA_URL if path.startswith("/v2/stocks/") else ALPACA_BASE_URL
    r = requests.get(base + path, headers=_HDR, timeout=10)
    r.raise_for_status()
    return r.json()

def main():
    print("\n" + "=" * 50)
    print("  W118 Bot Status")
    print("=" * 50)

    # Positions
    positions = _get("/v2/positions")
    print(f"\n📍 Open Positions ({len(positions)}):")
    if positions:
        for p in positions:
            pl = float(p.get("unrealized_pl") or 0)
            pct = float(p.get("unrealized_plpc") or 0) * 100
            print(f"   {p['symbol']:8} {p['qty']:4} shares  ${float(p['current_price']):.4f}  P&L ${pl:+.2f} ({pct:+.1f}%)")
    else:
        print("   (none)")

    # Open orders
    orders = _get("/v2/orders?status=open&limit=50")
    print(f"\n📋 Open Orders ({len(orders)}):")
    for o in orders[:10]:
        price = o.get("limit_price") or o.get("stop_price") or "market"
        print(f"   {o['symbol']:8} {o['side']:4} {o['qty']:4} @ {price}  [{o['type']}]")
    if len(orders) > 10:
        print(f"   ... and {len(orders)-10} more")

    # Today's trades
    log_path = Path(__file__).parent.parent / "data" / "trade_log.json"
    if log_path.exists():
        data = json.loads(log_path.read_text())
        today = date.today().isoformat()
        today_trades = [t for t in data["trades"] if t.get("date") == today]
        print(f"\n📈 Today's Entries ({len(today_trades)}):")
        for t in today_trades:
            print(f"   {t['time']}  {t['ticker']:8} @ ${t['entry']}  stop ${t['stop']}  T1 ${t['t1']}")
        if not today_trades:
            print("   (none yet)")

    # Account value
    try:
        acct = _get("/v2/account")
        print(f"\n💰 Paper Account: ${float(acct['portfolio_value']):,.2f}  "
              f"(cash ${float(acct['cash']):,.2f})")
    except Exception:
        pass

    print()

if __name__ == "__main__":
    main()
