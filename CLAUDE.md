# tradingbaby — Claude Code Briefing

> Auto-loaded every session. Updated by PreCompact hook. Last manual update: 2026-06-03.

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

**AHMA 5m is the clearest entry-state screenshot**: K=24.43, D=10.48. K just crossed 20 from below,
D still at 10. Pine Script trigger: `ta.crossover(k, 20)` ← confirmed correct.

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

## n8n Automation Setup

**n8n URL:** https://n8n-scrz.srv1493928.hstgr.cloud
**Plan:** Free (no Variables — keys hardcoded in code nodes)
**MCP:** Instance-level MCP enabled → Claude Code can directly edit/create/run workflows

### Architecture (rebuilt 2026-06-03)

```
TradingView Pro (Yassss screener + W118 alerts)
        │ webhook POST {ticker, price, signal}
        ▼
n8n: W118 TV Webhook Receiver  ← PRIMARY
        │ BUY → Alpaca market buy + STOP + T1/T2/T3 + Telegram
        │ EXIT → cancel orders + market sell + Telegram
        │
FMP Scanner (backup, every 6 min, 4am-5pm ET)
        │ real-time gainers → W118 conditions check → same Alpaca flow
```

### Workflows
| Workflow | File | Trigger | Status |
|----------|------|---------|--------|
| W118 TV Webhook Receiver | n8n/w118_tv_webhook.json | TradingView webhook POST | ⚠️ Import + configure |
| W118 Full Auto Scanner | n8n/w118_full_scanner.json | Every 6 min, 4am–5pm ET | ⚠️ Update code node |
| W118 Auto Paper Trading | n8n/w118_auto_paper_trading.json | Gmail | ❌ Deprecated |

### W118 TV Webhook Receiver — How it works
1. TradingView fires W118 BUY or EXIT alert → POST to n8n webhook URL
2. Parse + Guard node: validates ticker/price/signal, checks Alpaca positions (MAX=3)
3. IF BUY: place Alpaca market buy → STOP(-8%) + T1(+15%) + T2(+30%) + T3(+60%) → Telegram
4. IF EXIT: cancel all open orders for ticker → market sell full position → Telegram

### W118 Full Auto Scanner — How it works (backup)
1. Runs every 6 min, **4am–5pm ET only** (UTC 8-21 time gate built in)
2. Pulls real-time top gainers from **FMP API** (financialmodelingprep.com — free, 250/day)
3. Checks each candidate: K>D, price>ZLSMA-50, volume 4x avg
4. On signal: same Alpaca BUY + bracket orders + Telegram flow

### When you update scanner code in n8n
**Only update the "W118 Full Scanner" code node** — paste jsCode from the JSON file.
Need 3 keys at top: ALPACA_KEY_ID, ALPACA_SECRET_KEY, FMP_API_KEY.

### Telegram
- Bot: @RichAlertOls_bot | Chat ID: 8223032422 | Credential: "W118 Telegram Bot"

### Alpaca Paper Trading
- **Recommended balance: $10,000** (not $1k — need room for 3 simultaneous positions)
- Paper mode only — real trades done manually on Webull/Schwab
- Reset balance at: alpaca.markets → Paper Trading → Reset Account

## Security Rules
- **NEVER paste API keys in chat** — only in Colab cells or n8n node code directly
- Keys belong in: n8n code node top constants, Colab cell variables — nowhere else
