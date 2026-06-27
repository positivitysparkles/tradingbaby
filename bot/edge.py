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
