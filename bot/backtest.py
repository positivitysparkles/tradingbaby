"""
W118 Historical Backtester
==========================
Replays 5-minute bars through the exact same entry/exit logic the live bot uses.
Seeds the Chart DNA pattern profile with hundreds of data points.

Usage:
  python bot/backtest.py                       # all historical tickers, 60 days
  python bot/backtest.py AHMA CRVO CDT         # specific tickers only
  python bot/backtest.py --days 30             # last 30 days
  python bot/backtest.py --seed                # save DNA profile for live bot
  python bot/backtest.py --discover            # find 200-500 recent small-cap runners
  python bot/backtest.py --discover --seed     # discover + seed DNA profile
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent))
from indicators import (check_all_entry, check_exit_signal, compute_chart_dna,
                         catalyst_score, check_setup_b_entry, check_setup_b_exit)
from edge import (grade_setup, grade_setup_b, mine_chart_patterns)

MIN_PRICE      = 0.10
MAX_PRICE      = 15.00
REL_VOL_MIN    = 1.5
DEEP_CURL_RESET = 30.0
VWAP_TOLERANCE = 0.005
OVERBOUGHT_K   = 85.0
STOP_PCT       = 0.08
T1_PCT         = 0.15
T2_PCT         = 0.30
T3_PCT         = 0.60

DATA_DIR = Path(__file__).parent.parent / "data"


def fetch_bars_5m(ticker: str, days: int = 60) -> list | None:
    try:
        df = yf.Ticker(ticker).history(period=f"{days}d", interval="5m", prepost=True)
        if df is None or df.empty:
            return None
        bars = [
            {"o": float(row["Open"]), "h": float(row["High"]),
             "l": float(row["Low"]),  "c": float(row["Close"]),
             "v": max(0, int(row["Volume"])),
             "t": idx.isoformat()}
            for idx, row in df.iterrows()
            if not (row["Open"] != row["Open"])
        ]
        return bars if len(bars) >= 100 else None
    except Exception as e:
        print(f"  [bars] {ticker}: {e}")
        return None


def fetch_daily(ticker: str) -> list | None:
    try:
        df = yf.Ticker(ticker).history(period="3mo", interval="1d")
        if df is None or df.empty:
            return None
        return [
            {"o": float(row["Open"]), "h": float(row["High"]),
             "l": float(row["Low"]),  "c": float(row["Close"]),
             "v": max(0, int(row["Volume"])),
             "t": idx.isoformat()}
            for idx, row in df.iterrows()
            if not (row["Open"] != row["Open"])
        ]
    except Exception:
        return None


def discover_runners(max_price: float = 15.0) -> list:
    """Find small-cap runners using TradingView scanner + Yahoo gainers."""
    tv_headers = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
        "Origin":  "https://www.tradingview.com",
        "Referer": "https://www.tradingview.com/",
        "Accept":  "application/json",
    }
    tickers: set = set()
    print(f"Discovering small-cap runners under ${max_price:.0f}...")

    # Method 1: TradingView scanner — multiple passes with different change thresholds
    # to catch stocks at different points in their run
    for min_change in [5.0, 10.0, 20.0, 50.0]:
        try:
            for chg_field, vol_field in [("change", "volume"),
                                         ("premarket_change", "premarket_volume")]:
                body = {
                    "filter": [
                        {"left": chg_field,  "operation": "greater",  "right": min_change},
                        {"left": "close",    "operation": "in_range", "right": [0.10, max_price]},
                        {"left": vol_field,  "operation": "greater",  "right": 500_000},
                    ],
                    "options":  {"lang": "en"},
                    "symbols":  {"query": {"types": []}, "tickers": []},
                    "columns":  ["name", "close", chg_field, vol_field],
                    "sort":     {"sortBy": chg_field, "sortOrder": "desc"},
                    "range":    [0, 200],
                    "markets":  ["america"],
                }
                r = requests.post("https://scanner.tradingview.com/america/scan",
                                  json=body, headers=tv_headers, timeout=15)
                if r.ok:
                    rows = r.json().get("data") or []
                    for row in rows:
                        sym = row.get("s", "")
                        if ":" in sym:
                            tickers.add(sym.split(":", 1)[1])
            print(f"  TradingView scan (change>{min_change}%): total {len(tickers)} tickers")
            time.sleep(1)
        except Exception as e:
            print(f"  TradingView scan failed: {e}")

    # Method 2: Yahoo Finance small-cap gainers
    for scr_id in ["small_cap_gainers", "aggressive_small_caps", "most_actives"]:
        try:
            r = requests.get(
                "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved",
                params={"scrIds": scr_id, "count": 100,
                        "formatted": "false", "lang": "en-US", "region": "US"},
                headers={"User-Agent": tv_headers["User-Agent"]},
                timeout=10,
            )
            if r.ok:
                quotes = r.json().get("finance", {}).get("result", [{}])[0].get("quotes", [])
                for q in quotes:
                    sym = q.get("symbol", "")
                    price = q.get("regularMarketPrice", 999)
                    if sym and price <= max_price and price >= 0.10:
                        tickers.add(sym)
                print(f"  Yahoo {scr_id}: total {len(tickers)} tickers")
        except Exception:
            pass
        time.sleep(0.5)

    # Method 3: TradingView "top gainers" performance screen (weekly/monthly movers)
    for perf_field in ["Perf.W", "Perf.1M"]:
        try:
            body = {
                "filter": [
                    {"left": perf_field, "operation": "greater", "right": 0.20},
                    {"left": "close",    "operation": "in_range", "right": [0.10, max_price]},
                    {"left": "volume",   "operation": "greater",  "right": 200_000},
                ],
                "options": {"lang": "en"},
                "symbols": {"query": {"types": []}, "tickers": []},
                "columns": ["name", "close", perf_field, "volume"],
                "sort":    {"sortBy": perf_field, "sortOrder": "desc"},
                "range":   [0, 200],
                "markets": ["america"],
            }
            r = requests.post("https://scanner.tradingview.com/america/scan",
                              json=body, headers=tv_headers, timeout=15)
            if r.ok:
                rows = r.json().get("data") or []
                for row in rows:
                    sym = row.get("s", "")
                    if ":" in sym:
                        tickers.add(sym.split(":", 1)[1])
            print(f"  TradingView {perf_field}: total {len(tickers)} tickers")
            time.sleep(1)
        except Exception:
            pass

    # Method 4: yfinance seed list — broad small-cap universe, filter to 10%+ movers
    # Kept as fallback in case TradingView/Yahoo are blocked from VPS
    tv_count = len(tickers)
    seed_tickers = _yfinance_seed_scan(max_price)
    tickers.update(seed_tickers)
    if seed_tickers:
        print(f"  yfinance seed scan: +{len(seed_tickers)} new (total {len(tickers)})")

    print(f"\nDiscovered {len(tickers)} unique tickers "
          f"({tv_count} from TV/Yahoo, {len(seed_tickers)} from yfinance seed)\n")
    return sorted(tickers)


def _yfinance_seed_scan(max_price: float = 15.0) -> set:
    """Scan a broad small-cap list via yfinance daily bars for recent 10%+ days."""
    seed_list = [
        "ABTS", "ACRV", "AEMD", "AHMA", "AIMD", "AIXI", "AKAN", "ALBT",
        "ALLR", "ALTO", "AMST", "ANNA", "APRE", "ARTL", "ASBP", "ASTC",
        "ATAI", "ATER", "ATPC", "AUVI", "BATL", "BBBY", "BCG", "BCDA",
        "BEAT", "BENF", "BFRG", "BIAF", "BIYA", "BJDX", "BLIN", "BLNK",
        "BNED", "BOLT", "BOXL", "BTAI", "BTBT", "BTMD", "BURU", "BYND",
        "CDT", "CELU", "CENN", "CETX", "CLPS", "COOK", "CORZ", "CRIS",
        "CRVO", "DAVE", "DFLI", "EAST", "EOSE", "EVGO", "FCEL", "FUBO",
        "GALT", "GASS", "GDEV", "GFAI", "GILT", "GOEV", "GROM", "GRPN",
        "GSAT", "HOOD", "HUSA", "HYMC", "IDEX", "IMPP", "INDO", "IONQ",
        "ISPC", "IZEA", "JOBY", "KAVL", "KIRK", "KPLT", "KULR", "LAZR",
        "LCID", "LMFA", "LOOP", "MBIO", "MEGL", "MGNX", "MNKD", "MNTS",
        "MULN", "MVST", "NEGG", "NKLA", "NVAX", "OCGN", "PHUN", "PIXY",
        "PLUG", "PRAX", "QUBT", "RBLX", "RNXT", "SDIG", "SENS", "SKLZ",
        "SOFI", "SOLO", "SOUN", "SPCE", "SRNE", "TELL", "TLIS", "TNXP",
        "TPST", "TTOO", "VERB", "VLD", "VNET", "WKHS", "XELA", "ZAPP",
    ]
    found = set()
    batch_size = 40
    for i in range(0, len(seed_list), batch_size):
        batch = seed_list[i:i + batch_size]
        try:
            data = yf.download(batch, period="60d", interval="1d",
                               progress=False, threads=True)
            if data.empty:
                continue
            for t in batch:
                try:
                    col = ("Close", t) if ("Close", t) in data.columns else None
                    if col is None:
                        continue
                    closes = data[col].dropna()
                    if closes.empty:
                        continue
                    last_price = float(closes.iloc[-1])
                    if last_price > max_price or last_price < 0.10:
                        continue
                    daily_returns = closes.pct_change() * 100
                    if (daily_returns > 10).any():
                        found.add(t)
                except Exception:
                    continue
        except Exception:
            continue
        time.sleep(0.3)
    return found


def simulate_trade(bars: list, entry_idx: int, entry_price: float) -> dict:
    """Walk forward from entry, apply stop/trailing/signal exits, track MFE/MAE."""
    stop = entry_price * (1 - STOP_PCT)
    t1 = entry_price * (1 + T1_PCT)
    t2 = entry_price * (1 + T2_PCT)
    t3 = entry_price * (1 + T3_PCT)

    t1_hit = t2_hit = False
    trailing_stop = stop
    mfe = mae = 0.0
    exit_price = exit_reason = None
    exit_idx = entry_idx
    dna_snapshots: list = []

    max_hold = min(entry_idx + 200, len(bars))
    for i in range(entry_idx + 1, max_hold):
        high, low, close = bars[i]["h"], bars[i]["l"], bars[i]["c"]

        pct_h = (high - entry_price) / entry_price * 100
        pct_l = (entry_price - low) / entry_price * 100
        mfe = max(mfe, pct_h)
        mae = max(mae, pct_l)

        if not t1_hit and high >= t1:
            t1_hit = True
            trailing_stop = entry_price
        if not t2_hit and high >= t2:
            t2_hit = True
            trailing_stop = close * 0.90
        if t2_hit:
            trailing_stop = max(trailing_stop, close * 0.90)

        if (i - entry_idx) % 10 == 0 and i - entry_idx >= 10:
            window = bars[max(0, i - 99):i + 1]
            if len(window) >= 20:
                snap = compute_chart_dna(window)
                snap["bars_into_trade"] = i - entry_idx
                dna_snapshots.append(snap)

        if low <= stop:
            exit_price, exit_reason, exit_idx = stop, "hard_stop", i
            break
        if t1_hit and close <= trailing_stop:
            exit_price, exit_reason, exit_idx = trailing_stop, "trailing_stop", i
            break
        if i - entry_idx >= 5:
            window = bars[max(0, i - 99):i + 1]
            if len(window) >= 20:
                reason = check_exit_signal(window)
                if reason:
                    exit_price, exit_reason, exit_idx = close, reason, i
                    break
        if high >= t3:
            exit_price, exit_reason, exit_idx = t3, "t3_target", i
            break

    if exit_price is None:
        exit_idx = max_hold - 1
        exit_price = bars[exit_idx]["c"]
        exit_reason = "end_of_data"

    pnl = round((exit_price - entry_price) / entry_price * 100, 2)
    return {
        "entry_price": round(entry_price, 4),
        "exit_price": round(exit_price, 4),
        "exit_reason": exit_reason,
        "pct_return": pnl,
        "realized_pnl": round(pnl, 2),
        "mfe_pct": round(mfe, 2),
        "mae_pct": round(mae, 2),
        "bars_held": exit_idx - entry_idx,
        "t1_hit": t1_hit,
        "t2_hit": t2_hit,
        "dna_snapshots": dna_snapshots,
    }


def backtest_ticker(ticker: str, bars: list, daily_bars: list | None = None) -> list:
    """Walk 5m bars, fire entries on both setups, simulate each trade."""
    trades: list = []
    cooldown_until = 0
    window_size = 100

    for i in range(window_size, len(bars) - 20):
        if i < cooldown_until:
            continue
        window = bars[i - window_size:i + 1]

        # Setup A
        ok, info = check_all_entry(window, MIN_PRICE, MAX_PRICE, REL_VOL_MIN,
                                   DEEP_CURL_RESET, vwap_tol=VWAP_TOLERANCE,
                                   overbought_k=OVERBOUGHT_K)
        if ok:
            price = info["price"]
            catalyst_tier = None
            if daily_bars:
                bar_date = str(bars[i].get("t", ""))[:10]
                dw = [d for d in daily_bars if str(d.get("t", ""))[:10] <= bar_date]
                if dw:
                    catalyst_tier, _ = catalyst_score(window, dw[-5:])
            grade = grade_setup(info, catalyst_tier)
            dna = compute_chart_dna(window)

            trade = simulate_trade(bars, i, price)
            trade.update(ticker=ticker, setup="A", grade=grade,
                         catalyst=catalyst_tier, bar_time=bars[i].get("t", ""),
                         chart_dna=dna, k_value=info.get("k"),
                         d_value=info.get("d"), vol_ratio=info.get("vol_ratio"),
                         deep_curl=info.get("deep_curl"), rsi_entry=dna.get("rsi_entry"))
            trades.append(trade)
            cooldown_until = i + trade["bars_held"] + 10
            continue

        # Setup B (only if A didn't fire)
        ok_b, info_b = check_setup_b_entry(window, MIN_PRICE, MAX_PRICE)
        if ok_b:
            price = info_b["price"]
            grade_b = grade_setup_b(info_b, None)
            dna = compute_chart_dna(window)

            trade = simulate_trade(bars, i, price)
            trade.update(ticker=ticker, setup="B", grade=grade_b,
                         catalyst=None, bar_time=bars[i].get("t", ""),
                         chart_dna=dna, vol_ratio=info_b.get("vol_ratio"),
                         rsi_entry=dna.get("rsi_entry"))
            trades.append(trade)
            cooldown_until = i + trade["bars_held"] + 10

    return trades


def print_results(all_trades: list):
    if not all_trades:
        print("No trades generated.")
        return

    wins = sum(1 for t in all_trades if t["pct_return"] > 0)
    losses = len(all_trades) - wins
    wr = wins / len(all_trades) * 100
    net = sum(t["pct_return"] for t in all_trades)
    avg_mfe = sum(t["mfe_pct"] for t in all_trades) / len(all_trades)
    avg_mae = sum(t["mae_pct"] for t in all_trades) / len(all_trades)
    avg_hold = sum(t["bars_held"] for t in all_trades) / len(all_trades)

    print(f"Win rate: {wr:.1f}%  ({wins}W / {losses}L)")
    print(f"Net return (sum of %): {net:+.1f}%")
    print(f"Avg MFE: +{avg_mfe:.1f}%  |  Avg MAE: -{avg_mae:.1f}%")
    print(f"Avg bars held: {avg_hold:.0f}")

    for label, subset in [("Setup A", [t for t in all_trades if t["setup"] == "A"]),
                          ("Setup B", [t for t in all_trades if t["setup"] == "B"])]:
        if not subset:
            continue
        sw = sum(1 for t in subset if t["pct_return"] > 0)
        swr = sw / len(subset) * 100
        spnl = sum(t["pct_return"] for t in subset)
        print(f"\n{label}: {len(subset)} trades · {swr:.0f}% win · {spnl:+.1f}%")

    grades: dict = {}
    for t in all_trades:
        g = t.get("grade", "?")
        grades.setdefault(g, {"w": 0, "l": 0, "pnl": 0.0})
        grades[g]["pnl"] += t["pct_return"]
        if t["pct_return"] > 0:
            grades[g]["w"] += 1
        else:
            grades[g]["l"] += 1
    print("\nGrade breakdown:")
    for g in ["A+", "A", "B", "C"]:
        d = grades.get(g)
        if not d:
            continue
        n = d["w"] + d["l"]
        gwr = d["w"] / n * 100 if n else 0
        print(f"  {g}: {gwr:.0f}% ({n} trades) {d['pnl']:+.1f}%")

    exits: dict = {}
    for t in all_trades:
        r = t["exit_reason"]
        exits.setdefault(r, {"count": 0, "pnl": 0.0})
        exits[r]["count"] += 1
        exits[r]["pnl"] += t["pct_return"]
    print("\nExit reasons:")
    for r, d in sorted(exits.items(), key=lambda x: -x[1]["count"]):
        print(f"  {r}: {d['count']} trades  {d['pnl']:+.1f}%")


def print_dna_analysis(all_trades: list) -> dict:
    dna_records: list = []
    for t in all_trades:
        dna = t.get("chart_dna") or {}
        if not dna:
            continue
        record = dict(dna)
        record["realized_pnl"] = t["pct_return"]
        record["grade"] = t.get("grade")
        record["setup"] = t.get("setup")
        dna_records.append(record)

    if not dna_records:
        return {}

    profile = mine_chart_patterns(dna_records)
    print(f"DNA trades analyzed: {profile.get('dna_trades', 0)}")
    print(f"Baseline win rate: {profile.get('baseline_wr', 0):.1f}%")

    for label, key, icon in [("Sweet spots (+15pp)", "sweet_spots", "✅"),
                             ("Danger zones (-15pp)", "danger_zones", "⚠️")]:
        items = profile.get(key, [])
        if items:
            print(f"\n{icon} {label}:")
            for s in items[:5]:
                print(f"  {s['feature']}={s['bucket']}: {s['win_rate']:.0f}% "
                      f"(lift {s['lift']:+.0f}pp, n={s['count']})")

    combos = profile.get("top_combos", [])
    if combos:
        print(f"\n🔗 Top 2-feature combos:")
        for c in combos[:5]:
            print(f"  {c['features']}: {c['combo']} → {c['win_rate']:.0f}% "
                  f"(lift {c['lift']:+.0f}pp, n={c['count']})")

    return profile


def print_dna_evolution(all_trades: list):
    """Analyze how DNA features shift during winning vs losing trades."""
    win_snaps: list = []
    loss_snaps: list = []
    for t in all_trades:
        snaps = t.get("dna_snapshots", [])
        if not snaps:
            continue
        bucket = win_snaps if t["pct_return"] > 0 else loss_snaps
        bucket.extend(snaps)

    if not win_snaps and not loss_snaps:
        return

    print(f"Snapshots: {len(win_snaps)} from winners, {len(loss_snaps)} from losers\n")

    features = ["momentum_5", "vol_accel", "range_compression", "rsi_entry", "macd_slope"]
    for feat in features:
        wv = [s[feat] for s in win_snaps if s.get(feat) is not None]
        lv = [s[feat] for s in loss_snaps if s.get(feat) is not None]
        if wv and lv:
            aw = sum(wv) / len(wv)
            al = sum(lv) / len(lv)
            diff = aw - al
            arrow = "▲" if diff > 0 else "▼"
            print(f"  {feat}: winners avg {aw:.3f} vs losers avg {al:.3f}  ({arrow} {abs(diff):.3f})")

    # Early vs late evolution (do winning trades accelerate?)
    for result_label, snaps in [("Winners", win_snaps), ("Losers", loss_snaps)]:
        if len(snaps) < 4:
            continue
        early = [s for s in snaps if s.get("bars_into_trade", 0) <= 20]
        late = [s for s in snaps if s.get("bars_into_trade", 0) > 20]
        if not early or not late:
            continue
        for feat in ["momentum_5", "vol_accel"]:
            ev = [s[feat] for s in early if s.get(feat) is not None]
            lv = [s[feat] for s in late if s.get(feat) is not None]
            if ev and lv:
                ae = sum(ev) / len(ev)
                al = sum(lv) / len(lv)
                arrow = "▲" if al > ae else "▼"
                print(f"  {result_label} {feat}: early {ae:.3f} → late {al:.3f} {arrow}")


def main():
    args = sys.argv[1:]
    days = 60
    seed = False
    discover = False
    tickers: list = []

    i = 0
    while i < len(args):
        if args[i] == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
            i += 2
        elif args[i] == "--seed":
            seed = True
            i += 1
        elif args[i] == "--discover":
            discover = True
            i += 1
        else:
            tickers.append(args[i].upper())
            i += 1

    if discover:
        discovered = discover_runners(MAX_PRICE)
        # Merge with historical tickers for maximum coverage
        trades_file = DATA_DIR / "trades-parsed.json"
        if trades_file.exists():
            raw = json.loads(trades_file.read_text())
            historical = raw.get("trades", raw) if isinstance(raw, dict) else raw
            hist_tickers = set(t["ticker"] for t in historical if isinstance(t, dict))
            discovered_set = set(discovered)
            tickers = sorted(discovered_set | hist_tickers)
            print(f"Combined: {len(discovered)} discovered + {len(hist_tickers)} historical "
                  f"= {len(tickers)} unique tickers")
        else:
            tickers = discovered

    if not tickers:
        trades_file = DATA_DIR / "trades-parsed.json"
        if trades_file.exists():
            raw = json.loads(trades_file.read_text())
            historical = raw.get("trades", raw) if isinstance(raw, dict) else raw
            tickers = sorted(set(t["ticker"] for t in historical if isinstance(t, dict)))
            print(f"Using {len(tickers)} tickers from historical trades")
        else:
            print("Usage: python bot/backtest.py [TICKER ...] [--days N] [--seed] [--discover]")
            sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  W118 Backtester — {len(tickers)} tickers × {days} days of 5m bars")
    print(f"{'=' * 60}\n")

    all_trades: list = []
    skipped: list = []

    for idx, ticker in enumerate(tickers):
        print(f"[{idx + 1}/{len(tickers)}] {ticker} ...", end=" ", flush=True)
        bars = fetch_bars_5m(ticker, days)
        if not bars:
            print("skipped (no bars)")
            skipped.append(ticker)
            time.sleep(0.5)
            continue
        daily = fetch_daily(ticker)
        trades = backtest_ticker(ticker, bars, daily)
        wins = sum(1 for t in trades if t["pct_return"] > 0)
        losses = len(trades) - wins
        total_pct = sum(t["pct_return"] for t in trades)
        if trades:
            print(f"{len(trades)} trades ({wins}W/{losses}L) {total_pct:+.1f}%")
        else:
            print("0 signals")
        all_trades.extend(trades)
        time.sleep(0.3)

    print(f"\n{'=' * 60}")
    print(f"  BACKTEST RESULTS")
    print(f"{'=' * 60}")
    print(f"Tickers tested: {len(tickers) - len(skipped)}/{len(tickers)}\n")
    print_results(all_trades)

    print(f"\n{'=' * 60}")
    print(f"  CHART DNA ANALYSIS")
    print(f"{'=' * 60}")
    profile = print_dna_analysis(all_trades)

    print(f"\n{'=' * 60}")
    print(f"  INTRADAY DNA EVOLUTION")
    print(f"{'=' * 60}")
    print_dna_evolution(all_trades)

    # Save results
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_trades = [{k: v for k, v in t.items() if k != "dna_snapshots"}
                   for t in all_trades]
    out_file = DATA_DIR / "backtest_results.json"
    out_file.write_text(json.dumps({
        "run_date": datetime.now(timezone.utc).isoformat(),
        "tickers_tested": len(tickers) - len(skipped),
        "days": days,
        "total_trades": len(all_trades),
        "trades": save_trades,
    }, indent=2, default=str))
    print(f"\nResults saved to {out_file}")

    if seed and profile:
        seed_file = DATA_DIR / "backtest_dna_profile.json"
        seed_file.write_text(json.dumps(profile, indent=2))
        print(f"DNA profile seeded to {seed_file}")
        print("The live bot will load this on startup to bootstrap DNA scoring.")

    if skipped:
        print(f"Skipped (no 5m bars): {', '.join(skipped[:15])}"
              + (f" +{len(skipped) - 15} more" if len(skipped) > 15 else ""))


if __name__ == "__main__":
    main()
