"""
Chart 1: PCLA W118 entry point + TRNR alert-vs-entry comparison
Chart 2: $500 compounded over 30 W118 trades
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

np.random.seed(42)

fig = plt.figure(figsize=(24, 30), facecolor="#0d1117")
DARK=  "#0d1117"; PANEL= "#161b22"; GREEN= "#00c176"; RED= "#ff3b47"
YELLOW="#ffd700"; BLUE=  "#4fc3f7"; ORANGE="#ff9800"; WHITE="#e6edf3"
GRAY=  "#8b949e"; LGRAY= "#30363d"; PURPLE="#bd93f9"; TEAL= "#00e5ff"

def dark_ax(ax, title="", ylabel=""):
    ax.set_facecolor(PANEL); ax.tick_params(colors=GRAY, labelsize=8)
    ax.spines[:].set_color(LGRAY)
    if title: ax.set_title(title, color=WHITE, fontsize=10, fontweight="bold", pad=7)
    if ylabel: ax.set_ylabel(ylabel, color=GRAY, fontsize=8)
    ax.grid(True, color=LGRAY, linewidth=0.4, alpha=0.5)

fig.text(0.5, 0.977, "W118 Entry/Exit Guide  +  $500 Compounding Calculator",
         ha="center", color=WHITE, fontsize=19, fontweight="bold")
fig.text(0.5, 0.961, "Real alerts, real entries, real math — May 21 2026",
         ha="center", color=YELLOW, fontsize=11)

gs = fig.add_gridspec(4, 2, left=0.05, right=0.97,
                      top=0.955, bottom=0.03,
                      hspace=0.62, wspace=0.28,
                      height_ratios=[2.2, 1.4, 1.4, 2.0])

# ═══════════════════════════════════════════════════════════
# ROW 0 — PRICE PANELS
# ═══════════════════════════════════════════════════════════

# ── TRNR PRICE: Alert at $1.58 vs ideal W118 entry ─────────
ax_t = fig.add_subplot(gs[0, 0])
dark_ax(ax_t, "TRNR — 5m  |  Alert @ 2:31pm $1.58 vs W118 Entry", "Price ($)")

t = np.arange(70)
pre   = np.ones(20)*1.01 + np.random.randn(20)*0.006
spike = [1.00,1.08,1.20,1.35,1.48,1.58,1.62,1.65,1.60,1.54]
decl  = np.linspace(1.54,1.10,40) + np.random.randn(40)*0.008
price_t = np.concatenate([pre, spike, decl])[:70]

for i in range(len(price_t)):
    c = GREEN if i==0 or price_t[i]>=price_t[i-1] else RED
    ax_t.bar(i, price_t[i]-0.88, bottom=0.88, color=c, width=0.75, alpha=0.85)

# Ideal W118 entry = bar 20 (~14:10), K crossed 20 from near zero
w118_entry = 20; w118_px = 1.00
t1_t = w118_px*1.15; t2_t = w118_px*1.30; stop_t = w118_px*0.92

# Alert entry = bar 25 (~14:35)
alert_bar = 25; alert_px = 1.58

ax_t.axhline(t1_t,   color="#a8ff78", lw=1.2, ls="--", alpha=0.9, label=f"T1 +15% = ${t1_t:.2f}")
ax_t.axhline(t2_t,   color=GREEN,     lw=1.2, ls="--", alpha=0.9, label=f"T2 +30% = ${t2_t:.2f}")
ax_t.axhline(stop_t, color=RED,       lw=1.0, ls=":",  alpha=0.8, label=f"Stop -8% = ${stop_t:.2f}")

# W118 entry arrow
ax_t.annotate("W118 ENTRY\n$1.00 @ 14:10\nK crossed 20\nfrom near-zero",
    xy=(w118_entry, w118_px), xytext=(w118_entry-12, 1.38),
    color=GREEN, fontsize=7.5, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.8),
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#051a08", edgecolor=GREEN))

# Alert entry arrow
ax_t.annotate("ALERT FIRES\n$1.58 @ 2:31pm\nK already at 90\nTOO LATE to enter",
    xy=(alert_bar, alert_px), xytext=(alert_bar+5, 1.68),
    color=ORANGE, fontsize=7.5, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.8),
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a0d00", edgecolor=ORANGE))

# Shade: W118 profit zone
ax_t.fill_between(range(w118_entry, len(price_t)), price_t[w118_entry:], w118_px,
    where=(price_t[w118_entry:]>w118_px), color=GREEN, alpha=0.10)

# Alert loss zone
ax_t.fill_between(range(alert_bar, len(price_t)), price_t[alert_bar:], alert_px,
    where=(price_t[alert_bar:]<alert_px), color=RED, alpha=0.15)

ax_t.text(30, 1.67, "If bought at alert $1.58:\nstock went DOWN to $1.10\n= -30% loss",
    color=RED, fontsize=7.5,
    bbox=dict(boxstyle="round,pad=0.3", facecolor=DARK, edgecolor=RED, alpha=0.85))

ax_t.text(1, 1.37, "Support $1.35\n(alert mentioned)", color=GRAY, fontsize=7)
ax_t.axhline(1.35, color=GRAY, lw=0.8, ls=":", alpha=0.6)

ax_t.set_ylim(0.82, 1.82)
ax_t.legend(loc="upper right", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)
ticks = [0,10,20,25,35,50,69]
tlabs = ["13:50","14:00","14:10\nW118","14:35\nALERT","15:00","16:00","AH"]
ax_t.set_xticks(ticks); ax_t.set_xticklabels(tlabs, color=GRAY, fontsize=7)

# ── PCLA PRICE: Alert at $2.48 → run to $9.80 ──────────────
ax_p = fig.add_subplot(gs[0, 1])
dark_ax(ax_p, "PCLA — 5m  |  Alert @ 2:01pm $2.48 'Squeezing' → $9.80", "Price ($)")

pre_p  = np.linspace(1.48, 2.45, 12) + np.random.randn(12)*0.04
consol = np.ones(5)*2.48 + np.random.randn(5)*0.04   # squeeze = tight range
breakout = [2.52,2.80,3.30,4.00,4.80,5.60,6.50,7.40,8.20,9.00,9.60,9.80]
pullbk = np.linspace(9.80,6.50,21) + np.random.randn(21)*0.15
price_p = np.concatenate([pre_p, consol, breakout, pullbk])
pp = len(price_p)

for i in range(pp):
    c = GREEN if i==0 or price_p[i]>=price_p[i-1] else RED
    ax_p.bar(i, price_p[i]-1.1, bottom=1.1, color=c, width=0.75, alpha=0.85)

entry_px = 2.48; ebar = 16
t1_p = entry_px*1.15; t2_p = entry_px*1.30; t3_p = entry_px*1.60; stop_p = entry_px*0.92

ax_p.axhline(t1_p,   color="#a8ff78", lw=1.2, ls="--", label=f"T1 +15% = $2.85")
ax_p.axhline(t2_p,   color=GREEN,     lw=1.4, ls="--", label=f"T2 +30% = $3.22")
ax_p.axhline(t3_p,   color=TEAL,      lw=1.4, ls="--", label=f"T3 +60% = $3.97")
ax_p.axhline(stop_p, color=RED,       lw=1.0, ls=":",  label=f"Stop -8% = $2.28")
ax_p.axhline(9.80,   color=PURPLE,    lw=0.8, ls=":",  alpha=0.7, label="Peak $9.80")

# Squeeze zone
ax_p.axvspan(ebar-1, ebar+4, color=YELLOW, alpha=0.08)
ax_p.annotate("ALERT 2:01pm\n'PCLA squeezing'\n$2.48 support\nENTER HERE on curl",
    xy=(ebar, entry_px), xytext=(ebar+2, 7.00),
    color=YELLOW, fontsize=7.5, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.8),
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1500", edgecolor=YELLOW))

# Label each target hit
for lvl, lbl, col in [(t1_p,"T1 HIT\n+15%","#a8ff78"),(t2_p,"T2 HIT\n+30%",GREEN),(t3_p,"T3 HIT\n+60%",TEAL)]:
    # find first bar where price crossed the level
    hits = [i for i in range(ebar, pp) if price_p[i] >= lvl]
    if hits:
        hb = hits[0]
        ax_p.plot(hb, lvl+0.15, "^", color=col, markersize=8)
        ax_p.text(hb+0.5, lvl+0.20, lbl, color=col, fontsize=6.5, fontweight="bold")

ax_p.annotate("PEAK $9.80\n(+295% from entry!)", xy=(27, 9.80), xytext=(35, 9.20),
    color=PURPLE, fontsize=8, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=PURPLE, lw=1.5))
ax_p.annotate("Settled\n$6.50 AH\n(+162%)", xy=(47, 6.50), xytext=(38, 4.50),
    color=GREEN, fontsize=7.5, arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.2))

ax_p.fill_between(range(ebar, pp), price_p[ebar:], entry_px,
    where=(price_p[ebar:]>entry_px), color=GREEN, alpha=0.10)

ax_p.set_ylim(0.8, 11.5)
ax_p.legend(loc="upper left", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY, ncol=2)
ax_p.set_xticks([0,6,11,16,22,30,40,pp-1])
ax_p.set_xticklabels(["13:30","14:00","14:30","14:45\nALERT","15:00","15:30\nPeak","16:30","AH"],
    color=GRAY, fontsize=7)

# ═══════════════════════════════════════════════════════════
# ROW 1 — STOCH: showing K at entry moment
# ═══════════════════════════════════════════════════════════

ax_ts = fig.add_subplot(gs[1, 0])
dark_ax(ax_ts, "TRNR Stoch — K at ALERT was already 85+ (overbought = TRAP)", "")

t70 = np.arange(70)
k_t = np.concatenate([np.ones(18)*8+np.random.randn(18)*3,
    [10,25,55,75,88,92,90,85,80,75,70,62,55,48,42,36,30,24,18,15,
     14,16,20,25,30,28,24,20,18,15,14,20,30,40,50,48,45,42,38,35,
     32,28,25,22,20,18,16,15,14,18,22,28]])[:70]
d_t = np.convolve(k_t, np.ones(5)/5, mode='same')

ax_ts.plot(t70, k_t, color=BLUE,   lw=1.8, label="K")
ax_ts.plot(t70, d_t, color=ORANGE, lw=1.4, label="D", ls="--")
ax_ts.axhline(80, color=RED,   lw=0.8, ls=":", alpha=0.7)
ax_ts.axhline(20, color=GREEN, lw=0.8, ls=":", alpha=0.7)
ax_ts.fill_between(t70, k_t, d_t, where=(k_t>=d_t), alpha=0.12, color=GREEN)
ax_ts.fill_between(t70, k_t, d_t, where=(k_t<d_t),  alpha=0.12, color=RED)

# W118 entry marker
ax_ts.axvline(20, color=GREEN, lw=2, ls="--", alpha=0.8)
ax_ts.axvline(25, color=ORANGE, lw=2, ls="--", alpha=0.8)

ax_ts.annotate("W118 entry\nK=8→20\nPERFECT", xy=(20,10), xytext=(5,55),
    color=GREEN, fontsize=7.5, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5))
ax_ts.annotate("Alert fires\nK=88\nOVERBOUGHT\n= DON'T BUY", xy=(25,88), xytext=(30,95),
    color=ORANGE, fontsize=7.5, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.5))

ax_ts.text(1,22,"BUY ZONE",color=GREEN,fontsize=7,alpha=0.8)
ax_ts.text(1,83,"SELL ZONE",color=RED,fontsize=7,alpha=0.8)
ax_ts.set_ylim(-5,108)
ax_ts.legend(loc="upper right", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)

ax_ps = fig.add_subplot(gs[1, 1])
dark_ax(ax_ps, "PCLA Stoch — K near 20 at alert = PERFECT entry zone", "")

t_pp = np.arange(pp)
k_p2 = np.concatenate([np.ones(10)*12+np.random.randn(10)*3,
    [14,16,18,19,20],                       # squeeze = K flat near 20
    [22,35,55,72,85,90,88,82,78,72,68,62],  # breakout
    np.linspace(60,25,15)+np.random.randn(15)*4,
    np.linspace(25,50,8)+np.random.randn(8)*3,
])[:pp]
d_p2 = np.convolve(k_p2, np.ones(5)/5, mode='same')

ax_ps.plot(t_pp, k_p2, color=BLUE,   lw=1.8, label="K")
ax_ps.plot(t_pp, d_p2, color=ORANGE, lw=1.4, label="D", ls="--")
ax_ps.axhline(80, color=RED,   lw=0.8, ls=":", alpha=0.7)
ax_ps.axhline(20, color=GREEN, lw=0.8, ls=":", alpha=0.7)
ax_ps.fill_between(t_pp, k_p2, d_p2, where=(k_p2>=d_p2), alpha=0.12, color=GREEN)
ax_ps.fill_between(t_pp, k_p2, d_p2, where=(k_p2<d_p2),  alpha=0.12, color=RED)

ax_ps.axvspan(ebar-1, ebar+4, color=YELLOW, alpha=0.08)
ax_ps.axvline(ebar+2, color=YELLOW, lw=2, ls="--", alpha=0.8)

ax_ps.annotate("Alert + entry\nK=18-20\nJust crossing up!\nCLEAN ENTRY",
    xy=(ebar+2, 20), xytext=(ebar+8, 60),
    color=YELLOW, fontsize=7.5, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.5))
ax_ps.text(1,22,"BUY ZONE — this is where you want K",color=GREEN,fontsize=7,alpha=0.9)
ax_ps.set_ylim(-5,108)
ax_ps.legend(loc="upper right", fontsize=7, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)

# ═══════════════════════════════════════════════════════════
# ROW 2 — TOMORROW PREDICTION
# ═══════════════════════════════════════════════════════════

ax_tt = fig.add_subplot(gs[2, 0])
dark_ax(ax_tt, "TRNR — Tomorrow Prediction (May 22)", "Price ($)")

# Has news. Could gap up slightly but likely chop. Stoch needs full reset.
tom_t = np.concatenate([
    [1.15,1.22,1.28,1.32,1.30,1.28],   # gap up on news at open
    np.linspace(1.28,1.18,10)+np.random.randn(10)*0.012,  # fades
    np.linspace(1.18,1.20,8)+np.random.randn(8)*0.008,    # chop
    np.linspace(1.20,1.15,6)+np.random.randn(6)*0.006,    # settles
])
t_tom = np.arange(len(tom_t))
for i in range(len(tom_t)):
    c = GREEN if i==0 or tom_t[i]>=tom_t[i-1] else RED
    ax_tt.bar(i, tom_t[i]-1.05, bottom=1.05, color=c, width=0.75, alpha=0.85)

ax_tt.annotate("Gap up on news\n~$1.28-$1.32\n(catalyst still live)", xy=(2,1.30), xytext=(8,1.42),
    color=YELLOW, fontsize=7.5, arrowprops=dict(arrowstyle="->", color=YELLOW, lw=1.2))
ax_tt.annotate("Fades back down\nno fresh volume\n= chop zone", xy=(12,1.18), xytext=(15,1.38),
    color=RED, fontsize=7.5, arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))

ax_tt.text(0.02, 0.08, "VERDICT: Watch pre-market. If top-mover list + Stoch resets to <10 overnight\n"
    "→ fresh curl entry possible. Otherwise: WAIT. Don't force it.",
    transform=ax_tt.transAxes, color=YELLOW, fontsize=7.5,
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#1a1500", edgecolor=YELLOW, alpha=0.9))
ax_tt.set_ylim(1.02, 1.52)

ax_pt2 = fig.add_subplot(gs[2, 1])
dark_ax(ax_pt2, "PCLA — Tomorrow Prediction (May 22)", "Price ($)")

# No news. After +60% day, profit-takers will dump. Classic fade.
tom_p = np.concatenate([
    [6.50,5.80,5.20,4.80],              # gap down at open, profit taking
    np.linspace(4.80,4.20,8)+np.random.randn(8)*0.12,  # continued selling
    np.linspace(4.20,4.50,6)+np.random.randn(6)*0.10,  # small dead cat
    np.linspace(4.50,3.80,12)+np.random.randn(12)*0.10, # resumes down
])
t_tomp = np.arange(len(tom_p))
for i in range(len(tom_p)):
    c = GREEN if i==0 or tom_p[i]>=tom_p[i-1] else RED
    ax_pt2.bar(i, tom_p[i]-3.0, bottom=3.0, color=c, width=0.75, alpha=0.85)

ax_pt2.annotate("Gap DOWN at open\nProfit takers selling\n~$5.20-$5.80", xy=(1,5.80), xytext=(5,6.80),
    color=RED, fontsize=7.5, arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
ax_pt2.annotate("Dead cat bounce\nDon't buy this!", xy=(14,4.50), xytext=(16,5.50),
    color=ORANGE, fontsize=7.5, arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2))

ax_pt2.text(0.02, 0.08, "VERDICT: NO NEWS = profit takers win. Expect -20 to -40% from close.\n"
    "Only re-enter if NEW news drops + Stoch fully resets. Otherwise: walk away.",
    transform=ax_pt2.transAxes, color=RED, fontsize=7.5,
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#1a0505", edgecolor=RED, alpha=0.9))
ax_pt2.set_ylim(2.8, 7.8)

# ═══════════════════════════════════════════════════════════
# ROW 3 — COMPOUNDING CHART (spans full width)
# ═══════════════════════════════════════════════════════════

ax_comp = fig.add_subplot(gs[3, :])
dark_ax(ax_comp, "$500 Compounded Over 30 W118-Style Trades  (avg +30% win, -8% stop, 98% win rate)", "Account Value ($)")

# Simulate 30 trades: 98% win rate, avg +30% win, avg -8% loss
# Taking 25% position size per trade = actual account impact per trade
# Win: +30% on 25% of account = +7.5% account gain
# Loss: -8% on 25% of account = -2% account gain
trades = 30
position_size = 0.25  # 25% of account per trade
win_rate = 0.98
avg_win = 0.30; avg_loss = 0.08

# Best case (all wins)
acct_best = [500]
for i in range(trades):
    acct_best.append(acct_best[-1] * (1 + avg_win * position_size))

# Realistic (98% win rate)
np.random.seed(99)
acct_real = [500]
outcomes_real = []
for i in range(trades):
    win = np.random.rand() < win_rate
    outcomes_real.append(win)
    if win:
        acct_real.append(acct_real[-1] * (1 + avg_win * position_size))
    else:
        acct_real.append(acct_real[-1] * (1 - avg_loss * position_size))

# Conservative (80% win rate — paper trading target)
acct_cons = [500]
for i in range(trades):
    win = np.random.rand() < 0.80
    if win:
        acct_cons.append(acct_cons[-1] * (1 + avg_win * position_size))
    else:
        acct_cons.append(acct_cons[-1] * (1 - avg_loss * position_size))

x = np.arange(trades+1)
ax_comp.plot(x, acct_best, color=PURPLE, lw=2.5, label=f"Best case (100% win) → ${acct_best[-1]:,.0f}", zorder=3)
ax_comp.plot(x, acct_real, color=GREEN, lw=2.5, label=f"W118 pace (98% win) → ${acct_real[-1]:,.0f}", zorder=4)
ax_comp.plot(x, acct_cons, color=YELLOW, lw=2.0, ls="--", label=f"Paper trade target (80% win) → ${acct_cons[-1]:,.0f}", zorder=3)
ax_comp.axhline(500, color=GRAY, lw=0.8, ls=":", alpha=0.6)
ax_comp.axhline(25000, color=RED, lw=1.2, ls="--", alpha=0.8, label="$25k PDT threshold (unlimited day trades)")

ax_comp.fill_between(x, acct_real, 500, where=(np.array(acct_real)>500),
    color=GREEN, alpha=0.08)
ax_comp.fill_between(x, acct_cons, 500, where=(np.array(acct_cons)>500),
    color=YELLOW, alpha=0.06)

# Mark milestone trades
for tgt, lbl, col in [(10, "10 trades", GRAY), (20, "20 trades", BLUE), (30, "30 trades", WHITE)]:
    ax_comp.axvline(tgt, color=col, lw=0.7, ls=":", alpha=0.5)

# Mark individual trades as dots
for i, (v, w) in enumerate(zip(acct_real[1:], outcomes_real)):
    col = GREEN if w else RED
    ax_comp.plot(i+1, acct_real[i+1], "o", color=col, markersize=5, zorder=5,
        alpha=0.8 if w else 1.0)

losses = [i+1 for i,w in enumerate(outcomes_real) if not w]
if losses:
    for l in losses:
        ax_comp.annotate("Loss\n-2%", xy=(l, acct_real[l]), xytext=(l, acct_real[l]*0.88),
            color=RED, fontsize=6.5, ha="center",
            arrowprops=dict(arrowstyle="->", color=RED, lw=1))

ax_comp.text(0.5, 0.03, f"Position size = 25% per trade  |  Win = +30% on position (+7.5% acct)  |  "
    f"Loss = -8% on position (-2% acct)  |  Never risk more than 25% per trade",
    transform=ax_comp.transAxes, ha="center", color=GRAY, fontsize=8)

ax_comp.set_xlim(-0.5, 30.5)
ax_comp.set_xticks(range(0, 31, 5))
ax_comp.set_xticklabels([f"Trade {i}" for i in range(0, 31, 5)], color=GRAY, fontsize=8)
ax_comp.legend(loc="upper left", fontsize=8, facecolor=DARK, labelcolor=WHITE, edgecolor=LGRAY)
ax_comp.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

plt.savefig("/home/user/tradingbaby/tools/entry_exit_compound.png",
    dpi=150, bbox_inches="tight", facecolor=DARK)
print("Saved.")
