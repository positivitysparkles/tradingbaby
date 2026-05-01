"""
Curl if Flow — Backtester
Weatherman118 system | reverse-engineered by positivitysparkles

For each historical trade in trades-parsed.json, this script:
  1. Pulls 5m OHLCV data from yfinance for the trade date
  2. Calculates Stochastic RSI K (RSI=14, Stoch=14, K_smooth=3, D_smooth=3)
  3. Calculates ZLSMA-50 and Smoothed Heikin Ashi
  4. Finds the first bar where K crosses above 20 (ta.crossover equivalent)
  5. Compares signal price to actual entry price and eventual day high
  6. Reports "signal capture %" — how much of the move was available from signal bar

Output: CSV + summary statistics proving entries happen BEFORE / AT the spike.

Usage:
    pip install yfinance pandas numpy
    python backtest_curl_if_flow.py
    python backtest_curl_if_flow.py --ticker AKAN --date 2026-04-28
    python backtest_curl_if_flow.py --output results.csv --verbose
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

try:
    import numpy as np
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("Missing dependencies. Run: pip install yfinance pandas numpy")
    sys.exit(1)

TRADES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trades-parsed.json")

# ── INDICATOR CALCULATIONS ────────────────────────────────────────────────────

def smoothed_ha(df: pd.DataFrame, len1: int = 10, len2: int = 10) -> pd.DataFrame:
    """Double-EMA smoothed Heikin Ashi. Returns df with sha_open, sha_close, sha_green."""
    ha_close = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
    ha_open = ha_close.copy()
    for i in range(1, len(ha_open)):
        ha_open.iloc[i] = (ha_open.iloc[i - 1] + ha_close.iloc[i - 1]) / 2

    def dema(series, n):
        e1 = series.ewm(span=n, adjust=False).mean()
        e2 = e1.ewm(span=n, adjust=False).mean()
        return e1  # single EMA pass each time — pine uses sequential EMA

    sha_close_s = ha_close.ewm(span=len1, adjust=False).mean().ewm(span=len2, adjust=False).mean()
    sha_open_s  = ha_open.ewm(span=len1, adjust=False).mean().ewm(span=len2, adjust=False).mean()

    df = df.copy()
    df["sha_close"] = sha_close_s
    df["sha_open"]  = sha_open_s
    df["sha_green"] = df["sha_close"] > df["sha_open"]
    return df


def zlsma(df: pd.DataFrame, length: int = 50) -> pd.DataFrame:
    """Zero Lag SMA = 2*EMA(n) - EMA(EMA(n))."""
    ema1 = df["Close"].ewm(span=length, adjust=False).mean()
    ema2 = ema1.ewm(span=length, adjust=False).mean()
    df = df.copy()
    df["zlsma"] = 2 * ema1 - ema2
    df["above_zlsma"] = df["Close"] > df["zlsma"]
    return df


def stoch_rsi(df: pd.DataFrame, rsi_len: int = 14, stoch_len: int = 14,
              k_smooth: int = 3, d_smooth: int = 3) -> pd.DataFrame:
    """Stochastic RSI with K and D smoothing."""
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=rsi_len - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=rsi_len - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))

    stoch_min = rsi.rolling(stoch_len).min()
    stoch_max = rsi.rolling(stoch_len).max()
    k_raw = 100 * (rsi - stoch_min) / (stoch_max - stoch_min).replace(0, float("nan"))
    k = k_raw.rolling(k_smooth).mean()
    d = k.rolling(d_smooth).mean()

    df = df.copy()
    df["rsi"] = rsi
    df["stoch_k"] = k
    df["stoch_d"] = d
    return df


def crossover(series: pd.Series, level: float) -> pd.Series:
    """Returns True where series crosses UP through level (was below, now above)."""
    was_below = series.shift(1) < level
    now_above = series >= level
    return was_below & now_above


def volume_surge(df: pd.DataFrame, mult: float = 1.5, lookback: int = 20) -> pd.DataFrame:
    df = df.copy()
    df["avg_vol"] = df["Volume"].rolling(lookback).mean()
    df["vol_surge"] = df["Volume"] >= df["avg_vol"] * mult
    return df


# ── SIGNAL DETECTION ─────────────────────────────────────────────────────────

def find_entry_signal(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all indicators and mark entry signals."""
    df = smoothed_ha(df)
    df = zlsma(df)
    df = stoch_rsi(df)
    df = volume_surge(df)

    df["k_crossover_20"] = crossover(df["stoch_k"], 20)
    df["k_above_d"]      = df["stoch_k"] > df["stoch_d"]

    df["entry_signal"] = (
        df["k_crossover_20"] &
        df["k_above_d"]      &
        df["sha_green"]      &
        df["above_zlsma"]    &
        df["vol_surge"]
    )
    return df


# ── FETCH AND ANALYZE ─────────────────────────────────────────────────────────

def fetch_day_data(ticker: str, date_str: str) -> pd.DataFrame | None:
    """Download 5m data for ticker on given date (extended hours)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    start = dt - timedelta(days=5)  # need lookback for indicators
    end   = dt + timedelta(days=1)

    try:
        raw = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval="5m",
            prepost=True,
            auto_adjust=True,
            progress=False,
        )
    except Exception as e:
        print(f"  [yfinance error] {ticker} {date_str}: {e}")
        return None

    if raw is None or raw.empty:
        return None

    # Filter to target date only (keep full history for indicator warmup)
    return raw


def analyze_trade(trade: dict, verbose: bool = False) -> dict:
    """Analyze a single trade — find signal bar, compare to entry price and high."""
    ticker   = trade["ticker"]
    date_str = trade["date"]
    entry    = trade["entry_price"]
    day_high = trade["high"]
    session  = trade["session"]
    pct_gain = trade["pct_gain"]

    result = {
        "ticker":      ticker,
        "date":        date_str,
        "session":     session,
        "entry_price": entry,
        "day_high":    day_high,
        "reported_pct": pct_gain,
        "signal_found":    False,
        "signal_time":     None,
        "signal_price":    None,
        "signal_k":        None,
        "signal_d":        None,
        "signal_to_high_pct":  None,
        "entry_vs_signal_pct": None,
        "capture_pct":         None,
        "verdict":             "NO_DATA",
        "error":       None,
    }

    df = fetch_day_data(ticker, date_str)
    if df is None or df.empty:
        result["error"] = "No data from yfinance"
        return result

    df = find_entry_signal(df)

    # Filter to the trading date only
    date_dt = datetime.strptime(date_str, "%Y-%m-%d")
    if hasattr(df.index, "tz") and df.index.tz is not None:
        import pytz
        et = pytz.timezone("America/New_York")
        day_df = df[df.index.tz_convert(et).normalize() == pd.Timestamp(date_dt, tz=et)]
    else:
        day_df = df[df.index.date == date_dt.date()]  # type: ignore

    if day_df.empty:
        result["error"] = "No bars on trade date"
        return result

    # Session filter
    if hasattr(day_df.index, "tz") and day_df.index.tz is not None:
        import pytz
        et = pytz.timezone("America/New_York")
        hours = day_df.index.tz_convert(et).hour + day_df.index.tz_convert(et).minute / 60
        if session == "PM":
            day_df = day_df[hours < 9.5]   # before 9:30 ET
        else:
            day_df = day_df[(hours >= 9.5) & (hours < 16)]

    signals = day_df[day_df["entry_signal"] == True]

    if signals.empty:
        result["verdict"] = "NO_SIGNAL"
        if verbose:
            print(f"  {ticker} {date_str} — no entry signal found on {session} bars")
        return result

    # Take the first signal bar
    sig_bar  = signals.iloc[0]
    sig_time = signals.index[0]
    sig_price = float(sig_bar["Close"])
    sig_k     = float(sig_bar["stoch_k"])
    sig_d     = float(sig_bar["stoch_d"])

    # Max high from signal bar onwards (what was available to capture)
    from_signal = day_df.loc[sig_time:]
    available_high = float(from_signal["High"].max())

    signal_to_high_pct  = (available_high - sig_price) / sig_price * 100
    entry_vs_signal_pct = (entry - sig_price) / sig_price * 100
    # capture_pct: fraction of the full move (day_high - sig_price) that the reported gain covers
    full_move = day_high - sig_price
    if full_move > 0:
        capture_pct = (day_high - entry) / full_move * 100
    else:
        capture_pct = 0.0

    # Verdict
    if entry <= sig_price * 1.02:
        verdict = "AT_SIGNAL"      # entry within 2% of signal bar close
    elif entry <= sig_price * 1.10:
        verdict = "NEAR_SIGNAL"    # entry within 10% — slight lag but ok
    elif entry > sig_price * 1.10:
        verdict = "CHASING"        # entry well after signal
    else:
        verdict = "UNKNOWN"

    result.update({
        "signal_found":        True,
        "signal_time":         str(sig_time),
        "signal_price":        round(sig_price, 4),
        "signal_k":            round(sig_k, 2),
        "signal_d":            round(sig_d, 2),
        "signal_to_high_pct":  round(signal_to_high_pct, 1),
        "entry_vs_signal_pct": round(entry_vs_signal_pct, 1),
        "capture_pct":         round(capture_pct, 1),
        "verdict":             verdict,
    })

    if verbose:
        print(
            f"  {ticker} {date_str} [{session}] | "
            f"signal@{sig_price:.2f} (K={sig_k:.1f}) → entry@{entry:.2f} "
            f"({entry_vs_signal_pct:+.1f}%) → high@{day_high:.2f} "
            f"| from signal: +{signal_to_high_pct:.1f}% | verdict: {verdict}"
        )

    return result


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Curl if Flow — backtester")
    parser.add_argument("--ticker", help="Analyze only this ticker")
    parser.add_argument("--date",   help="Only this date (YYYY-MM-DD)")
    parser.add_argument("--output", default="backtest_results.csv", help="CSV output path")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--max", type=int, default=0, help="Max trades to analyze (0=all)")
    args = parser.parse_args()

    with open(TRADES_PATH) as f:
        data = json.load(f)
    trades = data["trades"]

    if args.ticker:
        trades = [t for t in trades if t["ticker"] == args.ticker]
    if args.date:
        trades = [t for t in trades if t["date"] == args.date]
    if args.max:
        trades = trades[: args.max]

    print(f"\nCurl if Flow Backtest — {len(trades)} trades\n{'─'*60}")

    results = []
    for i, trade in enumerate(trades, 1):
        label = f"{trade['ticker']} {trade['date']} [{trade['session']}]"
        print(f"[{i:02d}/{len(trades)}] {label}", end="", flush=True)
        res = analyze_trade(trade, verbose=False)
        results.append(res)
        verdict = res["verdict"]
        sig_to_high = f"+{res['signal_to_high_pct']:.1f}%" if res["signal_to_high_pct"] else "n/a"
        print(f" → {verdict} | from signal: {sig_to_high}")
        if args.verbose and res.get("error"):
            print(f"    error: {res['error']}")

    df_res = pd.DataFrame(results)
    out_path = os.path.join(os.path.dirname(__file__), args.output)
    df_res.to_csv(out_path, index=False)
    print(f"\nResults saved: {out_path}")

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    found = df_res[df_res["signal_found"] == True]
    total = len(df_res)
    n_found = len(found)

    print(f"\n{'═'*60}")
    print(f"SUMMARY — {total} trades analyzed, {n_found} signals found ({n_found/total*100:.0f}%)")
    print(f"{'─'*60}")

    if n_found > 0:
        for verdict in ["AT_SIGNAL", "NEAR_SIGNAL", "CHASING"]:
            count = (found["verdict"] == verdict).sum()
            pct = count / n_found * 100
            print(f"  {verdict:<15} {count:>4} trades  ({pct:.0f}%)")

        avg_sig_to_high = found["signal_to_high_pct"].mean()
        avg_capture     = found["capture_pct"].mean()
        avg_entry_lag   = found["entry_vs_signal_pct"].mean()

        print(f"\n  Avg move from signal bar:    +{avg_sig_to_high:.1f}%")
        print(f"  Avg entry vs signal price:   {avg_entry_lag:+.1f}%")
        print(f"  Avg capture of full move:    {avg_capture:.0f}%")
        print(f"\n  Best signal-to-high:  +{found['signal_to_high_pct'].max():.0f}%  ({found.loc[found['signal_to_high_pct'].idxmax(), 'ticker']})")
        print(f"  Worst capture:        {found['capture_pct'].min():.0f}%  ({found.loc[found['capture_pct'].idxmin(), 'ticker']})")

    no_data = (df_res["verdict"] == "NO_DATA").sum()
    no_sig  = (df_res["verdict"] == "NO_SIGNAL").sum()
    if no_data or no_sig:
        print(f"\n  No yfinance data:   {no_data} trades")
        print(f"  Signal not found:   {no_sig} trades (filter conditions not met)")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
