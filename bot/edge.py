"""
Edge Engine — the self-improving brain for the Curl-if-Flow bot.

Pure logic, no I/O (bot.py owns all Supabase/Telegram). Three jobs:

  1. grade_setup()        — label every entry A+/A/B/C from its setup DNA + catalyst.
  2. size_for_grade()     — grade-scaled dollar sizing, HARD-clamped to [min, max].
  3. compute_edge_profile() / should_autobuy() — the "learn, then tighten" loop:
        • LEARNING (few closed trades): take every valid signal to gather data.
        • TIGHTENING (enough data): auto-buy only the grades that actually win;
          restrict the rest to manual alerts.
     The gate can only ever REMOVE trades (more selective) — it never loosens a
     rule, never raises a cap, never widens a stop. The bot stays caged.

Kept dependency-free so it unit-tests offline with synthetic trade dicts.
"""

from __future__ import annotations


# ── 1. Grading ────────────────────────────────────────────────────────────────

GRADE_ORDER = {"A+": 3, "A": 2, "B": 1, "C": 0}


def grade_setup(info: dict, catalyst_tier: str | None) -> str:
    """
    A+/A/B/C from entry-time data (mirrors the scanner/audit.py A+ scale).

    The A+ "Shelf Bounce" DNA (from the June-19 chart study): a deep StochRSI reset
    that curls up while price holds above Session VWAP. So a clean VWAP reclaim counts
    as an edge signal alongside the catalyst — every June-19 runner held above VWAP.

      A+ = full pass + deep curl + (strong catalyst tier 1/2 OR clean above VWAP)
      A  = full pass + (deep curl OR any catalyst OR above VWAP)
      B  = full technical pass only (no extra edge)
      C  = below full pass (won't normally reach auto-buy)
    """
    score = info.get("score", 0) or 0
    mx    = info.get("max", 5) or 5
    if score < mx:
        return "C"
    deep       = bool(info.get("deep_curl"))
    above_vwap = info.get("above_vwap") is True
    strong_cat = catalyst_tier in ("tier_1", "tier_2")
    has_cat    = catalyst_tier is not None
    if deep and (strong_cat or above_vwap):
        return "A+"
    if deep or has_cat or above_vwap:
        return "A"
    return "B"


def grade_setup_b(info: dict, catalyst_tier: str | None) -> str:
    """
    Setup B grading — uses multi-timeframe confirmation instead of deep curl.
      A+ = full core pass + MTF (15m AND 1H bullish) + strong catalyst
      A  = full core pass + MTF (15m OR 1H) OR any catalyst
      B  = full core pass only
      C  = below full pass
    """
    score = info.get("score", 0) or 0
    mx    = info.get("max", 4) or 4
    if score < mx:
        return "C"
    mtf_both  = info.get("mtf_15m") and info.get("mtf_1h")
    mtf_any   = info.get("mtf_15m") or info.get("mtf_1h")
    strong_cat = catalyst_tier in ("tier_1", "tier_2")
    has_cat    = catalyst_tier is not None
    if mtf_both and (strong_cat or has_cat):
        return "A+"
    if mtf_any or has_cat:
        return "A"
    return "B"


# ── 2. Sizing ─────────────────────────────────────────────────────────────────

def size_for_grade(grade: str, by_grade: dict, base: float,
                   dmin: float, dmax: float) -> float:
    """
    Dollar size for a grade, HARD-clamped to [dmin, dmax] so a grade can never push
    a single trade above the ceiling no matter what the table says. Unknown grades
    fall back to `base`.
    """
    dollars = by_grade.get(grade, base)
    return max(dmin, min(dmax, float(dollars)))


# ── 3. Edge memory ────────────────────────────────────────────────────────────

def _bucket_stats(trades: list[dict], key_fn) -> dict:
    """Group trades by key_fn(t) → {count, wins, win_rate, avg_pnl} per bucket."""
    out: dict = {}
    for t in trades:
        k = key_fn(t)
        if k is None:
            continue
        b = out.setdefault(str(k), {"count": 0, "wins": 0, "pnl": 0.0})
        pnl = t.get("realized_pnl")
        pnl = float(pnl) if pnl is not None else 0.0
        b["count"] += 1
        b["pnl"]   += pnl
        if pnl > 0:
            b["wins"] += 1
    for b in out.values():
        b["win_rate"] = round(b["wins"] / b["count"] * 100, 1) if b["count"] else 0.0
        b["avg_pnl"]  = round(b["pnl"] / b["count"], 2) if b["count"] else 0.0
    return out


# ── Chart DNA bucket functions ───────────────────────────────────────────────

def _momentum_bucket(t: dict, key: str = "momentum_5") -> str | None:
    v = t.get(key)
    if v is None:
        return None
    v = float(v)
    if v < -2:  return "falling"
    if v < 0:   return "flat-down"
    if v < 2:   return "flat-up"
    if v < 5:   return "rising"
    return "surging"


def _vwap_dist_bucket(t: dict) -> str | None:
    v = t.get("vwap_dist_pct")
    if v is None:
        return None
    v = float(v)
    if v < -1:  return "below VWAP"
    if v < 0.5: return "at VWAP (shelf)"
    if v < 2:   return "near"
    if v < 5:   return "stretched"
    return "chasing"


def _zlsma_dist_bucket(t: dict) -> str | None:
    v = t.get("zlsma_dist_pct")
    if v is None:
        return None
    v = float(v)
    if v < 0:   return "below"
    if v < 1:   return "on ZLSMA"
    if v < 3:   return "near"
    if v < 5:   return "above"
    return "extended"


def _k_reset_bucket(t: dict) -> str | None:
    v = t.get("k_reset_depth")
    if v is None:
        return None
    v = float(v)
    if v < 10:  return "zero (0-10)"
    if v < 25:  return "deep (10-25)"
    if v < 40:  return "moderate (25-40)"
    return "shallow (40+)"


def _vol_accel_bucket(t: dict) -> str | None:
    v = t.get("vol_accel")
    if v is None:
        return None
    v = float(v)
    if v < 0.5: return "dying"
    if v < 0.8: return "fading"
    if v < 1.5: return "steady"
    if v < 2.5: return "rising"
    return "surging"


def _range_comp_bucket(t: dict) -> str | None:
    v = t.get("range_compression")
    if v is None:
        return None
    v = float(v)
    if v < 0.4: return "tight coil"
    if v < 0.7: return "compressed"
    if v < 1.0: return "normal"
    return "expanding"


def _day_range_bucket(t: dict) -> str | None:
    v = t.get("day_range_pct")
    if v is None:
        return None
    v = float(v)
    if v < 25:  return "bottom quarter"
    if v < 50:  return "lower half"
    if v < 75:  return "upper half"
    return "top quarter"


def _rsi_bucket(t: dict) -> str | None:
    v = t.get("rsi_entry")
    if v is None:
        return None
    v = float(v)
    if v < 40:  return "RSI <40"
    if v < 50:  return "RSI 40-50"
    if v < 60:  return "RSI 50-60"
    if v < 70:  return "RSI 60-70"
    return "RSI 70+"


def _macd_slope_bucket(t: dict) -> str | None:
    v = t.get("macd_slope")
    if v is None:
        return None
    v = float(v)
    if v < -0.001:  return "decelerating"
    if v < 0.001:   return "flat"
    if v < 0.01:    return "accelerating"
    return "strong accel"


def _vol_bucket(t: dict) -> str | None:
    v = t.get("vol_ratio")
    if v is None:
        return None
    v = float(v)
    if v < 2: return "1.5-2x"
    if v < 3: return "2-3x"
    if v < 5: return "3-5x"
    return "5x+"


def _k_bucket(t: dict) -> str | None:
    k = t.get("k_value")
    if k is None:
        return None
    k = float(k)
    if k <= 30: return "0-30 deep reset"
    if k <= 55: return "30-55 mid"
    if k <= 75: return "55-75 rising"
    return "75-85 high"


def compute_edge_profile(closed_trades: list[dict]) -> dict:
    """Bucket closed trades by every dimension that might carry edge."""
    return {
        "grade":     _bucket_stats(closed_trades, lambda t: t.get("grade")),
        "session":   _bucket_stats(closed_trades, lambda t: t.get("session")),
        "catalyst":  _bucket_stats(closed_trades, lambda t: t.get("catalyst")),
        "deep_curl": _bucket_stats(closed_trades,
                                   lambda t: "deep" if t.get("deep_curl") else "standard"),
        "vol":       _bucket_stats(closed_trades, _vol_bucket),
        "k_entry":   _bucket_stats(closed_trades, _k_bucket),
        # Chart DNA dimensions (old trades without DNA → None → skipped)
        "momentum_5":  _bucket_stats(closed_trades, lambda t: _momentum_bucket(t, "momentum_5")),
        "momentum_10": _bucket_stats(closed_trades, lambda t: _momentum_bucket(t, "momentum_10")),
        "vwap_dist":   _bucket_stats(closed_trades, _vwap_dist_bucket),
        "zlsma_dist":  _bucket_stats(closed_trades, _zlsma_dist_bucket),
        "k_reset":     _bucket_stats(closed_trades, _k_reset_bucket),
        "vol_accel":   _bucket_stats(closed_trades, _vol_accel_bucket),
        "range_comp":  _bucket_stats(closed_trades, _range_comp_bucket),
        "day_range":   _bucket_stats(closed_trades, _day_range_bucket),
        "rsi":         _bucket_stats(closed_trades, _rsi_bucket),
        "macd_slope":  _bucket_stats(closed_trades, _macd_slope_bucket),
    }


def phase_for(n_closed: int, learn_threshold: int) -> str:
    return "learning" if n_closed < learn_threshold else "tightening"


def should_autobuy(grade: str, edge_profile: dict, n_closed: int,
                   learn_threshold: int, winrate_floor: float,
                   min_sample: int) -> tuple[bool, str]:
    """
    The learn→tighten gate.

    LEARNING phase (n_closed < learn_threshold): allow every valid signal so we
    gather data across grades.

    TIGHTENING phase: only auto-buy a grade once it has a real sample
    (count >= min_sample) AND a win-rate >= floor. Grades that underperform get
    held (manual alert only). While a grade's sample is still building, the
    high-conviction A+/A are allowed through and B/C are held — a conservative,
    restrict-only bias. This never loosens anything.
    """
    if n_closed < learn_threshold:
        return True, f"learning {n_closed}/{learn_threshold} — taking all valid signals"

    g = (edge_profile.get("grade") or {}).get(grade)
    if g and g["count"] >= min_sample:
        if g["win_rate"] >= winrate_floor * 100:
            return True, f"{grade} proven {g['win_rate']:.0f}% over {g['count']}"
        return False, f"{grade} weak {g['win_rate']:.0f}% over {g['count']} — alert only"

    if grade in ("A+", "A"):
        return True, f"{grade} high-conviction (history building)"
    return False, f"{grade} held — building sample"


def edge_summary(profile: dict, n_closed: int, phase: str) -> str:
    """One-line headline for Telegram + the dashboard."""
    g = profile.get("grade") or {}
    parts = [f"{gr} {g[gr]['win_rate']:.0f}%({g[gr]['count']})"
             for gr in ("A+", "A", "B", "C") if gr in g]
    grade_str = " · ".join(parts) if parts else "no closed trades yet"

    sess = {k: v for k, v in (profile.get("session") or {}).items() if v["count"] >= 2}
    best = ""
    if sess:
        bs = max(sess.items(), key=lambda x: x[1]["win_rate"])
        best = f" · best session: {bs[0]} {bs[1]['win_rate']:.0f}%"

    return f"Phase: {phase} · {n_closed} closed · grades {grade_str}{best}"


# ── 4. Chart DNA pattern mining + scoring ────────────────────────────────────

_DNA_FEATURES = [
    ("momentum_5",  lambda t: _momentum_bucket(t, "momentum_5")),
    ("momentum_10", lambda t: _momentum_bucket(t, "momentum_10")),
    ("vwap_dist",   _vwap_dist_bucket),
    ("zlsma_dist",  _zlsma_dist_bucket),
    ("k_reset",     _k_reset_bucket),
    ("vol_accel",   _vol_accel_bucket),
    ("range_comp",  _range_comp_bucket),
    ("day_range",   _day_range_bucket),
    ("rsi",         _rsi_bucket),
    ("macd_slope",  _macd_slope_bucket),
]


def mine_chart_patterns(closed_trades: list[dict], min_bucket_n: int = 3) -> dict:
    """
    Deep pattern analysis on Chart DNA features. Returns sweet spots (buckets that
    win significantly above baseline), danger zones (significantly below), and the
    strongest two-feature combos. Backward compatible: trades without DNA columns
    are silently filtered out.
    """
    dna_trades = [t for t in closed_trades if t.get("momentum_5") is not None]
    if len(dna_trades) < min_bucket_n:
        return {"sweet_spots": [], "danger_zones": [], "top_combos": [],
                "baseline_wr": 0, "dna_trades": 0}

    total = len(dna_trades)
    total_wins = sum(1 for t in dna_trades if float(t.get("realized_pnl", 0)) > 0)
    baseline_wr = total_wins / total * 100 if total else 0

    sweet_spots: list = []
    danger_zones: list = []

    for name, fn in _DNA_FEATURES:
        buckets: dict = {}
        for t in dna_trades:
            b = fn(t)
            if b is None:
                continue
            buckets.setdefault(b, {"wins": 0, "count": 0})
            buckets[b]["count"] += 1
            if float(t.get("realized_pnl", 0)) > 0:
                buckets[b]["wins"] += 1

        for bucket, stats in buckets.items():
            if stats["count"] < min_bucket_n:
                continue
            wr = stats["wins"] / stats["count"] * 100
            lift = wr - baseline_wr
            entry = {"feature": name, "bucket": bucket, "win_rate": round(wr, 1),
                     "count": stats["count"], "lift": round(lift, 1)}
            if lift >= 15:
                sweet_spots.append(entry)
            elif lift <= -15:
                danger_zones.append(entry)

    sweet_spots.sort(key=lambda x: -x["lift"])
    danger_zones.sort(key=lambda x: x["lift"])

    # Two-feature combo analysis (10 choose 2 = 45 combos)
    top_combos: list = []
    for i in range(len(_DNA_FEATURES)):
        for j in range(i + 1, len(_DNA_FEATURES)):
            name_i, fn_i = _DNA_FEATURES[i]
            name_j, fn_j = _DNA_FEATURES[j]
            combos: dict = {}
            for t in dna_trades:
                bi, bj = fn_i(t), fn_j(t)
                if bi is None or bj is None:
                    continue
                key = f"{bi} + {bj}"
                combos.setdefault(key, {"wins": 0, "count": 0})
                combos[key]["count"] += 1
                if float(t.get("realized_pnl", 0)) > 0:
                    combos[key]["wins"] += 1
            for combo_key, stats in combos.items():
                if stats["count"] < min_bucket_n:
                    continue
                wr = stats["wins"] / stats["count"] * 100
                lift = wr - baseline_wr
                if abs(lift) >= 15:
                    top_combos.append({"features": f"{name_i} × {name_j}",
                                       "combo": combo_key, "win_rate": round(wr, 1),
                                       "count": stats["count"], "lift": round(lift, 1)})

    top_combos.sort(key=lambda x: -abs(x["lift"]))

    return {
        "sweet_spots": sweet_spots[:10],
        "danger_zones": danger_zones[:10],
        "top_combos": top_combos[:10],
        "baseline_wr": round(baseline_wr, 1),
        "dna_trades": len(dna_trades),
    }


def chart_dna_score(dna: dict, pattern_profile: dict) -> tuple[int, str]:
    """
    Score a new entry 0–100 from its Chart DNA vs historical pattern matches.
    50 = neutral. Each sweet spot/danger zone match shifts ±1–5 points; top
    combo matches add ±3. Returns (score, top_reason).
    """
    if not pattern_profile or not dna or not pattern_profile.get("dna_trades"):
        return 50, "no pattern data yet"

    score = 50
    reasons: list = []

    dna_buckets: dict = {}
    for name, fn in _DNA_FEATURES:
        b = fn(dna)
        if b is not None:
            dna_buckets[name] = b

    for spot in pattern_profile.get("sweet_spots", []):
        if dna_buckets.get(spot["feature"]) == spot["bucket"]:
            pts = min(5, max(1, int(spot["lift"] / 5)))
            score += pts
            reasons.append(f"+{pts} {spot['feature']}={spot['bucket']} ({spot['win_rate']:.0f}%)")

    for zone in pattern_profile.get("danger_zones", []):
        if dna_buckets.get(zone["feature"]) == zone["bucket"]:
            pts = min(5, max(1, int(abs(zone["lift"]) / 5)))
            score -= pts
            reasons.append(f"-{pts} {zone['feature']}={zone['bucket']} ({zone['win_rate']:.0f}%)")

    for combo in pattern_profile.get("top_combos", []):
        parts = combo["combo"].split(" + ")
        features = combo["features"].split(" × ")
        if len(parts) == 2 and len(features) == 2:
            if dna_buckets.get(features[0]) == parts[0] and dna_buckets.get(features[1]) == parts[1]:
                pts = 3 if combo["lift"] > 0 else -3
                score += pts
                sign = "+" if pts > 0 else ""
                reasons.append(f"{sign}{pts} combo {combo['features']} ({combo['win_rate']:.0f}%)")

    score = max(0, min(100, score))
    top_reason = reasons[0] if reasons else "neutral (no strong patterns yet)"
    return score, top_reason
