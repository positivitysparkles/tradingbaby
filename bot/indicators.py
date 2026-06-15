"""W118 technical indicator calculations — pure Python, no pandas/numpy needed."""


def _ema(values: list, period: int) -> list:
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def zlsma(closes: list, period: int = 50) -> float | None:
    """Zero-Lag SMA: 2×EMA(n) − EMA(EMA(n)). Price must be ABOVE this to enter."""
    if len(closes) < period * 2:
        return None
    e1 = _ema(closes, period)
    e2 = _ema(e1, period)
    return 2 * e1[-1] - e2[-1]


def stochrsi(closes: list) -> tuple[float | None, float | None]:
    """StochRSI(14,14,3,3). Returns (K, D). Entry requires K > D."""
    rp, sp, ks, ds = 14, 14, 3, 3
    if len(closes) < rp + sp + ks + ds:
        return None, None

    ch = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    ag = sum(max(c, 0) for c in ch[:rp]) / rp
    al = sum(max(-c, 0) for c in ch[:rp]) / rp
    rsi_vals = []
    for i in range(rp, len(ch)):
        ag = (ag * (rp - 1) + max(ch[i], 0)) / rp
        al = (al * (rp - 1) + max(-ch[i], 0)) / rp
        rsi_vals.append(100 - 100 / (1 + ag / al) if al else 100)

    raw_k = []
    for i in range(sp - 1, len(rsi_vals)):
        window = rsi_vals[i - sp + 1 : i + 1]
        lo, hi = min(window), max(window)
        raw_k.append(0 if hi == lo else (rsi_vals[i] - lo) / (hi - lo) * 100)

    sk = [sum(raw_k[i - ks + 1 : i + 1]) / ks for i in range(ks - 1, len(raw_k))]
    sd = [sum(sk[i - ds + 1 : i + 1]) / ds for i in range(ds - 1, len(sk))]

    if len(sk) < 2 or not sd:
        return None, None
    return sk[-1], sd[-1]


def macd_hist(closes: list) -> float | None:
    """MACD(12,26,9) histogram. Must be > 0 to enter (momentum building, not fading)."""
    if len(closes) < 35:
        return None
    e12 = _ema(closes, 12)
    e26 = _ema(closes, 26)
    macd_line = [a - b for a, b in zip(e12, e26)]
    sig_line = _ema(macd_line, 9)
    return macd_line[-1] - sig_line[-1]


def supertrend(bars: list, period: int = 10, mult: float = 2.0) -> int | None:
    """
    Supertrend(ATR=10, source=hl2, mult=2). Returns 1=bullish, -1=bearish.
    This is the PRIMARY entry trigger — enter when it flips to 1.
    """
    if len(bars) < period + 2:
        return None

    highs  = [b["h"] for b in bars]
    lows   = [b["l"] for b in bars]
    closes = [b["c"] for b in bars]

    # Wilder's ATR
    trs = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(1, len(bars))
    ]
    atr = [0.0] * len(trs)
    atr[period - 1] = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr[i] = (atr[i - 1] * (period - 1) + trs[i]) / period

    ub = [0.0] * len(bars)
    lb = [0.0] * len(bars)
    d  = [1]   * len(bars)

    for i in range(period, len(bars)):
        hl2 = (highs[i] + lows[i]) / 2
        a   = atr[i - 1]
        rub = hl2 + mult * a
        rlb = hl2 - mult * a

        if i == period:
            ub[i] = rub; lb[i] = rlb; d[i] = 1
            continue

        # Bands only move toward price (persistence rule)
        ub[i] = rub if (rub < ub[i - 1] or closes[i - 1] > ub[i - 1]) else ub[i - 1]
        lb[i] = rlb if (rlb > lb[i - 1] or closes[i - 1] < lb[i - 1]) else lb[i - 1]

        if   d[i - 1] == -1 and closes[i] > ub[i]: d[i] = 1
        elif d[i - 1] ==  1 and closes[i] < lb[i]: d[i] = -1
        else: d[i] = d[i - 1]

    return d[-1]


def check_all_entry(bars: list, min_price: float, max_price: float, rel_vol_min: float) -> tuple[bool, dict]:
    """
    Run all 5 W118 entry conditions. Returns (passed, details_dict).
    bars: list of dicts with keys h, l, c, v (from Alpaca IEX)
    """
    closes = [b["c"] for b in bars]
    price  = closes[-1]

    if not (min_price <= price <= max_price):
        return False, {"fail": "price_range", "price": price}

    # 1. Supertrend bullish — PRIMARY trigger
    st = supertrend(bars)
    if st != 1:
        return False, {"fail": "supertrend_bearish"}

    # 2. StochRSI K > D
    k, d = stochrsi(closes)
    if k is None or k <= d:
        fail = f"K {k:.1f} <= D {d:.1f}" if k is not None else "stochrsi_error"
        return False, {"fail": fail}

    # 3. Price above ZLSMA-50
    zl = zlsma(closes)
    if zl is None or price <= zl:
        fail = f"price ${price:.4f} below ZLSMA ${zl:.4f}" if zl is not None else "zlsma_error"
        return False, {"fail": fail}

    # 4. MACD histogram > 0
    hist = macd_hist(closes)
    if hist is None or hist <= 0:
        fail = f"MACD hist {hist:.5f}" if hist is not None else "macd_error"
        return False, {"fail": fail}

    # 5. Volume > rel_vol_min × 20-bar average
    vols    = [b["v"] for b in bars[-21:-1]]
    avg_vol = sum(vols) / len(vols) if vols else 0
    cur_vol = bars[-1]["v"]
    if cur_vol < avg_vol * rel_vol_min:
        return False, {"fail": f"vol {cur_vol:.0f} < {rel_vol_min}x avg {avg_vol:.0f}"}

    return True, {
        "price":      price,
        "k":          round(k, 1),
        "d":          round(d, 1),
        "zlsma":      round(zl, 4),
        "macd_hist":  round(hist, 6),
        "vol_ratio":  round(cur_vol / avg_vol, 1) if avg_vol else 0,
    }


def check_exit_signal(bars: list) -> str | None:
    """
    Check W118 signal-based exits. Returns reason string or None.
    Called on every scan cycle for each open position.
    """
    closes = [b["c"] for b in bars]

    k, _ = stochrsi(closes)
    if k is not None and k < 20:
        return f"K_below_20 (K={k:.1f})"

    price = closes[-1]
    zl = zlsma(closes)
    if zl and price < zl:
        return f"below_ZLSMA (price={price:.4f} ZLSMA={zl:.4f})"

    st = supertrend(bars)
    if st == -1:
        return "supertrend_bearish"

    return None
