# tradingbaby — Claude Code Briefing

> Auto-loaded every session. Last manual update: 2026-06-25.

## What this project is

Reverse-engineering Weatherman118's "Curl if Flow" NASDAQ small-cap momentum system.
Goal: find the exact Pine Script / indicator settings that replicate his near-100% win rate,
then use it for paper trading until we hit consistent profitability.

Owner: positivitysparkles | Google Drive: iris.at.ps@positivitysparkles.com
GitHub repo: positivitysparkles/tradingbaby | Branch: claude/push-tradingbaby-ESEFn

## Read these files first every session

```
.claude/memory/vault.json          ← structured memory from last compact
data/settings.json                 ← full reverse-engineered system spec
data/trades-parsed.json            ← 101 historical trades, 98.0% win rate
```

## The System — "Curl if Flow"

**Author:** Weatherman118 | **Universe:** NASDAQ small-caps $0.10–$15, float <10M (tightened 2026-06-05)

### Entry System (updated 2026-06-25)

**Step 1 — Stock Discovery (Scanner):**
- TradingView scanner → filter: price $0.10–$15, change > 10%, rel vol > 1.5x
- Absolute volume > 1M shares (filters out dead stocks)
- Yahoo predefined gainers kept as fallback. Price ceiling raised $5→$15 on 2026-06-17 (BIRD lesson)

**Step 2 — Chart Confirmation:**
| # | Condition | Timeframe | Weight |
|---|-----------|-----------|--------|
| 1 | **Pivot Point SuperTrend flips bullish** (Period=2, Factor=3, ATR=10) | 5m | PRIMARY trigger |
| 2 | Price above ZLSMA-50 | 5m | critical — NEVER trade below |
| 3 | StochRSI K > D AND K rising | 5m | critical |
| 4 | Volume > 1.5x 20-bar average | 5m | soft (score only — dries up during coil) |
| 5 | Catalyst: Tier 1 (FDA/merger) > Tier 2 (halt-resume) > Tier 3 (momentum) | — | confirming |
| 6 | **Price holds above Session VWAP** | 5m | hard gate w/ 0.5% tolerance |
| 7 | **RSI(14) > 50** | 5m | soft confirmation (score only, never blocks) |

**Note:** MACD settings (5,10,16) — faster than standard 12,26,9, fires in sync with PPST. `hist > 0` = hard gate in CORE. StochRSI requires K rising (K > K_prev) in addition to K > D.

### Condition priority tiers (MUST vs soft)
- **Tier 1 — Structure (hard MUST):** PPST green (5m) · Price > VWAP · Price > ZLSMA-50
- **Tier 2 — Ignition (entry timing):** StochRSI K>D & rising · MACD hist > 0
- **Tier 3 — Quality/context (soft):** Volume > 1.5× · RSI > 50 · MACD line > 0
- **PPST is a hard gate to BUY, not to WATCH.** Bearish-PPST names STAY on watchlist — the flip to bullish IS the entry.
- **Auto-buy = CORE:** PPST green + above VWAP + above ZLSMA + Stoch hook + MACD hist > 0 + K < 85 (not overbought). Volume/RSI/MACD-line are SOFT — raise grade but never block.

### ⭐ The A+ "Shelf Bounce" pattern (codified from June-19 chart study)
The highest-probability entry is the **second-leg continuation**, not the first vertical spike:
1. **Anchor spike** breaks above Session VWAP + pushes PPST cloud solid bullish
2. **Shelf compression** — price pulls back and trades flat ON the ZLSMA-50 / VWAP, volume dries up
3. **Reset + hook** — StochRSI K resets low (≲30) then hooks up (K>D and **rising**); MACD hist flips dark-red→green near zero
4. **Trigger** — PPST prints a fresh bullish flip
- **VWAP is the divider:** every June-19 runner (ATPC +42%, CRVO, CDT +47%) held above VWAP.
- **Reset zone = ≤30, NOT <25.** Owner's A+ CDT entry was K=33.9.

**Step 3 — Entry:**
- Enter on 5m PPST buy signal, OR zoom to 1m for a better price if signal already fired
- **Session gate:** bot pauses NEW entries 10:30am–3pm ET (midday chop, re-enabled June-25). Exits still run all day.
- **Deep-curl flag:** if StochRSI K reloaded near 0 (≤30) within last ~12 bars before curling up → ⭐ in alerts (stronger entry). Feeds audit.

### Indicator Settings (all confirmed)
- **Pivot Point SuperTrend:** Pivot Period=2, ATR Factor=3, ATR Period=10 (replaces regular Supertrend — June-25)
- **Stoch RSI:** RSI=14, Stoch=14, K_smooth=3, D_smooth=3, Source=Close
- **ZLSMA-50:** 2×EMA(close,50) − EMA(EMA(close,50),50) | color: yellow
- **MACD:** 5, 10, 16 (faster than standard — fires in sync with PPST)
- **RSI:** 14-period standalone (soft confirmation, June-25)
- **VWAP:** Anchor=Session, Source=HL2 — `vwap_session()` in indicators.py
- **Chandelier Exit (CE):** ATR Period=10, Multiplier=2, Use Close for Extremums=✓

### Exit Rules
| Exit | Trigger | Action |
|------|---------|--------|
| Stop | -8% from entry | Hard stop, no exceptions |
| T1 | +15% | Trim 1/3; software trailing stop moves to breakeven |
| T2 | +30% | Trim 1/3; software trailing stop trails 10% below current price |
| T3 | +60% | Trail 10% on final 1/3 — let it run |
| PPST exit | PPST flips bearish | Exit (structure reversed) |
| ZLSMA exit | Price closes below ZLSMA-50 | Exit (uptrend support gone) |
| Chandelier exit | Close below CE line (ATR 10/2) | Exit — ride the runner (RTH-only) |
| MACD crossover | MACD histogram < 0 (blue below orange) | Exit (momentum reversing, June-25) |
| Trailing stop | Price retreats to raised stop after T1/T2 | Software exit (June-25) |

**Software trailing stop** (`_trail` dict, persisted to `data/trail_state.json`):
- T1 hit (+15%) → stop moves from -8% to breakeven (entry price)
- T2 hit (+30%) → stop trails 10% below current, updates every scan
- Only fires after T1 (never locks in a loss beyond the hard -8%)

### Setup B "Trend Rider" (dual-strategy, added 2026-06-27)

A second, simpler setup running alongside Setup A. Both collect data independently.

**Entry (all 4 required for CORE pass):**
| # | Condition | Details |
|---|-----------|---------|
| 1 | PPST bullish on 5m | Same Period=2, Factor=3, ATR=10 as Setup A |
| 2 | Standard MACD (12,26,9) blue > orange AND rising | NOT the fast (5,10,16) |
| 3 | Volume increasing | Current bar > prev bar OR > 20-bar avg |
| 4 | RSI(14) > 50 | Hard gate (not soft like Setup A) |

**MTF bonus (not blocking, feeds grade):** 15m PPST bullish +1, 1H PPST bullish +1

**Exit:** PPST bearish flip OR MACD(12,26,9) blue < orange. Same -8% stop + T1/T2/T3 trailing.

**Grading:**
- A+ = full core pass + MTF (15m AND 1H bullish) + strong catalyst
- A  = full core pass + MTF (15m OR 1H) OR any catalyst
- B  = full core pass only
- C  = below full pass

**Position limits:** 5 simultaneous per setup, 10 total combined. Separate edge profiles.

**Config:** `SETUP_B_ENABLED = True` in config.py. All knobs have getattr defaults.

### Session Priority
- **Premarket 4am–9:30am EST** = highest priority (56% of wins)
- RTH open 9:30–10:30am = high priority
- Midday 10:30am–3pm = **AVOID** (confirmed -$23.24 over 15 trades, June-25 audit)
- Power hour 3–4pm = small size only

## Trade Data Summary (Historical)
- **101 trades** | 2026-03-23 to 2026-04-30 | 99W / 2L | **98.0% win rate**
- Avg winner: +53.7% | Avg loser: -13.5% | Best: UGRO +692.0%

## Pattern-Learning Data (live bot, as of 2026-06-25)
- **26 closed trades** | 23% win rate | -$53.39 net (learning phase — bot taking all signals)
- 4 trades remain until Edge Engine shifts from LEARNING → TIGHTENING (auto-blocks losing grades)
- C grades: 25% win rate, 20 trades — bulk of losses, will be pruned at tightening
- K=75-85: 0% win rate over 7 trades — overbought at entry confirmed bad
- Midday: 15 trades, -$23.24 — chop confirmed, AVOID_MIDDAY re-enabled
- MFE avg +19.7% vs exit avg -3.0% — exits too early on winners; trailing stop addresses this

## Automation — Python Bot (replaces n8n, 2026-06-15)

**Run on MacBook:** `python bot/bot.py`
**Setup:** Edit `bot/config.py` → paste Alpaca paper keys + Telegram token

### Architecture

```
Yahoo Finance free screener  ←  auto discovery (no API key needed)
data/watchlist.json          ←  manual tickers (python bot/add_ticker.py TICKER)
        │
        ▼
bot/bot.py  (runs every 1 min, 2am–4pm MT / 4am–6pm ET — all-day observation)
        │  checks all 7 W118 conditions via bot/indicators.py
        │
        ├── CORE PASS → Alpaca paper buy + STOP(-8%) + T1(+15%) + T2(+30%) + T3(+60%)
        │              + software trailing stop initialized
        │              + Telegram BUY alert
        │
        ├── Open position check → trailing stop update + signal exits
        │              → market sell + Telegram EXIT alert
        │
        └── 4:30pm ET daily → Telegram audit (trades, P&L, pattern insights)
            Monday 5pm ET  → Telegram weekly win rate summary
```

### Bot files
| File | Purpose |
|------|---------|
| `bot/config.py` | API keys + trade rules (edit this once) |
| `bot/bot.py` | Main loop — run this |
| `bot/indicators.py` | PPST, RSI, StochRSI, ZLSMA, MACD, VWAP, Chandelier, catalyst proxy |
| `bot/edge.py` | Edge Engine — A+/A/B/C grading, grade-scaled sizing, learn→tighten gate, K-range bucketing, Chart DNA mining + scoring; `grade_setup_b()` for Setup B grading |
| `bot/add_ticker.py` | `python bot/add_ticker.py AHMA JRSH` |
| `bot/status.py` | Quick positions/P&L check |

### Edge Engine (self-improving, caged)
Every entry is graded **A+/A/B/C**. Sizing is **flat $100/trade** during the learning phase (all grades equal — gathering data). The bot **learns then tightens**: it takes every valid signal until `LEARN_THRESHOLD` (50) closed trades exist, then auto-buys only grades proven to win (≥`EDGE_WINRATE_FLOOR` over ≥`EDGE_MIN_SAMPLE`). Edge profile buckets by: grade, session, catalyst, deep_curl, vol ratio, K-at-entry range. Recomputed on startup + daily audit, cached to `data/edge_profile.json` + `w118_edge` (Supabase). Setup B has its own independent edge profile and learning phase, starting at 0 closed trades.

### Chart DNA Pattern Learning (added 2026-06-27)
10 numerical features captured at every entry, describing the chart's shape:
| # | Feature | What it captures |
|---|---------|-----------------|
| 1 | `momentum_5` | Short-term price acceleration (5 bars) |
| 2 | `momentum_10` | Medium-term trend strength (10 bars) |
| 3 | `vwap_dist_pct` | Distance from VWAP (shelf bounce = ~0%) |
| 4 | `zlsma_dist_pct` | How stretched above trend support |
| 5 | `k_reset_depth` | Stoch reset depth (deeper = stronger spring) |
| 6 | `vol_accel` | Volume accelerating or dying |
| 7 | `range_compression` | Coil/shelf pattern (lower = tighter) |
| 8 | `day_range_pct` | Pullback entry (0%) vs chase (100%) |
| 9 | `rsi_entry` | RSI(14) momentum confirmation |
| 10 | `macd_slope` | MACD histogram direction |

**Mining:** `mine_chart_patterns()` in edge.py buckets each feature into ranges, computes win rates vs baseline, finds sweet spots (+15pp lift), danger zones (-15pp), and the strongest two-feature combos.

**Scoring:** `chart_dna_score()` scores new entries 0-100 based on matches against the mined pattern profile. 50=neutral, sweet spot matches add points, danger zone matches subtract.

**Config:** `DNA_GATE_ENABLED = False` (default). Advisory-only — DNA score appears in Telegram alerts and the daily audit but never blocks trades. Set to True to let low scores block auto-buy.

**Supabase:** 11 new columns on `w118_trades` (10 features + `dna_score`). Run the ALTER TABLE statements from `supabase/schema.sql` in the SQL Editor.

### Key data files (runtime, gitignored)
| File | Contents |
|------|----------|
| `data/trail_state.json` | Trailing stop state per ticker (entry, stop, t1_hit, t2_hit) |
| `data/exit_pending.json` | In-flight exit orders (restart-safe dedup) |
| `data/watch_sent.json` | WATCH alert throttle + outcome tracking |
| `data/edge_profile.json` | Edge Engine cached profile |

### Quick start
```bash
pip install requests schedule
# Edit bot/config.py → paste 3 values: ALPACA_KEY_ID, ALPACA_SECRET_KEY, TELEGRAM_TOKEN
python bot/bot.py
```

### Telegram
- Bot: @RichAlertOls_bot | Chat ID: 8223032422 | Token: in config.py (never in chat)
- **QUIET_ALERTS = True** — only trade alerts + daily/weekly audit push to Telegram. Everything else is log-only (journalctl).

### Alpaca Paper Trading
- **Recommended balance: $10,000** (reset at alpaca.markets → Paper Trading → Reset Account)
- Paper mode only — real trades done manually on Webull/Schwab

### Legacy n8n workflows (kept for reference, not active)
| File | Status |
|------|--------|
| n8n/w118_full_scanner.json | ⚠️ Not active — replaced by bot/ |
| n8n/w118_tv_webhook.json | ⚠️ Not active — replaced by bot/ |
| n8n/w118_auto_paper_trading.json | ❌ Deprecated |

## Colab Setup Note
Google Drive asks to connect every new Colab session — this is by design (security). Fix: add
this as the first cell in every Colab notebook:
```python
from google.colab import drive
import os
if not os.path.isdir('/content/drive/MyDrive'):
    drive.mount('/content/drive')
print("✅ Drive ready")
```

## Infrastructure — Confirmed Working

### Supabase
- **Trading project:** `lgzzuppprbokfobhycov.supabase.co` — this is the ONLY Supabase project for trading
- **Tables:** `w118_trades` (logs every entry + MFE/MAE/bars_held) + `w118_edge` (edge engine snapshots)
- **RLS:** anon key = read-only (dashboard). Service role key in VPS `bot/config.py` = write.
- **Dashboard anon key:** `sb_publishable_qIqnOFvjWSVquqlCpDIj2Q_t468MohI` (public/safe)
- **DO NOT TOUCH** the healing project (`suqfqnrxkjhmrzbkzrze`) — unrelated to trading
- **Pending migration** (run once in SQL Editor if not done):
  ```sql
  ALTER TABLE w118_trades ADD COLUMN IF NOT EXISTS mfe_pct   numeric(6,2);
  ALTER TABLE w118_trades ADD COLUMN IF NOT EXISTS mae_pct   numeric(6,2);
  ALTER TABLE w118_trades ADD COLUMN IF NOT EXISTS bars_held integer;
  ```

### VPS Bot (Hostinger)
- Bot lives at: `/root/tradingbaby/bot/bot.py`
- Service name: `w118bot`
- Key commands:
  ```
  sudo systemctl status w118bot       # is it running?
  sudo journalctl -fu w118bot         # live log stream
  sudo journalctl -u w118bot -n 50 --no-pager   # last 50 lines
  sudo systemctl restart w118bot      # restart after config/code change
  git pull origin main                # pull latest fixes (from /root/tradingbaby/)
  ```
- Config on VPS: `/root/tradingbaby/bot/config.py` (gitignored — keys live here only)
- Required in config: `ALPACA_KEY_ID`, `ALPACA_SECRET_KEY`, `TELEGRAM_TOKEN`, `SUPABASE_URL`, `SUPABASE_KEY`

### Dashboard (Vercel)
- Vercel env vars must match the trading Supabase project:
  - `NEXT_PUBLIC_SUPABASE_URL` = `https://lgzzuppprbokfobhycov.supabase.co`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `sb_publishable_qIqnOFvjWSVquqlCpDIj2Q_t468MohI`

### Current config on VPS (as of 2026-06-25) — MUST be set manually in config.py
- `MAX_POSITIONS = 5`
- `MAX_DAILY_TRADES = 9999`
- `AVOID_MIDDAY = True` ← **MUST set this in VPS config.py** (explicit False in config overrides in-code default)
- `REQUIRE_1M_FRESH = False`
- `LEARNING_FLAT_SIZE = 100` (all grades flat $100/trade during learning phase)
- `TICKER_COOLDOWN_H = 24` (24h before same ticker can re-buy)

## All PRs / Bug fixes shipped
| Fix | PR | Date |
|-----|----|------|
| `buy_$` SyntaxError crash-loop | earlier | 2026-06 |
| Edge Engine (A+/A/B/C grading, learn→tighten) | #59 | 2026-06-19 |
| Exit spam loop (100+ TNON alerts) | #63 | 2026-06-19 |
| Premarket OPG sell / bracket orders blocked shares | #63 | 2026-06-19 |
| Restart re-alert dedup (`exit_pending.json`) | #63 | 2026-06-19 |
| RTH hard stop blocked by bracket orders | #63 | 2026-06-19 |
| AVOID_MIDDAY disabled for data collection | #67 | 2026-06-19 |
| get_bars `feed=sip` + min 10 bars | #67 | 2026-06-19 |
| yfinance bars fallback + vol-0 fix | #70 | 2026-06-19 |
| VWAP entry gate (condition #6) | #71 | 2026-06-19 |
| Chandelier Exit trailing stop | #71 | 2026-06-19 |
| Scanner tightened (MAX_FLOAT 20M→10M) | #71 | 2026-06-19 |
| 24h ticker cooldown + $100 flat sizing | #83 | 2026-06-22 |
| Daily self-audit Telegram (`_self_audit_insights`) | #84 | 2026-06-22 |
| MFE/MAE tracking + WATCH outcomes + K-range bucketing | #85 | 2026-06-22 |
| Pivot Point SuperTrend (Period=2, Factor=3, ATR=10) | #86 | 2026-06-25 |
| RSI(14) soft entry confirmation | #86 | 2026-06-25 |
| MACD bearish crossover exit signal | #86 | 2026-06-25 |
| MAE/MFE bug fix (filter to post-entry bars, fix sign) | #86 | 2026-06-25 |
| AVOID_MIDDAY re-enabled (default True) | #86 | 2026-06-25 |
| Software trailing stop (T1→breakeven, T2→trail 10%) | #87 | 2026-06-25 |
| Setup B "Trend Rider" dual-strategy architecture | #91 | 2026-06-27 |
| Learning threshold raised 30→50 (both setups) | #92 | 2026-06-27 |
| Chart DNA pattern learning (10 features + mining + scoring) | #93 | 2026-06-27 |

## Pending features (roadmap)
- [ ] Historical backtesting — run `check_all_entry()` on 6-month bar history for our early-bird tickers. Needs Polygon.io (~$30/mo) or Alpaca historical 5m data. See June-25 conversation.
- [ ] Short selling — Phase 2 after longs hit 60%+ win rate. Small-caps have hard-to-borrow issues.
- [ ] Multi-agent coworker — research agent (backtesting), pattern agent (nightly Supabase mining), risk monitor (parallel to bot).

## Critical lessons learned — DO NOT REPEAT
1. **`feed=sip` is correct** for Alpaca paper trading. DO NOT switch to iex — our small-cap NASDAQ universe has ZERO IEX coverage.
2. **30-bar minimum was too strict.** Indicator functions handle sparse data (return None → blocker). Bar minimum is 10.
3. **`REQUIRE_1M_FRESH = False`** — this gate blocks 5/5 setups when 1m is consolidating. Leave it False.
4. **`AVOID_MIDDAY = True` must be set explicitly in VPS config.py.** The getattr default (True) does NOT override an explicit `AVOID_MIDDAY = False` in config.py. Always check: `grep AVOID_MIDDAY /root/tradingbaby/bot/config.py`.
5. **After ANY PR merge → always `git pull origin main && sudo systemctl restart w118bot` on VPS.** The VPS bot does not auto-update.
6. **Heartbeat "No candidates found this scan"** = bars fetch failing (feed issue or bars < minimum). Not a conditions problem.
7. **TWO relative-volume knobs — never conflate them.** `SCANNER_REL_VOL_MIN` (3.0) = TradingView discovery filter. `REL_VOL_MIN` (1.5) = 5-min bar volume check. KEEP bar check at 1.5.
8. **VWAP gate fails open.** No timestamps/volume → VWAP condition skipped (not failed).
9. **Exit timing:** June-25 audit showed MFE avg +19.7% vs exit avg -3.0%. Bot was exiting at losses while stocks later went up 19%. Root cause: ZLSMA/Chandelier signal exits firing during healthy pullbacks. PPST reduces whipsaws; trailing stop preserves profit once T1 hits.
10. **MAE -23.7% was a data artifact.** Fixed in PR #86 — now filters to bars after `_sb_entry_ts[ticker]`. Real MAE on a -8% stop system should be 2–8%.
11. **PPST replaced regular Supertrend (June-25).** Uses confirmed swing pivot highs/lows as band anchors instead of rolling hl2 → fewer whipsaw flips during consolidation. Settings: Period=2, Factor=3, ATR=10.

## What "no alerts" means
The **30-min heartbeat** (💓) shows TOP BLOCKERS in journalctl (not Telegram — QUIET_ALERTS is on).
- "No candidates found this scan" → bars fetch failing (check feed, API key, bot restart)
- Any other blocker → conditions failing (expected during slow market)
If no heartbeat for >1 hour → `sudo systemctl status w118bot`

## Security Rules
- **NEVER paste API keys or secret keys in chat** — only in VPS config.py directly
- The `sb_publishable_...` anon key IS safe to share (read-only by design)
- Service role key = NEVER in chat, NEVER in git
