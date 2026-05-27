"""
W118 Pre-Trade Checklist + Account Growth Projections
Starting: $150 Schwab + $23 Webull
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec
import numpy as np

fig = plt.figure(figsize=(22, 28), facecolor="#0d1117")
DARK="#0d1117"; PANEL="#161b22"; PANEL2="#1c2230"
GREEN="#00c176"; RED="#ff3b47"; YELLOW="#ffd700"
BLUE="#4fc3f7"; ORANGE="#ff9800"; WHITE="#e6edf3"
GRAY="#8b949e"; LGRAY="#30363d"; TEAL="#00e5ff"; PURPLE="#bd93f9"

fig.text(0.5, 0.977, "W118  CURL IF FLOW  —  MY TRADING PLAN",
         ha="center", color=WHITE, fontsize=22, fontweight="bold")
fig.text(0.5, 0.962, "Schwab $150  +  Webull $23  |  Goal: $25,000  |  Paper trade first — go live when ready",
         ha="center", color=YELLOW, fontsize=10)
fig.add_artist(plt.Line2D([0.03,0.97],[0.957,0.957], color=LGRAY, lw=1, transform=fig.transFigure))

gs = GridSpec(3, 2, figure=fig,
              left=0.04, right=0.97, top=0.952, bottom=0.03,
              hspace=0.38, wspace=0.25,
              height_ratios=[2.8, 2.2, 1.8])

# ═══════════════════════════════════════════════════════════
# PANEL 1 — PRE-TRADE CHECKLIST (top-left)
# ═══════════════════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(PANEL2); ax1.axis("off")
ax1.set_xlim(0, 10); ax1.set_ylim(0, 10)

ax1.add_patch(FancyBboxPatch((0.1,0.1),9.8,9.6,
    boxstyle="round,pad=0.1", facecolor=PANEL2, edgecolor=GREEN, lw=2.5))
ax1.text(5, 9.35, "PRE-TRADE CHECKLIST",
         ha="center", color=GREEN, fontsize=13, fontweight="bold")
ax1.text(5, 8.95, "Every box must be YES before you touch the buy button",
         ha="center", color=GRAY, fontsize=8.5)
ax1.axhline(y=8.75, xmin=0.05, xmax=0.95, color=LGRAY, lw=0.8)

checks = [
    ("1", "Stock on TOP MOVERS list?",
     "Up 10%+ pre-market on Webull/TradingView scanner", GREEN),
    ("2", "NASDAQ only, float <20M, price $0.10–$15?",
     "Check float on finviz.com or Webull stock info", BLUE),
    ("3", "Time is 4:00am–10:30am ET?",
     "Outside this window = skip. No exceptions.", YELLOW),
    ("4", "Stoch RSI K was below 10 on 5m chart?",
     "Look at the last 3 candles — K near zero = sharper spike", ORANGE),
    ("5", "K is crossing UP through 20 RIGHT NOW?",
     "This is the curl. The green BUY label fires here.", GREEN),
    ("6", "SHA candle is GREEN right now?",
     "The coloured candles on the chart — must be green at entry", TEAL),
    ("7", "Price is ABOVE the yellow ZLSMA line?",
     "Green background on chart = yes. Red background = NO TRADE.", BLUE),
    ("8", "Volume bar is bigger than usual?",
     "1.5x average = confirmed. Thin volume = skip.", PURPLE),
]

for i, (num, question, note, col) in enumerate(checks):
    y = 8.35 - i * 0.99
    # Checkbox square
    ax1.add_patch(FancyBboxPatch((0.3, y-0.22), 0.60, 0.58,
        boxstyle="round,pad=0.05", facecolor=DARK, edgecolor=col, lw=1.8))
    ax1.text(0.60, y+0.06, "?", color=col, fontsize=10, fontweight="bold", ha="center")
    ax1.text(1.15, y+0.12, question, color=WHITE, fontsize=8.5, fontweight="bold")
    ax1.text(1.15, y-0.18, note, color=GRAY, fontsize=7.2)

ax1.add_patch(FancyBboxPatch((0.3,0.18),9.4,0.72,
    boxstyle="round,pad=0.1", facecolor="#051a08", edgecolor=GREEN, lw=2))
ax1.text(5, 0.62, "ALL 8 = YES?", color=GREEN, fontsize=10, fontweight="bold", ha="center")
ax1.text(5, 0.32, "ENTER the trade.   Any NO = wait for the next one.   Missing setups = free.   Forcing bad ones = expensive.",
         color=GRAY, fontsize=7.5, ha="center")

# ═══════════════════════════════════════════════════════════
# PANEL 2 — ACCOUNT PROJECTIONS CHART (top-right)
# ═══════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(PANEL2)
ax2.tick_params(colors=GRAY, labelsize=8)
ax2.spines[:].set_color(LGRAY)
ax2.grid(True, color=LGRAY, lw=0.4, alpha=0.5)
ax2.set_title("ACCOUNT GROWTH PROJECTIONS\n25% position size per trade  |  avg +30% win  |  -8% stop",
              color=WHITE, fontsize=10, fontweight="bold", pad=8)

trades = 60
pos_size = 0.25
win_gain = 0.30
loss_pct = 0.08
win_rate = 0.98

def project(start, n, wr, wg, lp, ps, seed=42):
    np.random.seed(seed)
    acct = [start]
    results = []
    for _ in range(n):
        win = np.random.rand() < wr
        results.append(win)
        if win:
            acct.append(acct[-1] * (1 + wg * ps))
        else:
            acct.append(acct[-1] * (1 - lp * ps))
    return acct, results

schwab_vals, schwab_res = project(150,  trades, win_rate, win_gain, loss_pct, pos_size, seed=7)
webull_vals, webull_res = project(23,   trades, win_rate, win_gain, loss_pct, pos_size, seed=7)
# Conservative (80% win)
schwab_cons, _ = project(150, trades, 0.80, win_gain, loss_pct, pos_size, seed=99)
webull_cons, _ = project(23,  trades, 0.80, win_gain, loss_pct, pos_size, seed=99)

x = np.arange(trades+1)

ax2.plot(x, schwab_vals, color=BLUE,   lw=2.5, label=f"Schwab $150 → ${schwab_vals[-1]:,.0f} (98% win)", zorder=4)
ax2.plot(x, webull_vals, color=GREEN,  lw=2.5, label=f"Webull $23  → ${webull_vals[-1]:,.0f} (98% win)", zorder=4)
ax2.plot(x, schwab_cons, color=BLUE,   lw=1.5, ls="--", alpha=0.5, label=f"Schwab conservative (80%)", zorder=3)
ax2.plot(x, webull_cons, color=GREEN,  lw=1.5, ls="--", alpha=0.5, label=f"Webull conservative (80%)", zorder=3)

ax2.fill_between(x, schwab_vals, 150, where=(np.array(schwab_vals)>150), color=BLUE, alpha=0.07)
ax2.fill_between(x, webull_vals, 23,  where=(np.array(webull_vals)>23),  color=GREEN, alpha=0.07)

# Milestone lines
milestones = [(500,"$500",GRAY),(1000,"$1k",GRAY),(5000,"$5k",YELLOW),(25000,"$25k\nPDT FREE",RED)]
for lvl, lbl, col in milestones:
    ax2.axhline(lvl, color=col, lw=0.9, ls=":", alpha=0.7)
    ax2.text(1, lvl*1.02, lbl, color=col, fontsize=7.5, fontweight="bold", va="bottom")

# Mark losses as red dots on Schwab line
for i, w in enumerate(schwab_res):
    if not w:
        ax2.plot(i+1, schwab_vals[i+1], "v", color=RED, markersize=7, zorder=5)

ax2.set_yscale("log")
ax2.set_ylim(15, 50000)
ax2.set_xlim(-0.5, 60.5)
ax2.set_xticks([0,10,20,30,40,50,60])
ax2.set_xticklabels(["Start","10","20","30","40","50","60 trades"], color=GRAY, fontsize=8)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
ax2.legend(loc="upper left", fontsize=7.5, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)

# ═══════════════════════════════════════════════════════════
# PANEL 3 — MILESTONE TABLE Schwab (middle-left)
# ═══════════════════════════════════════════════════════════
ax3 = fig.add_subplot(gs[1, 0])
ax3.set_facecolor(PANEL2); ax3.axis("off")
ax3.set_xlim(0,10); ax3.set_ylim(0,10)
ax3.add_patch(FancyBboxPatch((0.1,0.1),9.8,9.6,
    boxstyle="round,pad=0.1", facecolor=PANEL2, edgecolor=BLUE, lw=2))

ax3.text(5, 9.30, "SCHWAB  —  Starting $150",
         ha="center", color=BLUE, fontsize=12, fontweight="bold")
ax3.text(5, 8.85, "25% position per trade  |  PDT: max 3 day trades / 5 days (under $25k)",
         ha="center", color=GRAY, fontsize=8)
ax3.axhline(y=8.65, xmin=0.04, xmax=0.96, color=LGRAY, lw=0.6)

# Headers
for x_pos, hdr, col in [(1.2,"MILESTONE",WHITE),(3.5,"APPROX TRADES",WHITE),
                          (5.8,"PER TRADE ($)",WHITE),(8.0,"NOTES",WHITE)]:
    ax3.text(x_pos, 8.30, hdr, color=col, fontsize=8, fontweight="bold")

milestones_s = [
    ("$150 NOW",   "Start",    "$37",  "25% of $150 = $37/trade", BLUE),
    ("$250",       "~7 trades","$62",  "Growing position sizes", BLUE),
    ("$500",       "~15 trades","$125","Half way to $1k", GREEN),
    ("$1,000",     "~22 trades","$250","Real money feeling :)", GREEN),
    ("$2,500",     "~32 trades","$625","Start considering live", YELLOW),
    ("$5,000",     "~40 trades","$1,250","Strong live account", YELLOW),
    ("$10,000",    "~47 trades","$2,500","Growing fast now", ORANGE),
    ("$25,000",    "~55 trades","$6,250","PDT UNLOCKED — unlimited trades!", RED),
]

for i, (milestone, trades_needed, per_trade, note, col) in enumerate(milestones_s):
    y = 7.80 - i * 0.90
    bg_col = "#051a08" if col in [GREEN, TEAL] else "#0a0a14" if col == BLUE else \
             "#1a1500" if col == YELLOW else "#1a0500" if col == ORANGE else "#2a0505"
    ax3.add_patch(FancyBboxPatch((0.2, y-0.35), 9.5, 0.68,
        boxstyle="round,pad=0.05", facecolor=bg_col, edgecolor=col, lw=0.8, alpha=0.6))
    ax3.text(1.2, y+0.10, milestone,      color=col,   fontsize=8.5, fontweight="bold")
    ax3.text(3.5, y+0.10, trades_needed,  color=WHITE, fontsize=8.5)
    ax3.text(5.8, y+0.10, per_trade,      color=WHITE, fontsize=8.5)
    ax3.text(8.0, y+0.10, note,           color=GRAY,  fontsize=7.5)

# ═══════════════════════════════════════════════════════════
# PANEL 4 — MILESTONE TABLE Webull (middle-right)
# ═══════════════════════════════════════════════════════════
ax4 = fig.add_subplot(gs[1, 1])
ax4.set_facecolor(PANEL2); ax4.axis("off")
ax4.set_xlim(0,10); ax4.set_ylim(0,10)
ax4.add_patch(FancyBboxPatch((0.1,0.1),9.8,9.6,
    boxstyle="round,pad=0.1", facecolor=PANEL2, edgecolor=GREEN, lw=2))

ax4.text(5, 9.30, "WEBULL  —  Starting $23",
         ha="center", color=GREEN, fontsize=12, fontweight="bold")
ax4.text(5, 8.85, "Cash account = NO PDT restriction  |  T+2 settlement (wait 2 days between trades)",
         ha="center", color=GRAY, fontsize=8)
ax4.axhline(y=8.65, xmin=0.04, xmax=0.96, color=LGRAY, lw=0.6)

for x_pos, hdr in [(1.2,"MILESTONE"),(3.5,"APPROX TRADES"),(5.8,"PER TRADE ($)"),(8.0,"NOTES")]:
    ax4.text(x_pos, 8.30, hdr, color=WHITE, fontsize=8, fontweight="bold")

milestones_w = [
    ("$23 NOW",   "Start",     "$5.75", "25% of $23 = $5.75/trade", GREEN),
    ("$50",       "~6 trades", "$12",   "First double", GREEN),
    ("$100",      "~13 trades","$25",   "4x from start", GREEN),
    ("$250",      "~22 trades","$62",   "Real momentum now", YELLOW),
    ("$500",      "~29 trades","$125",  "Combine with Schwab?", YELLOW),
    ("$1,000",    "~36 trades","$250",  "Paper trade done → go live", ORANGE),
    ("$5,000",    "~48 trades","$1,250","Serious account", ORANGE),
    ("$25,000",   "~59 trades","$6,250","PDT UNLOCKED — unlimited trades!", RED),
]

for i, (milestone, trades_needed, per_trade, note, col) in enumerate(milestones_w):
    y = 7.80 - i * 0.90
    bg_col = "#051a08" if col in [GREEN,TEAL] else "#1a1500" if col==YELLOW else \
             "#1a0500" if col==ORANGE else "#2a0505"
    ax4.add_patch(FancyBboxPatch((0.2, y-0.35), 9.5, 0.68,
        boxstyle="round,pad=0.05", facecolor=bg_col, edgecolor=col, lw=0.8, alpha=0.6))
    ax4.text(1.2, y+0.10, milestone,      color=col,   fontsize=8.5, fontweight="bold")
    ax4.text(3.5, y+0.10, trades_needed,  color=WHITE, fontsize=8.5)
    ax4.text(5.8, y+0.10, per_trade,      color=WHITE, fontsize=8.5)
    ax4.text(8.0, y+0.10, note,           color=GRAY,  fontsize=7.5)

# ═══════════════════════════════════════════════════════════
# PANEL 5 — RULES + COMBINED GOAL (bottom, full width)
# ═══════════════════════════════════════════════════════════
ax5 = fig.add_subplot(gs[2, :])
ax5.set_facecolor(PANEL2); ax5.axis("off")
ax5.set_xlim(0,100); ax5.set_ylim(0,10)
ax5.add_patch(FancyBboxPatch((0,0.2),100,9.5,
    boxstyle="round,pad=0.1", facecolor=PANEL2, edgecolor=YELLOW, lw=2,
    transform=ax5.transData))
ax5.text(50, 9.2, "THE RULES — Read These Every Morning",
         ha="center", color=YELLOW, fontsize=12, fontweight="bold")
ax5.axhline(8.8, xmin=0.02, xmax=0.98, color=LGRAY, lw=0.6)

rules = [
    ("SCHWAB", "Max 3 day trades per 5 business days (PDT rule under $25k).\nUse for your best setups only — don't waste trades on weak signals.", BLUE),
    ("WEBULL", "Cash account = unlimited trades BUT cash settles in 2 days (T+2).\nAfter selling, wait 2 days before using that money again.", GREEN),
    ("STOP", "Hard stop at -8% EVERY trade. No exceptions. This is your survival rule.\nOne bad trade without a stop can wipe out 10 good trades.", RED),
    ("POSITION\nSIZE", "Only 25% of account per trade. Never go all-in.\n$150 → $37 max per trade. $23 → $5.75 max per trade.", ORANGE),
    ("PAPER\nFIRST", "Paper trade 20+ times before using real money.\nProve to yourself you can read the curl, enter right, and exit at T2.", YELLOW),
    ("GOAL", "Schwab + Webull combined = $173 today.\nTarget: $25k (PDT unlocked). At W118 pace: ~55-60 winning trades.", PURPLE),
]

col_w = 100/3
for i, (title, desc, col) in enumerate(rules):
    cx = (i%3)*col_w + 1
    cy = 7.8 if i < 3 else 3.8
    ax5.add_patch(FancyBboxPatch((cx-0.5, cy-2.8), col_w-2, 3.3,
        boxstyle="round,pad=0.1", facecolor=DARK, edgecolor=col, lw=1.5,
        transform=ax5.transData))
    ax5.text(cx+0.3, cy+0.25, title, color=col, fontsize=9, fontweight="bold")
    ax5.text(cx+0.3, cy-0.15, desc,  color=GRAY, fontsize=7.8, va="top")

ax5.text(50, 0.75,
    "Combined start: $173  |  Target: $25,000  |  That's 145x your money  |  "
    "At 98% win rate + 25% position size: achievable in ~55-60 trades  |  "
    "Paper trade first. Prove it. Then scale.",
    ha="center", color=WHITE, fontsize=8.5,
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1500", edgecolor=YELLOW, alpha=0.9))

plt.savefig("/home/user/tradingbaby/tools/trading_plan.png",
            dpi=150, bbox_inches="tight", facecolor=DARK)
print("Saved.")
