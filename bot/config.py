# ── PASTE YOUR KEYS HERE (never share this file) ─────────────────────────────
ALPACA_KEY_ID     = "PASTE_YOUR_KEY_ID"       # alpaca.markets → Paper Trading → API Keys
ALPACA_SECRET_KEY = "PASTE_YOUR_SECRET_KEY"
TELEGRAM_TOKEN    = "PASTE_YOUR_BOT_TOKEN"    # message @BotFather to get this
# ─────────────────────────────────────────────────────────────────────────────

TELEGRAM_CHAT_ID  = "8223032422"   # already set up ✓

# Alpaca endpoints (paper trading)
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
ALPACA_DATA_URL = "https://data.alpaca.markets"

# Trade rules (W118 system)
MAX_DAILY_TRADES  = 3         # hard cap — bot stops entering new trades after this
MAX_POSITIONS     = 3         # max simultaneous open positions
SHARES_PER_TRADE  = 10        # fixed lot size for paper trading
STOP_PCT          = 0.08      # -8% hard stop
T1_PCT            = 0.15      # +15% first target
T2_PCT            = 0.30      # +30% second target
T3_PCT            = 0.60      # +60% third target
T1_SHARES         = 3         # shares to sell at T1
T2_SHARES         = 3         # shares to sell at T2
T3_SHARES         = 4         # shares to sell at T3

# Scanner filters (W118 universe — matches Colab scanner exactly)
MIN_PRICE         = 0.10
MAX_PRICE         = 15.00     # matches TradingView Yassss screen
MAX_FLOAT         = 20_000_000 # float < 20M shares — low float = explosive moves
MIN_CHANGE_PCT    = 10.0      # minimum % gain to consider
MIN_ABS_VOLUME    = 1_000_000 # absolute volume floor (HTLM lesson)
REL_VOL_MIN       = 4.0       # relative volume minimum
SCAN_INTERVAL_MIN = 1         # how often to scan in minutes

# Time gate (UTC). Summer: MT = UTC-6, ET = UTC-4
GATE_OPEN_UTC  = 8            # 2:00am MT / 4:00am ET  (premarket start)
GATE_CLOSE_UTC = 22           # 4:00pm MT / 6:00pm ET  (run all day, end at MT close)
