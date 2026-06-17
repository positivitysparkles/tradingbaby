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


def stochrsi(closes: list) -> tuple[float | None, float | None, float | None]:
    """
    StochRSI(14,14,3,3). Returns (K, D, K_prev).
    Entry requires K > D AND K rising (K > K_prev).
    """
    rp, sp, ks, ds = 14, 14, 3, 3
    if len(closes) < rp + sp + ks + ds:
        return None, None, None

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
        return None, None, None
    return sk[-1], sd[-1], sk[-2]


def macd_hist(closes: list) -> float | None:
    """
    MACD(5,10,16) histogram. Blue line (MACD) must be above red line (signal).
    Faster settings than standard 12,26,9 — fires earlier, in sync with Supertrend.
    """
    if len(closes) < 32:
        return None
    e5  = _ema(closes, 5)
    e10 = _ema(closes, 10)
    macd_line = [a - b for a, b in zip(e5, e10)]
    sig_line  = _ema(macd_line, 16)
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
    Run all W118 entry conditions. Returns (passed, details_dict).

    Checks ALL conditions instead of short-circuiting so we can score
    partial setups (4/5) for WATCH alerts. ZLSMA is skipped (not failed)
    when insufficient bar history — the other 4 conditions are sufficient.

    info dict always contains: score, max, blockers, price, k, d, vol_ratio
    On full pass: fail=None. On partial: fail = joined blocker string.
    """
    closes = [b["c"] for b in bars]
    price  = closes[-1]

    if not (min_price <= price <= max_price):
        return False, {"fail": "price_range", "price": price, "score": 0, "max": 5,
                       "blockers": ["price out of range"], "k": None, "d": None,
                       "vol_ratio": 0, "zlsma": None, "macd_hist": None}

    passed   = 0
    blockers = []

    # 1. Supertrend bullish — PRIMARY trigger
    st = supertrend(bars)
    if st == 1:
        passed += 1
    else:
        blockers.append("Supertrend bearish")

    # 2. StochRSI K > D AND K rising
    k, d, k_prev = stochrsi(closes)
    if k is None:
        blockers.append("StochRSI error")
    elif k <= d:
        blockers.append(f"K {k:.1f} below D {d:.1f}")
    elif k_prev is not None and k < k_prev:
        blockers.append(f"Stoch not rising ({k_prev:.1f}→{k:.1f})")
    else:
        passed += 1

    # 3. Price above ZLSMA-50 — skip (not fail) when insufficient bar history.
    #    New stocks / halted-and-resumed may have <100 5m bars; the other 4
    #    conditions are strong enough without ZLSMA in those cases.
    zl = zlsma(closes)
    if zl is None:
        pass   # not enough history — treat as unknown, not a failure
    elif price > zl:
        passed += 1
    else:
        blockers.append(f"below ZLSMA ${zl:.3f}")

    # 4. MACD(5,10,16) histogram > 0
    hist = macd_hist(closes)
    if hist is None:
        blockers.append("MACD error")
    elif hist > 0:
        passed += 1
    else:
        blockers.append(f"MACD {hist:.4f}")

    # 5. Volume > rel_vol_min × 20-bar average
    vols    = [b["v"] for b in bars[-21:-1]]
    avg_vol = sum(vols) / len(vols) if vols else 0
    cur_vol = bars[-1]["v"]
    vol_ratio = cur_vol / avg_vol if avg_vol else 0
    if vol_ratio >= rel_vol_min:
        passed += 1
    else:
        blockers.append(f"vol {vol_ratio:.1f}x below {rel_vol_min:.0f}x")

    # Max possible is 4 when ZLSMA is skipped, 5 otherwise
    max_possible = 5 if zl is not None else 4

    info = {
        "price":     price,
        "score":     passed,
        "max":       max_possible,
        "k":         round(k, 1)      if k    is not None else None,
        "d":         round(d, 1)      if d    is not None else None,
        "k_prev":    round(k_prev, 1) if k_prev is not None else None,
        "zlsma":     round(zl, 4)     if zl   is not None else None,
        "macd_hist": round(hist, 5)   if hist  is not None else None,
        "vol_ratio": round(vol_ratio, 1),
        "blockers":  blockers,
        "fail":      " | ".join(blockers) if blockers else None,
    }

    return (passed >= max_possible), info


def check_exit_signal(bars: list) -> str | None:
    """
    Check W118 signal-based exits. Returns reason string or None.
    Called on every scan cycle for each open position.
    """
    closes = [b["c"] for b in bars]

    k, _, _ = stochrsi(closes)
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
