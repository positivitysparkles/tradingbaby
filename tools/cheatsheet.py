"""
W118 Curl if Flow — One-Page Cheat Sheet
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec
import numpy as np

fig = plt.figure(figsize=(20, 26), facecolor="#0d1117")
DARK="#0d1117"; PANEL="#161b22"; PANEL2="#1c2230"
GREEN="#00c176"; RED="#ff3b47"; YELLOW="#ffd700"
BLUE="#4fc3f7"; ORANGE="#ff9800"; WHITE="#e6edf3"
GRAY="#8b949e"; LGRAY="#30363d"; TEAL="#00e5ff"; PURPLE="#bd93f9"

def box(ax, x, y, w, h, fc, ec, lw=1.5, radius=0.02):
    ax.add_patch(FancyBboxPatch((x,y),w,h,
        boxstyle=f"round,pad={radius}", facecolor=fc, edgecolor=ec, linewidth=lw,
        transform=ax.transAxes, clip_on=False))

# ── TITLE ─────────────────────────────────────────────────────────
fig.text(0.5, 0.978, "W118  CURL IF FLOW  —  CHEAT SHEET",
         ha="center", color=WHITE, fontsize=24, fontweight="bold",
         fontfamily="monospace")
fig.text(0.5, 0.963, "Weatherman118  |  NASDAQ Small-Cap Momentum  |  5m Chart  |  Intraday Only",
         ha="center", color=GRAY, fontsize=10)

# Divider
fig.add_artist(plt.Line2D([0.03,0.97],[0.957,0.957], color=LGRAY, lw=1, transform=fig.transFigure))

gs = GridSpec(3, 3, figure=fig,
              left=0.03, right=0.97, top=0.952, bottom=0.02,
              hspace=0.42, wspace=0.28)

# ═══════════════════════════════════════════════════════════
# PANEL 1 — WHAT IS THE CURL? (top-left, spans 2 cols)
# ═══════════════════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0, :2])
ax1.set_facecolor(PANEL2); ax1.set_xlim(0,100); ax1.set_ylim(-8,115)
ax1.tick_params(colors=GRAY, labelsize=8); ax1.spines[:].set_color(LGRAY)
ax1.grid(True, color=LGRAY, lw=0.4, alpha=0.5)
ax1.set_title("WHAT IS THE CURL?  —  The One Moment That Matters",
              color=YELLOW, fontsize=11, fontweight="bold", pad=8)

t = np.linspace(0,100,200)
# K line: flat near 0-5, then curls up through 20, rises to 70s
K = np.where(t < 80,
    3 + 2*np.sin(t*0.15) + np.random.randn(200)*1.5,
    3 + (t-80)**1.8 * 0.08)
K = np.clip(K, 0, 100)
# Smooth
def smooth(arr, w):
    return np.convolve(arr, np.ones(w)/w, mode='same')
K = smooth(K, 8)
D = smooth(K, 14)

ax1.axhline(80, color=RED,   lw=1, ls=":", alpha=0.6)
ax1.axhline(20, color=GREEN, lw=1.5, ls="--", alpha=0.9)
ax1.axhline(10, color=YELLOW,lw=0.8, ls=":", alpha=0.5)
ax1.axhline(0,  color=GRAY,  lw=0.5, alpha=0.4)

ax1.plot(t, K, color=BLUE,   lw=2.5, label="K (fast line — blue)", zorder=4)
ax1.plot(t, D, color=ORANGE, lw=1.8, label="D (slow line — orange)", ls="--", zorder=3)

# Shade the "dead zone" pre-curl
ax1.axvspan(0, 80, color="#ff3b47", alpha=0.04)
ax1.axvspan(80, 100, color="#00c176", alpha=0.06)

# Find crossover point
cross_idx = np.where((K[:-1]<20) & (K[1:]>=20))[0]
if len(cross_idx):
    cx = t[cross_idx[0]+1]
    ky = 20
    ax1.axvline(cx, color=GREEN, lw=2.5, ls="-", alpha=0.9, zorder=5)
    ax1.plot(cx, ky, "o", color=GREEN, markersize=14, zorder=6)
    ax1.annotate("THE CURL\nK crosses 20\nfrom below\n= BUY NOW",
        xy=(cx, ky), xytext=(cx+4, 50),
        color=GREEN, fontsize=10, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=GREEN, lw=2),
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#051a08", edgecolor=GREEN, lw=2))

# Annotate phases
ax1.text(20, 7, "K sitting near 0-10\n(sellers exhausted, stock dead)\nWAITING for the curl",
         color=GRAY, fontsize=8.5, ha="center",
         bbox=dict(boxstyle="round,pad=0.3", facecolor=DARK, edgecolor=LGRAY))
ax1.text(90, 60, "K rising fast\nmomentum\nbuilding",
         color=GREEN, fontsize=8.5, ha="center",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#051a08", edgecolor=GREEN))

ax1.text(1, 22, "ENTRY LINE (K=20)", color=GREEN, fontsize=8, fontweight="bold")
ax1.text(1, 82, "OVERBOUGHT (K=80) — start trimming", color=RED, fontsize=8)
ax1.text(1, 5, "IDEAL PRE-ENTRY ZONE (K<10)", color=YELLOW, fontsize=8)

ax1.legend(loc="upper left", fontsize=9, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)
ax1.set_xticks([]); ax1.set_yticks([0,10,20,50,80,100])

# ═══════════════════════════════════════════════════════════
# PANEL 2 — 6 ENTRY CONDITIONS (top-right)
# ═══════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[0, 2])
ax2.set_facecolor(PANEL2); ax2.axis("off")
ax2.set_xlim(0,10); ax2.set_ylim(0,10)
ax2.set_title("6 ENTRY CONDITIONS\n(ALL must be YES)",
              color=GREEN, fontsize=10, fontweight="bold", pad=6)
ax2.add_patch(FancyBboxPatch((0.1,0.1),9.8,9.6,
    boxstyle="round,pad=0.1", facecolor=PANEL2, edgecolor=GREEN, lw=2))

conditions = [
    ("1", "K crosses UP through 20", "Stoch RSI curl — the trigger", GREEN),
    ("2", "K is above D at cross", "Fast line > slow line = momentum", GREEN),
    ("3", "K was below 10 recently", "Deeper dip = sharper spike", YELLOW),
    ("4", "SHA candle is GREEN", "Smoothed HA = buyers in control", BLUE),
    ("5", "Price ABOVE ZLSMA-50", "Yellow line = the 'flow' zone", ORANGE),
    ("6", "Volume >= 1.5x avg", "Confirms real buying, not fake", TEAL),
]
for i, (num, cond, note, col) in enumerate(conditions):
    y = 8.8 - i*1.42
    ax2.add_patch(FancyBboxPatch((0.3, y-0.35), 0.7, 0.75,
        boxstyle="round,pad=0.05", facecolor=col, edgecolor=col, alpha=0.25))
    ax2.text(0.65, y+0.07, num, color=col, fontsize=11, fontweight="bold", ha="center")
    ax2.text(1.2, y+0.07, cond, color=WHITE, fontsize=8, fontweight="bold")
    ax2.text(1.2, y-0.22, note, color=GRAY, fontsize=7)

ax2.text(5, 0.5, "ALL 6 = GREEN  →  ENTER", color=GREEN,
         fontsize=9, fontweight="bold", ha="center",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#051a08", edgecolor=GREEN))

# ═══════════════════════════════════════════════════════════
# PANEL 3 — EXIT RULES (middle-left)
# ═══════════════════════════════════════════════════════════
ax3 = fig.add_subplot(gs[1, 0])
ax3.set_facecolor(PANEL2); ax3.axis("off")
ax3.set_xlim(0,10); ax3.set_ylim(0,10)
ax3.set_title("EXIT RULES — In Order", color=RED, fontsize=10, fontweight="bold", pad=6)
ax3.add_patch(FancyBboxPatch((0.1,0.1),9.8,9.6,
    boxstyle="round,pad=0.1", facecolor=PANEL2, edgecolor=RED, lw=2))

exits = [
    ("STOP", "-8%", "Hard stop. No exceptions.\nThis is your maximum loss.", RED, "⬛"),
    ("T1",   "+15%", "Sell 1/3. Move stop\nto breakeven. Free ride.", "#a8ff78", "▲"),
    ("T2",   "+30%", "Sell 1/3 more. Trail\nstop 10%. Or exit 100%.", GREEN, "▲▲"),
    ("T3",   "+60%", "Trail 10% on last 1/3.\nLet runners run.", TEAL, "▲▲▲"),
    ("SHA",  "2 red candles", "SHA flips red 2x in a row\n= momentum fading, exit.", ORANGE, "⚠"),
    ("K<20", "K drops below 20", "Stoch momentum gone.\nClose position.", ORANGE, "⚠"),
    ("ZLSMA","Price < ZLSMA line", "Trend broken.\nExit immediately.", RED, "⚠"),
]
for i, (name, lvl, note, col, icon) in enumerate(exits):
    y = 9.0 - i*1.22
    ax3.text(0.4, y, icon, color=col, fontsize=9)
    ax3.text(1.1, y+0.08, f"{name}  {lvl}", color=col, fontsize=8.5, fontweight="bold")
    ax3.text(1.1, y-0.30, note, color=GRAY, fontsize=7)
    if i < len(exits)-1:
        ax3.axhline(y-0.52, xmin=0.05, xmax=0.95, color=LGRAY, lw=0.5)

# ═══════════════════════════════════════════════════════════
# PANEL 4 — FAST EXIT 3 RULES (middle-center)
# ═══════════════════════════════════════════════════════════
ax4 = fig.add_subplot(gs[1, 1])
ax4.set_facecolor(PANEL2); ax4.axis("off")
ax4.set_xlim(0,10); ax4.set_ylim(0,10)
ax4.set_title("3 FAST-EXIT RULES\n(Pine Script — all ON by default)", color=YELLOW, fontsize=10, fontweight="bold", pad=6)
ax4.add_patch(FancyBboxPatch((0.1,0.1),9.8,9.6,
    boxstyle="round,pad=0.1", facecolor=PANEL2, edgecolor=YELLOW, lw=2))

rules = [
    ("RULE 1", "K DEPTH FILTER",
     "K must have been below 10\nwithin 3 bars before the curl.\nDeeper dip = sharper spike.\nSkip curls from above 10.",
     YELLOW, "k[1]<10 or k[2]<10 or k[3]<10"),
    ("RULE 2", "TIME GATE",
     "Only enter 4:00am–10:30am ET.\n82% of wins = PM or RTH open.\nMidday signals = slow or fail.\nNo trades after 10:30am.",
     ORANGE, "4am ≤ bar_time ≤ 10:30am"),
    ("RULE 3", "HARD T2 EXIT",
     "Exit 100% at T2 (+30%).\nNo chasing T3.\n82% of wins exit at ≤60%.\nClean 1-2hr exit every time.",
     TEAL, "Exit 100% @ +30%"),
]
for i, (rule, name, desc, col, code) in enumerate(rules):
    y = 8.8 - i*2.95
    ax4.add_patch(FancyBboxPatch((0.2, y-1.8), 9.5, 2.3,
        boxstyle="round,pad=0.1", facecolor=DARK, edgecolor=col, lw=1.5))
    ax4.text(0.5, y+0.20, rule, color=col, fontsize=7, fontweight="bold", alpha=0.8)
    ax4.text(0.5, y-0.05, name, color=col, fontsize=9, fontweight="bold")
    ax4.text(0.5, y-0.32, desc, color=GRAY, fontsize=7.5, va="top")
    ax4.text(0.5, y-1.58,  f"  {code}", color=col, fontsize=7.5,
             fontfamily="monospace",
             bbox=dict(boxstyle="round,pad=0.2", facecolor="#0a0a0a", edgecolor=col, alpha=0.6))

# ═══════════════════════════════════════════════════════════
# PANEL 5 — DO vs DON'T (middle-right)
# ═══════════════════════════════════════════════════════════
ax5 = fig.add_subplot(gs[1, 2])
ax5.set_facecolor(PANEL2); ax5.axis("off")
ax5.set_xlim(0,10); ax5.set_ylim(0,10)
ax5.set_title("DO  vs  DON'T", color=WHITE, fontsize=10, fontweight="bold", pad=6)

ax5.add_patch(FancyBboxPatch((0.1,5.2),4.6,4.5,
    boxstyle="round,pad=0.1", facecolor="#051a08", edgecolor=GREEN, lw=2))
ax5.add_patch(FancyBboxPatch((5.1,5.2),4.6,4.5,
    boxstyle="round,pad=0.1", facecolor="#1a0505", edgecolor=RED, lw=2))

ax5.text(2.4, 9.4, "DO", color=GREEN, fontsize=13, fontweight="bold", ha="center")
ax5.text(7.4, 9.4, "DON'T", color=RED, fontsize=13, fontweight="bold", ha="center")

dos = ["Enter at the curl\n(K crosses 20)",
       "Use 5m as primary\nchart",
       "Close by 10:30am\nentry cutoff",
       "Take stop at -8%\nno matter what",
       "Exit same day\nalways"]
donts = ["Chase after alert\n(K already 80+)",
         "Buy mid-spike\n(too late)",
         "Hold overnight\never",
         "Move stop lower\n'hoping'",
         "Trade midday\n(10:30am–3pm)"]

for i, (d, dn) in enumerate(zip(dos, donts)):
    y = 8.6 - i*0.88
    ax5.text(0.3, y, "✓", color=GREEN, fontsize=9, fontweight="bold")
    ax5.text(0.9, y, d, color=WHITE, fontsize=7.2)
    ax5.text(5.3, y, "✗", color=RED, fontsize=9, fontweight="bold")
    ax5.text(5.9, y, dn, color=WHITE, fontsize=7.2)

# Bottom DO/DON'T
ax5.add_patch(FancyBboxPatch((0.1,0.2),9.6,4.7,
    boxstyle="round,pad=0.1", facecolor=PANEL, edgecolor=LGRAY, lw=1))
ax5.text(5, 4.6, "3 QUESTIONS — Ask Every Chart", color=YELLOW,
         fontsize=8, fontweight="bold", ha="center")
qs = [
    ("Q1", "Is K crossing 20 from near-zero RIGHT NOW?", "Yes = enter  |  No = wait"),
    ("Q2", "Is the MACD histogram green and growing?",   "Yes = alive  |  Red = done"),
    ("Q3", "Did the spike already happen without me?",    "Yes = skip   |  No = look for curl"),
]
for i, (q, question, ans) in enumerate(qs):
    y = 3.8 - i*1.18
    ax5.text(0.3, y+0.10, q, color=YELLOW, fontsize=7.5, fontweight="bold")
    ax5.text(1.3, y+0.10, question, color=WHITE, fontsize=7.5)
    ax5.text(1.3, y-0.22, ans, color=GRAY, fontsize=7)

# ═══════════════════════════════════════════════════════════
# PANEL 6 — TRADINGVIEW ALERT SETUP (bottom, full width)
# ═══════════════════════════════════════════════════════════
ax6 = fig.add_subplot(gs[2, :])
ax6.set_facecolor(PANEL2); ax6.axis("off")
ax6.set_xlim(0,100); ax6.set_ylim(0,10)
ax6.set_title("HOW TO SET THE TRADINGVIEW ALERT — Get notified the SECOND a curl fires",
              color=TEAL, fontsize=11, fontweight="bold", pad=8)
ax6.add_patch(FancyBboxPatch((0,0.1),100,9.6,
    boxstyle="round,pad=0.1", facecolor=PANEL2, edgecolor=TEAL, lw=2,
    transform=ax6.transData))

steps = [
    ("STEP 1", "Load Pine Script", "Open TradingView → any NASDAQ small-cap 5m chart.\nClick Indicators → Invite-only or My Scripts → paste W118 script.\nMake sure you see the SHA candles + yellow ZLSMA line.", TEAL),
    ("STEP 2", "Open Alert Dialog", "Click the ALARM CLOCK icon in the top toolbar (or press Alt+A).\nOr right-click the chart → Add Alert.", BLUE),
    ("STEP 3", "Set Condition", "Condition dropdown → select 'W118 Curl if Flow'\n"
     "→ then select 'Curl if Flow Entry' from the second dropdown.\n"
     "This fires ONLY when ALL 6 conditions are met + K depth + time gate.", GREEN),
    ("STEP 4", "Set Frequency", "Select: 'Once Per Bar' (fires once per 5m candle max).\nDO NOT use 'Once Per Bar Close' — that's too slow, you'll miss the entry.", YELLOW),
    ("STEP 5", "Notifications", "Check: App notifications (phone) + Email.\nMessage box: leave default or type 'W118 CURL ENTRY — {{ticker}} @ ${{close}} K={{plot_0}}'", ORANGE),
    ("STEP 6", "Repeat for Exit Alerts", "Repeat steps for: 'SHA Exit Warning', 'K Crossed Below 20', 'Below ZLSMA Exit'.\nThese tell you WHEN TO SELL just as clearly as the buy signal.", RED),
]

col_w = 100/3
for i, (step, title, desc, col) in enumerate(steps):
    col_idx = i % 3; row_idx = i // 3
    x = col_idx * col_w + 1
    y = 8.5 - row_idx * 4.4
    ax6.add_patch(FancyBboxPatch((x-0.5, y-3.6), col_w-2, 4.0,
        boxstyle="round,pad=0.15", facecolor=DARK, edgecolor=col, lw=1.5,
        transform=ax6.transData))
    ax6.text(x+0.3, y+0.15, step, color=col, fontsize=8, fontweight="bold",
             fontfamily="monospace")
    ax6.text(x+0.3, y-0.30, title, color=WHITE, fontsize=9, fontweight="bold")
    ax6.text(x+0.3, y-0.68, desc, color=GRAY, fontsize=7.5, va="top",
             wrap=True, multialignment="left")

# Bottom note
ax6.text(50, 0.55,
    "NOTE: The Pine Script already has 7 built-in alertconditions. "
    "You just need to add them in TradingView. Each stock needs its own alert. "
    "Set them PRE-MARKET every morning on your watchlist.",
    color=YELLOW, fontsize=8, ha="center",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1500", edgecolor=YELLOW, alpha=0.9))

plt.savefig("/home/user/tradingbaby/tools/cheatsheet.png",
            dpi=150, bbox_inches="tight", facecolor=DARK)
print("Saved.")
