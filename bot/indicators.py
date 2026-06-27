"""W118 technical indicator calculations — pure Python, no pandas/numpy needed."""


def _ema(values: list, period: int) -> list:
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def rsi(closes: list, period: int = 14) -> float | None:
    """RSI(period). Returns 0–100 or None when insufficient data."""
    if len(closes) < period + 1:
        return None
    ch = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    ag = sum(max(c, 0) for c in ch[:period]) / period
    al = sum(max(-c, 0) for c in ch[:period]) / period
    for c in ch[period:]:
        ag = (ag * (period - 1) + max(c, 0)) / period
        al = (al * (period - 1) + max(-c, 0)) / period
    return 100 - 100 / (1 + ag / al) if al else 100


def zlsma(closes: list, period: int = 50) -> float | None:
    """Zero-Lag SMA: 2×EMA(n) − EMA(EMA(n)). Price must be ABOVE this to enter."""
    if len(closes) < period * 2:
        return None
    e1 = _ema(closes, period)
    e2 = _ema(e1, period)
    return 2 * e1[-1] - e2[-1]


def stochrsi(closes: list, curl_lookback: int = 12
            ) -> tuple[float | None, float | None, float | None, float | None]:
    """
    StochRSI(14,14,3,3). Returns (K, D, K_prev, K_recent_low).
    Entry requires K > D AND K rising (K > K_prev).
    K_recent_low = lowest smoothed-K over the last `curl_lookback` bars — used to
    flag a "deep curl" (K reloaded near 0 before turning up = stronger setup).
    """
    rp, sp, ks, ds = 14, 14, 3, 3
    if len(closes) < rp + sp + ks + ds:
        return None, None, None, None

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
        return None, None, None, None
    recent_low = min(sk[-curl_lookback:])
    return sk[-1], sd[-1], sk[-2], recent_low


def macd(closes: list, fast: int = 5, slow: int = 10, signal: int = 16) -> tuple[float | None, float | None]:
    """
    MACD. Returns (macd_line, histogram).
    Default (5,10,16) = W118 fast — fires in sync with Supertrend.
    Call with (12,26,9) for standard MACD (Setup B).
    """
    min_len = slow + signal + 2
    if len(closes) < min_len:
        return None, None
    e_fast = _ema(closes, fast)
    e_slow = _ema(closes, slow)
    macd_line = [a - b for a, b in zip(e_fast, e_slow)]
    sig_line  = _ema(macd_line, signal)
    return macd_line[-1], macd_line[-1] - sig_line[-1]


def macd_hist(closes: list) -> float | None:
    """Back-compat helper — just the histogram from macd()."""
    return macd(closes)[1]


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


def pivot_point_supertrend(bars: list, pivot_period: int = 2,
                           atr_factor: float = 3.0, atr_period: int = 10) -> int | None:
    """
    Pivot Point SuperTrend. Returns 1=bullish, -1=bearish.
    Settings from IMG_4105: Pivot Period=2, ATR Factor=3, ATR Period=10.
    Anchors ATR bands on confirmed swing pivot highs/lows (period bars each side) rather than
    rolling hl2 — bands only step when a new pivot is confirmed, reducing whipsaw vs. regular ST.
    """
    min_bars = pivot_period * 2 + atr_period + 2
    if len(bars) < min_bars:
        return None
    highs  = [b["h"] for b in bars]
    lows   = [b["l"] for b in bars]
    closes = [b["c"] for b in bars]

    # Wilder's ATR (same as supertrend())
    trs = [max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
           for i in range(1, len(bars))]
    atr_v = [0.0] * len(trs)
    atr_v[atr_period - 1] = sum(trs[:atr_period]) / atr_period
    for i in range(atr_period, len(trs)):
        atr_v[i] = (atr_v[i - 1] * (atr_period - 1) + trs[i]) / atr_period

    # Track last confirmed pivot high/low.
    # A pivot at bar index conf_i is confirmed after pivot_period more bars have elapsed.
    ph = highs[0]
    pl = lows[0]
    trend = 1

    for i in range(pivot_period * 2, len(bars)):
        conf_i = i - pivot_period
        if conf_i >= pivot_period:
            lo_w, hi_w = conf_i - pivot_period, conf_i + pivot_period + 1
            if highs[conf_i] == max(highs[lo_w:hi_w]):
                ph = highs[conf_i]
            if lows[conf_i] == min(lows[lo_w:hi_w]):
                pl = lows[conf_i]
        atr = atr_v[i - 1] if i - 1 < len(atr_v) else atr_v[-1]
        upper = ph + atr_factor * atr
        lower = pl - atr_factor * atr
        if closes[i] > upper:
            trend = 1
        elif closes[i] < lower:
            trend = -1
        # else: persist previous trend

    return trend


def vwap_session(bars: list) -> float | None:
    """
    Session-anchored VWAP (matches the user's TradingView VWAP: Anchor=Session,
    Source=HL2). Resets each trading day, so we average only the bars that share the
    LAST bar's date. Source = (high+low)/2, weighted by volume.

    Returns None (fail-open, like ZLSMA) when bars carry no timestamp ("t") or have
    zero volume — a young/halted name should not be blocked just for thin data.
    """
    if not bars or "t" not in bars[-1]:
        return None
    last_day = str(bars[-1]["t"])[:10]            # YYYY-MM-DD of the latest bar
    num = den = 0.0
    for b in bars:
        if str(b.get("t", ""))[:10] != last_day:
            continue
        v = b.get("v", 0) or 0
        hl2 = (b["h"] + b["l"]) / 2
        num += hl2 * v
        den += v
    return (num / den) if den else None


def chandelier_exit(bars: list, period: int = 10, mult: float = 2.0) -> dict | None:
    """
    Chandelier Exit (ATR=10, mult=2, use-close for extremums) — the user's CE 10 2.
    Long-stop = highest_close(period) − mult × ATR(period). State is bullish while
    close holds above the long-stop, and flips bearish on a close below it.

    Returns {"long_stop": float, "state": 1|-1} or None when history is too thin.
    Mirrors the Wilder-ATR used in supertrend().
    """
    if len(bars) < period + 2:
        return None

    highs  = [b["h"] for b in bars]
    lows   = [b["l"] for b in bars]
    closes = [b["c"] for b in bars]

    trs = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(1, len(bars))
    ]
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period

    # "Use close price for extremums" = highest CLOSE over the lookback, not highest high
    highest_close = max(closes[-period:])
    long_stop = highest_close - mult * atr
    state = 1 if closes[-1] >= long_stop else -1
    return {"long_stop": long_stop, "state": state}


def check_all_entry(bars: list, min_price: float, max_price: float, rel_vol_min: float,
                    deep_curl_reset: float = 20.0, vwap_tol: float = 0.005,
                    vwap_gate: bool = True, overbought_k: float = 85.0,
                    pivot_period: int = 2, atr_factor: float = 3.0) -> tuple[bool, dict]:
    """
    Run all W118 entry conditions. Returns (CORE_pass, details_dict).

    The first return value is the AUTO-BUY gate = the priority-tier "core":
      Tier-1 (Supertrend green + above VWAP + above ZLSMA) + Stoch hook (K>D & rising,
      not overbought) + MACD histogram > 0.
    Volume and MACD-line-above-zero are SOFT — they raise the score/grade but do NOT
    block a buy (6/6 rarely lines up; the Edge Engine prunes weak grades via learn→
    tighten). `score`/`max` in the info dict still tally all 6 for grading + display.

    Checks ALL conditions instead of short-circuiting so we can score
    partial setups for WATCH alerts. ZLSMA / VWAP are skipped (not failed)
    when insufficient bar history.

    `deep_curl_reset`: if StochRSI K dipped below this within the lookback and is
    now curling up, the setup is flagged deep_curl=True (stronger reload). This is
    INFORMATIONAL only — it does not gate entry, just enriches alerts + the audit.

    info dict always contains: score, max, blockers, price, k, d, vol_ratio, deep_curl
    On full pass: fail=None. On partial: fail = joined blocker string.
    """
    closes = [b["c"] for b in bars]
    price  = closes[-1]

    if not (min_price <= price <= max_price):
        return False, {"fail": "price_range", "price": price, "score": 0, "max": 5,
                       "blockers": ["price out of range"], "k": None, "d": None,
                       "vol_ratio": 0, "zlsma": None, "macd_hist": None, "deep_curl": False}

    passed   = 0
    blockers = []

    # 1. Pivot Point SuperTrend bullish — PRIMARY trigger (Period=2, Factor=3, ATR=10)
    st = pivot_point_supertrend(bars, pivot_period=pivot_period, atr_factor=atr_factor)
    if st == 1:
        passed += 1
    else:
        blockers.append("Supertrend bearish")

    # 2. StochRSI K > D AND K rising
    k, d, k_prev, k_low = stochrsi(closes)
    if k is None:
        blockers.append("StochRSI error")
    elif k <= d:
        blockers.append(f"K {k:.1f} below D {d:.1f}")
    elif k_prev is not None and k < k_prev:
        blockers.append(f"Stoch not rising ({k_prev:.1f}→{k:.1f})")
    else:
        passed += 1

    # Deep-curl flag (informational, not a gate): K reloaded near 0 then turned up.
    deep_curl = (k_low is not None and k_low <= deep_curl_reset)

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

    # 4. MACD(5,10,16): blue line above ZERO (sustained uptrend) AND histogram > 0
    #    (momentum turning up). Both = the A+ runner structure. Line-above-zero is
    #    what the histogram-only check was missing — it rejects dead-cat bounces.
    m_line, hist = macd(closes)
    if hist is None or m_line is None:
        blockers.append("MACD error")
    elif m_line <= 0:
        blockers.append(f"MACD line {m_line:.4f} below zero (not in uptrend)")
    elif hist <= 0:
        blockers.append(f"MACD hist {hist:.4f} (momentum fading)")
    else:
        passed += 1

    # 5. Volume > rel_vol_min × 20-bar average.
    #    yfinance pads the live edge with 0-volume "forming" bars, so a naive bars[-2]
    #    reads 0 → "Vol 0.0x" false rejections on EVERY ticker (blocks all auto-buys).
    #    Strip trailing 0-volume bars first, then use the last CLOSED bar (vbars[-2]).
    vbars = bars
    while len(vbars) > 22 and vbars[-1]["v"] == 0:
        vbars = vbars[:-1]
    vols    = [b["v"] for b in vbars[-22:-2]]  # 20 completed bars before the last closed
    avg_vol = sum(vols) / len(vols) if vols else 0
    cur_vol = vbars[-2]["v"]                   # last CLOSED bar (trailing zeros stripped)
    vol_ratio = cur_vol / avg_vol if avg_vol else 0
    if vol_ratio >= rel_vol_min:
        passed += 1
    else:
        blockers.append(f"vol {vol_ratio:.1f}x below {rel_vol_min:.1f}x")

    # 6. VWAP shelf gate — price holding above Session VWAP (the A+ Shelf Bounce's
    #    absolute support; it's what separated every runner from the WKSP chop). Hard
    #    gate WITH tolerance: a coil sitting ON the line (a sub-tolerance wick below)
    #    still counts. Fail-open (skip, not block) when VWAP can't be computed.
    vw = vwap_session(bars) if vwap_gate else None
    above_vwap = None
    if vw is None:
        pass   # no timestamps / no volume → don't block (like ZLSMA)
    elif price >= vw * (1 - vwap_tol):
        above_vwap = True
        passed += 1
    else:
        above_vwap = False
        blockers.append(f"below VWAP ${vw:.3f}")

    # 7. RSI(14) > 50 — soft momentum confirmation (score only, never gates entry)
    rsi_val = rsi(closes)

    # Max possible: start at 5, +1 if VWAP was evaluated, −1 if ZLSMA was skipped, +1 if RSI data available
    max_possible = 5
    if vw is not None:
        max_possible += 1
    if zl is None:
        max_possible -= 1
    if rsi_val is not None:
        max_possible += 1
        if rsi_val > 50:
            passed += 1
        else:
            blockers.append(f"RSI {rsi_val:.0f} below 50")

    # ── CORE auto-buy gate (priority tiers) ───────────────────────────────────
    # MUST: Supertrend green + above VWAP + above ZLSMA + Stoch hook (K>D rising,
    #       not overbought) + MACD hist > 0. Volume + MACD-line are SOFT (score only).
    # Skipped ZLSMA/VWAP (no history) count as OK — never block on missing data.
    not_overbought = (k is not None and k < overbought_k)
    stoch_hook = (k is not None and d is not None and k > d
                  and (k_prev is None or k >= k_prev))
    core_pass = (
        st == 1
        and ((zl is None) or (price > zl))            # ZLSMA: pass or skip
        and ((above_vwap is None) or (above_vwap is True))  # VWAP: pass or skip
        and stoch_hook and not_overbought
        and (hist is not None and hist > 0)           # MACD histogram (ignition)
    )

    info = {
        "price":     price,
        "score":     passed,
        "max":       max_possible,
        "core":      core_pass,
        "overbought": (k is not None and k >= overbought_k),
        "k":         round(k, 1)      if k    is not None else None,
        "d":         round(d, 1)      if d    is not None else None,
        "k_prev":    round(k_prev, 1) if k_prev is not None else None,
        "k_low":     round(k_low, 1)  if k_low is not None else None,
        "deep_curl": deep_curl,
        "zlsma":     round(zl, 4)     if zl   is not None else None,
        "vwap":      round(vw, 4)     if vw   is not None else None,
        "above_vwap": above_vwap,
        "macd_hist": round(hist, 5)     if hist    is not None else None,
        "macd_line": round(m_line, 5)   if m_line  is not None else None,
        "rsi":       round(rsi_val, 1)  if rsi_val is not None else None,
        "vol_ratio": round(vol_ratio, 1),
        "full_pass": (passed >= max_possible),
        "blockers":  blockers,
        "fail":      " | ".join(blockers) if blockers else None,
    }

    return core_pass, info


def is_fresh_1m(bars_1m: list) -> tuple[bool, str]:
    """
    Micro-timeframe freshness gate — W118's "zoom to 1m" step.

    The 5-min checks lag: by the time all 5 confirm on 5-min, the 1-min move is
    often already rolling over (e.g. ATPC bought at the $3.43 top as it faded).
    After a 5/5 pass we pull 1-min bars and only allow the entry if the 1-min
    trend is STILL alive:
      • 1-min MACD histogram > 0   (momentum still positive, not fading) — primary
      • 1-min Stoch K not falling   (micro-curl hasn't rolled over yet)

    We deliberately DON'T require 1m K>D: on a strong push StochRSI saturates at
    100 (K==D==100), which is the strongest momentum, not a stale signal. The
    decisive "rolling over" tell is MACD going negative and K turning DOWN — that
    is what caught the ATPC $3.43 top-chase (MACD already red, Stoch falling).

    Fails OPEN (returns fresh=True) when there isn't enough 1-min history to
    compute the indicators — new/halted-and-resumed names shouldn't be blocked
    just for being young. Returns (fresh, reason_if_stale).
    """
    closes = [b["c"] for b in bars_1m]

    hist = macd_hist(closes)
    if hist is None:
        return True, ""                      # not enough 1m history → don't block
    if hist <= 0:
        return False, f"1m MACD {hist:.4f} not positive (fading)"

    k, d, k_prev, _ = stochrsi(closes)
    if k is None or k_prev is None:
        return True, ""                      # not enough 1m history → don't block
    if k < k_prev:
        return False, f"1m Stoch falling ({k_prev:.1f}->{k:.1f})"

    return True, ""


def catalyst_score(bars_5m: list, daily_bars: list | None = None) -> tuple[str | None, str]:
    """
    Price-action catalyst proxy — the W118 6th condition without a news feed.
    Returns (tier, reason) where tier ∈ {"tier_1","tier_2","tier_3", None}.

      tier_1 — news-scale gap: today's open ≥20% above prior daily close
               (FDA / merger / earnings profile).
      tier_2 — halt-resume signature (an intrabar jump ≥5% on a volume spike) OR a
               day-2/3 runner (prior daily bar green with an expanding range).
      tier_3 — a mover in our universe but none of the above (weaker catalyst).
      None   — nothing notable.

    Uses Alpaca bar dicts (keys o,h,l,c,v). `daily_bars` is optional; without it the
    gap/runner checks are skipped and only the intraday halt-resume + tier_3 fallback
    apply. Pure price/volume — no API keys, nothing for the user to wire up.
    """
    if not bars_5m:
        return None, "no data"

    # 1. News-scale daily gap (needs ≥2 daily bars)
    if daily_bars and len(daily_bars) >= 2:
        prior_close = daily_bars[-2].get("c")
        today_open  = daily_bars[-1].get("o")
        if prior_close and today_open and prior_close > 0:
            gap = (today_open - prior_close) / prior_close
            if gap >= 0.20:
                return "tier_1", f"gap +{gap*100:.0f}% (news-scale)"

    # 2a. Halt-resume signature on recent 5m bars: a bar that opened far from the
    #     prior bar's close on a volume spike (the LULD resume re-print).
    recent = bars_5m[-12:]
    vols    = [b.get("v", 0) for b in recent]
    med_vol = sorted(vols)[len(vols) // 2] if vols else 0
    for i in range(1, len(recent)):
        prev_c = recent[i - 1].get("c")
        cur_o  = recent[i].get("o")
        cur_v  = recent[i].get("v", 0)
        if prev_c and cur_o and prev_c > 0:
            jump = abs(cur_o - prev_c) / prev_c
            if jump >= 0.05 and med_vol and cur_v >= 2 * med_vol:
                return "tier_2", f"halt-resume jump {jump*100:.0f}% on {cur_v/med_vol:.1f}x vol"

    # 2b. Day-2/3 runner: prior daily bar closed green with an expanding range.
    if daily_bars and len(daily_bars) >= 3:
        d1, d2 = daily_bars[-2], daily_bars[-3]
        rng1 = d1.get("h", 0) - d1.get("l", 0)
        rng2 = d2.get("h", 0) - d2.get("l", 0)
        if d1.get("c", 0) > d1.get("o", 0) and rng1 > rng2 > 0:
            return "tier_2", "day-2/3 runner (prior day green, range expanding)"

    # 3. Still a mover intraday → weak catalyst
    first_c, last_c = bars_5m[0].get("c"), bars_5m[-1].get("c")
    if first_c and last_c and first_c > 0 and (last_c - first_c) / first_c >= 0.05:
        return "tier_3", "in-momentum (intraday +5%)"

    return None, "no catalyst signal"


# ── Chart DNA — 10 numerical features describing the chart shape at entry ────

def compute_chart_dna(bars: list) -> dict:
    """
    Compute 10 numerical features describing the chart's shape at entry time.
    Returns dict with all 10 features (each float | None). Safe on sparse data —
    features that can't be computed return None (bucketing skips them).
    """
    if len(bars) < 20:
        return {}

    closes = [b["c"] for b in bars]
    highs = [b["h"] for b in bars]
    lows = [b["l"] for b in bars]
    price = closes[-1]
    dna: dict = {}

    # 1. momentum_5: short-term price acceleration (5 bars back)
    if len(closes) >= 6 and closes[-6] > 0:
        dna["momentum_5"] = round((price - closes[-6]) / closes[-6] * 100, 2)
    else:
        dna["momentum_5"] = None

    # 2. momentum_10: medium-term trend strength (10 bars back)
    if len(closes) >= 11 and closes[-11] > 0:
        dna["momentum_10"] = round((price - closes[-11]) / closes[-11] * 100, 2)
    else:
        dna["momentum_10"] = None

    # 3. vwap_dist_pct: distance from session VWAP (shelf bounce = ~0%)
    vw = vwap_session(bars)
    dna["vwap_dist_pct"] = round((price - vw) / vw * 100, 2) if vw and vw > 0 else None

    # 4. zlsma_dist_pct: how stretched above trend support
    zl = zlsma(closes)
    dna["zlsma_dist_pct"] = round((price - zl) / zl * 100, 2) if zl and zl > 0 else None

    # 5. k_reset_depth: deepest K dip in last 12 bars (lower = stronger spring)
    _, _, _, k_low = stochrsi(closes, curl_lookback=12)
    dna["k_reset_depth"] = round(k_low, 2) if k_low is not None else None

    # 6. vol_accel: recent volume acceleration (last 3 bars / prev 10 bars avg)
    vols = [b["v"] for b in bars]
    if len(vols) >= 13:
        recent_3 = sum(vols[-3:]) / 3
        prev_10 = sum(vols[-13:-3]) / 10
        dna["vol_accel"] = round(recent_3 / prev_10, 2) if prev_10 > 0 else None
    else:
        dna["vol_accel"] = None

    # 7. range_compression: coil/shelf detection (tighter = stronger breakout)
    ranges = [highs[i] - lows[i] for i in range(len(bars))]
    if len(ranges) >= 20:
        avg_5 = sum(ranges[-5:]) / 5
        avg_20 = sum(ranges[-20:]) / 20
        dna["range_compression"] = round(avg_5 / avg_20, 2) if avg_20 > 0 else None
    else:
        dna["range_compression"] = None

    # 8. day_range_pct: where in today's range (0=pullback entry, 100=chase)
    last_day = str(bars[-1].get("t", ""))[:10]
    if last_day:
        day_h = [b["h"] for b in bars if str(b.get("t", ""))[:10] == last_day]
        day_l = [b["l"] for b in bars if str(b.get("t", ""))[:10] == last_day]
        if day_h and day_l:
            dh, dl = max(day_h), min(day_l)
            rng = dh - dl
            dna["day_range_pct"] = round((price - dl) / rng * 100, 1) if rng > 0 else None
        else:
            dna["day_range_pct"] = None
    else:
        dna["day_range_pct"] = None

    # 9. rsi_entry: RSI(14) momentum confirmation
    rsi_val = rsi(closes)
    dna["rsi_entry"] = round(rsi_val, 1) if rsi_val is not None else None

    # 10. macd_slope: MACD histogram direction (hist[-1] - hist[-2])
    fast_p, slow_p, sig_p = 5, 10, 16
    if len(closes) >= slow_p + sig_p + 3:
        ef = _ema(closes, fast_p)
        es = _ema(closes, slow_p)
        ml = [a - b for a, b in zip(ef, es)]
        sl = _ema(ml, sig_p)
        hv = [ml[i] - sl[i] for i in range(len(sl))]
        if len(hv) >= 2:
            dna["macd_slope"] = round(hv[-1] - hv[-2], 6)
        else:
            dna["macd_slope"] = None
    else:
        dna["macd_slope"] = None

    return dna


# ── Setup B "Trend Rider" entry/exit ─────────────────────────────────────────

def check_setup_b_entry(bars_5m: list, min_price: float, max_price: float,
                        bars_15m: list | None = None, bars_1h: list | None = None,
                        pivot_period: int = 2, atr_factor: float = 3.0) -> tuple[bool, dict]:
    """
    Setup B entry check. Simpler than Setup A — no StochRSI, ZLSMA, or VWAP.
    CORE: PPST bullish + MACD(12,26,9) blue>orange & rising + vol up + RSI>50.
    MTF confirmation (15m/1H PPST bullish) feeds grade, doesn't block.
    """
    closes = [b["c"] for b in bars_5m]
    price  = closes[-1]
    info: dict = {"price": price, "setup": "B", "blockers": []}

    if price < min_price or price > max_price:
        info["fail"] = f"price ${price} outside range"
        return False, info

    passed, max_possible = 0, 4
    blockers: list = []

    # 1. PPST bullish on 5m
    st = pivot_point_supertrend(bars_5m, pivot_period=pivot_period, atr_factor=atr_factor)
    if st == 1:
        passed += 1
    else:
        blockers.append("PPST bearish")

    # 2. Standard MACD (12,26,9) blue > orange AND rising
    min_macd_len = 26 + 9 + 2
    if len(closes) >= min_macd_len:
        e_fast = _ema(closes, 12)
        e_slow = _ema(closes, 26)
        ml = [a - b for a, b in zip(e_fast, e_slow)]
        sl = _ema(ml, 9)
        macd_line_val = ml[-1]
        macd_line_prev = ml[-2]
        signal_val = sl[-1]
        macd_above = macd_line_val > signal_val
        macd_rising = macd_line_val > macd_line_prev
        info["macd_line_std"] = round(macd_line_val, 6)
        info["macd_signal_std"] = round(signal_val, 6)
        info["macd_rising"] = macd_rising
        if macd_above and macd_rising:
            passed += 1
        else:
            if not macd_above:
                blockers.append(f"MACD(12,26,9) blue below orange")
            elif not macd_rising:
                blockers.append(f"MACD(12,26,9) not rising")
    else:
        blockers.append("not enough bars for MACD(12,26,9)")

    # 3. Volume increasing
    vols = [b["v"] for b in bars_5m]
    vol_cur = vols[-1]
    vol_prev = vols[-2] if len(vols) >= 2 else 0
    vol_avg = sum(vols[-20:]) / min(len(vols), 20) if vols else 0
    vol_up = vol_cur > vol_prev or vol_cur > vol_avg
    info["vol_ratio"] = round(vol_cur / vol_avg, 2) if vol_avg > 0 else None
    if vol_up:
        passed += 1
    else:
        blockers.append("volume not increasing")

    # 4. RSI(14) > 50
    rsi_val = rsi(closes)
    info["rsi"] = round(rsi_val, 1) if rsi_val is not None else None
    if rsi_val is not None and rsi_val > 50:
        passed += 1
    else:
        blockers.append(f"RSI {rsi_val:.0f} ≤ 50" if rsi_val else "RSI unavailable")

    info["score"] = passed
    info["max"] = max_possible
    core_pass = passed == max_possible

    # Multi-timeframe confirmation (bonus, not blocking)
    mtf_15m = False
    mtf_1h = False
    if bars_15m and len(bars_15m) >= pivot_period * 2 + 12:
        st_15 = pivot_point_supertrend(bars_15m, pivot_period=pivot_period, atr_factor=atr_factor)
        mtf_15m = st_15 == 1
    if bars_1h and len(bars_1h) >= pivot_period * 2 + 12:
        st_1h = pivot_point_supertrend(bars_1h, pivot_period=pivot_period, atr_factor=atr_factor)
        mtf_1h = st_1h == 1
    info["mtf_15m"] = mtf_15m
    info["mtf_1h"] = mtf_1h

    info["blockers"] = blockers
    info["fail"] = "; ".join(blockers) if blockers else None
    info["full_pass"] = core_pass
    return core_pass, info


def check_setup_b_exit(bars: list, pivot_period: int = 2,
                       atr_factor: float = 3.0) -> str | None:
    """
    Setup B exit signals. Simpler than Setup A — no ZLSMA, no Chandelier.
    Just PPST bearish flip or MACD(12,26,9) blue crosses below orange.
    """
    closes = [b["c"] for b in bars]

    st = pivot_point_supertrend(bars, pivot_period=pivot_period, atr_factor=atr_factor)
    if st == -1:
        return "supertrend_bearish"

    m_line, hist = macd(closes, 12, 26, 9)
    if m_line is not None and hist is not None and hist < 0:
        return "macd_std_bearish_cross"

    return None


def check_exit_signal(bars: list, chandelier: bool = True,
                      ce_period: int = 10, ce_mult: float = 2.0,
                      pivot_period: int = 2, atr_factor: float = 3.0) -> str | None:
    """
    Check W118 signal-based exits. Returns reason string or None.
    Called on every scan cycle for each open position.

    Structure-aware: a StochRSI reset (K dipping below 20) inside an intact
    uptrend is HEALTHY consolidation — the oscillator reloading for the next
    leg — not a reason to bail. We only exit when the trend STRUCTURE breaks:
      • Supertrend flips bearish (trend reversed), or
      • Price loses ZLSMA-50 (uptrend support gone), or
      • Price closes below the Chandelier Exit line (CE 10/2 trailing stop) — the
        W118 "ride it until a full candle closes under the green CE line" rule.
    K<20 on its own = hold. This avoids whipsaw exits during consolidation.
    The -8% hard stop (scan loop) and T1/T2/T3 targets still cap risk/reward.
    """
    closes = [b["c"] for b in bars]
    price  = closes[-1]

    # Structure exit 1 — trend reversal (Pivot Point SuperTrend)
    st = pivot_point_supertrend(bars, pivot_period=pivot_period, atr_factor=atr_factor)
    if st == -1:
        return "supertrend_bearish"

    # Structure exit 2 — lost uptrend support
    zl = zlsma(closes)
    if zl and price < zl:
        return f"below_ZLSMA (price={price:.4f} ZLSMA={zl:.4f})"

    # Structure exit 3 — Chandelier Exit trailing stop (additional exit)
    if chandelier:
        ce = chandelier_exit(bars, ce_period, ce_mult)
        if ce and ce["state"] == -1:
            return f"chandelier_stop (close {price:.4f} < {ce['long_stop']:.4f})"

    # Structure exit 4 — MACD bearish crossover (blue line crosses below orange signal)
    m_line, hist = macd(closes)
    if hist is not None and hist < 0:
        return "macd_bearish_cross"

    # StochRSI K<20 deliberately does NOT trigger an exit while structure holds.
    # When K resets and then curls back up with structure intact, the scanner
    # re-enters on the next leg — we don't want to be whipsawed out first.
    return None
