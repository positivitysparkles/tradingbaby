# Curl if Flow — Automated Scanner & Paper Trader

Three scripts that replace W118's manual pre-market routine and paper trade the system automatically.

## Quick Start

```bash
pip install yfinance pandas numpy requests pytz finviz

# Step 1: Pre-market (run at 4am–7am ET)
python pre_market_scanner.py

# Step 2: Monitor for signals all day (run 4am–4pm ET)
python signal_monitor.py

# Step 3: Check your paper trade status anytime
python audit.py --report
python audit.py --auto-close   # updates open trades with current price
```

## Setup Alerts (takes 2 minutes)

### Discord (recommended)
1. Open any Discord server you control
2. Server Settings → Integrations → Webhooks → New Webhook → Copy URL
3. Paste URL into `config.json` → `discord_webhook_url`

### Telegram
1. Message @BotFather on Telegram → `/newbot` → get token
2. Message your new bot once, then visit:
   `https://api.telegram.org/bot<TOKEN>/getUpdates` → copy `chat.id`
3. Paste both into `config.json`

## Data Sources

| Source | Cost | Delay | Float | Best For |
|--------|------|-------|-------|----------|
| yfinance | Free | 15min | No | Testing, backtesting |
| Finviz | Free | ~1min | Yes | Pre-market scanning |
| Alpaca | Free (paper) | Real-time | No | Live signal monitoring |
| Polygon.io | $29/mo | Real-time | Yes | Production use |

**To use Alpaca instead of yfinance** (real-time, free paper account):
```python
# In signal_monitor.py, replace fetch_5m() with Alpaca data:
import alpaca_trade_api as tradeapi
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url='https://paper-api.alpaca.markets')
bars = api.get_bars(ticker, '5Min', limit=100).df
```

## The Full Pipeline

```
4:00am  pre_market_scanner.py  →  data/watchlist.json
  ↓         (finds top NASDAQ gainers, filters by float/price/catalyst tier)

4:05am  signal_monitor.py      →  checks conditions every 5 min
  ↓         (Stoch RSI curl + SHA green + ZLSMA + volume surge)
  ↓         (fires Discord/Telegram alert when all conditions align)
  ↓         (logs paper trade to data/paper_trades.json automatically)

Anytime  audit.py              →  grades trades, tracks win rate vs W118's 98%
```

## What Needs Your Eyes (Catalyst Check)

The one thing that can't be fully automated yet:
- **Is there a real catalyst?** (FDA news, halt-resume, China momentum)
- When the signal fires, check Yahoo Finance news for the ticker
- Grade it Tier 1/2/3 in `paper_trades.json` after checking

This is condition #6 — it filters out false breakouts. Worth 30 seconds of manual check.

## Closing Paper Trades

```bash
# Auto-close based on current price (checks T1/T2/stop)
python audit.py --auto-close

# Manual close
python audit.py --close AKAN 45.00

# Grade a trade manually
python audit.py --grade AKAN_2026042808 A+
```

## Self-Audit Target

The system self-audits every trade against W118's benchmarks:
- **Target**: 90%+ win rate on paper → go live with minimum size
- **W118 benchmark**: 98% win rate, avg winner +53.7%
- Pattern analysis shows which conditions correlate with wins/losses
- Use this data to refine the Pine Script conditions over time
