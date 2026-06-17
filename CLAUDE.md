# tradingbaby — Claude Code Briefing

> Auto-loaded every session. Updated by PreCompact hook. Last manual update: 2026-06-15.

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
- Yahoo Finance free screener → filter: price $0.10–$5, float < 10M, change > 10%, rel vol > 4x
- Absolute volume > 1M shares (filters out dead stocks like HTLM 69K)

**Step 2 — Chart Confirmation (ALL required):**
| # | Condition | Timeframe | Weight |
|---|-----------|-----------|--------|
| 1 | **Supertrend flips bullish (green)** | 5m | PRIMARY trigger |
| 2 | Price above ZLSMA-50 | 5m | critical — NEVER trade below |
| 3 | StochRSI K > D | 5m | critical |
| 4 | Volume > 4x 20-bar average | 5m | confirming |
| 5 | Catalyst: Tier 1 (FDA/merger) > Tier 2 (halt-resume) > Tier 3 (China momentum) | — | confirming |

**Note:** MACD settings changed to (5,10,16) on 2026-06-17 — faster than standard 12,26,9, fires in sync with Supertrend rather than lagging. Blue line above red = histogram > 0 = hard gate. StochRSI now requires K rising (K > K_prev) in addition to K > D.

**Step 3 — Entry:**
- Enter on 5m Supertrend buy signal, OR zoom to 1m for a better price if signal already fired

### Indicator Settings (all confirmed)
- **Supertrend:** ATR Period=10, Source=(H+L)/2, ATR Multiplier=2, Change ATR Calc=✓
- **Stoch RSI:** RSI=14, Stoch=14, K_smooth=3, D_smooth=3, Source=Close
- **ZLSMA-50:** 2×EMA(close,50) − EMA(EMA(close,50),50) | color: yellow
- **MACD:** 12, 26, 9 | histogram > 0 = momentum building, not fading
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
| `bot/indicators.py` | Supertrend, StochRSI, ZLSMA, MACD |
| `bot/add_ticker.py` | `python bot/add_ticker.py AHMA JRSH` |
| `bot/status.py` | Quick positions/P&L check |

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

## Open Positions (2026-06-15)
| Ticker | Entry | Account | Stop | T1 | T2 | T3 |
|--------|-------|---------|------|----|----|-----|
| CAST | TBD | TBD | entry×0.92 | entry×1.15 | entry×1.30 | entry×1.60 |
| HQ | TBD | TBD | entry×0.92 | entry×1.15 | entry×1.30 | entry×1.60 |

**Note:** Entry prices for CAST and HQ not yet logged — user to confirm. CALC/VVOS status from June 5 unknown (assumed closed).

## Security Rules
- **NEVER paste API keys in chat** — only in Colab cells or n8n node code directly
- Keys belong in: n8n code node top constants, Colab cell variables — nowhere else
