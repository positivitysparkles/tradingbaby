"""
W118 Curl if Flow — Autonomous Paper Trading Bot
================================================
Runs continuously. Active 4am–11am ET. Finds NASDAQ small-cap momentum
setups, executes on Alpaca paper account, self-audits daily at 4:30pm ET.

Quick start:
  pip install requests schedule
  # Edit config.py → paste Alpaca keys + Telegram token
  python bot/bot.py

No FMP key, no extra signups. Uses Yahoo Finance (free) + Alpaca IEX data.
"""

import json
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
import schedule

# ── Bootstrap path so we can import siblings ─────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ALPACA_KEY_ID, ALPACA_SECRET_KEY, ALPACA_BASE_URL, ALPACA_DATA_URL,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
    MAX_DAILY_TRADES, MAX_POSITIONS, SHARES_PER_TRADE,
    STOP_PCT, T1_PCT, T2_PCT, T3_PCT, T1_SHARES, T2_SHARES, T3_SHARES,
    MIN_PRICE, MAX_PRICE, MIN_CHANGE_PCT, MIN_ABS_VOLUME, REL_VOL_MIN,
    SCAN_INTERVAL_MIN, GATE_OPEN_UTC, GATE_CLOSE_UTC,
)
from indicators import check_all_entry, check_exit_signal

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("w118")

ET  = timezone(timedelta(hours=-4))   # EDT. Change to -5 after Nov daylight saving.
UTC = timezone.utc

DATA_DIR   = Path(__file__).parent.parent / "data"
TRADE_LOG  = DATA_DIR / "trade_log.json"
MANUAL_WL  = DATA_DIR / "watchlist.json"

# ── Alpaca REST helpers ───────────────────────────────────────────────────────

_HDR = {
    "APCA-API-KEY-ID":     ALPACA_KEY_ID,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
    "Content-Type":        "application/json",
}

def _alpaca(method: str, path: str, **kwargs) -> dict | list:
    base = ALPACA_DATA_URL if path.startswith("/v2/stocks/") else ALPACA_BASE_URL
    r = requests.request(method, base + path, headers=_HDR, timeout=15, **kwargs)
    r.raise_for_status()
    return r.json()

def get_positions() -> list:
    try:
        return _alpaca("GET", "/v2/positions")
    except Exception as e:
        log.warning(f"get_positions: {e}")
        return []

def get_held() -> set:
    return {p["symbol"] for p in get_positions()}

def get_open_orders() -> list:
    try:
        return _alpaca("GET", "/v2/orders?status=open&limit=200")
    except Exception:
        return []

def cancel_ticker_orders(ticker: str):
    for o in get_open_orders():
        if o["symbol"] == ticker:
            try:
                _alpaca("DELETE", f"/v2/orders/{o['id']}")
            except Exception:
                pass

def get_bars(ticker: str, limit: int = 100) -> list | None:
    try:
        data = _alpaca("GET", f"/v2/stocks/{ticker}/bars",
                       params={"timeframe": "5Min", "limit": limit,
                               "feed": "iex", "adjustment": "raw"})
        bars = data.get("bars") or []
        return bars if len(bars) >= 50 else None
    except Exception as e:
        log.debug(f"bars {ticker}: {e}")
        return None

def place_order(ticker: str, qty: int, side: str, otype: str,
                limit_price: float = None, stop_price: float = None,
                tif: str = "gtc") -> bool:
    body: dict = {"symbol": ticker, "qty": qty, "side": side,
                  "type": otype, "time_in_force": tif}
    if limit_price:
        body["limit_price"] = str(round(limit_price, 2))
    if stop_price:
        body["stop_price"] = str(round(stop_price, 2))
    try:
        _alpaca("POST", "/v2/orders", json=body)
        return True
    except Exception as e:
        log.error(f"order {ticker} {side} {otype}: {e}")
        return False

def market_sell_position(ticker: str) -> bool:
    cancel_ticker_orders(ticker)
    for p in get_positions():
        if p["symbol"] == ticker:
            qty = abs(int(float(p["qty"])))
            if qty > 0:
                return place_order(ticker, qty, "sell", "market", tif="day")
    return False

# ── Telegram ──────────────────────────────────────────────────────────────────

def tg(msg: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=8,
        )
    except Exception as e:
        log.warning(f"Telegram: {e}")

# ── Stock discovery ───────────────────────────────────────────────────────────

def _yahoo_gainers() -> list[str]:
    """Free Yahoo Finance predefined screener — no API key needed."""
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved",
            params={"scrIds": "day_gainers", "count": 50,
                    "formatted": "false", "lang": "en-US", "region": "US"},
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            timeout=12,
        )
        quotes = r.json()["finance"]["result"][0]["quotes"]
        tickers = []
        for q in quotes:
            price = q.get("regularMarketPrice") or 0
            chg   = q.get("regularMarketChangePercent") or 0
            vol   = q.get("regularMarketVolume") or 0
            exch  = q.get("fullExchangeName") or ""
            if not (MIN_PRICE <= price <= MAX_PRICE):
                continue
            if chg < MIN_CHANGE_PCT:
                continue
            if vol < MIN_ABS_VOLUME:
                continue
            if not any(x in exch for x in ("NASDAQ", "Nasdaq")):
                continue
            tickers.append(q["symbol"])
            if len(tickers) >= 25:
                break
        log.info(f"[discovery] Yahoo: {len(tickers)} candidates")
        return tickers
    except Exception as e:
        log.warning(f"[discovery] Yahoo failed: {e}")
        return []

def _manual_watchlist() -> list[str]:
    """Tickers added manually via add_ticker.py — today's list only."""
    if not MANUAL_WL.exists():
        return []
    try:
        data = json.loads(MANUAL_WL.read_text())
        if data.get("date") != date.today().isoformat():
            return []
        return [s["ticker"] for s in data.get("stocks", [])]
    except Exception:
        return []

def discover() -> list[str]:
    manual = _manual_watchlist()
    auto   = _yahoo_gainers()
    seen, result = set(), []
    for t in (manual + auto):   # manual list gets priority
        if t not in seen:
            seen.add(t); result.append(t)
    return result

# ── Trade log ─────────────────────────────────────────────────────────────────

def _load_log() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if TRADE_LOG.exists():
        try:
            return json.loads(TRADE_LOG.read_text())
        except Exception:
            pass
    return {"trades": []}

def _save_log(data: dict):
    TRADE_LOG.write_text(json.dumps(data, indent=2))

def trades_today() -> int:
    today = date.today().isoformat()
    return sum(1 for t in _load_log()["trades"] if t.get("date") == today)

def log_trade(ticker: str, price: float, info: dict):
    data = _load_log()
    data["trades"].append({
        "date":      date.today().isoformat(),
        "time":      datetime.now(ET).strftime("%H:%M ET"),
        "ticker":    ticker,
        "entry":     price,
        "stop":      round(price * (1 - STOP_PCT), 4),
        "t1":        round(price * (1 + T1_PCT), 4),
        "t2":        round(price * (1 + T2_PCT), 4),
        "t3":        round(price * (1 + T3_PCT), 4),
        "signals":   info,
        "status":    "open",
    })
    _save_log(data)

# ── Trade execution ───────────────────────────────────────────────────────────

def execute_buy(ticker: str, price: float, info: dict):
    stop = round(price * (1 - STOP_PCT), 2)
    t1   = round(price * (1 + T1_PCT), 2)
    t2   = round(price * (1 + T2_PCT), 2)
    t3   = round(price * (1 + T3_PCT), 2)

    ok = place_order(ticker, SHARES_PER_TRADE, "buy", "market", tif="day")
    if not ok:
        log.error(f"[buy] BUY order failed for {ticker}")
        return

    # Bracket orders
    place_order(ticker, SHARES_PER_TRADE, "sell", "stop",  stop_price=stop)
    place_order(ticker, T1_SHARES,        "sell", "limit", limit_price=t1)
    place_order(ticker, T2_SHARES,        "sell", "limit", limit_price=t2)
    place_order(ticker, T3_SHARES,        "sell", "limit", limit_price=t3)

    log_trade(ticker, price, info)

    msg = (
        f"<b>🟢 W118 AUTO BUY — {ticker}</b>\n"
        f"Entry: ${price:.4f}  ×{SHARES_PER_TRADE} shares\n"
        f"K={info['k']}  D={info['d']}  MACD={info['macd_hist']:.5f}  Vol {info['vol_ratio']}x\n"
        f"🛑 Stop:  ${stop}  (-8%)\n"
        f"🎯 T1: ${t1}  (+15%)  ×{T1_SHARES}\n"
        f"   T2: ${t2}  (+30%)  ×{T2_SHARES}\n"
        f"   T3: ${t3}  (+60%)  ×{T3_SHARES}"
    )
    tg(msg)
    log.info(f"[buy] {ticker} @ ${price}  stop=${stop}  T1=${t1}  T2=${t2}  T3=${t3}")

def execute_exit(ticker: str, reason: str):
    sold = market_sell_position(ticker)
    if sold:
        tg(f"<b>🔴 W118 EXIT — {ticker}</b>\nReason: {reason}")
        log.info(f"[exit] {ticker}: {reason}")

# ── Self-audit ────────────────────────────────────────────────────────────────

def daily_audit():
    today = date.today().isoformat()
    log_data = _load_log()
    today_trades = [t for t in log_data["trades"] if t.get("date") == today]

    try:
        all_orders = _alpaca("GET", f"/v2/orders?status=all&limit=100&after={today}T00:00:00Z")
        buys  = [o for o in all_orders if o["side"] == "buy"  and o["status"] in ("filled", "partially_filled")]
        sells = [o for o in all_orders if o["side"] == "sell" and o["status"] in ("filled", "partially_filled")]
    except Exception:
        buys = sells = []

    positions = get_positions()
    pos_lines = ""
    for p in positions:
        pl = float(p.get("unrealized_pl") or 0)
        pos_lines += f"  {p['symbol']}: {p['qty']} shares  P&L ${pl:+.2f}\n"

    trades_lines = ""
    for t in today_trades:
        trades_lines += f"  {t['time']} {t['ticker']} @ ${t['entry']}  stop ${t['stop']}  T1 ${t['t1']}\n"

    msg = (
        f"<b>📊 W118 Daily Audit — {today}</b>\n"
        f"Trades fired: {len(today_trades)} / {MAX_DAILY_TRADES} limit\n"
        f"Buy fills: {len(buys)}  |  Sell fills: {len(sells)}\n"
        f"Open positions: {len(positions)}\n"
    )
    if pos_lines:
        msg += f"\n<b>Open now:</b>\n{pos_lines}"
    if trades_lines:
        msg += f"\n<b>Today's entries:</b>\n{trades_lines}"

    tg(msg)
    log.info("[audit] Daily audit sent to Telegram")

def weekly_audit():
    log_data = _load_log()
    trades   = log_data["trades"]
    if not trades:
        tg("📊 Weekly audit: no trades logged yet.")
        return

    # Pull Alpaca closed orders for win/loss calculation
    try:
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        orders = _alpaca("GET", f"/v2/orders?status=all&limit=500&after={week_ago}T00:00:00Z")
        sell_fills = [
            o for o in orders
            if o["side"] == "sell" and o["status"] in ("filled", "partially_filled")
        ]
    except Exception:
        sell_fills = []

    week_trades = [t for t in trades
                   if t.get("date", "") >= (date.today() - timedelta(days=7)).isoformat()]

    msg = (
        f"<b>📈 W118 Weekly Audit</b>\n"
        f"Entries this week: {len(week_trades)}\n"
        f"Sell orders filled: {len(sell_fills)}\n"
        f"Total logged trades: {len(trades)}\n"
        f"\nCheck alpaca.markets → Paper Trading → Account History for full P&L.\n"
        f"Compare win rate to 98% historical benchmark."
    )
    tg(msg)
    log.info("[audit] Weekly audit sent")

# ── Main scan loop ────────────────────────────────────────────────────────────

def _in_gate() -> bool:
    h = datetime.now(UTC).hour
    return GATE_OPEN_UTC <= h < GATE_CLOSE_UTC

def scan():
    if not _in_gate():
        return

    now = datetime.now(ET).strftime("%H:%M ET")
    log.info(f"[scan] ── {now} ─────────────────────────────────────")

    held = get_held()

    # Check signal exits on existing positions first
    for ticker in list(held):
        bars = get_bars(ticker, limit=60)
        if not bars:
            continue
        reason = check_exit_signal(bars)
        if reason:
            execute_exit(ticker, reason)
            held.discard(ticker)

    # Check trade + position caps before scanning for new entries
    if trades_today() >= MAX_DAILY_TRADES:
        log.info(f"[scan] Daily limit reached ({MAX_DAILY_TRADES}). No new entries.")
        return
    if len(held) >= MAX_POSITIONS:
        log.info(f"[scan] Position cap reached ({MAX_POSITIONS}). No new entries.")
        return

    candidates = discover()
    log.info(f"[scan] {len(candidates)} candidates → checking W118 conditions")

    for ticker in candidates:
        if ticker in held:
            continue
        if trades_today() >= MAX_DAILY_TRADES or len(get_held()) >= MAX_POSITIONS:
            break

        bars = get_bars(ticker)
        if not bars:
            continue

        ok, info = check_all_entry(bars, MIN_PRICE, MAX_PRICE, REL_VOL_MIN)
        if ok:
            log.info(f"[SIGNAL] {ticker} — ALL 5 CONDITIONS PASS: {info}")
            execute_buy(ticker, info["price"], info)
            held = get_held()
        else:
            log.debug(f"[skip] {ticker}: {info.get('fail', info)}")

        time.sleep(0.4)   # rate limit: ~40 reqs/min for 100 candidates max

    log.info(f"[scan] done. Positions: {len(get_held())} / {MAX_POSITIONS}")

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("  W118 Curl if Flow — Auto Paper Trading Bot")
    log.info(f"  Gate: {GATE_OPEN_UTC}:00–{GATE_CLOSE_UTC}:00 UTC  (4am–11am ET)")
    log.info(f"  Max {MAX_DAILY_TRADES} trades/day  |  {MAX_POSITIONS} positions max")
    log.info(f"  Scans every {SCAN_INTERVAL_MIN} min")
    log.info("=" * 60)

    # Validate keys are filled in
    if "PASTE" in ALPACA_KEY_ID or "PASTE" in ALPACA_SECRET_KEY:
        log.error("Fill in ALPACA_KEY_ID and ALPACA_SECRET_KEY in bot/config.py first.")
        sys.exit(1)
    if "PASTE" in TELEGRAM_TOKEN:
        log.error("Fill in TELEGRAM_TOKEN in bot/config.py first.")
        sys.exit(1)

    tg(
        f"🤖 <b>W118 Bot started</b>\n"
        f"Gate: 4am–11am ET  |  Max {MAX_DAILY_TRADES} trades/day\n"
        f"Universe: NASDAQ $0.10–$5, vol>1M, chg>10%, relVol>{REL_VOL_MIN}x\n"
        f"Conditions: Supertrend ✓ K>D ✓ price>ZLSMA ✓ MACD>0 ✓ vol>4x"
    )

    schedule.every(SCAN_INTERVAL_MIN).minutes.do(scan)
    schedule.every().day.at("20:30").do(daily_audit)    # 4:30pm ET = 20:30 UTC
    schedule.every().monday.at("21:00").do(weekly_audit) # Monday 5pm ET

    scan()  # run once immediately on startup

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
