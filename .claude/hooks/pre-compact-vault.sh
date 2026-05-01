#!/bin/bash
# tradingbaby PreCompact vault writer.
# Saves all confirmed system knowledge, current data state, and pending tasks
# so the next session starts fully informed without re-reading the docs.
#
# Called by ~/.claude/hooks/pre-compact-vault.sh with args:
#   $1 = vault file path
#   $2 = timestamp
#   $3 = transcript path

set -euo pipefail

VAULT_FILE="${1:-/home/user/tradingbaby/.claude/memory/vault.json}"
TIMESTAMP="${2:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}"

TRADES_JSON="/home/user/tradingbaby/data/trades-parsed.json"
SETTINGS_JSON="/home/user/tradingbaby/data/settings.json"

python3 - <<PYEOF
import json, os

vault_file = "$VAULT_FILE"
timestamp = "$TIMESTAMP"
trades_path = "$TRADES_JSON"
settings_path = "$SETTINGS_JSON"

# Load existing vault
vault = {}
if os.path.exists(vault_file):
    try:
        with open(vault_file) as f:
            vault = json.load(f)
    except:
        vault = {}

# ── CONFIRMED SYSTEM KNOWLEDGE ────────────────────────────────────────────────
vault["project"] = "tradingbaby"
vault["system_name"] = "Curl if Flow"
vault["author"] = "Weatherman118"
vault["last_compact"] = timestamp
vault.setdefault("compact_count", 0)
vault["compact_count"] += 1

vault["confirmed_entry_conditions"] = {
    "stoch_rsi": {
        "trigger": "K crosses UP through 20 from below — ta.crossover(k, 20)",
        "requirement": "K must be above D at trigger",
        "pre_entry_state": "K typically at 0-10 before cross (near absolute zero)",
        "settings": "RSI=14, Stoch=14, K_smooth=3, D_smooth=3, Source=Close"
    },
    "smoothed_ha": {
        "trigger": "Current candle must be green (sha_close > sha_open)",
        "calculation": "Double EMA(10,10) on Heikin Ashi values",
        "note": "First green candle after red = curl forming"
    },
    "zlsma_50": {
        "trigger": "Price (close) must be ABOVE ZLSMA-50",
        "formula": "2 * EMA(close,50) - EMA(EMA(close,50),50)",
        "rule": "NEVER enter if price is below ZLSMA-50 — trade is invalid"
    },
    "volume": {
        "trigger": "Volume >= 1.5x the 20-bar average",
        "weight": "confirming (not critical)"
    },
    "float": "< 20M shares, $0.10-$15, NASDAQ only",
    "catalyst": "Tier 1 (FDA/merger/earnings), Tier 2 (halt-resume/sympathy), Tier 3 (China momentum)"
}

vault["confirmed_exit_rules"] = {
    "hard_stop": "-8% from entry — no exceptions",
    "T1": "+15% — trim 1/3, move stop to breakeven",
    "T2": "+30% — trim 1/3 of original, trail 10%",
    "T3": "+60% — trail 10% on final 1/3",
    "sha_exit": "SHA flips red for 2+ consecutive candles",
    "zlsma_exit": "Price closes below ZLSMA-50",
    "stoch_exit": "Stoch RSI K crosses back below 20"
}

vault["confirmed_reentry_rule"] = "Stoch RSI must RESET BELOW 20 and curl UP again — not just mid-range pullback"

vault["chart_data_extracted"] = {
    "YAAS_1m": {"K": 37.04, "D": 24.35, "context": "Curling through 20s at entry"},
    "YAAS_5m": {"K": 93.42, "D": 89.62, "context": "Overbought during run"},
    "BIYA_5m": {"K": 9.29, "D": 7.11, "context": "Near zero pre-spike"},
    "BIYA_1m": {"K": 18.24, "D": 7.78, "context": "Sub-20 curling at entry"},
    "ATER_5m": {"K": 0.69, "D": 0.00, "context": "Absolute zero pre-spike"},
    "ATER_1m": {"K": 39.27, "D": 19.49, "context": "Curling through 20 at entry"},
    "AKAN_5m_reentry": {"K": 14.41, "D": 11.75, "context": "Below 20 re-entry setup"},
    "SAGT_5m": {"K": 1.70, "D": 0.14, "context": "Absolute zero pre-spike"},
    "SAGT_1m": {"K": 41.21, "D": 28.19, "context": "Curling 20-40 at entry"},
    "SAFX_5m": {"K": 17.53, "D": 9.30, "context": "Below 20 pre-spike"},
    "SAFX_1m": {"K": 93.03, "D": 81.91, "context": "After move (overbought)"},
    "USEG_5m": {"K": 16.38, "D": 5.52, "context": "Reset after PM spike"},
    "FATN_1m": {"K": 58, "D": 47, "context": "Mid-range at entry — less ideal"},
    "FATN_5m": {"K": 93, "D": 81, "context": "Overbought during run"}
}

vault["key_insight"] = (
    "Pre-entry Stoch RSI K is consistently 0-20 (usually 0-10) on the 5m chart. "
    "Entry fires at the moment K crosses above 20. The Pine Script ta.crossover(k, 20) is correct. "
    "This IS the beginning of the spike — not chasing."
)

# ── LIVE TRADE DATA ──────────────────────────────────────────────────────────
if os.path.exists(trades_path):
    with open(trades_path) as f:
        data = json.load(f)
    vault["trade_data"] = {
        "total_trades": data["stats"]["total_trades"],
        "win_rate_pct": data["stats"]["win_rate_pct"],
        "wins": data["stats"]["wins"],
        "losses": data["stats"]["losses"],
        "avg_winner_pct": data["stats"]["avg_winner_pct"],
        "avg_loser_pct": data["stats"]["avg_loser_pct"],
        "best_trade": data["stats"]["best_trade"],
        "pm_wins": data["stats"]["pm_wins"],
        "rth_wins": data["stats"]["rth_wins"],
        "date_range": f"{data['trades'][0]['date']} to {data['trades'][-1]['date']}"
    }

# ── FILE LOCATIONS ────────────────────────────────────────────────────────────
vault["key_files"] = {
    "trades": "/home/user/tradingbaby/data/trades-parsed.json",
    "settings": "/home/user/tradingbaby/data/settings.json",
    "pine_script": "/home/user/tradingbaby/pine-script/weatherman118-curl-flow.pine",
    "journal": "/home/user/tradingbaby/journal/index.html",
    "parser": "/home/user/tradingbaby/parser/discord_parser.py",
    "backtest": "/home/user/tradingbaby/backtest/backtest_curl_if_flow.py",
    "vault": vault_file
}

vault["github"] = {
    "repo": "positivitysparkles/tradingbaby",
    "branch": "claude/push-tradingbaby-ESEFn",
    "google_drive_email": "iris.at.ps@positivitysparkles.com"
}

# ── PENDING TASKS ─────────────────────────────────────────────────────────────
vault["pending_tasks"] = [
    "Run backtest_curl_if_flow.py against all 52 trades to measure signal capture %",
    "Read March 23-28 PDF from Google Drive (Canva march 23-28 2026 day trades.pdf) — file was too large last attempt",
    "Pine Script: optionally add pre-condition that K was below 10 before the crossover",
    "Continue adding new Discord recaps to trades-parsed.json as user shares them",
    "Paper trade system — use journal/index.html to log live trades",
    "Build confidence to 843%+ win consistency before going live"
]

vault["open_questions"] = [
    "Exact Stoch RSI K value at entry — confirmed as 'crossing above 20' but is there a min pre-entry depth?",
    "Does SHA need 2+ consecutive green candles or just the current one?",
    "On re-entries: full reset below 20 confirmed — but does price need to touch ZLSMA-50?",
    "Volume multiplier: 1.5x confirmed in settings — is it ever eyeballed higher?",
    "Session timing: PM entries have higher win rate (56%) — is midday always avoided?"
]

with open(vault_file, "w") as f:
    json.dump(vault, f, indent=2)

print(f"[tradingbaby vault] Saved to {vault_file} (compact #{vault['compact_count']})")
PYEOF
