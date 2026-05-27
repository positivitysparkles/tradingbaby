"""
Signal Monitor — Curl if Flow System
Watches the watchlist every 5 minutes during market hours.
When all 6 conditions align → fires alert + logs paper trade.

Usage:
    python signal_monitor.py                              # watches data/watchlist.json
    python signal_monitor.py --tickers AKAN SNBR SKLZ    # manual tickers
    python signal_monitor.py --once                       # single scan, no loop
    python signal_monitor.py --interval 60               # scan every 60 seconds

Requires:
    pip install yfinance pandas numpy requests
    Set DISCORD_WEBHOOK_URL in scanner/config.json or as env var.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import pytz

try:
    import numpy as np
    import pandas as pd
    import yfinance as yf
    import requests
except ImportError:
    print("Run: pip install yfinance pandas numpy requests pytz")
    sys.exit(1)

ET = pytz.timezone("America/New_York")
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH     = os.path.join(os.path.dirname(__file__), "config.json")
WATCHLIST_PATH  = os.path.join(BASE_DIR, "data", "watchlist.json")
PAPER_LOG_PATH  = os.path.join(BASE_DIR, "data", "paper_trades.json")
SIGNALS_LOG     = os.path.join(BASE_DIR, "data", "signals_log.json")


# ── CONFIG ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    defaults = {
        "discord_webhook_url": os.environ.get("DISCORD_WEBHOOK_URL", ""),
        "telegram_bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
        "paper_account_size": 5000,
        "risk_per_trade_pct": 2.0,
        "stop_loss_pct": 8.0,
        "t1_pct": 15.0,
        "t2_pct": 30.0,
        "t3_pct": 60.0,
        "trail_pct": 10.0,
        "vol_mult": 1.5,
        "vol_lookback": 20,
        "stoch_rsi_len": 14,
        "stoch_len": 14,
        "k_smooth": 3,
        "d_smooth": 3,
        "sha_len1": 10,
        "sha_len2": 10,
        "zlsma_len": 50,
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            user_cfg = json.load(f)
        defaults.update(user_cfg)
    return defaults


# ── MARKET HOURS ──────────────────────────────────────────────────────────────

def is_market_open(extended: bool = True) -> bool:
    """Check if we're in trading hours (extended = premarket from 4am ET)."""
    now_et = datetime.now(ET)
    if now_et.weekday() >= 5:
        return False
    hour = now_et.hour + now_et.minute / 60
    if extended:
        return 4.0 <= hour < 20.0   # 4am–8pm ET
    return 9.5 <= hour < 16.0       # RTH only


def session_label(dt_et: datetime) -> str:
    hour = dt_et.hour + dt_et.minute / 60
    if hour < 9.5:
        return "PM"
    if hour < 16.0:
        return "RTH"
    return "AH"


# ── INDICATOR CALCULATIONS ────────────────────────────────────────────────────

def calc_stoch_rsi(df: pd.DataFrame, rsi_len=14, stoch_len=14,
                   k_smooth=3, d_smooth=3) -> pd.DataFrame:
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    ag    = gain.ewm(com=rsi_len - 1, adjust=False).mean()
    al    = loss.ewm(com=rsi_len - 1, adjust=False).mean()
    rs    = ag / al.replace(0, float("nan"))
    rsi   = 100 - (100 / (1 + rs))
    lo    = rsi.rolling(stoch_len).min()
    hi    = rsi.rolling(stoch_len).max()
    k_raw = 100 * (rsi - lo) / (hi - lo).replace(0, float("nan"))
    k     = k_raw.rolling(k_smooth).mean()
    d     = k.rolling(d_smooth).mean()
    df = df.copy()
    df["stoch_k"] = k
    df["stoch_d"] = d
    return df


def calc_sha(df: pd.DataFrame, len1=10, len2=10) -> pd.DataFrame:
    ha_c = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
    ha_o = ha_c.copy()
    for i in range(1, len(ha_o)):
        ha_o.iloc[i] = (ha_o.iloc[i - 1] + ha_c.iloc[i - 1]) / 2
    sha_c = ha_c.ewm(span=len1, adjust=False).mean().ewm(span=len2, adjust=False).mean()
    sha_o = ha_o.ewm(span=len1, adjust=False).mean().ewm(span=len2, adjust=False).mean()
    df = df.copy()
    df["sha_close"] = sha_c
    df["sha_open"]  = sha_o
    df["sha_green"] = sha_c > sha_o
    return df


def calc_zlsma(df: pd.DataFrame, length=50) -> pd.DataFrame:
    e1 = df["Close"].ewm(span=length, adjust=False).mean()
    e2 = e1.ewm(span=length, adjust=False).mean()
    df = df.copy()
    df["zlsma"]      = 2 * e1 - e2
    df["above_zlsma"] = df["Close"] > df["zlsma"]
    return df


def calc_volume(df: pd.DataFrame, mult=1.5, lookback=20) -> pd.DataFrame:
    df = df.copy()
    df["avg_vol"]  = df["Volume"].rolling(lookback).mean()
    df["vol_surge"] = df["Volume"] >= df["avg_vol"] * mult
    return df


def get_all_conditions(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    df = calc_stoch_rsi(df, cfg["stoch_rsi_len"], cfg["stoch_len"],
                        cfg["k_smooth"], cfg["d_smooth"])
    df = calc_sha(df, cfg["sha_len1"], cfg["sha_len2"])
    df = calc_zlsma(df, cfg["zlsma_len"])
    df = calc_volume(df, cfg["vol_mult"], cfg["vol_lookback"])

    df["k_crossover_20"] = (df["stoch_k"].shift(1) < 20) & (df["stoch_k"] >= 20)
    df["k_above_d"]      = df["stoch_k"] > df["stoch_d"]
    df["entry_signal"]   = (
        df["k_crossover_20"] &
        df["k_above_d"]      &
        df["sha_green"]      &
        df["above_zlsma"]    &
        df["vol_surge"]
    )
    return df


# ── FETCH DATA ────────────────────────────────────────────────────────────────

def fetch_5m(ticker: str, days_back: int = 5) -> pd.DataFrame | None:
    try:
        df = yf.download(ticker, period=f"{days_back}d", interval="5m",
                         prepost=True, auto_adjust=True, progress=False)
        if df is None or df.empty:
            return None
        return df
    except Exception as e:
        print(f"  [fetch] {ticker}: {e}")
        return None


# ── SIGNAL CHECK ──────────────────────────────────────────────────────────────

def check_signal(ticker: str, cfg: dict) -> dict | None:
    """
    Returns signal dict if entry conditions fire on the latest bar, else None.
    """
    df = fetch_5m(ticker)
    if df is None or len(df) < 60:
        return None

    df = get_all_conditions(df, cfg)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if not last["entry_signal"]:
        return None

    # Pre-entry K depth (ideally was below 10-20 on previous bar)
    pre_k = float(prev["stoch_k"]) if not pd.isna(prev["stoch_k"]) else 0

    now_et = datetime.now(ET)
    return {
        "ticker":      ticker,
        "signal_time": now_et.isoformat(),
        "session":     session_label(now_et),
        "price":       round(float(last["Close"]), 4),
        "stoch_k":     round(float(last["stoch_k"]), 2),
        "stoch_d":     round(float(last["stoch_d"]), 2),
        "pre_k":       round(pre_k, 2),
        "sha_green":   bool(last["sha_green"]),
        "above_zlsma": bool(last["above_zlsma"]),
        "vol_surge":   bool(last["vol_surge"]),
        "vol_ratio":   round(float(last["Volume"] / last["avg_vol"]), 2) if last["avg_vol"] > 0 else 0,
        "zlsma":       round(float(last["zlsma"]), 4),
        "conditions_met": 6,  # all 6 — catalyst not auto-checkable
        "note": "Auto-signal: verify catalyst manually before trading",
    }


# ── ALERTS ────────────────────────────────────────────────────────────────────

def send_discord_alert(signal: dict, webhook_url: str) -> None:
    if not webhook_url:
        return
    tier_note = signal.get("note", "")
    msg = (
        f"🔥 **CURL IF FLOW SIGNAL** — `${signal['ticker']}`\n"
        f"```\n"
        f"Time:    {signal['signal_time'][:19]} ET [{signal['session']}]\n"
        f"Price:   ${signal['price']}\n"
        f"Stoch K: {signal['stoch_k']}  D: {signal['stoch_d']}  Pre-K: {signal['pre_k']}\n"
        f"SHA:     {'GREEN ✅' if signal['sha_green'] else 'RED ❌'}\n"
        f"ZLSMA:   {'ABOVE ✅' if signal['above_zlsma'] else 'BELOW ❌'}\n"
        f"Volume:  {signal['vol_ratio']}x avg {'✅' if signal['vol_surge'] else '❌'}\n"
        f"```\n"
        f"⚠️ {tier_note}\n"
        f"Stop: -8% → ${signal['price'] * 0.92:.2f} | "
        f"T1: +15% → ${signal['price'] * 1.15:.2f} | "
        f"T2: +30% → ${signal['price'] * 1.30:.2f}"
    )
    try:
        requests.post(webhook_url, json={"content": msg}, timeout=5)
    except Exception as e:
        print(f"  [discord] Alert failed: {e}")


def send_telegram_alert(signal: dict, bot_token: str, chat_id: str) -> None:
    if not bot_token or not chat_id:
        return
    msg = (
        f"🔥 CURL IF FLOW: ${signal['ticker']} @ ${signal['price']}\n"
        f"K={signal['stoch_k']} D={signal['stoch_d']} [{signal['session']}]\n"
        f"Vol: {signal['vol_ratio']}x | SHA: {'✅' if signal['sha_green'] else '❌'} "
        f"| ZLSMA: {'✅' if signal['above_zlsma'] else '❌'}\n"
        f"Stop -8%→${signal['price']*0.92:.2f} T1+15%→${signal['price']*1.15:.2f}"
    )
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=5)
    except Exception as e:
        print(f"  [telegram] Alert failed: {e}")


# ── PAPER TRADE LOGGER ────────────────────────────────────────────────────────

def log_paper_trade(signal: dict, cfg: dict) -> dict:
    """Create a paper trade entry from a signal. Returns the trade dict."""
    account  = cfg["paper_account_size"]
    risk_usd = account * (cfg["risk_per_trade_pct"] / 100)
    stop_pct = cfg["stop_loss_pct"] / 100
    position_usd = risk_usd / stop_pct
    shares   = int(position_usd / signal["price"])

    trade = {
        "id":           f"{signal['ticker']}_{signal['signal_time'][:19].replace(':', '')}",
        "ticker":       signal["ticker"],
        "entry_price":  signal["price"],
        "entry_time":   signal["signal_time"],
        "session":      signal["session"],
        "shares":       shares,
        "position_usd": round(shares * signal["price"], 2),
        "stop_price":   round(signal["price"] * (1 - stop_pct), 4),
        "t1_price":     round(signal["price"] * (1 + cfg["t1_pct"] / 100), 4),
        "t2_price":     round(signal["price"] * (1 + cfg["t2_pct"] / 100), 4),
        "t3_price":     round(signal["price"] * (1 + cfg["t3_pct"] / 100), 4),
        "stoch_k":      signal["stoch_k"],
        "stoch_d":      signal["stoch_d"],
        "pre_k":        signal["pre_k"],
        "vol_ratio":    signal["vol_ratio"],
        "status":       "open",
        "conditions":   {
            "stoch_curl": True,
            "k_above_d":  True,
            "sha_green":  signal["sha_green"],
            "above_zlsma": signal["above_zlsma"],
            "vol_surge":  signal["vol_surge"],
            "catalyst":   None,  # manual check required
        },
        "grade":        None,
        "result":       None,
        "exit_price":   None,
        "exit_time":    None,
        "pct_gain":     None,
        "pnl_usd":      None,
        "t1_hit":       False,
        "t2_hit":       False,
        "stop_moved_be": False,
        "note":         "",
    }

    # Load existing paper trades
    paper = {"trades": [], "stats": {}}
    if os.path.exists(PAPER_LOG_PATH):
        with open(PAPER_LOG_PATH) as f:
            paper = json.load(f)

    paper["trades"].append(trade)
    _update_paper_stats(paper)

    with open(PAPER_LOG_PATH, "w") as f:
        json.dump(paper, f, indent=2)

    return trade


def _update_paper_stats(paper: dict) -> None:
    trades   = paper["trades"]
    closed   = [t for t in trades if t["status"] == "closed"]
    wins     = [t for t in closed if t.get("result") == "win"]
    losses   = [t for t in closed if t.get("result") == "loss"]
    open_ct  = len([t for t in trades if t["status"] == "open"])

    paper["stats"] = {
        "total_closed":  len(closed),
        "wins":          len(wins),
        "losses":        len(losses),
        "open":          open_ct,
        "win_rate_pct":  round(len(wins) / len(closed) * 100, 1) if closed else 0,
        "avg_winner_pct": round(sum(t["pct_gain"] for t in wins) / len(wins), 1) if wins else 0,
        "avg_loser_pct":  round(sum(t["pct_gain"] for t in losses) / len(losses), 1) if losses else 0,
        "total_pnl_usd": round(sum(t.get("pnl_usd", 0) or 0 for t in closed), 2),
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


# ── LOG SIGNAL ────────────────────────────────────────────────────────────────

def log_signal(signal: dict) -> None:
    log = []
    if os.path.exists(SIGNALS_LOG):
        with open(SIGNALS_LOG) as f:
            log = json.load(f)
    log.append(signal)
    with open(SIGNALS_LOG, "w") as f:
        json.dump(log[-500:], f, indent=2)  # keep last 500 signals


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Curl if Flow — Signal Monitor")
    parser.add_argument("--tickers", nargs="+", help="Tickers to monitor (overrides watchlist)")
    parser.add_argument("--watchlist", default=WATCHLIST_PATH, help="Path to watchlist.json")
    parser.add_argument("--interval", type=int, default=300, help="Scan interval in seconds (default 300 = 5min)")
    parser.add_argument("--once", action="store_true", help="Scan once and exit")
    parser.add_argument("--no-paper", action="store_true", help="Don't log paper trades")
    parser.add_argument("--no-alert", action="store_true", help="Don't send alerts")
    args = parser.parse_args()

    cfg = load_config()

    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    elif os.path.exists(args.watchlist):
        with open(args.watchlist) as f:
            wl = json.load(f)
        tickers = [s["ticker"] for s in wl.get("stocks", [])]
        print(f"[monitor] Loaded {len(tickers)} tickers from {args.watchlist}")
    else:
        print(f"[monitor] No watchlist found at {args.watchlist}")
        print("[monitor] Run pre_market_scanner.py first, or pass --tickers")
        sys.exit(1)

    alerted_today: set[str] = set()  # avoid duplicate alerts per ticker per session

    print(f"[monitor] Watching: {', '.join(tickers)}")
    print(f"[monitor] Scan interval: {args.interval}s | Paper trades: {not args.no_paper} | Alerts: {not args.no_alert}")
    print(f"[monitor] Press Ctrl+C to stop\n")

    while True:
        now_et = datetime.now(ET)
        scan_time = now_et.strftime("%H:%M:%S ET")

        if not is_market_open():
            print(f"[{scan_time}] Market closed — waiting...")
            if args.once:
                break
            time.sleep(60)
            continue

        print(f"[{scan_time}] Scanning {len(tickers)} tickers...", end="", flush=True)

        signals_found = 0
        for ticker in tickers:
            signal = check_signal(ticker, cfg)
            if signal is None:
                continue

            signals_found += 1
            alert_key = f"{ticker}_{now_et.strftime('%Y%m%d_%H')}"

            print(f"\n  🔥 SIGNAL: {ticker} @ ${signal['price']} "
                  f"K={signal['stoch_k']} D={signal['stoch_d']} "
                  f"[{signal['session']}] vol={signal['vol_ratio']}x")

            log_signal(signal)

            if alert_key not in alerted_today:
                alerted_today.add(alert_key)

                if not args.no_paper:
                    trade = log_paper_trade(signal, cfg)
                    print(f"  📝 Paper trade logged: {trade['shares']} shares @ ${trade['entry_price']}")
                    print(f"     Stop: ${trade['stop_price']} | T1: ${trade['t1_price']} | T2: ${trade['t2_price']}")

                if not args.no_alert:
                    send_discord_alert(signal, cfg.get("discord_webhook_url", ""))
                    send_telegram_alert(signal,
                                        cfg.get("telegram_bot_token", ""),
                                        cfg.get("telegram_chat_id", ""))

        if signals_found == 0:
            print(f" no signals.")

        if args.once:
            break

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
