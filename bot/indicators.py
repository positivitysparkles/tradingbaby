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


def macd(closes: list) -> tuple[float | None, float | None]:
    """
    MACD(5,10,16). Returns (macd_line, histogram).

    • histogram > 0  → macd_line above signal line = momentum turning up right now.
      This is the W118 gate: "blue line above red line."

    Faster than standard 12,26,9 — fires in sync with Supertrend, not lagging.
    """
    if len(closes) < 32:
        return None, None
    e5  = _ema(closes, 5)
    e10 = _ema(closes, 10)
    macd_line = [a - b for a, b in zip(e5, e10)]
    sig_line  = _ema(macd_line, 16)
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


def check_all_entry(bars: list, min_price: float, max_price: float, rel_vol_min: float,
                    deep_curl_reset: float = 20.0) -> tuple[bool, dict]:
    """
    Run all W118 entry conditions. Returns (passed, details_dict).

    Checks ALL conditions instead of short-circuiting so we can score
    partial setups (4/5) for WATCH alerts. ZLSMA is skipped (not failed)
    when insufficient bar history — the other 4 conditions are sufficient.

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

    # 1. Supertrend bullish — PRIMARY trigger
    st = supertrend(bars)
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
    if hist is None:
        blockers.append("MACD error")
    elif hist <= 0:
        blockers.append(f"MACD hist {hist:.4f} (momentum fading)")
    else:
        passed += 1

    # 5. Volume > rel_vol_min × 20-bar average.
    #    Use the last CLOSED bar (bars[-2]), not the forming one (bars[-1]).
    #    A freshly-opened 5m bar has near-zero volume for most of its life and
    #    produces "Vol 0.0x" false rejections that block real setups.
    vols    = [b["v"] for b in bars[-22:-2]]  # 20 completed bars before the last closed
    avg_vol = sum(vols) / len(vols) if vols else 0
    cur_vol = bars[-2]["v"]                   # last CLOSED bar
    vol_ratio = cur_vol / avg_vol if avg_vol else 0
    if vol_ratio >= rel_vol_min:
        passed += 1
    else:
        blockers.append(f"vol {vol_ratio:.1f}x below {rel_vol_min:.1f}x")

    # Max possible is 4 when ZLSMA is skipped, 5 otherwise
    max_possible = 5 if zl is not None else 4

    info = {
        "price":     price,
        "score":     passed,
        "max":       max_possible,
        "k":         round(k, 1)      if k    is not None else None,
        "d":         round(d, 1)      if d    is not None else None,
        "k_prev":    round(k_prev, 1) if k_prev is not None else None,
        "k_low":     round(k_low, 1)  if k_low is not None else None,
        "deep_curl": deep_curl,
        "zlsma":     round(zl, 4)     if zl   is not None else None,
        "macd_hist": round(hist, 5)   if hist   is not None else None,
        "macd_line": round(m_line, 5) if m_line is not None else None,
        "vol_ratio": round(vol_ratio, 1),
        "blockers":  blockers,
        "fail":      " | ".join(blockers) if blockers else None,
    }

    return (passed >= max_possible), info


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


def check_exit_signal(bars: list) -> str | None:
    """
    Check W118 signal-based exits. Returns reason string or None.
    Called on every scan cycle for each open position.

    Structure-aware: a StochRSI reset (K dipping below 20) inside an intact
    uptrend is HEALTHY consolidation — the oscillator reloading for the next
    leg — not a reason to bail. We only exit when the trend STRUCTURE breaks:
      • Supertrend flips bearish (trend reversed), or
      • Price loses ZLSMA-50 (uptrend support gone).
    K<20 on its own = hold. This avoids whipsaw exits during consolidation.
    The -8% hard stop (scan loop) and T1/T2/T3 targets still cap risk/reward.
    """
    closes = [b["c"] for b in bars]
    price  = closes[-1]

    # Structure exit 1 — trend reversal
    st = supertrend(bars)
    if st == -1:
        return "supertrend_bearish"

    # Structure exit 2 — lost uptrend support
    zl = zlsma(closes)
    if zl and price < zl:
        return f"below_ZLSMA (price={price:.4f} ZLSMA={zl:.4f})"

    # StochRSI K<20 deliberately does NOT trigger an exit while structure holds.
    # When K resets and then curls back up with structure intact, the scanner
    # re-enters on the next leg — we don't want to be whipsawed out first.
    return None
