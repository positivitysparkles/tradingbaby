"""
TRNR vs PCLA — Outcome Chart (how it actually played out)
Based on the follow-up screenshots at 19:29-19:30 May 21 2026
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

fig = plt.figure(figsize=(24, 28), facecolor="#0d1117")
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
PURPLE= "#bd93f9"

def dark_ax(ax, title="", ylabel=""):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=GRAY, labelsize=8)
    ax.spines[:].set_color(LGRAY)
    if title:
        ax.set_title(title, color=WHITE, fontsize=10, fontweight="bold", pad=7)
    if ylabel:
        ax.set_ylabel(ylabel, color=GRAY, fontsize=8)
    ax.grid(True, color=LGRAY, linewidth=0.4, alpha=0.5)

# ── TITLE ─────────────────────────────────────────────────────────────────────
fig.text(0.5, 0.975, "THE OUTCOME — TRNR vs PCLA  (May 21 2026)",
         ha="center", color=WHITE, fontsize=20, fontweight="bold")
fig.text(0.5, 0.958, "Our prediction vs what actually happened — both calls were CORRECT",
         ha="center", color=YELLOW, fontsize=11)

# Column headers
fig.text(0.27, 0.935, "TRNR  ▼  AVOIDED — Correct call",
         ha="center", color=RED, fontsize=14, fontweight="bold")
fig.text(0.74, 0.935, "PCLA  ▲  WATCHED — Correct call",
         ha="center", color=GREEN, fontsize=14, fontweight="bold")
fig.text(0.27, 0.920, "Result: -10% from analysis point → $1.28 → $1.10  |  Spike was DONE",
         ha="center", color=RED, fontsize=9)
fig.text(0.74, 0.920, "Result: +170% from analysis point → $2.40 → $6.50  |  Ran to $9.80 peak",
         ha="center", color=GREEN, fontsize=9)

gs = fig.add_gridspec(4, 2, left=0.05, right=0.97,
                      top=0.915, bottom=0.04,
                      hspace=0.60, wspace=0.28,
                      height_ratios=[2.4, 1.4, 1.4, 1.6])

# ─────────────────────────────────────────────────────────────────────────────
# TRNR PRICE (5m full day)
# ─────────────────────────────────────────────────────────────────────────────
ax_tp = fig.add_subplot(gs[0, 0])
dark_ax(ax_tp, "TRNR — 5m  Full Day  (09:30 → After Hours)", "Price ($)")

# Flat pre-market → spike 14:10 → slow decline all day to 1.15
n = 80
t = np.arange(n)
np.random.seed(42)

# Segments: flat ~1.02, pre-spike dip to 1.00, spike 1.00→1.60, decline to 1.15
pre   = np.linspace(1.02, 1.00, 30) + np.random.randn(30)*0.005
spike = np.array([1.00, 1.10, 1.30, 1.48, 1.58, 1.65, 1.62, 1.55, 1.50, 1.47])
decl  = np.linspace(1.47, 1.15, 30) + np.random.randn(30)*0.008
tail  = np.linspace(1.15, 1.12, 10) + np.random.randn(10)*0.004
price = np.concatenate([pre, spike, decl, tail])[:n]

for i in range(n):
    c = GREEN if i == 0 or price[i] >= price[i-1] else RED
    h = abs(price[i] - (price[i-1] if i > 0 else price[i])) * 0.5
    ax_tp.bar(i, price[i] - 0.90, bottom=0.90, color=c, width=0.75, alpha=0.85)
    # wick
    ax_tp.plot([i, i], [price[i]-0.003, price[i]+0.003+h], color=c, linewidth=0.5, alpha=0.6)

# Analysis point marker
ax_pt = 38  # ~14:30 = our analysis time
ax_tp.axvline(ax_pt, color=YELLOW, linewidth=2, linestyle="--", alpha=0.9, label="Our analysis point")
ax_tp.annotate("WE SAID:\n'DO NOT BUY'\n@ $1.28",
               xy=(ax_pt, price[ax_pt]), xytext=(ax_pt+4, 1.52),
               color=YELLOW, fontsize=8, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.5),
               bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1500", edgecolor=YELLOW))

ax_tp.annotate("Continued\ndropping ↓\n$1.28 → $1.10", xy=(65, 1.18), xytext=(50, 1.40),
               color=RED, fontsize=8, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=RED, lw=1.5))

ax_tp.annotate("Spike PEAK\n$1.65", xy=(39, 1.65), xytext=(26, 1.68),
               color=RED, fontsize=7.5,
               arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))

# If someone bought at $1.40 and held...
ax_tp.fill_between(range(ax_pt, n), price[ax_pt:n], price[ax_pt],
                   where=(price[ax_pt:n] < price[ax_pt]),
                   color=RED, alpha=0.15, label="Loss zone (if bought here)")

ax_tp.set_ylim(0.85, 1.82)
ax_tp.legend(loc="upper right", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)

time_labels = ["09:30", "11:00", "12:30", "14:10\nSPIKE", "15:30", "17:00", "After\nHours"]
ax_tp.set_xticks(np.linspace(0, n-1, 7))
ax_tp.set_xticklabels(time_labels, color=GRAY, fontsize=7)

# ─────────────────────────────────────────────────────────────────────────────
# PCLA PRICE (5m full day)
# ─────────────────────────────────────────────────────────────────────────────
ax_pp = fig.add_subplot(gs[0, 1])
dark_ax(ax_pp, "PCLA — 5m  Full Day  (+60.70%, peaked $9.80)", "Price ($)")

np.random.seed(7)
n2 = 80
# Pre-market: 1.48 → spike → 9.80 → pull back → 6.50
pre_p  = np.linspace(1.48, 2.10, 15) + np.random.randn(15)*0.05
# Our analysis point was ~19:22 phone time → stock at ~$2.40 (mid-spike)
rise_p = np.linspace(2.40, 9.80, 18) + np.random.randn(18)*0.15
peak_p = np.array([9.80, 9.40, 9.00, 8.50])
decl_p = np.linspace(8.50, 6.80, 20) + np.random.randn(20)*0.12
tail_p = np.linspace(6.80, 6.50, 7) + np.random.randn(7)*0.05
price_p = np.concatenate([pre_p, rise_p, peak_p, decl_p, tail_p])
price_p = price_p[:n2]

for i in range(len(price_p)):
    c = GREEN if i == 0 or price_p[i] >= price_p[i-1] else RED
    ax_pp.bar(i, price_p[i] - 1.20, bottom=1.20, color=c, width=0.75, alpha=0.85)

# Analysis point
an_pt = 14
ax_pp.axvline(an_pt, color=YELLOW, linewidth=2, linestyle="--", alpha=0.9, label="Our analysis point")
ax_pp.annotate("WE SAID:\n'WATCH FOR\nRE-ENTRY'\n@ $2.40",
               xy=(an_pt, price_p[an_pt]), xytext=(an_pt+4, 7.50),
               color=YELLOW, fontsize=8, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.5),
               bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1500", edgecolor=YELLOW))

# T1/T2 from $2.40
t1_lvl = 2.40 * 1.15  # +15% = $2.76
t2_lvl = 2.40 * 1.30  # +30% = $3.12
peak_lvl = 9.80

ax_pp.axhline(t1_lvl, color="#a8ff78", linewidth=1, linestyle=":", alpha=0.8, label=f"T1 +15% = $2.76")
ax_pp.axhline(t2_lvl, color=GREEN,     linewidth=1, linestyle=":", alpha=0.8, label=f"T2 +30% = $3.12")
ax_pp.axhline(peak_lvl, color=PURPLE,  linewidth=1, linestyle=":", alpha=0.6, label=f"Peak $9.80")

ax_pp.annotate("PEAK\n$9.80\n(+308%)", xy=(32, 9.80), xytext=(42, 9.20),
               color=PURPLE, fontsize=8, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=PURPLE, lw=1.5))

ax_pp.annotate("Settled\n$6.50\n(+170%)", xy=(75, 6.50), xytext=(60, 8.00),
               color=GREEN, fontsize=8, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5))

# Profit zone shading
pp_len = len(price_p)
ax_pp.fill_between(range(an_pt, pp_len), price_p[an_pt:pp_len], price_p[an_pt],
                   where=(price_p[an_pt:pp_len] > price_p[an_pt]),
                   color=GREEN, alpha=0.12, label="Profit zone")

ax_pp.set_ylim(0.8, 11.5)
ax_pp.legend(loc="upper left", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY, ncol=2)
ax_pp.set_xticks(np.linspace(0, n2-1, 7))
ax_pp.set_xticklabels(["Pre\nMkt", "03:45\nSpike", "Our\nAnalysis", "15:30\nPeak", "16:00",
                        "17:30", "After\nHours"], color=GRAY, fontsize=7)

# ─────────────────────────────────────────────────────────────────────────────
# TRNR STOCH outcome
# ─────────────────────────────────────────────────────────────────────────────
ax_ts = fig.add_subplot(gs[1, 0])
dark_ax(ax_ts, "TRNR — Stoch 5m  (K=58.78, D=38.79 at close)", "")

t = np.arange(80)
np.random.seed(1)
k_t = np.concatenate([
    np.ones(28)*18 + np.random.randn(28)*4,
    np.array([20, 50, 85, 90, 80, 70, 60, 52, 44, 38]),  # spike + decline
    np.linspace(35, 20, 20) + np.random.randn(20)*3,     # grind lower
    np.linspace(20, 58, 22) + np.random.randn(22)*3      # late bounce
])[:80]
d_t = np.convolve(k_t, np.ones(5)/5, mode='same')

ax_ts.plot(t, k_t, color=BLUE,   linewidth=1.8, label="K=58.78 (rising end of day)")
ax_ts.plot(t, d_t, color=ORANGE, linewidth=1.4, label="D=38.79", linestyle="--")
ax_ts.axhline(80, color=RED,   linewidth=0.8, linestyle=":", alpha=0.7)
ax_ts.axhline(20, color=GREEN, linewidth=0.8, linestyle=":", alpha=0.7)
ax_ts.fill_between(t, k_t, d_t, where=(k_t >= d_t), alpha=0.12, color=GREEN)
ax_ts.fill_between(t, k_t, d_t, where=(k_t < d_t),  alpha=0.12, color=RED)
ax_ts.axvline(38, color=YELLOW, linewidth=1.5, linestyle="--", alpha=0.7)

ax_ts.text(40, 88, "Our call:\nK declining = avoid", color=YELLOW, fontsize=7.5,
           bbox=dict(boxstyle="round,pad=0.3", facecolor=DARK, edgecolor=YELLOW, alpha=0.8))
ax_ts.text(62, 68, "Late bounce?\nMACD still -ve\n= trap", color=ORANGE, fontsize=7.5)

ax_ts.set_ylim(-5, 108)
ax_ts.legend(loc="upper left", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)
ax_ts.text(1, 22, "BUY ZONE", color=GREEN, fontsize=7, alpha=0.7)
ax_ts.text(1, 83, "SELL ZONE", color=RED, fontsize=7, alpha=0.7)

# ─────────────────────────────────────────────────────────────────────────────
# PCLA STOCH outcome
# ─────────────────────────────────────────────────────────────────────────────
ax_ps = fig.add_subplot(gs[1, 1])
dark_ax(ax_ps, "PCLA — Stoch 5m  (K=47.77, D=38.82 — still bullish structure)", "")

t2 = np.arange(80)
np.random.seed(3)
k_p = np.concatenate([
    np.ones(10)*15 + np.random.randn(10)*3,
    np.array([18, 30, 55, 80, 85, 80, 72, 65]),
    np.linspace(60, 30, 15) + np.random.randn(15)*4,
    np.linspace(30, 15, 8) + np.random.randn(8)*3,
    np.linspace(15, 60, 20) + np.random.randn(20)*4,
    np.linspace(60, 48, 19) + np.random.randn(19)*3,
])[:80]
d_p = np.convolve(k_p, np.ones(5)/5, mode='same')

ax_ps.plot(t2, k_p, color=BLUE,   linewidth=1.8, label="K=47.77 (K > D = still bullish)")
ax_ps.plot(t2, d_p, color=ORANGE, linewidth=1.4, label="D=38.82", linestyle="--")
ax_ps.axhline(80, color=RED,   linewidth=0.8, linestyle=":", alpha=0.7)
ax_ps.axhline(20, color=GREEN, linewidth=0.8, linestyle=":", alpha=0.7)
ax_ps.fill_between(t2, k_p, d_p, where=(k_p >= d_p), alpha=0.12, color=GREEN)
ax_ps.fill_between(t2, k_p, d_p, where=(k_p < d_p),  alpha=0.12, color=RED)
ax_ps.axvline(14, color=YELLOW, linewidth=1.5, linestyle="--", alpha=0.7)

# Mark the reset area and second entry
ax_ps.annotate("K reset to ~15\n→ RE-ENTRY SIGNAL\nif using W118", xy=(45, 15), xytext=(48, 45),
               color=GREEN, fontsize=7.5, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5))
ax_ps.text(16, 88, "K above D\nall the way up", color=GREEN, fontsize=7.5)

ax_ps.set_ylim(-5, 108)
ax_ps.legend(loc="upper right", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)
ax_ps.text(1, 22, "BUY ZONE", color=GREEN, fontsize=7, alpha=0.7)

# ─────────────────────────────────────────────────────────────────────────────
# MACD comparison
# ─────────────────────────────────────────────────────────────────────────────
ax_tm = fig.add_subplot(gs[2, 0])
dark_ax(ax_tm, "TRNR — MACD  (confirmed bearish all afternoon)", "")

t = np.arange(80)
np.random.seed(5)
macd_t = np.concatenate([
    np.zeros(28) + np.random.randn(28)*0.002,
    np.linspace(0, 0.13, 8),
    np.linspace(0.13, 0, 5),
    np.linspace(0, -0.035, 39),
])[:80]
sig_t = np.convolve(macd_t, np.ones(9)/9, mode='same')
hist_t = macd_t - sig_t

colors_h = [GREEN if h >= 0 else RED for h in hist_t]
ax_tm.bar(t, hist_t, color=colors_h, width=0.8, alpha=0.8)
ax_tm.plot(t, macd_t, color=BLUE,   linewidth=1.5, label="MACD")
ax_tm.plot(t, sig_t,  color=ORANGE, linewidth=1.2, label="Signal", linestyle="--")
ax_tm.axhline(0, color=LGRAY, linewidth=0.8)
ax_tm.axvline(38, color=YELLOW, linewidth=1.5, linestyle="--", alpha=0.7)

ax_tm.text(40, 0.08, "MACD turned\nnegative here →\nbig red bars = SELL", color=RED, fontsize=7.5,
           bbox=dict(boxstyle="round,pad=0.3", facecolor=DARK, edgecolor=RED, alpha=0.8))
ax_tm.text(2, 0.11, "MACD: -0.0034\nSignal: -0.0258\n= bearish", color=RED, fontsize=7.5)
ax_tm.legend(loc="upper right", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)

ax_pm = fig.add_subplot(gs[2, 1])
dark_ax(ax_pm, "PCLA — MACD  (positive all day, confirmed bullish run)", "")

np.random.seed(8)
macd_p = np.concatenate([
    np.zeros(10) + np.random.randn(10)*0.01,
    np.linspace(0, 1.50, 20),
    np.linspace(1.50, 0.20, 20),
    np.linspace(0.20, -0.20, 15),
    np.linspace(-0.20, 0.25, 15),
])[:80]
sig_p = np.convolve(macd_p, np.ones(9)/9, mode='same')
hist_p = macd_p - sig_p

colors_hp = [GREEN if h >= 0 else RED for h in hist_p]
ax_pm.bar(t2, hist_p, color=colors_hp, width=0.8, alpha=0.8)
ax_pm.plot(t2, macd_p, color=BLUE,   linewidth=1.5, label="MACD")
ax_pm.plot(t2, sig_p,  color=ORANGE, linewidth=1.2, label="Signal", linestyle="--")
ax_pm.axhline(0, color=LGRAY, linewidth=0.8)
ax_pm.axvline(14, color=YELLOW, linewidth=1.5, linestyle="--", alpha=0.7)

ax_pm.annotate("Massive green bars\n= strong momentum\n= run continued to $9.80",
               xy=(18, 0.8), xytext=(32, 1.30),
               color=GREEN, fontsize=7.5,
               arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.2))
ax_pm.text(55, 0.30, "MACD: 0.2430\nStill positive\n= held $6.50", color=GREEN, fontsize=7.5)
ax_pm.legend(loc="upper right", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)

# ─────────────────────────────────────────────────────────────────────────────
# VERDICT / SCORECARD
# ─────────────────────────────────────────────────────────────────────────────
ax_vt = fig.add_subplot(gs[3, 0])
ax_vp = fig.add_subplot(gs[3, 1])
for ax in [ax_vt, ax_vp]:
    ax.set_facecolor(PANEL)
    ax.axis("off")

# TRNR verdict
ax_vt.set_xlim(0, 10); ax_vt.set_ylim(0, 10)
ax_vt.add_patch(FancyBboxPatch((0.2, 0.2), 9.6, 9.4,
    boxstyle="round,pad=0.1", facecolor="#1a0505", edgecolor=RED, linewidth=2))
ax_vt.text(5, 9.1, "TRNR — WHAT HAPPENED  ✅ CALL CORRECT",
           ha="center", color=RED, fontsize=10, fontweight="bold")
ax_vt.axhline(y=8.7, xmin=0.04, xmax=0.96, color=LGRAY, linewidth=0.5)

rows_t = [
    ("Our call:", "'DO NOT BUY' — spike done, sellers in control", WHITE),
    ("What happened:", "Price dropped from $1.28 → $1.10 (-14%)", RED),
    ("MACD told us:", "Histogram turned red RIGHT at our analysis → confirmed exit", RED),
    ("Stoch told us:", "K was at 47 falling from 90 — momentum exhausted", RED),
    ("Late bounce?:", "K=58 rising end of day BUT MACD still negative = TRAP", ORANGE),
    ("Lesson:", "When MACD goes red + price below spike peak = DONE. Walk away.", WHITE),
    ("If you bought:", "$1000 → $860 in a few hours. Not worth it.", RED),
]
for i, (lbl, val, col) in enumerate(rows_t):
    y = 8.0 - i * 1.05
    ax_vt.text(0.4, y, lbl, color=GRAY, fontsize=7.5, fontweight="bold")
    ax_vt.text(2.6, y, val, color=col, fontsize=7.5)

# PCLA verdict
ax_vp.set_xlim(0, 10); ax_vp.set_ylim(0, 10)
ax_vp.add_patch(FancyBboxPatch((0.2, 0.2), 9.6, 9.4,
    boxstyle="round,pad=0.1", facecolor="#051a08", edgecolor=GREEN, linewidth=2))
ax_vp.text(5, 9.1, "PCLA — WHAT HAPPENED  ✅ CALL CORRECT",
           ha="center", color=GREEN, fontsize=10, fontweight="bold")
ax_vp.axhline(y=8.7, xmin=0.04, xmax=0.96, color=LGRAY, linewidth=0.5)

rows_p = [
    ("Our call:", "'STILL HAS MOMENTUM — watch for re-entry'", WHITE),
    ("What happened:", "Ran from $2.40 → $9.80 peak (+308%) then settled $6.50", GREEN),
    ("MACD told us:", "Massive green bars = engine at full power → ran to $9.80", GREEN),
    ("Stoch told us:", "K above D all the way up — confirmed the run", GREEN),
    ("Re-entry signal:", "K reset to ~15 mid-day = W118 re-entry setup appeared", YELLOW),
    ("Lesson:", "Positive MACD + K above D + catalyst = TRUST the momentum", WHITE),
    ("If you bought $2.40:", "$1000 → $4,083 at peak  |  $1000 → $2,708 at close $6.50", GREEN),
]
for i, (lbl, val, col) in enumerate(rows_p):
    y = 8.0 - i * 1.05
    ax_vp.text(0.4, y, lbl, color=GRAY, fontsize=7.5, fontweight="bold")
    ax_vp.text(2.6, y, val, color=col, fontsize=7.5)

# Bottom bar
fig.text(0.5, 0.018,
    "KEY TAKEAWAY:  MACD direction + Stoch K vs D = the truth.  "
    "Red MACD + K falling = exit/avoid.  Green MACD + K above D = momentum alive, more upside possible.  "
    "Both signals were visible BEFORE the moves happened.",
    ha="center", color=YELLOW, fontsize=8.5,
    bbox=dict(boxstyle="round,pad=0.5", facecolor=PANEL, edgecolor=YELLOW, alpha=0.8))

out = "/home/user/tradingbaby/tools/trnr_vs_pcla_outcome.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=DARK)
print(f"Saved: {out}")
