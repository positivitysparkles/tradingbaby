#!/usr/bin/env python3
"""
W118 Morning Toolkit — 3 tools in one file

1. Position Size Calculator
2. Chart Auto-Grader (checks all W118 conditions on any ticker)
3. Morning Scanner (finds candidates + grades them)

Usage in Colab:
    !pip install yfinance pandas numpy finvizfinance -q
    exec(open('w118_toolkit.py').read())

    pos_size(213, 9.45, signal_price=8.37)
    grade_ticker('QTTB')
    morning_scan()
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("Run: !pip install yfinance")

try:
    import requests as _requests
except ImportError:
    _requests = None


# ══ ALPACA API — paper trading + real-time data ══════════════════════════════

ALPACA_KEY_ID     = None
ALPACA_SECRET_KEY = None
_ALPACA_PAPER_URL = "https://paper-api.alpaca.markets/v2"
_ALPACA_DATA_URL  = "https://data.alpaca.markets/v2"

def set_alpaca_keys(key_id: str, secret_key: str):
    """Set Alpaca paper trading keys. Call once per session."""
    global ALPACA_KEY_ID, ALPACA_SECRET_KEY
    ALPACA_KEY_ID     = key_id
    ALPACA_SECRET_KEY = secret_key
    result = _alpaca_get(_ALPACA_PAPER_URL, "account")
    if result and result.get("status") == "ACTIVE":
        equity = float(result.get("equity", 0))
        bp     = float(result.get("buying_power", 0))
        print(f"✅ Alpaca paper account connected")
        print(f"   Equity: ${equity:,.2f}  |  Buying power: ${bp:,.2f}")
    else:
        print(f"⚠️  Alpaca keys set but connection test failed. Check key/secret.")

def _alpaca_headers() -> dict:
    return {
        "APCA-API-KEY-ID":     ALPACA_KEY_ID     or "",
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY or "",
    }

def _alpaca_get(base: str, endpoint: str, params: dict = None) -> dict | None:
    if not ALPACA_KEY_ID or not _requests:
        return None
    try:
        r = _requests.get(f"{base}/{endpoint}", headers=_alpaca_headers(),
                          params=params or {}, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def _alpaca_bars(ticker: str, timeframe: str = '5m', days: int = 5) -> pd.DataFrame:
    """Fetch OHLCV bars from Alpaca data API. Falls back gracefully if unavailable."""
    if not ALPACA_KEY_ID:
        return pd.DataFrame()
    from datetime import datetime, timedelta
    tf_map = {'1m': '1Min', '5m': '5Min', '15m': '15Min', '1h': '1Hour'}
    tf = tf_map.get(timeframe, '5Min')
    start = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    end   = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    params = {"timeframe": tf, "start": start, "end": end,
              "limit": 5000, "feed": "iex", "sort": "asc"}
    data = _alpaca_get(_ALPACA_DATA_URL, f"stocks/{ticker}/bars", params)
    if not data or not data.get("bars"):
        return pd.DataFrame()
    rows = data["bars"]
    df = pd.DataFrame(rows)
    df.rename(columns={"o": "Open", "h": "High", "l": "Low",
                        "c": "Close", "v": "Volume", "t": "Datetime"}, inplace=True)
    df["Datetime"] = pd.to_datetime(df["Datetime"])
    df.set_index("Datetime", inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]

def _alpaca_snapshot(ticker: str) -> dict | None:
    """Latest price snapshot from Alpaca."""
    data = _alpaca_get(_ALPACA_DATA_URL, f"stocks/{ticker}/snapshot", {"feed": "iex"})
    return data  # returns latestTrade, latestQuote, minuteBar, etc.

def alpaca_account():
    """Print paper account summary — equity, buying power, P&L."""
    result = _alpaca_get(_ALPACA_PAPER_URL, "account")
    if not result:
        print("⚠️  Not connected. Call set_alpaca_keys() first.")
        return
    equity    = float(result.get("equity", 0))
    cash      = float(result.get("cash", 0))
    bp        = float(result.get("buying_power", 0))
    pl        = float(result.get("unrealized_pl", 0))
    last_eq   = float(result.get("last_equity", equity))
    day_pl    = equity - last_eq
    print(f"\n{'═'*42}")
    print(f"  📋 ALPACA PAPER ACCOUNT")
    print(f"{'═'*42}")
    print(f"  Equity:       ${equity:>10,.2f}")
    print(f"  Cash:         ${cash:>10,.2f}")
    print(f"  Buying power: ${bp:>10,.2f}")
    print(f"  Day P&L:      ${day_pl:>+10,.2f}")
    print(f"  Open P&L:     ${pl:>+10,.2f}")
    print(f"{'═'*42}\n")


# ══ FMP API — real-time data layer ══════════════════════════════════════════

FMP_API_KEY = None  # set with: set_fmp_key('your_key_here')

def set_fmp_key(key: str):
    """Set your FMP API key (financialmodelingprep.com — free tier, 250 req/day)."""
    global FMP_API_KEY
    FMP_API_KEY = key
    result = _fmp_gainers()
    if result is not None:
        print(f"✅ FMP API connected — real-time gainers active ({len(result)} stocks today)")
    else:
        print(f"⚠️  FMP API key set but connection test failed. Check the key.")

def _fmp_gainers(max_price: float = 15.0, min_price: float = 0.10) -> list | None:
    """Fetch real-time top gainers from FMP. Free tier: 250 req/day."""
    if not FMP_API_KEY or not _requests:
        return None
    try:
        url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={FMP_API_KEY}"
        r = _requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        return [g for g in data
                if min_price <= (g.get("price") or 0) <= max_price]
    except Exception:
        return None


# ══ TOOL 1: POSITION SIZE CALCULATOR ════════════════════════════════════════

def pos_size(account_cash: float, entry_price: float, signal_price: float = None,
             shares_override: int = None):
    """
    Calculate position size for a W118 trade.

    Args:
        account_cash:   Trading cash available (e.g. 213)
        entry_price:    Price you're entering at
        signal_price:   BUY signal price (to check chase %)
        shares_override: Override calculated shares with a specific number
    """
    stop      = round(entry_price * 0.92, 2)   # hard -8% stop
    risk_ps   = entry_price - stop              # risk per share
    t1        = round(entry_price * 1.15, 2)
    t2        = round(entry_price * 1.30, 2)
    t3        = round(entry_price * 1.60, 2)

    # Share counts at different risk levels
    shares_5  = max(1, int((account_cash * 0.05) / risk_ps))
    shares_10 = max(1, int((account_cash * 0.10) / risk_ps))
    shares_max = max(1, int(account_cash / entry_price))

    # Chase check
    chase_pct = ((entry_price - signal_price) / signal_price * 100) if signal_price else None

    LINE = "─" * 42
    print(f"\n{'═'*42}")
    print(f"  💰 POSITION SIZE CALCULATOR")
    print(f"{'═'*42}")
    print(f"  Account cash:   ${account_cash:,.2f}")
    print(f"  Entry price:    ${entry_price:.2f}")

    if chase_pct is not None:
        flag = "✅" if chase_pct <= 3 else "⚠️ " if chase_pct <= 8 else "🚨"
        chase_label = "clean entry" if chase_pct <= 3 else "borderline chase" if chase_pct <= 8 else "BUS CHASE — wait for re-entry"
        print(f"  Signal price:   ${signal_price:.2f}  →  {flag} {chase_pct:.1f}% above ({chase_label})")

    print(f"\n  {LINE}")
    print(f"  🛑  Stop loss:   ${stop:.2f}  (-8%)")
    print(f"  🎯  T1 target:   ${t1:.2f}  (+15%) — trim 1/3, move stop to breakeven")
    print(f"  🎯  T2 target:   ${t2:.2f}  (+30%) — trim 1/3, trail 10%")
    print(f"  🎯  T3 target:   ${t3:.2f}  (+60%) — trail final 1/3, let it run")
    print(f"\n  {LINE}")
    print(f"  📊  Sizing options:")
    print(f"      Conservative  (5% risk):  {shares_5:>4} shares  → max loss ${shares_5*risk_ps:>6.2f}")
    print(f"      Standard     (10% risk):  {shares_10:>4} shares  → max loss ${shares_10*risk_ps:>6.2f}")
    print(f"      All-in (max afford):       {shares_max:>4} shares  → position ${shares_max*entry_price:>6.2f}")

    if shares_override:
        loss = shares_override * risk_ps
        pct  = loss / account_cash * 100
        print(f"\n  You entered {shares_override} shares:")
        print(f"      Position value: ${shares_override * entry_price:.2f}")
        print(f"      Max loss:       ${loss:.2f}  ({pct:.1f}% of account)")

    print(f"{'═'*42}\n")


# ══ TOOL 2: CHART AUTO-GRADER ═══════════════════════════════════════════════

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def _stoch_rsi(close: pd.Series, rsi_len=14, stoch_len=14, k_smooth=3, d_smooth=3):
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=rsi_len - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=rsi_len - 1, adjust=False).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    rsi      = 100 - 100 / (1 + rs)
    lo       = rsi.rolling(stoch_len).min()
    hi       = rsi.rolling(stoch_len).max()
    stoch    = (rsi - lo) / (hi - lo).replace(0, np.nan) * 100
    k        = stoch.rolling(k_smooth).mean()
    d        = k.rolling(d_smooth).mean()
    return k, d

def _zlsma(close: pd.Series, period=50) -> pd.Series:
    e1 = _ema(close, period)
    e2 = _ema(e1, period)
    return 2 * e1 - e2

def _sha_green(df: pd.DataFrame) -> pd.Series:
    """Smoothed Heikin Ashi — returns True where candle is green."""
    ha_close = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    ha_open  = ha_close.copy()
    for i in range(1, len(df)):
        ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2
    sha_c = _ema(ha_close, 10)
    sha_o = _ema(ha_open, 10)
    return sha_c > sha_o

def grade_ticker(ticker: str, timeframe: str = '5m', period: str = '5d',
                 signal_price: float = None) -> dict | None:
    """
    Download live chart data and check all W118 entry conditions.

    Args:
        ticker:       Stock symbol (e.g. 'QTTB')
        timeframe:    '1m' or '5m' (default '5m')
        period:       yfinance period string — must be '1d','5d','1mo','3mo','6mo','1y'
                      (NOT '5m' or '1m' — those are intervals, not periods)
        signal_price: BUY signal price for chase check (optional)

    Returns: dict with score and values, or None on error
    """
    # Guard against common mistake of passing interval as period
    _invalid_periods = {'1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h'}
    if period in _invalid_periods:
        print(f"  ⚠  period='{period}' is an interval, not a period. Using '5d' instead.")
        period = '5d'

    print(f"\n{'═'*42}")
    print(f"  📊 CHART GRADER — {ticker} ({timeframe})")
    print(f"{'═'*42}")

    # Data source priority: Alpaca → Massive → yfinance
    data = pd.DataFrame()
    source = "yfinance"

    if ALPACA_KEY_ID:
        data = _alpaca_bars(ticker, timeframe, days=5)
        if not data.empty and len(data) >= 30:
            source = "Alpaca"
        else:
            data = pd.DataFrame()

    if data.empty and MASSIVE_API_KEY:
        data = _massive_bars(ticker, timeframe, days=5)
        if not data.empty and len(data) >= 30:
            source = "Massive"
        else:
            data = pd.DataFrame()

    if data.empty:
        attempts = [
            (period, timeframe),
            ('5d',  timeframe),
            ('1mo', timeframe),
            ('5d',  '1m'),
            ('7d',  '1m'),
        ]
        for try_period, try_tf in attempts:
            data = yf.download(ticker, period=try_period, interval=try_tf,
                               progress=False, prepost=True)
            if not data.empty and len(data) >= 30:
                if try_period != period or try_tf != timeframe:
                    print(f"  ℹ  Using period='{try_period}' tf='{try_tf}' (auto-fallback)")
                timeframe = try_tf
                break
        if not data.empty:
            # Flatten MultiIndex columns (yfinance 0.2+)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)

    if data.empty or len(data) < 30:
        print(f"  ⚠  No data found for {ticker}. Check the ticker symbol is correct.")
        print(f"     (Some foreign/new listings aren't available in yfinance)")
        return None

    print(f"  📡 Data: {source}")

    close  = data['Close'].astype(float)
    volume = data['Volume'].astype(float)
    price  = float(close.iloc[-1])

    k, d     = _stoch_rsi(close)
    zl       = _zlsma(close)
    sha      = _sha_green(data)
    vol_avg  = volume.rolling(20).mean()

    k_now  = float(k.iloc[-1])
    k_prev = float(k.iloc[-2])
    d_now  = float(d.iloc[-1])
    zl_now = float(zl.iloc[-1])
    sha_now = bool(sha.iloc[-1])
    rv      = float(volume.iloc[-1] / vol_avg.iloc[-1]) if vol_avg.iloc[-1] > 0 else 0

    # W118 conditions
    stoch_ok = (k_prev < 20) and (k_now >= 20) and (k_now > d_now)
    sha_ok   = sha_now
    zl_ok    = price > zl_now
    vol_ok   = rv >= 1.5
    price_ok = 0.10 <= price <= 15.0

    # Bonus: K depth check (was K < 10 recently = stronger signal)
    k_min_recent = float(k.iloc[-10:].min())
    k_depth_bonus = k_min_recent < 10

    conds  = [stoch_ok, sha_ok, zl_ok, vol_ok, price_ok]
    score  = sum(conds)

    chase_pct = ((price - signal_price) / signal_price * 100) if signal_price else None

    LINE = "─" * 42
    print(f"  Price:     ${price:.4f}")
    if chase_pct is not None:
        flag = "✅" if chase_pct <= 3 else "⚠️ " if chase_pct <= 8 else "🚨"
        print(f"  Signal:    ${signal_price:.2f}  ({flag} {chase_pct:.1f}% above)")
    print(f"\n  {LINE}")
    print(f"  {'✅' if stoch_ok else '❌'}  Stoch RSI K curl ↑ thru 20, K>D")
    print(f"       K={k_now:.1f}  D={d_now:.1f}  prev_K={k_prev:.1f}")
    if k_depth_bonus:
        print(f"       ⭐ K reached {k_min_recent:.1f} recently (deep curl = stronger)")
    print(f"  {'✅' if sha_ok else '❌'}  SHA candle {'GREEN' if sha_ok else 'RED'}")
    print(f"  {'✅' if zl_ok else '❌'}  Price {'above' if zl_ok else 'BELOW'} ZLSMA-50  (ZLSMA=${zl_now:.4f})")
    if not zl_ok:
        print(f"       🚫 BELOW ZLSMA — W118 says NO TRADE")
    print(f"  {'✅' if vol_ok else '❌'}  Relative volume {rv:.1f}x  (need ≥1.5x)")
    print(f"  {'✅' if price_ok else '❌'}  Price ${price:.2f} {'in range' if price_ok else 'OUT OF $0.10–$15 range'}")
    print(f"\n  {LINE}")

    if score == 5:
        grade = "🏆 A+ — FIRE. All conditions green."
    elif score == 4 and zl_ok:
        grade = "✅ A  — Strong. One condition missing."
    elif score == 3 and zl_ok:
        grade = "🟡 B  — Wait for more confirmation."
    elif not zl_ok:
        grade = "🚫 F  — BELOW ZLSMA. Do not trade."
    else:
        grade = "❌ NO-GO — Too many conditions missing."

    print(f"  GRADE: {grade}  ({score}/5)")

    if score == 5:
        stop = price * 0.92
        print(f"\n  ⚡ VALID ENTRY — Set stop at ${stop:.2f} immediately after fill")

    print(f"{'═'*42}\n")

    return {
        'ticker': ticker, 'price': price, 'score': score,
        'k': k_now, 'd': d_now, 'rv': rv, 'zl_ok': zl_ok,
        'grade': grade
    }


# ══ TOOL 3: MORNING SCANNER ══════════════════════════════════════════════════

def _quick_k(ticker: str) -> float | None:
    """Fast K-value snapshot — used to pre-filter scanner candidates."""
    try:
        data = pd.DataFrame()
        if ALPACA_KEY_ID:
            data = _alpaca_bars(ticker, '5m', days=5)
        if data.empty and MASSIVE_API_KEY:
            data = _massive_bars(ticker, '5m', days=5)
        if data.empty:
            data = yf.download(ticker, period='5d', interval='5m',
                               progress=False, prepost=True)
            if not data.empty and isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
        if data.empty or len(data) < 30:
            return None
        close = data['Close'].astype(float)
        k, _ = _stoch_rsi(close)
        return round(float(k.iloc[-1]), 1)
    except Exception:
        return None


def morning_scan(min_change_pct: float = 10.0, max_price: float = 15.0,
                 max_float_m: float = 10.0, grade_top: int = 5,
                 k_max: float = 40.0):
    """
    Scan for W118 candidates using FMP real-time gainers + Alpaca bar data.

    Args:
        min_change_pct: Minimum % gain today (default 10%)
        max_price:      Max stock price (default $15)
        max_float_m:    Max float in millions (default 10M — tightened 2026-06-05)
        grade_top:      How many candidates to auto-grade (default 5)
        k_max:          Only grade tickers where K < this value (default 40)
    """
    if not FMP_API_KEY:
        print("⚠️  FMP key not set. Call set_fmp_key('YOUR_KEY') first.")
        print("    Get a free key at: financialmodelingprep.com")
        return

    print(f"\n{'═'*42}")
    print(f"  🔍 W118 SCANNER  (FMP real-time gainers)")
    print(f"  Filters: >{min_change_pct}% | <${max_price} | Float<{max_float_m}M")
    print(f"  Grading only K<{k_max} (skips overbought)")
    print(f"{'═'*42}\n")

    gainers = _fmp_gainers(max_price=max_price)
    if not gainers:
        print("  No gainers returned. Check FMP key or market hours.")
        return

    # Build a simple DataFrame for display
    rows = []
    for g in gainers:
        chg = g.get("changesPercentage") or g.get("changePercent") or 0
        vol = g.get("volume") or 0
        price = g.get("price") or 0
        if chg < min_change_pct:
            continue
        if vol < 1_000_000:  # absolute volume filter
            continue
        rows.append({
            "Ticker":  g.get("symbol", ""),
            "Price":   price,
            "Change":  chg,
            "Volume":  vol,
            "Company": g.get("name", ""),
        })

    if not rows:
        print(f"  No candidates >{min_change_pct}% with vol>1M right now.")
        return

    import pandas as pd
    df = pd.DataFrame(rows).sort_values("Change", ascending=False)

    # Quick K pre-check on top 15 candidates
    print(f"  Quick K-check on top 15 candidates (skipping K>{k_max})...\n")
    tickers_top = list(df['Ticker'].head(15))
    k_values = {}
    for t in tickers_top:
        k_val = _quick_k(t)
        k_values[t] = k_val
        bar = '🟢' if k_val is not None and k_val < 20 else '🟡' if k_val is not None and k_val < 40 else '🔴'
        k_str = f"K={k_val}" if k_val is not None else "K=n/a"
        print(f"    {bar} {t:<6}  {k_str}")

    print(f"\n  Found {len(df)} candidates:\n")
    print(f"  {'#':>2}  {'Ticker':<7}  {'Price':>6}  {'Change':>7}  {'K':>6}  {'Volume':>10}  Company")
    print(f"  {'─'*72}")
    for i, (_, row) in enumerate(df.head(15).iterrows(), 1):
        t = row['Ticker']
        k_val = k_values.get(t)
        k_str = f"{k_val:>5.1f}" if k_val is not None else "  n/a"
        flag = ' 🎯' if k_val is not None and k_val < 20 else ''
        print(f"  {i:>2}. {t:<7}  ${float(row['Price']):>5.2f}  {row['Change']:>+6.1f}%  {k_str}  {str(row['Volume']):>10}  {str(row.get('Company',''))[:18]}{flag}")

    # Grade only candidates with K < k_max, up to grade_top
    fresh = [t for t in tickers_top if k_values.get(t) is not None and k_values[t] < k_max]
    fresh_sorted = sorted(fresh, key=lambda t: k_values[t])   # lowest K first

    if not fresh:
        print(f"\n  ⚠  No candidates with K<{k_max} right now. Market may be mid-run.")
        print(f"     Try again in 30 min, or use: morning_scan(k_max=60) to loosen")
        return

    print(f"\n  {len(fresh)} candidates have K<{k_max} — grading top {min(grade_top, len(fresh))} (lowest K first)...\n")
    results = []
    for ticker in fresh_sorted[:grade_top]:
        r = grade_ticker(ticker)
        if r:
            results.append(r)

    if results:
        results.sort(key=lambda x: x['score'], reverse=True)
        print(f"\n{'═'*42}")
        print(f"  🏆 FINAL RANKING")
        print(f"{'═'*42}")
        for i, r in enumerate(results, 1):
            zlsma_flag = "" if r['zl_ok'] else "  🚫 BELOW ZLSMA"
            print(f"  {i}. {r['ticker']:<6}  {r['score']}/5  K={r['k']:.0f}  RV={r['rv']:.1f}x  ${r['price']:.2f}{zlsma_flag}")
        print(f"{'═'*42}\n")
        print(f"  Top pick: {results[0]['ticker']} — {results[0]['grade']}")


# ══ QUICK START ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("W118 Toolkit loaded. Available commands:")
    print("  pos_size(213, 9.45, signal_price=8.37)")
    print("  grade_ticker('QTTB')")
    print("  morning_scan()")
