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
REL_VOL_MIN       = 1.5       # relative volume minimum — matches Colab grader (was 4.0, too strict, blocked nearly every entry)
SCAN_INTERVAL_MIN = 1         # how often to scan in minutes

# Time gate (UTC). Summer: MT = UTC-6, ET = UTC-4
GATE_OPEN_UTC  = 8            # 2:00am MT / 4:00am ET  (premarket start)
GATE_CLOSE_UTC = 22           # 4:00pm MT / 6:00pm ET  (run all day, end at MT close)

# Session timing — avoid the midday chop (W118: 56% of wins are premarket;
# 10:30am-3pm ET is the dead zone). NEW ENTRIES are paused midday; exits on
# open positions ALWAYS run regardless of time. Power hour (3-4pm) stays open.
AVOID_MIDDAY    = True
MIDDAY_START_ET = 10.5        # 10:30am ET — entries pause
MIDDAY_END_ET   = 15.0        # 3:00pm ET  — entries resume (power hour)

# Entry quality — deep-curl flag (informational only, no gate). StochRSI K that
# recently dipped near 0 then curled up = stronger reload (Colab grader's ⭐).
# Shown in alerts + logged so the audit can learn if deep curls win more often.
DEEP_CURL_RESET = 20.0        # K dipped below this in the lookback = deep curl
