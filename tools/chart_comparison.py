"""
TRNR vs PCLA — Day Trading Comparison Chart
Annotated educational image based on TradingView screenshots (May 21 2026)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

fig = plt.figure(figsize=(22, 26), facecolor="#0d1117")
fig.patch.set_facecolor("#0d1117")

DARK  = "#0d1117"
PANEL = "#161b22"
GREEN = "#00c176"
RED   = "#ff3b47"
YELLOW= "#ffd700"
BLUE  = "#4fc3f7"
ORANGE= "#ff9800"
WHITE = "#e6edf3"
GRAY  = "#8b949e"
LGRAY = "#30363d"

def dark_ax(ax, title="", ylabel=""):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=GRAY, labelsize=8)
    ax.spines[:].set_color(LGRAY)
    if title:
        ax.set_title(title, color=WHITE, fontsize=10, fontweight="bold", pad=6)
    if ylabel:
        ax.set_ylabel(ylabel, color=GRAY, fontsize=8)
    ax.grid(True, color=LGRAY, linewidth=0.4, alpha=0.6)

# ── TITLE ─────────────────────────────────────────────────────────────────────
fig.text(0.5, 0.97, "TRNR  vs  PCLA — Day Trading Expert Analysis",
         ha="center", va="top", color=WHITE, fontsize=18, fontweight="bold")
fig.text(0.5, 0.955, "May 21 2026  |  5m & 1m Charts  |  Indicators: Stoch(5,3,3) + MACD(12,26,9) + Supertrend",
         ha="center", va="top", color=GRAY, fontsize=10)

# ─────────────────────────────────────────────────────────────────────────────
# ROW LABELS
# ─────────────────────────────────────────────────────────────────────────────
fig.text(0.27, 0.925, "TRNR  (Interactive Strength Inc.)",
         ha="center", color=RED, fontsize=13, fontweight="bold")
fig.text(0.27, 0.908, "▼ -4.76% today  |  HEADING DOWN  |  DO NOT BUY",
         ha="center", color=RED, fontsize=10)

fig.text(0.74, 0.925, "PCLA  (PicoCELA Inc.)",
         ha="center", color=GREEN, fontsize=13, fontweight="bold")
fig.text(0.74, 0.908, "▲ +60.70% today  |  STILL HAS MOMENTUM  |  WATCH FOR RE-ENTRY",
         ha="center", color=GREEN, fontsize=10)

# ─────────────────────────────────────────────────────────────────────────────
# GRID: 4 rows × 2 cols
# left=TRNR, right=PCLA
# row0=price, row1=stoch 5m, row2=stoch 1m, row3=summary
# ─────────────────────────────────────────────────────────────────────────────
gs = fig.add_gridspec(4, 2, left=0.05, right=0.97,
                      top=0.90, bottom=0.04,
                      hspace=0.55, wspace=0.28,
                      height_ratios=[2.2, 1.4, 1.4, 1.6])

# ── TRNR PRICE (5m) ───────────────────────────────────────────────────────────
ax_tp = fig.add_subplot(gs[0, 0])
dark_ax(ax_tp, "TRNR — 5m Price Action", "Price ($)")

t = np.arange(40)
# Simulate: flat → spike at t=20 → decline
base = np.ones(20) * 1.02 + np.random.randn(20)*0.01
spike = np.array([1.00, 1.02, 1.05, 1.15, 1.38, 1.55, 1.60, 1.58,
                  1.52, 1.48, 1.44, 1.42, 1.38, 1.35, 1.32, 1.30, 1.28, 1.27, 1.29, 1.28])
price = np.concatenate([base, spike])

colors = []
for i in range(1, len(price)):
    colors.append(GREEN if price[i] >= price[i-1] else RED)
colors.insert(0, GREEN)

for i in range(len(price)):
    c = colors[i]
    ax_tp.bar(i, price[i] - 0.95, bottom=0.95, color=c, width=0.7, alpha=0.85)

ax_tp.axhline(1.15, color=YELLOW, linewidth=1.2, linestyle="--", label="T1 +15%")
ax_tp.axhline(1.30, color=GREEN,  linewidth=1.2, linestyle="--", label="T2 +30%")
ax_tp.axhline(0.92, color=RED,    linewidth=1.2, linestyle="--", label="Stop -8%")

ax_tp.annotate("SPIKE\n14:10", xy=(20, 1.00), xytext=(14, 1.10),
               color=GREEN, fontsize=8, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5))
ax_tp.annotate("NOW FALLING\n$1.28 ↓", xy=(37, 1.28), xytext=(28, 1.50),
               color=RED, fontsize=8, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))
ax_tp.annotate("Spike DONE\nSell pressure", xy=(26, 1.48), xytext=(26, 1.62),
               color=ORANGE, fontsize=7.5,
               arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2))

ax_tp.set_ylim(0.88, 1.72)
ax_tp.legend(loc="upper left", fontsize=7, facecolor=DARK, labelcolor=WHITE,
             edgecolor=LGRAY)
ax_tp.set_xticks([0, 10, 20, 30, 39])
ax_tp.set_xticklabels(["Pre\nSpike", "12:00", "14:10\nSPIKE", "14:40", "15:00"], color=GRAY, fontsize=7)

# Supertrend label
ax_tp.text(5, 0.97, "Supertrend: BEARISH (red dots)", color=RED, fontsize=7.5,
           bbox=dict(boxstyle="round,pad=0.3", facecolor=DARK, edgecolor=RED, alpha=0.8))

# ── PCLA PRICE (5m) ───────────────────────────────────────────────────────────
ax_pp = fig.add_subplot(gs[0, 1])
dark_ax(ax_pp, "PCLA — 5m Price Action  (+60.70%)", "Price ($)")

# Flat for days → huge spike pre-market May 21 → consolidates at $2.40
base_p = np.ones(28) * 1.48 + np.random.randn(28)*0.03
spike_p = np.array([1.45, 1.50, 2.00, 2.80, 3.60, 4.20, 5.40, 5.80,
                    5.50, 4.80, 3.80, 3.00])
tail_p = np.array([2.60, 2.50, 2.45, 2.40, 2.38, 2.40, 2.42, 2.40, 2.41, 2.40])
price_p = np.concatenate([base_p, spike_p, tail_p])

for i in range(len(price_p)):
    c = GREEN if i == 0 or price_p[i] >= price_p[i-1] else RED
    ax_pp.bar(i, price_p[i] - 1.30, bottom=1.30, color=c, width=0.7, alpha=0.85)

ax_pp.annotate("PRE-MARKET\nSPIKE +60%", xy=(30, 2.00), xytext=(20, 4.50),
               color=GREEN, fontsize=8, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5))
ax_pp.annotate("Consolidating\n$2.40", xy=(47, 2.40), xytext=(40, 3.20),
               color=YELLOW, fontsize=8, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.5))
ax_pp.annotate("MACD still\npositive", xy=(49, 2.40), xytext=(36, 1.60),
               color=BLUE, fontsize=7.5,
               arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.2))

ax_pp.set_ylim(1.1, 6.8)
ax_pp.set_xticks([0, 14, 28, 33, 39, 49])
ax_pp.set_xticklabels(["May14", "May15", "May18", "May21\n03:45", "Spike\nPeak", "Now\n$2.40"],
                       color=GRAY, fontsize=7)
ax_pp.text(2, 5.8, "Supertrend: BULLISH (green dots)", color=GREEN, fontsize=7.5,
           bbox=dict(boxstyle="round,pad=0.3", facecolor=DARK, edgecolor=GREEN, alpha=0.8))
ax_pp.text(2, 5.1, "Still above Supertrend support", color=GREEN, fontsize=7.5)

# ── TRNR STOCH 5m ─────────────────────────────────────────────────────────────
ax_ts5 = fig.add_subplot(gs[1, 0])
dark_ax(ax_ts5, "TRNR — Stoch(5,3,3)  5m", "Value")

t = np.arange(40)
k_t5 = np.concatenate([np.ones(28)*15 + np.random.randn(28)*3,
                        np.array([20, 45, 85, 92, 88, 80, 72, 65, 58, 52, 47, 42])])
d_t5 = np.convolve(k_t5, np.ones(3)/3, mode='same')

ax_ts5.plot(t, k_t5, color=BLUE, linewidth=1.8, label="K=47.34")
ax_ts5.plot(t, d_t5, color=ORANGE, linewidth=1.4, label="D=41.11", linestyle="--")
ax_ts5.axhline(80, color=RED,  linewidth=0.8, linestyle=":", alpha=0.7)
ax_ts5.axhline(20, color=GREEN,linewidth=0.8, linestyle=":", alpha=0.7)
ax_ts5.fill_between(t, k_t5, d_t5, where=(k_t5 >= d_t5), alpha=0.15, color=GREEN)
ax_ts5.fill_between(t, k_t5, d_t5, where=(k_t5 < d_t5),  alpha=0.15, color=RED)

ax_ts5.annotate("K peaked at 92\n(overbought)", xy=(21, 92), xytext=(10, 95),
               color=RED, fontsize=7.5,
               arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
ax_ts5.annotate("K=47, DECLINING\nMomentum dead", xy=(38, 47), xytext=(25, 65),
               color=RED, fontsize=7.5, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))
ax_ts5.text(1, 23, "BUY ZONE", color=GREEN, fontsize=7, alpha=0.8)
ax_ts5.text(1, 83, "SELL ZONE", color=RED, fontsize=7, alpha=0.8)

ax_ts5.set_ylim(-5, 108)
ax_ts5.legend(loc="upper left", fontsize=7.5, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)

# ── PCLA STOCH 5m ─────────────────────────────────────────────────────────────
ax_ps5 = fig.add_subplot(gs[1, 1])
dark_ax(ax_ps5, "PCLA — Stoch(5,3,3)  5m", "Value")

t = np.arange(50)
k_p5 = np.concatenate([
    20 + np.random.randn(28)*5,
    np.array([22, 35, 65, 88, 92, 85, 75, 62, 55, 50, 48, 46]),
    np.ones(10)*45 + np.random.randn(10)*2
])
d_p5 = np.convolve(k_p5, np.ones(3)/3, mode='same')

ax_ps5.plot(t, k_p5, color=BLUE, linewidth=1.8, label="K=45.80")
ax_ps5.plot(t, d_p5, color=ORANGE, linewidth=1.4, label="D=36.93", linestyle="--")
ax_ps5.axhline(80, color=RED,  linewidth=0.8, linestyle=":", alpha=0.7)
ax_ps5.axhline(20, color=GREEN,linewidth=0.8, linestyle=":", alpha=0.7)
ax_ps5.fill_between(t, k_p5, d_p5, where=(k_p5 >= d_p5), alpha=0.15, color=GREEN)
ax_ps5.fill_between(t, k_p5, d_p5, where=(k_p5 < d_p5),  alpha=0.15, color=RED)

ax_ps5.annotate("K ABOVE D\n(bullish)", xy=(44, 46), xytext=(32, 68),
               color=GREEN, fontsize=7.5, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5))
ax_ps5.annotate("Not overbought\non 5m → room to run", xy=(46, 45), xytext=(33, 30),
               color=YELLOW, fontsize=7.5,
               arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.2))
ax_ps5.text(1, 23, "BUY ZONE", color=GREEN, fontsize=7, alpha=0.8)
ax_ps5.text(1, 83, "SELL ZONE", color=RED, fontsize=7, alpha=0.8)

ax_ps5.set_ylim(-5, 108)
ax_ps5.legend(loc="upper left", fontsize=7.5, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)

# ── TRNR STOCH 1m ─────────────────────────────────────────────────────────────
ax_ts1 = fig.add_subplot(gs[2, 0])
dark_ax(ax_ts1, "TRNR — Stoch(5,3,3)  1m  |  Possible dead-cat bounce?", "Value")

t1 = np.arange(60)
k_t1 = np.concatenate([
    70 + np.random.randn(5)*4,
    np.array([75, 80, 85, 90, 88, 82, 70, 60, 50, 40, 35, 30, 28, 26, 27]),
    np.ones(40)*27 + np.random.randn(40)*3
])[:60]
d_t1 = np.convolve(k_t1, np.ones(3)/3, mode='same')

ax_ts1.plot(t1, k_t1, color=BLUE, linewidth=1.8, label="K=26.50")
ax_ts1.plot(t1, d_t1, color=ORANGE, linewidth=1.4, label="D=17.38", linestyle="--")
ax_ts1.axhline(80, color=RED,  linewidth=0.8, linestyle=":", alpha=0.7)
ax_ts1.axhline(20, color=GREEN,linewidth=0.8, linestyle=":", alpha=0.7)
ax_ts1.fill_between(t1, k_t1, d_t1, where=(k_t1 >= d_t1), alpha=0.15, color=GREEN)
ax_ts1.fill_between(t1, k_t1, d_t1, where=(k_t1 < d_t1),  alpha=0.15, color=RED)

ax_ts1.annotate("K=26.50 near low\nK barely > D\nNOT a clean signal", xy=(58, 26), xytext=(38, 55),
               color=ORANGE, fontsize=7.5,
               arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.5))
ax_ts1.text(1, 23, "BUY ZONE", color=GREEN, fontsize=7, alpha=0.8)

ax_ts1.set_ylim(-5, 108)
ax_ts1.legend(loc="upper right", fontsize=7.5, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)

# Danger box
ax_ts1.text(0.5, 0.05, "⚠  MACD histogram NEGATIVE on 5m → bias is DOWN even if 1m bounces",
           transform=ax_ts1.transAxes, color=RED, fontsize=7.5,
           ha='center', va='bottom',
           bbox=dict(boxstyle="round,pad=0.4", facecolor="#2a0a0a", edgecolor=RED, alpha=0.9))

# ── PCLA STOCH 1m ─────────────────────────────────────────────────────────────
ax_ps1 = fig.add_subplot(gs[2, 1])
dark_ax(ax_ps1, "PCLA — Stoch(5,3,3)  1m  |  Re-entry setup forming?", "Value")

t1 = np.arange(60)
# Big spike, now pulling back from 90s toward 50-60s
k_p1 = np.concatenate([
    np.ones(10)*20 + np.random.randn(10)*3,
    np.array([22, 35, 55, 78, 90, 92, 88, 80, 75, 70, 67, 65, 63]),
    np.ones(37)*64 + np.random.randn(37)*3
])[:60]
d_p1 = np.convolve(k_p1, np.ones(3)/3, mode='same')

ax_ps1.plot(t1, k_p1, color=BLUE, linewidth=1.8, label="K=67.21")
ax_ps1.plot(t1, d_p1, color=ORANGE, linewidth=1.4, label="D=48.40", linestyle="--")
ax_ps1.axhline(80, color=RED,  linewidth=0.8, linestyle=":", alpha=0.7)
ax_ps1.axhline(20, color=GREEN,linewidth=0.8, linestyle=":", alpha=0.7)
ax_ps1.fill_between(t1, k_p1, d_p1, where=(k_p1 >= d_p1), alpha=0.15, color=GREEN)
ax_ps1.fill_between(t1, k_p1, d_p1, where=(k_p1 < d_p1),  alpha=0.15, color=RED)

ax_ps1.annotate("K=67 still ABOVE D=48\nBullish structure intact", xy=(55, 64), xytext=(28, 80),
               color=GREEN, fontsize=7.5, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5))
ax_ps1.annotate("RE-ENTRY ZONE:\nWatch for K to reset\nto 20 then curl up →",
               xy=(23, 20), xytext=(5, 45),
               color=YELLOW, fontsize=7.5,
               arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.5))
ax_ps1.text(1, 23, "BUY ZONE — watch here for re-entry", color=GREEN, fontsize=7, alpha=0.9)
ax_ps1.legend(loc="upper right", fontsize=7.5, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)
ax_ps1.set_ylim(-5, 108)

# ── SUMMARY PANELS ────────────────────────────────────────────────────────────
ax_sum_t = fig.add_subplot(gs[3, 0])
ax_sum_p = fig.add_subplot(gs[3, 1])

for ax in [ax_sum_t, ax_sum_p]:
    ax.set_facecolor(PANEL)
    ax.axis("off")

# TRNR Summary
ax_sum_t.set_xlim(0, 10)
ax_sum_t.set_ylim(0, 10)

rect_t = FancyBboxPatch((0.2, 0.2), 9.6, 9.4,
    boxstyle="round,pad=0.1", facecolor="#1a0505", edgecolor=RED, linewidth=2)
ax_sum_t.add_patch(rect_t)

ax_sum_t.text(5, 9.2, "TRNR VERDICT: STAY OUT",
              ha="center", color=RED, fontsize=11, fontweight="bold")
ax_sum_t.axhline(y=8.8, xmin=0.05, xmax=0.95, color=LGRAY, linewidth=0.5)

lines_t = [
    ("▼ Trend:", "BEARISH — price declining from spike peak", RED),
    ("Stoch 5m:", "K=47.34 mid-range & falling. No curl setup.", RED),
    ("Stoch 1m:", "K=26.50 low but MACD negative → no real bounce", ORANGE),
    ("MACD 5m:", "Histogram turned RED — sellers winning", RED),
    ("Supertrend:", "Flipped BEARISH after the spike", RED),
    ("Action:", "Do NOT buy. Wait for full reset to near-zero.", WHITE),
    ("If re-entry:", "Only if K drops to <10, then curls above 20 again", GRAY),
]
for i, (label, val, col) in enumerate(lines_t):
    y = 8.1 - i * 1.08
    ax_sum_t.text(0.5, y, label, color=GRAY, fontsize=8, fontweight="bold")
    ax_sum_t.text(2.8, y, val, color=col, fontsize=8)

# PCLA Summary
ax_sum_p.set_xlim(0, 10)
ax_sum_p.set_ylim(0, 10)

rect_p = FancyBboxPatch((0.2, 0.2), 9.6, 9.4,
    boxstyle="round,pad=0.1", facecolor="#051a08", edgecolor=GREEN, linewidth=2)
ax_sum_p.add_patch(rect_p)

ax_sum_p.text(5, 9.2, "PCLA VERDICT: WATCH FOR RE-ENTRY",
              ha="center", color=GREEN, fontsize=11, fontweight="bold")
ax_sum_p.axhline(y=8.8, xmin=0.05, xmax=0.95, color=LGRAY, linewidth=0.5)

lines_p = [
    ("▲ Day gain:", "+60.70% — strong catalyst, volume confirmed", GREEN),
    ("Stoch 5m:", "K=45.80 > D=36.93. K above D = bullish structure", GREEN),
    ("Stoch 1m:", "K=67.21 > D=48.40. Still above 50 → momentum alive", GREEN),
    ("MACD 5m:", "Strongly positive (0.26 vs signal 0.20)", GREEN),
    ("Supertrend:", "Still BULLISH (green dots)", GREEN),
    ("Action:", "If K pulls back to ~20 on 5m → re-entry signal", YELLOW),
    ("W118 rule:", "Wait for K<10 then crossover above 20 for cleanest entry", BLUE),
]
for i, (label, val, col) in enumerate(lines_p):
    y = 8.1 - i * 1.08
    ax_sum_p.text(0.5, y, label, color=GRAY, fontsize=8, fontweight="bold")
    ax_sum_p.text(2.8, y, val, color=col, fontsize=8)

# ── BOTTOM BAR ────────────────────────────────────────────────────────────────
fig.text(0.5, 0.015,
    "HOW TO READ:  Stoch K (blue line) crosses ABOVE D (orange) from below 20 = BUY signal  |  "
    "Stoch above 80 = OVERBOUGHT (sell zone)  |  MACD histogram green & growing = bullish  |  "
    "Supertrend green = uptrend, red = downtrend",
    ha="center", color=GRAY, fontsize=8,
    bbox=dict(boxstyle="round,pad=0.5", facecolor=PANEL, edgecolor=LGRAY))

out = "/home/user/tradingbaby/tools/trnr_vs_pcla_analysis.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=DARK)
print(f"Saved: {out}")
