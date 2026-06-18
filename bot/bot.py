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

import html
import json
import logging
import os
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
import schedule

# ── Bootstrap path so we can import siblings ─────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ALPACA_KEY_ID, ALPACA_SECRET_KEY, ALPACA_BASE_URL, ALPACA_DATA_URL,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
    MAX_DAILY_TRADES, MAX_POSITIONS, DOLLARS_PER_TRADE,
    STOP_PCT, T1_PCT, T2_PCT, T3_PCT,
    MIN_PRICE, MAX_PRICE, MAX_FLOAT, MIN_CHANGE_PCT, MIN_ABS_VOLUME, REL_VOL_MIN,
    SCAN_INTERVAL_MIN, GATE_OPEN_UTC, GATE_CLOSE_UTC,
    AVOID_MIDDAY, MIDDAY_START_ET, MIDDAY_END_ET, DEEP_CURL_RESET,
    EXT_HOURS_LIMIT_BUFFER, REQUIRE_1M_FRESH,
)
from indicators import check_all_entry, check_exit_signal, is_fresh_1m

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

def get_latest_price(ticker: str) -> float | None:
    """Real-time last trade price from Alpaca IEX feed. Used to show a live quote
    in MANUAL SETUP alerts instead of the (potentially stale) bar close."""
    try:
        data = _alpaca("GET", f"/v2/stocks/{ticker}/trades/latest",
                       params={"feed": "iex"})
        return float(data["trade"]["p"])
    except Exception:
        return None

def is_tradeable(ticker: str) -> bool:
    """Check Alpaca asset status before buying. Returns False when the stock is
    halted, not listed, or otherwise untradeable — prevents wasted 422 attempts."""
    try:
        asset = _alpaca("GET", f"/v2/assets/{ticker}")
        if not asset.get("tradable"):
            log.info(f"[skip] {ticker} not tradeable on Alpaca (status={asset.get('status')})")
            return False
        return True
    except Exception as e:
        log.warning(f"[asset-check] {ticker}: {e} — allowing buy attempt")
        return True   # fail open: don't block on API errors

def get_bars(ticker: str, limit: int = 100, timeframe: str = "5Min") -> list | None:
    try:
        data = _alpaca("GET", f"/v2/stocks/{ticker}/bars",
                       params={"timeframe": timeframe, "limit": limit,
                               "feed": "sip", "adjustment": "raw"})
        bars = data.get("bars") or []
        if len(bars) < 30:
            log.debug(f"bars {ticker} ({timeframe}): only {len(bars)} bars (need 30), skip")
            return None
        return bars
    except Exception as e:
        log.debug(f"bars {ticker} ({timeframe}): {e}")
        return None

def place_order(ticker: str, qty: int, side: str, otype: str,
                limit_price: float = None, stop_price: float = None,
                tif: str = "gtc", extended_hours: bool = False) -> bool:
    body: dict = {"symbol": ticker, "qty": qty, "side": side,
                  "type": otype, "time_in_force": tif}
    if limit_price:
        body["limit_price"] = str(round(limit_price, 2))
    if stop_price:
        body["stop_price"] = str(round(stop_price, 2))
    # Alpaca only accepts extended_hours on LIMIT + DAY orders. Premarket/afterhours
    # market orders silently sit at "new" and never fill — this is the flag that
    # makes premarket entries actually execute.
    if extended_hours:
        body["extended_hours"] = True
    try:
        _alpaca("POST", "/v2/orders", json=body)
        return True
    except requests.HTTPError as e:
        # Log the full Alpaca error body so we know the exact rejection reason
        # (e.g. "asset not active", "insufficient buying power", "account restricted")
        try:
            detail = e.response.json().get("message", e.response.text[:200])
        except Exception:
            detail = str(e)
        log.error(f"order {ticker} {side} {otype}: {e.response.status_code} — {detail}")
        return False
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
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=8,
        )
        if not r.ok:
            log.warning(f"Telegram {r.status_code}: {r.text[:120]}")
        else:
            log.debug("Telegram OK")
    except Exception as e:
        log.warning(f"Telegram: {e}")

# ── Stock discovery ───────────────────────────────────────────────────────────

# Browser-like headers — TradingView's scanner rejects bare requests (403)
_TV_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Origin":  "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
    "Accept":  "application/json",
}

def _tv_session_fields() -> tuple[str, str, str]:
    """
    Pick the right TradingView change/volume columns for the current session.
    The default 'change'/'volume' columns are REGULAR-session only — useless
    premarket. Before 9:30 ET use premarket_*, after 16:00 ET use postmarket_*.
    Returns (change_field, volume_field, session_label).
    """
    now_et = datetime.now(ET)
    hm = now_et.hour * 60 + now_et.minute
    if hm < 9 * 60 + 30:            # before 9:30 ET → premarket (W118's best window)
        return "premarket_change", "premarket_volume", "premarket"
    if hm >= 16 * 60:              # 16:00 ET or later → postmarket
        return "postmarket_change", "postmarket_volume", "postmarket"
    return "change", "volume", "regular"


def _tradingview_screener() -> list[str]:
    """
    Primary discovery — TradingView's public scanner, the same engine behind the
    Yassss screener. No crumb/login, and (unlike Yahoo) not rate-limited from a
    data-center IP. Session-aware so it catches premarket and afterhours gappers.
    """
    chg_field, vol_field, sess = _tv_session_fields()
    try:
        filters = [
            {"left": chg_field,               "operation": "greater",  "right": MIN_CHANGE_PCT},
            {"left": "close",                 "operation": "in_range", "right": [MIN_PRICE, MAX_PRICE]},
            {"left": vol_field,               "operation": "greater",  "right": MIN_ABS_VOLUME},
            {"left": "float_shares_outstanding", "operation": "less",  "right": MAX_FLOAT},
        ]
        # rel_vol_10d is a regular-session metric — only meaningful 9:30–16:00 ET
        if sess == "regular":
            filters.append(
                {"left": "relative_volume_10d_calc", "operation": "greater", "right": REL_VOL_MIN}
            )
        body = {
            "filter":   filters,
            "options":  {"lang": "en"},
            "symbols":  {"query": {"types": []}, "tickers": []},
            "columns":  ["name", "close", chg_field, vol_field],
            "sort":     {"sortBy": chg_field, "sortOrder": "desc"},
            "range":    [0, 50],
            "markets":  ["america"],
        }
        r = requests.post(
            "https://scanner.tradingview.com/america/scan",
            json=body, headers=_TV_HEADERS, timeout=15,
        )
        r.raise_for_status()
        rows = r.json().get("data") or []
        # row["s"] is "EXCHANGE:TICKER" — keep NASDAQ (W118 universe)
        tickers = [row["s"].split(":", 1)[1]
                   for row in rows
                   if row.get("s", "").startswith("NASDAQ:")][:40]
        log.info(f"[discovery] TradingView ({sess}): {len(tickers)} candidates {tickers[:8]}")
        return tickers
    except Exception as e:
        log.warning(f"[discovery] TradingView screener ({sess}) failed: {e}")
        return []


def _yahoo_gainers() -> list[str]:
    """Fallback: Yahoo Finance small_cap_gainers when Finviz is unavailable."""
    seen: set = set()
    tickers: list = []
    for scr_id in ["small_cap_gainers", "aggressive_small_caps"]:
        if len(tickers) >= 20:
            break
        try:
            r = requests.get(
                "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved",
                params={"scrIds": scr_id, "count": 100,
                        "formatted": "false", "lang": "en-US", "region": "US"},
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
                timeout=12,
            )
            for q in r.json()["finance"]["result"][0]["quotes"]:
                sym   = q.get("symbol", "")
                price = q.get("regularMarketPrice") or 0
                chg   = q.get("regularMarketChangePercent") or 0
                vol   = q.get("regularMarketVolume") or 0
                if sym in seen or not (MIN_PRICE <= price <= MAX_PRICE):
                    continue
                if chg < MIN_CHANGE_PCT or vol < MIN_ABS_VOLUME:
                    continue
                seen.add(sym); tickers.append(sym)
        except Exception as e:
            log.warning(f"[discovery] Yahoo {scr_id} failed: {e}")
    if tickers:
        log.info(f"[discovery] Yahoo fallback: {len(tickers)} candidates {tickers[:8]}")
    return tickers

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

# Discovery result cache — the screener endpoints are rate-limited (429 if hit
# every 1-min scan). A stock gapping 10%+ on 1M+ volume doesn't vanish in 60s,
# so we refresh the candidate list every DISCOVERY_TTL seconds and reuse it in
# between. W118 condition checks still run every scan on the cached list.
DISCOVERY_TTL = 300  # 5 min → screeners hit ~12×/hr instead of 60×/hr
_disc_cache: list[str] = []
_disc_cache_ts: float = 0.0

def discover() -> list[str]:
    global _disc_cache, _disc_cache_ts
    manual = _manual_watchlist()  # always fresh — cheap local file read

    if not _disc_cache_ts or (time.time() - _disc_cache_ts) >= DISCOVERY_TTL:
        _disc_cache_ts = time.time()  # mark attempt so a failure won't retry next scan
        tv = _tradingview_screener()     # primary: float<20M NASDAQ universe, same as Yassss
        # Yahoo only kicks in when TradingView returns nothing (premarket, after hours, outage)
        net = tv or _yahoo_gainers()
        if net:
            _disc_cache = net
        else:
            log.info("[discovery] screeners empty/rate-limited — keeping last cached list")

    seen, result = set(), []
    for t in (manual + _disc_cache):
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

def _is_rth() -> bool:
    """True only during regular trading hours (Mon-Fri 9:30am-4:00pm ET).
    Outside this window Alpaca rejects/parks market orders — we must use a
    limit order with extended_hours=True instead."""
    et = datetime.now(ET)
    if et.weekday() >= 5:          # Sat/Sun
        return False
    hours = et.hour + et.minute / 60.0
    return 9.5 <= hours < 16.0


def _confirm_position(ticker: str, timeout: int = 30) -> bool:
    """Poll Alpaca until the buy fill appears as a confirmed position."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if any(p["symbol"] == ticker for p in get_positions()):
            return True
        time.sleep(1)
    return False


def _place_oco_exit(ticker: str, qty: int, target: float, stop: float) -> bool:
    """
    Attach an OCO (one-cancels-other) exit on `qty` held shares: a take-profit
    limit at `target` AND a protective stop at `stop`, linked so when one fills
    the other auto-cancels. This puts a REAL broker-side stop on Alpaca that
    survives bot/VPS downtime. OCO is NOT allowed outside regular hours — caller
    falls back to a plain limit + the scan-loop software stop when this returns False.
    """
    body = {
        "symbol": ticker, "qty": qty, "side": "sell",
        "type": "limit", "time_in_force": "gtc",
        "order_class": "oco",
        "take_profit": {"limit_price": str(round(target, 2))},
        "stop_loss":   {"stop_price":  str(round(stop, 2))},
    }
    try:
        _alpaca("POST", "/v2/orders", json=body)
        return True
    except Exception as e:
        log.warning(f"[oco] {ticker} x{qty} tp={target}/sl={stop} rejected: {e}")
        return False


def execute_buy(ticker: str, price: float, info: dict):
    # Dynamic sizing: spend ~$100, split T1/T2/T3 proportionally (30%/30%/40%).
    # At least 3 shares so each leg gets at least 1.
    qty    = max(3, int(DOLLARS_PER_TRADE / price))
    t1_qty = qty // 3
    t2_qty = qty // 3
    t3_qty = qty - t1_qty - t2_qty   # remainder to T3 so total = qty exactly

    stop = round(price * (1 - STOP_PCT), 2)
    t1   = round(price * (1 + T1_PCT), 2)
    t2   = round(price * (1 + T2_PCT), 2)
    t3   = round(price * (1 + T3_PCT), 2)

    # Guard: skip halted / non-exchange stocks before even trying the order.
    # Alpaca returns 422 on halted stocks with no clear message — this check makes
    # the skip explicit and avoids burning the _bought_today slot on a bad order.
    if not is_tradeable(ticker):
        return False

    # Session-aware entry. RTH → market order (fills instantly). Premarket/afterhours
    # → marketable LIMIT (last × 1.02) + extended_hours, because Alpaca will NOT fill
    # a market order outside 9:30-16:00 ET (it parks at "new" forever).
    if _is_rth():
        ok = place_order(ticker, qty, "buy", "market", tif="day")
    else:
        buy_lim = round(price * (1 + EXT_HOURS_LIMIT_BUFFER), 2)
        ok = place_order(ticker, qty, "buy", "limit",
                         limit_price=buy_lim, tif="day", extended_hours=True)
        log.info(f"[buy] {ticker} extended-hours limit @ ${buy_lim} (last ${price:.4f})")
    if not ok:
        log.error(f"[buy] BUY order failed for {ticker}")
        return False

    # Poll until Alpaca confirms the position exists. A fixed sleep can still race;
    # polling is deterministic — targets land exactly when the fill is settled.
    if not _confirm_position(ticker, timeout=30):
        log.error(f"[buy] {ticker} position not confirmed after 30s — targets NOT placed")
        tg(f"<b>⚠️ {html.escape(ticker)}: fill unconfirmed after 30s</b>\nSet T1/T2/T3 manually on Alpaca!")
        log_trade(ticker, price, info)
        tg(
            f"<b>🟢 W118 AUTO BUY — {html.escape(ticker)}</b>\n"
            f"Entry: ${price:.4f}  ×{qty} shares (~${qty*price:.0f})\n"
            f"🛑 Stop: ${stop}  (-8%) — scan-enforced\n"
            f"🎯 T1: ${t1}  T2: ${t2}  T3: ${t3}  — SET MANUALLY"
        )
        return False

    # Attach exits as 3 OCO bracket legs (t1_qty+t2_qty+t3_qty = qty exactly, no
    # oversell). Each leg = take-profit + protective stop, linked. This puts a REAL
    # broker stop on every share, live on Alpaca, surviving bot/VPS downtime.
    # OCO is rejected outside RTH, so per leg we fall back to a plain resting limit;
    # the scan-loop -8% software stop still backstops those until RTH.
    legs = [("T1", t1_qty, t1), ("T2", t2_qty, t2), ("T3", t3_qty, t3)]
    res, oco_ok = {}, 0
    for name, lqty, tgt in legs:
        if _place_oco_exit(ticker, lqty, tgt, stop):
            res[name] = True
            oco_ok += 1
        else:
            res[name] = place_order(ticker, lqty, "sell", "limit", limit_price=tgt)

    if oco_ok == len(legs):
        stop_note = "live on Alpaca (OCO bracket)"
    elif oco_ok == 0:
        stop_note = "bot-enforced every minute (premarket — OCO opens at 9:30)"
    else:
        stop_note = "partial OCO + bot backup"

    log_trade(ticker, price, info)

    msg = (
        f"<b>🟢 W118 AUTO BUY — {html.escape(ticker)}</b>{' ⭐ DEEP CURL' if info.get('deep_curl') else ''}\n"
        f"Entry: ${price:.4f}  ×{qty} shares (~${qty*price:.0f})\n"
        f"K={info['k']}↑  D={info['d']}  MACD(5,10,16)={'▲' if info['macd_hist'] > 0 else '▽'}  Vol {info['vol_ratio']}x\n"
        f"🛑 Stop: ${stop}  (-8%) — {stop_note}\n"
        f"🎯 T1: ${t1}  (+15%)  ×{t1_qty} — {'✓' if res['T1'] else '❌ FAILED'}\n"
        f"   T2: ${t2}  (+30%)  ×{t2_qty} — {'✓' if res['T2'] else '❌ FAILED'}\n"
        f"   T3: ${t3}  (+60%)  ×{t3_qty} — {'✓' if res['T3'] else '❌ FAILED'}"
    )
    tg(msg)
    log.info(f"[buy] {ticker} @ ${price} ×{qty}sh (~${qty*price:.0f})  stop=${stop} ({stop_note})  "
             f"T1={'✓' if res['T1'] else '✗'} T2={'✓' if res['T2'] else '✗'} T3={'✓' if res['T3'] else '✗'}")
    return True

def execute_exit(ticker: str, reason: str):
    sold = market_sell_position(ticker)
    if sold:
        tg(f"<b>🔴 W118 EXIT — {ticker}</b>\nReason: {reason}")
        log.info(f"[exit] {ticker}: {reason}")

# ── Self-audit ────────────────────────────────────────────────────────────────

def _realized_pnl_today() -> tuple[dict, float, int, int]:
    """
    Pull Alpaca FILL activities for today, FIFO-match buys↔sells per symbol,
    return (per_symbol_dict, net_pnl, wins, losses).
    per_symbol_dict: {ticker: {"pnl": float, "qty": int, "avg_buy": float, "avg_sell": float}}
    """
    today = date.today().isoformat()
    try:
        acts = _alpaca("GET", "/v2/account/activities/FILL",
                       params={"after": f"{today}T00:00:00Z", "direction": "asc", "page_size": 500})
    except Exception:
        return {}, 0.0, 0, 0

    # Group fills by symbol
    by_sym: dict = {}
    for a in acts:
        sym = a.get("symbol", "")
        if not sym:
            continue
        by_sym.setdefault(sym, {"buys": [], "sells": []})
        entry = {"qty": float(a.get("qty", 0)), "price": float(a.get("price", 0))}
        if a.get("side") == "buy":
            by_sym[sym]["buys"].append(entry)
        else:
            by_sym[sym]["sells"].append(entry)

    result: dict = {}
    net = 0.0
    wins = losses = 0
    for sym, sides in by_sym.items():
        buy_q  = sum(e["qty"]   for e in sides["buys"])
        buy_$  = sum(e["qty"] * e["price"] for e in sides["buys"])
        sell_q = sum(e["qty"]   for e in sides["sells"])
        sell_$ = sum(e["qty"] * e["price"] for e in sides["sells"])
        matched = min(buy_q, sell_q)
        if matched <= 0 or buy_q <= 0:
            continue
        avg_buy  = buy_$ / buy_q
        avg_sell = sell_$ / sell_q if sell_q else 0
        pnl = (avg_sell - avg_buy) * matched
        result[sym] = {"pnl": pnl, "qty": int(matched), "avg_buy": avg_buy, "avg_sell": avg_sell}
        net += pnl
        if pnl > 0:
            wins += 1
        else:
            losses += 1
    return result, net, wins, losses


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

    # Realized P&L from closed trades today
    pnl_map, net_pnl, wins, losses = _realized_pnl_today()
    pnl_lines = ""
    for sym, s in sorted(pnl_map.items(), key=lambda x: -abs(x[1]["pnl"])):
        arrow = "🟢" if s["pnl"] >= 0 else "🔴"
        pnl_lines += (f"  {arrow} {sym}: {s['qty']}sh  "
                      f"avg in ${s['avg_buy']:.3f} → out ${s['avg_sell']:.3f}  "
                      f"P&L ${s['pnl']:+.2f}\n")

    msg = (
        f"<b>📊 W118 Daily Audit — {today}</b>\n"
        f"Entries today: {len(today_trades)}  |  Positions open: {len(positions)}\n"
        f"Buy fills: {len(buys)}  |  Sell fills: {len(sells)}\n"
    )
    if pnl_lines:
        win_rate = f"{wins/(wins+losses)*100:.0f}%" if (wins + losses) > 0 else "—"
        msg += (f"\n<b>Closed P&L today:</b>\n{pnl_lines}"
                f"Net: <b>${net_pnl:+.2f}</b>  ({wins}W / {losses}L  {win_rate})\n")
    if pos_lines:
        msg += f"\n<b>Open now (unrealized):</b>\n{pos_lines}"

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

def _in_midday_chop() -> bool:
    """True during the 10:30am-3pm ET dead zone. Pauses NEW entries only —
    exits on open positions still run every scan regardless of this."""
    if not AVOID_MIDDAY:
        return False
    et = datetime.now(ET)
    hours = et.hour + et.minute / 60.0
    return MIDDAY_START_ET <= hours < MIDDAY_END_ET

def _blocker_bucket(reason: str) -> str:
    """Map a check_all_entry fail string to a human bucket for the heartbeat."""
    r = reason.lower()
    if "supertrend" in r:                     return "Supertrend not green"
    if r.startswith("k ") or "stoch" in r:    return "StochRSI (K below D / not rising)"
    if "zlsma" in r:                          return "below ZLSMA"
    if "macd" in r:                           return "MACD not positive"
    if "vol" in r:                            return "volume under 1.5x"
    if "price" in r:                          return "price out of range"
    return "other"

_first_scan_of_day: str = ""
_last_summary: dict = {}     # populated each scan, read by the hourly heartbeat
_watch_sent: dict  = {}      # ticker → timestamp; throttle WATCH alerts to 1 per 10 min
_setup_sent: dict  = {}      # ticker → timestamp; throttle MANUAL SETUP alerts to 1 per 10 min
_bought_today: set = set()   # tickers already bought today — never double-buy the same name
_bought_day: str   = ""      # date the set above belongs to (reset on rollover)


def _send_setup_alert(ticker: str, info: dict, why: str) -> None:
    """A full 5/5 setup the bot could NOT auto-buy (daily cap / position cap /
    midday / already bought). Sends the COMPLETE manual trade plan — entry, stop,
    T1/T2/T3 — so the user can still paper-trade it by hand. Throttled 1/10 min."""
    last = _setup_sent.get(ticker, 0)
    if time.time() - last < 600:
        return
    _setup_sent[ticker] = time.time()
    bar_price  = info["price"]                 # last 5-min bar close (signal fired here)
    live_price = get_latest_price(ticker)      # real-time last trade
    price = live_price if live_price else bar_price
    price_note = "live" if live_price else "last 5m bar"
    qty   = max(3, int(DOLLARS_PER_TRADE / price))
    stop  = round(price * (1 - STOP_PCT), 2)
    t1    = round(price * (1 + T1_PCT), 2)
    t2    = round(price * (1 + T2_PCT), 2)
    t3    = round(price * (1 + T3_PCT), 2)
    curl  = " ⭐ DEEP CURL" if info.get("deep_curl") else ""
    macd  = "▲" if (info.get("macd_hist") or 0) > 0 else "▽"
    tg(
        f"🔔 <b>MANUAL SETUP — {html.escape(ticker)}</b>{curl}\n"
        f"<i>Bot can't auto-buy ({html.escape(why)}) — you can paper-trade it:</i>\n"
        f"Entry ~${price:.4f} ({price_note})  ×{qty} shares (~${qty*price:.0f})\n"
        f"K={info['k']}↑ D={info['d']}  MACD {macd}  Vol {info['vol_ratio']}x\n"
        f"🛑 Stop ${stop}  (-8%)\n"
        f"🎯 T1 ${t1} (+15%)   T2 ${t2} (+30%)   T3 ${t3} (+60%)"
    )
    log.info(f"[MANUAL] {ticker} full 5/5 setup — alert only ({why})")

def _send_watch_alert(ticker: str, info: dict) -> None:
    """Fire a Telegram WATCH alert when a ticker hits 4/5 conditions — manual entry cue."""
    last = _watch_sent.get(ticker, 0)
    if time.time() - last < 600:   # don't re-alert same ticker within 10 min
        return
    _watch_sent[ticker] = time.time()
    score    = info["score"]
    max_     = info["max"]
    missing  = html.escape(info.get("fail") or "—")   # escape so '<' can't break Telegram HTML
    curl = " ⭐deep-curl" if info.get("deep_curl") else ""
    tg(
        f"👀 <b>WATCH: {html.escape(ticker)}</b> — {score}/{max_} conditions{curl}\n"
        f"Price ${info['price']:.2f}  "
        f"K={info['k']}  Vol {info['vol_ratio']}x\n"
        f"Missing: {missing}\n"
        f"Check chart — manual entry possible"
    )
    log.info(f"[WATCH] {ticker}: {score}/{max_} — {info.get('fail')}")

def heartbeat() -> None:
    """Hourly Telegram pulse — proves the bot is alive and explains why no entry."""
    if not _in_gate():
        return
    s = _last_summary
    if not s:
        tg("💓 <b>W118 alive</b> — first scan still pending.")
        return
    if s.get("blockers"):
        top = sorted(s["blockers"].items(), key=lambda x: -x[1])
        blk = " · ".join(f"{name} ({n})" for name, n in top)
    else:
        blk = "—"
    mode = s.get("mode", "live")
    mode_line = "" if mode == "live" else f"\n⚠️ Auto-entries paused ({mode}) — manual setup alerts still firing"
    tg(
        f"💓 <b>W118 alive</b> — {s['time']}\n"
        f"Checked {s['candidates']} candidates · {s['positions']}/{MAX_POSITIONS} open · "
        f"{s['trades']} trades today\n"
        f"Setups passing all 5: <b>{s['signals']}</b>{mode_line}\n"
        f"Why no entry → {blk}"
    )
    log.info("[heartbeat] sent")

def scan():
    global _first_scan_of_day, _last_summary, _bought_today, _bought_day
    if not _in_gate():
        return

    now    = datetime.now(ET).strftime("%H:%M ET")
    today  = date.today().isoformat()
    log.info(f"[scan] ── {now} ─────────────────────────────────────")

    # Reset the once-per-day "already bought" guard when the date rolls over.
    if _bought_day != today:
        _bought_day = today
        _bought_today = set()

    # Send one "I'm alive" Telegram at the first scan of each day
    if _first_scan_of_day != today:
        _first_scan_of_day = today
        tg(f"⏰ <b>W118 Bot scanning</b> — {now}\nGate open. Running TradingView scanner...")

    held = get_held()

    # Check exits on existing positions first (signal exits + hard P&L stop backup)
    positions = get_positions()
    pos_map = {p["symbol"]: p for p in positions}
    for ticker in list(held):
        # Hard stop: P&L-based exit catches the -8% floor if the Alpaca stop order
        # failed to place (e.g. 403 timing race between buy fill and stop placement)
        if ticker in pos_map:
            pl_pct = float(pos_map[ticker].get("unrealized_plpc", 0))
            if pl_pct <= -STOP_PCT:
                execute_exit(ticker, f"hard_stop ({pl_pct*100:.1f}%)")
                held.discard(ticker)
                continue

        bars = get_bars(ticker, limit=100)
        if not bars:
            continue
        # Signal exits (Supertrend flip, ZLSMA break) only fire during RTH.
        # Premarket small-caps swing 6%+ on routine noise — firing on a single
        # bearish 5m candle at 07:41 stops us out of runners before the open
        # (see ATPC: bought $3.23, exited $3.03 premarket, ran to $6.00 at open).
        # The -8% hard stop above is always active; that's the only premarket exit.
        if _is_rth():
            reason = check_exit_signal(bars)
            if reason:
                execute_exit(ticker, reason)
                held.discard(ticker)

    # Decide whether AUTO entries are allowed right now. Even when they are NOT —
    # daily cap hit, position cap hit, or midday chop — we still scan and alert.
    # A tapped-out bot must not go silent: the user paper-trades the full plan by
    # hand off a "MANUAL SETUP" alert (entry + stop + T1/T2/T3).
    entries_open = True
    pause_reason = None
    if trades_today() >= MAX_DAILY_TRADES:
        entries_open, pause_reason = False, f"daily cap {MAX_DAILY_TRADES} reached"
    elif len(held) >= MAX_POSITIONS:
        entries_open, pause_reason = False, f"{MAX_POSITIONS} positions open"
    elif _in_midday_chop():
        entries_open, pause_reason = False, "midday chop (10:30am-3pm ET)"

    candidates = discover()
    log.info(f"[scan] {len(candidates)} candidates → checking W118 conditions"
             + ("" if entries_open else f"  (ALERT-ONLY: {pause_reason})"))

    blockers: Counter = Counter()
    signals = 0
    for ticker in candidates:
        if ticker in held:
            continue

        bars = get_bars(ticker)
        if not bars:
            continue

        ok, info = check_all_entry(bars, MIN_PRICE, MAX_PRICE, REL_VOL_MIN, DEEP_CURL_RESET)
        score, max_ = info.get("score", 0), info.get("max", 5)

        if ok:
            # Micro-timeframe freshness — W118's "zoom to 1m". The 5-min signal lags;
            # block it if the 1-min move is already rolling over (the ATPC $3.43 top
            # chase). Fails open when 1-min history is thin so young names aren't blocked.
            if REQUIRE_1M_FRESH:
                bars_1m = get_bars(ticker, limit=60, timeframe="1Min")
                if bars_1m:
                    fresh, why_stale = is_fresh_1m(bars_1m)
                    if not fresh:
                        log.info(f"[skip-stale] {ticker} 5/5 on 5m but {why_stale}")
                        blockers["1m rolling over (stale)"] += 1
                        time.sleep(0.15)
                        continue

            signals += 1
            curl = " ⭐deep-curl" if info.get("deep_curl") else ""
            # Can we actually auto-buy? Re-check live caps each pass so a buy made
            # earlier in THIS loop correctly flips later passes to alert-only.
            if ticker in _bought_today:
                why = "already bought today"
            elif not entries_open:
                why = pause_reason
            elif trades_today() >= MAX_DAILY_TRADES:
                why = f"daily cap {MAX_DAILY_TRADES} reached"
            elif len(get_held()) >= MAX_POSITIONS:
                why = f"{MAX_POSITIONS} positions open"
            else:
                why = None   # clear to buy

            if why is None:
                log.info(f"[SIGNAL] {ticker} — ALL PASS (auto-buy): price=${info['price']} K={info['k']}↑ MACD▲ vol={info['vol_ratio']}x{curl}")
                _bought_today.add(ticker)   # mark BEFORE the order so a slow fill can't trigger a repeat
                bought = execute_buy(ticker, info["price"], info)
                if not bought:
                    _bought_today.discard(ticker)  # order failed (e.g. halted) — allow retry next scan
                held = get_held()
            else:
                log.info(f"[SIGNAL] {ticker} — ALL PASS (manual, {why}){curl}")
                _send_setup_alert(ticker, info, why)
        else:
            # Tally each blocker individually for heartbeat
            for b in info.get("blockers", [info.get("fail", "unknown")]):
                blockers[_blocker_bucket(b)] += 1

            # WATCH only when one gate away AND Supertrend is already green —
            # the primary trigger must be on for it to be a real forming setup.
            st_green = "Supertrend bearish" not in info.get("blockers", [])
            if score >= max_ - 1 and st_green:
                _send_watch_alert(ticker, info)
            else:
                # Not close enough — silent debug only, no spam
                log.debug(f"[skip] {ticker} {score}/{max_}: {info.get('fail')}")

        time.sleep(0.15)  # ~6 reqs/sec — well under Alpaca's 200/min free limit

    _last_summary = {
        "time":       now,
        "candidates": len(candidates),
        "positions":  len(get_held()),
        "trades":     trades_today(),
        "signals":    signals,
        "blockers":   dict(blockers),
        "mode":       pause_reason or "live",
    }
    log.info(f"[scan] done. Positions: {len(get_held())} / {MAX_POSITIONS}"
             + ("" if entries_open else f"  (alert-only: {pause_reason})"))

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("  W118 Curl if Flow — Auto Paper Trading Bot")
    log.info(f"  Gate: {GATE_OPEN_UTC}:00–{GATE_CLOSE_UTC}:00 UTC  (2am–4pm MT / 4am–6pm ET)")
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
        f"Gate: 2am–4pm MT (4am–6pm ET)  |  Max {MAX_DAILY_TRADES} trades/day\n"
        f"Universe: NASDAQ $0.10–$15, vol>1M, chg>10%, relVol>{REL_VOL_MIN}x\n"
        f"Conditions: Supertrend ✓  K>D+rising ✓  price>ZLSMA ✓  MACD(5,10,16)>0 ✓  vol>{REL_VOL_MIN}x ✓"
    )

    schedule.every(SCAN_INTERVAL_MIN).minutes.do(scan)
    schedule.every().hour.do(heartbeat)                  # hourly "alive + why no entry" pulse
    schedule.every().day.at("20:30").do(daily_audit)     # 4:30pm ET = 20:30 UTC
    schedule.every().monday.at("21:00").do(weekly_audit) # Monday 5pm ET

    scan()  # run once immediately on startup

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
