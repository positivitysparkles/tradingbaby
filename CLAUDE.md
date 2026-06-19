# tradingbaby — Claude Code Briefing

> Auto-loaded every session. Last manual update: 2026-06-19.

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

### Entry System (updated 2026-06-17 — MACD dropped as hard gate)

**Step 1 — Stock Discovery (Scanner):**
- TradingView scanner (same engine as the Yassss screen) → filter: price $0.10–$15, change > 10%, rel vol > 1.5x
- Absolute volume > 1M shares (filters out dead stocks like HTLM 69K)
- Yahoo predefined gainers kept as crumb-free fallback. Price ceiling raised $5→$15 on 2026-06-17 (BIRD lesson)

**Step 2 — Chart Confirmation (ALL required):**
| # | Condition | Timeframe | Weight |
|---|-----------|-----------|--------|
| 1 | **Supertrend flips bullish (green)** | 5m | PRIMARY trigger |
| 2 | Price above ZLSMA-50 | 5m | critical — NEVER trade below |
| 3 | StochRSI K > D | 5m | critical |
| 4 | Volume > 1.5x 20-bar average | 5m | confirming (was 4x — too strict, matched to Colab grader 2026-06-17) |
| 5 | Catalyst: Tier 1 (FDA/merger) > Tier 2 (halt-resume) > Tier 3 (China momentum) | — | confirming |
| 6 | **Price holds above Session VWAP** | 5m | hard gate w/ 0.5% tolerance (added 2026-06-19) |

**Note:** MACD settings changed to (5,10,16) on 2026-06-17 — faster than standard 12,26,9, fires in sync with Supertrend rather than lagging. Blue line above red = histogram > 0 = hard gate. StochRSI now requires K rising (K > K_prev) in addition to K > D. **MACD stays 5/10/16 — confirmed by owner 2026-06-19** (charts also show 12/26/9 but the bot uses the faster one).

### Condition priority tiers (which of the 6 are MUST vs soft)
Not all 6 carry equal weight. From the chart study:
- **Tier 1 — Structure (hard MUST, never trade without):** Supertrend green (5m) · Price > VWAP · Price > ZLSMA-50. These define "is this even an uptrend." Every June-19 runner had all three; the WKSP chop broke VWAP.
- **Tier 2 — Ignition (the entry timing):** StochRSI K>D & rising (the *hook* = the trigger) · MACD hist > 0.
- **Tier 3 — Quality/context (soft):** Volume > 1.5× · MACD line > 0. **Volume is the soft one** — by design it DRIES UP during the coil; the surge prints on the breakout candle, so a hard volume gate can make us enter late.
- **Supertrend is a hard gate to BUY, not to WATCH.** Red-supertrend scanner names STAY on the watchlist — the flip back to green IS the entry. 5m = the gun; 1m = entry-price fine-tuning (`REQUIRE_1M_FRESH`, off).
- **Auto-buy = CORE, not 6/6 (2026-06-19, owner decision):** 6/6 rarely lines up, so AUTO-BUY now fires on the **CORE** gate = Supertrend green + above VWAP + above ZLSMA + Stoch hook (K>D & rising) + **MACD histogram > 0** + K < `OVERBOUGHT_K` (85). **Volume and MACD-line>0 are SOFT** — they raise the score/grade but never block. Relaxed entries grade C ($50, small) and the Edge Engine prunes them via learn→tighten if they lose. `check_all_entry` returns `core_pass` as the auto-buy flag; `score`/`max`/`full_pass` still tally all 6 for grading + display. Overbought K (e.g. NUCL K=98.8) is now blocked from auto-buy too, not just WATCH. (This supersedes the earlier `🌀 COIL` manual alert — those dry-coil setups are now CORE auto-buys.)

### ⭐ The A+ "Shelf Bounce" pattern (codified from June-19 chart study)
The highest-probability entry is the **second-leg continuation**, not the first vertical spike:
1. **Anchor spike** breaks above Session VWAP + pushes the Curl cloud solid green
2. **Shelf compression** — price pulls back and trades flat ON the ZLSMA-50 / VWAP, volume dries up
3. **Reset + hook** — StochRSI K resets low (≲30) then hooks up (K>D and **rising**); MACD hist flips dark-red→green near zero
4. **Trigger** — Supertrend prints a fresh green flip
- **VWAP is the divider:** every June-19 runner (ATPC +42%, CRVO, CDT +47%) held above VWAP; the WKSP chop did not.
- **Reset zone = ≤30, NOT <25.** The owner's own A+ CDT entry was K=33.9 — a stricter floor would have blocked the best trade. The *hook* is the trigger, not the absolute low.

**Step 3 — Entry:**
- Enter on 5m Supertrend buy signal, OR zoom to 1m for a better price if signal already fired
- **Session gate (2026-06-17):** bot pauses NEW entries 10:30am–3pm ET (midday chop). Exits still run all day. Premarket + open + power hour only. Toggle: `AVOID_MIDDAY` in config.
- **Deep-curl flag (2026-06-17):** if StochRSI K reloaded near 0 (≤20) within the last ~12 bars before curling up, the setup is marked ⭐ in alerts (stronger entry). Informational only — does not gate entry yet; feeds the audit.

### Indicator Settings (all confirmed)
- **Supertrend:** ATR Period=10, Source=(H+L)/2, ATR Multiplier=2, Change ATR Calc=✓
- **Stoch RSI:** RSI=14, Stoch=14, K_smooth=3, D_smooth=3, Source=Close
- **ZLSMA-50:** 2×EMA(close,50) − EMA(EMA(close,50),50) | color: yellow
- **MACD:** 5, 10, 16 (bot uses this — faster, fires with Supertrend) | line>0 AND hist>0 = hard gate
- **VWAP:** Anchor=Session, Source=HL2, Bands ×1 (added 2026-06-19) — `vwap_session()` in indicators.py
- **Chandelier Exit (CE):** ATR Period=10, Multiplier=2, Use Close for Extremums=✓ (added 2026-06-19)
- **SHA:** Double EMA(10,10) on Heikin Ashi values (visual reference only)

### Why Supertrend > W118 Buy Signal as trigger
The W118 Pine Script Buy label fires AFTER the move starts (lagging). Supertrend flips
at the trend change itself. Use W118 indicators as confirmation filters, Supertrend as the gun.

### Exit Rules
| Exit | Trigger | Action |
|------|---------|--------|
| Stop | -8% from entry | Hard stop, no exceptions |
| T1 | +15% | Trim 1/3, move stop to breakeven |
| T2 | +30% | Trim 1/3, trail stop 10% |
| T3 | +60% | Trail 10% on final 1/3 — let it run |
| SHA exit | SHA red 2+ consecutive candles | Exit |
| ZLSMA exit | Price closes below ZLSMA-50 | Exit |
| Stoch exit | K crosses back below 20 | Exit |
| **Chandelier exit** | Full candle closes below CE line (ATR 10/2) | Exit — ride the runner until this prints (added 2026-06-19, RTH-only) |

### Session Priority
- **Premarket 4am–9:30am EST** = highest priority (56% of wins)
- RTH open 9:30–10:30am = high priority
- Midday 10:30am–3pm = **AVOID** (chop kills momentum)
- Power hour 3–4pm = small size only

## Trade Data Summary (Historical)
- **101 trades** | 2026-03-23 to 2026-04-30 | 99W / 2L | **98.0% win rate**
- Avg winner: +53.7% | Avg loser: -13.5% | Best: UGRO +692.0%

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
        │  checks all 5 W118 conditions via bot/indicators.py
        │
        ├── ALL PASS → Alpaca paper buy + STOP(-8%) + T1(+15%) + T2(+30%) + T3(+60%)
        │              + Telegram BUY alert
        │
        ├── Open position check → signal exits (K<20, price<ZLSMA, ST bearish)
        │              → cancel orders + market sell + Telegram EXIT alert
        │
        └── 4:30pm ET daily → Telegram audit (trades, P&L, positions)
            Monday 5pm ET  → Telegram weekly win rate summary
```

### Bot files
| File | Purpose |
|------|---------|
| `bot/config.py` | API keys + trade rules (edit this once) |
| `bot/bot.py` | Main loop — run this |
| `bot/indicators.py` | Supertrend, StochRSI, ZLSMA, MACD, catalyst proxy |
| `bot/edge.py` | Edge Engine — A+/A/B/C grading, grade-scaled sizing, learn→tighten gate |
| `bot/add_ticker.py` | `python bot/add_ticker.py AHMA JRSH` |
| `bot/status.py` | Quick positions/P&L check |

### Edge Engine (self-improving, caged) — added 2026-06-19
Every entry is graded **A+/A/B/C** (full 5/5 + deep-curl + price-action catalyst =
A+). Sizing is **grade-scaled** ($150 A+ → $50 C) but hard-clamped to
`[DOLLARS_MIN, DOLLARS_MAX]`. The bot **learns then tightens**: it takes every valid
signal until `LEARN_THRESHOLD` (30) closed trades exist, then auto-buys only grades
proven to win (≥`EDGE_WINRATE_FLOOR` over ≥`EDGE_MIN_SAMPLE`) — restrict-only, never
loosens a cap. Edge profile recomputed on startup + daily audit, cached to
`data/edge_profile.json` + `w118_edge` (Supabase) for the dashboard. `MAX_POSITIONS`
raised 3→5 for the paper learning phase. All new knobs default in-code (no config.py
edit needed). Concurrency knob aside, a plain `git pull` + restart picks it all up.

### Quick start
```bash
pip install requests schedule
# Edit bot/config.py → paste 3 values: ALPACA_KEY_ID, ALPACA_SECRET_KEY, TELEGRAM_TOKEN
python bot/bot.py
```

### Telegram
- Bot: @RichAlertOls_bot | Chat ID: 8223032422 | Token: in config.py (never in chat)

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
One click, then it connects without re-asking within the same session.

## Infrastructure — Confirmed Working (2026-06-19)

### Supabase
- **Trading project:** `lgzzuppprbokfobhycov.supabase.co` — this is the ONLY Supabase project for trading
- **Tables:** `w118_trades` (logs every entry) + `w118_edge` (edge engine snapshots)
- **RLS:** anon key = read-only (dashboard). Service role key in VPS `bot/config.py` = write.
- **Dashboard anon key:** `sb_publishable_qIqnOFvjWSVquqlCpDIj2Q_t468MohI` (public/safe)
- **DO NOT TOUCH** the healing project (`suqfqnrxkjhmrzbkzrze`) — unrelated to trading

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

### Current config on VPS (as of 2026-06-19)
- `MAX_POSITIONS = 5` ✅ (raised from 3 for paper learning phase)
- `MAX_DAILY_TRADES = 9999` ✅ (effectively unlimited — run `grep MAX_DAILY_TRADES /root/tradingbaby/bot/config.py` to confirm)

## Bug fixes shipped (2026-06-19)
| Fix | PR | Status |
|-----|----|--------|
| `buy_$` SyntaxError crash-loop | earlier | ✅ merged |
| Edge Engine (A+/A/B/C grading, learn→tighten) | #59 | ✅ merged |
| Exit spam loop (100+ TNON alerts) | #63 | ✅ merged |
| Premarket OPG sell (bracket orders blocked shares) | #63 | ✅ merged |
| Restart re-alert dedup (`exit_pending.json`) | #63 | ✅ merged |
| RTH hard stop blocked by bracket orders | #63 | ✅ merged |
| [skip] logging at INFO level + 9:30am bell + 30min heartbeat | #63 | ✅ merged |
| AVOID_MIDDAY disabled for data collection phase | #67 | ✅ merged |
| get_bars silent failure: `feed=sip` + min 10 bars + visible logging | #67 | ✅ merged |
| yfinance bars (Alpaca SIP unavailable on paper) + vol-0 fix | #70 | ✅ merged |

## System upgrade shipped (2026-06-19) — VWAP + Chandelier + tighter scanner
From the June-19 chart study (`june 19 2026/` folder). All knobs default in-code — a plain
`git pull` + restart picks it up, no config.py edit needed.
| Change | Detail |
|--------|--------|
| **Session VWAP entry gate** | New condition #6. `price ≥ VWAP×(1−0.5%)` to auto-buy. Fail-open when no bars/volume. Feeds the A+ grade. `VWAP_GATE`, `VWAP_TOLERANCE`. |
| **Chandelier Exit** | New trailing exit (ATR 10/2). Fires alongside Supertrend/ZLSMA/-8%, RTH-only. `CHANDELIER_EXIT`, `CE_ATR_PERIOD`, `CE_ATR_MULT`. |
| **Scanner tightened** | `MAX_FLOAT` 20M→10M. New `SCANNER_REL_VOL_MIN=3.0` for TradingView discovery — **separate** from `REL_VOL_MIN=1.5` (the 5-min bar volume check, which must stay 1.5). |
| **Reset zone** | `DEEP_CURL_RESET` 20→30 (owner's A+ CDT entry was K=33.9; ≤25 would block it). |
| **Grade** | A+ now = full pass + deep curl + (strong catalyst OR clean above-VWAP). |
| `get_bars` carries `"t"` | ISO timestamp added per bar so session VWAP can reset daily. |

## Critical lessons learned (2026-06-19) — DO NOT REPEAT
1. **`feed=sip` is correct** for Alpaca paper trading. SIP covers all exchanges incl. NASDAQ.
   `feed=iex` only covers stocks that trade on IEX exchange — our small-cap NASDAQ universe
   has ZERO IEX coverage. Every stock returns empty bars on IEX. DO NOT switch to iex.
2. **30-bar minimum was too strict.** Individual indicator functions handle sparse data
   gracefully (return None → blocker added). Bar minimum is now 10.
3. **`REQUIRE_1M_FRESH = False`** — this gate was added in the Edge Engine PR overnight.
   It blocks 5/5 setups when 1m is consolidating. Leave it False.
4. **`AVOID_MIDDAY = False`** during data collection phase so bot trades all session hours.
5. **After ANY PR merge → always `git pull origin main && sudo systemctl restart w118bot` on VPS.**
   The VPS bot does not auto-update. Silence after a merge = old code still running.
6. **Heartbeat "No candidates found this scan"** = blockers Counter is empty = get_bars()
   returning None for every ticker (feed issue or bars < minimum). Not a conditions problem.
7. **TWO relative-volume knobs — never conflate them.** `SCANNER_REL_VOL_MIN` (3.0) is the
   TradingView *discovery* filter (which stocks get scanned). `REL_VOL_MIN` (1.5) is the
   *5-min bar* volume confirmation (vol > 1.5× 20-bar avg). The bar one being 4.0 is what
   blocked every entry — KEEP it at 1.5. Tighten discovery via `SCANNER_REL_VOL_MIN` only.
8. **VWAP gate fails open.** If a name has no timestamps/volume, the VWAP condition is
   skipped (max drops 6→5), not failed — a thin/halted name isn't blocked just for that.

## What "no alerts" means
The **30-min heartbeat** (💓) shows TOP BLOCKERS — exact condition failing most.
- "No candidates found this scan" → bars fetch failing (check feed, API key, bot restart)
- Any other blocker → conditions failing (expected during slow market periods)
If no heartbeat for >1 hour → `sudo systemctl status w118bot`

## Current config on VPS (as of 2026-06-19 ~11am ET)
- `MAX_POSITIONS = 5`
- `MAX_DAILY_TRADES = 9999`
- `AVOID_MIDDAY = False` (disabled for data collection)
- `REQUIRE_1M_FRESH = False`

## Security Rules
- **NEVER paste API keys or secret keys in chat** — only in VPS config.py directly
- The `sb_publishable_...` anon key IS safe to share (read-only by design)
- Service role key = NEVER in chat, NEVER in git
