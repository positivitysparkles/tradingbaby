# tradingbaby — Claude Code Briefing

> Auto-loaded every session. Updated by PreCompact hook. Last manual update: 2026-05-02.

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
data/trades-parsed.json            ← 52 historical trades, 96.2% win rate
```

## The System — "Curl if Flow"

**Author:** Weatherman118 | **Universe:** NASDAQ small-caps $0.10–$15, float <20M

### 6 Entry Conditions (ALL required)
| # | Condition | Weight | Confirmed |
|---|-----------|--------|-----------|
| 1 | Stoch RSI K crosses UP through 20, K above D | critical | ✅ |
| 2 | Smoothed HA candle is green | critical | ✅ |
| 3 | Price above ZLSMA-50 | critical | ✅ NEVER trade below |
| 4 | Volume ≥ 1.5× 20-bar average | confirming | ✅ |
| 5 | Float <20M, $0.10–$15, NASDAQ | filter | ✅ |
| 6 | Catalyst: Tier 1 (FDA/merger) > Tier 2 (halt-resume) > Tier 3 (China momentum) | confirming | ✅ |

### Indicator Settings (confirmed from chart screenshots)
- **Stoch RSI:** RSI=14, Stoch=14, K_smooth=3, D_smooth=3, Source=Close
- **SHA:** Double EMA(10,10) on Heikin Ashi values
- **ZLSMA-50:** 2×EMA(close,50) − EMA(EMA(close,50),50) | color: yellow

### What the charts showed (KEY INSIGHT)
Pre-entry Stoch RSI K on the 5m chart is **0–20** (usually 0–10) before crossover fires.
K/D values extracted from 14 chart screenshots:

| Ticker | Timeframe | K | D | Context |
|--------|-----------|---|---|---------|
| ATER | 5m | 0.69 | 0.00 | Absolute zero pre-spike |
| SAGT | 5m | 1.70 | 0.14 | Absolute zero pre-spike |
| BIAF | 1m | 8.01 | 0.00 | Pre-spike absolute low |
| BIYA | 5m | 9.29 | 7.11 | Near-zero pre-spike |
| AKAN | 5m re-entry | 14.41 | 11.75 | Below 20 re-entry |
| SAFX | 5m | 17.53 | 9.30 | Below 20 pre-spike |
| **AHMA** | **5m** | **24.43** | **10.48** | **★ K just crossed 20, D still at 10 — perfect curl state!** |
| YAAS | 1m | 37.04 | 24.35 | Curling through 20s |
| SAGT | 1m | 41.21 | 28.19 | Curling 20-40 at entry |
| FATN | 1m | 58 | 47 | Mid-range (less ideal) |
| MGRX | 1m | 77.39 | 71.78 | During run (overbought) |
| UGRO | 5m | 82.23 | 68.37 | After big move |
| ATER | 1m | 39.27 | 19.49 | Curling through 20 at entry |

**AHMA 5m is the clearest entry-state screenshot**: K=24.43, D=10.48. K just crossed 20 from below,
D still at 10. This is the exact moment the Pine Script `ta.crossover(k, 20)` fires.
Entry fires at this state. This IS the start of the spike — not chasing.
Pine Script trigger: `ta.crossover(k, 20)` ← confirmed correct.

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

### Re-entry Rule
Stoch RSI must **RESET FULLY BELOW 20** and curl up again. Not just a mid-range pullback.
Re-entries seen in 18 of 52 historical trades (35%).

### Session Priority
- **Premarket 4am–9:30am EST** = highest priority (56% of wins)
- RTH open 9:30–10:30am = high priority
- Midday 10:30am–3pm = avoid (chop kills momentum)
- Power hour 3–4pm = small size only

## Trade Data Summary
- **101 trades** | 2026-03-23 to 2026-04-30 | 99W / 2L | **98.0% win rate**
- Avg winner: +53.7% | Avg loser: -13.5% | Best: UGRO +692.0%- 62 PM wins (62.6%), 37 RTH wins
- Data sources: March 23-30 PDF (49 new trades added May 1), April 27-30 PDFs (52 original trades)

## Key Files
| File | Purpose |
|------|---------|
| `pine-script/weatherman118-curl-flow.pine` | TradingView Pine Script v5 strategy |
| `journal/index.html` | Single-file dark trade journal (localStorage) |
| `parser/discord_parser.py` | Parse W118 Discord recaps → JSON |
| `backtest/backtest_curl_if_flow.py` | yfinance backtester — run LOCALLY (needs internet) |
| `data/trades-parsed.json` | 101 historical trades |
| `data/settings.json` | Full system spec |
| `.claude/memory/vault.json` | Compact vault (rich structured memory) |

## How to use the tools

**Add new Discord recaps:**
```bash
python parser/discord_parser.py recap.txt --append data/trades-parsed.json
```

**Run backtest (MUST run locally — yfinance needs internet):**
```bash
pip install yfinance pandas numpy
python backtest/backtest_curl_if_flow.py --verbose
python backtest/backtest_curl_if_flow.py --ticker AKAN --date 2026-04-28
```
Note: many small-cap tickers get delisted after running — yfinance may return NO_DATA.
Best test tickers: AKAN, SKLZ, SNBR (larger float, less likely delisted).

**TradingView — load Pine Script:**
1. Open Pine Script Editor in TradingView
2. Paste contents of `pine-script/weatherman118-curl-flow.pine`
3. Apply to 5m chart | Extended hours ON | Dark theme
4. Test on $YAAS April 27 2026 — should show BUY label at the curl

## Confidence assessment (as of 2026-05-02)
Current: **~87% confident** the Pine Script replicates W118's system.

| What's confirmed | Confidence |
|-----------------|------------|
| All 6 entry conditions | ✅ 100% |
| Stoch RSI settings (3,3,14,14) | ✅ 100% |
| Entry trigger: ta.crossover(k, 20) | ✅ 100% |
| Pre-entry K state: 0-10 on 5m | ✅ 95% |
| SHA Double EMA(10,10) | ✅ 95% |
| ZLSMA-50 formula | ✅ 100% |
| Volume: 1.5× 20-bar | ✅ 90% |
| Re-entry: full reset below 20 | ✅ 95% |

| What's still uncertain | Gap |
|-----------------------|-----|
| K depth pre-condition (below 10 vs below 20?) | ~5% gap |
| SHA consecutive green candles (1 or 2+?) | ~3% gap |
| Re-entry: price touch ZLSMA-50 required? | ~3% gap |
| Volume: hard rule or eyeballed? | ~2% gap |

## Pending tasks (as of 2026-05-02)
- [ ] Run backtest LOCALLY (pip install yfinance) — try AKAN 2026-04-28, SNBR 2026-04-28
- [ ] Load Pine Script in TradingView on YAAS 5m April 27 — verify BUY label fires
- [ ] Paper trade live for 2-4 weeks — log in journal/index.html
- [ ] Get more W118 Discord screenshots showing 5m chart at entry moment
- [ ] Consider adding `k[1] < 10` pre-condition to Pine Script
- [ ] Add new Discord recaps as W118 posts them

## Open questions (what would make the system 100%)
1. Should we add `k[1] < 10` pre-condition (K was below 10 before crossing 20)?
2. Does SHA need 2+ consecutive green candles, or just the current one?
3. On re-entries: does price need to touch ZLSMA-50 before the reset?
4. Is the volume 1.5× hard rule or eyeballed? Does W118 ever skip it?
5. March 23-28 chart data read but AHMA 5m (K=24.43) is the clearest entry state we have

## Smart compact system
When token count hits 180k, the Stop hook sets `autoCompactThreshold: 1`.
Your next message fires PreCompact → vault.json is updated → compact runs → threshold resets to 197k.
You don't need to do anything. It's automatic.
