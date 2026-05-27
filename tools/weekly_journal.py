import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import json
import os

# ── load data ──────────────────────────────────────────────────────────────
journal_path = os.path.join(os.path.dirname(__file__), "../journal/weekly_log.json")
with open(journal_path) as f:
    data = json.load(f)

week_label = data["week"]
acct_start = data["account_start"]["total"]
acct_end   = data["account_end"]["total"]
trades     = [t for t in data["trades"] if t["ticker"]]
goal_wr    = data["goal_win_rate"]
summary    = data["summary"]

# ── computed stats ─────────────────────────────────────────────────────────
n = len(trades)
wins   = sum(1 for t in trades if t["result"] == "win")
losses = n - wins
win_rate = (wins / n * 100) if n else 0
rules_pct = (sum(1 for t in trades if t["all_rules_followed"]) / n * 100) if n else 0
total_pnl = sum(t["pnl_dollar"] for t in trades)
net_pct   = ((acct_end - acct_start) / acct_start * 100) if acct_start else 0

# ── figure setup ───────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 18), facecolor="#0d0d0d")
fig.text(0.5, 0.97, "W118 CURL IF FLOW — WEEKLY SCORECARD",
         ha="center", va="top", fontsize=18, fontweight="bold",
         color="white", fontfamily="monospace")
fig.text(0.5, 0.945, f"Week: {week_label}",
         ha="center", va="top", fontsize=11, color="#aaaaaa", fontfamily="monospace")

# ── helper ─────────────────────────────────────────────────────────────────
def box(ax, x, y, w, h, color, radius=0.05):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle=f"round,pad=0", linewidth=0,
        facecolor=color, transform=ax.transAxes, clip_on=False))

def stat_card(ax, label, value, subval, val_color, x, y, w=0.18, h=0.12):
    box(ax, x, y, w, h, "#1a1a2e")
    ax.text(x + w/2, y + h*0.72, str(value), ha="center", va="center",
            fontsize=22, fontweight="bold", color=val_color,
            fontfamily="monospace", transform=ax.transAxes)
    ax.text(x + w/2, y + h*0.35, label, ha="center", va="center",
            fontsize=9, color="#888888", fontfamily="monospace",
            transform=ax.transAxes)
    if subval:
        ax.text(x + w/2, y + h*0.10, subval, ha="center", va="center",
                fontsize=8, color="#555555", fontfamily="monospace",
                transform=ax.transAxes)

# ── top stat cards ─────────────────────────────────────────────────────────
ax_stats = fig.add_axes([0, 0, 1, 1], frameon=False)
ax_stats.set_xlim(0, 1); ax_stats.set_ylim(0, 1)
ax_stats.axis("off")

wr_color  = "#00ff88" if win_rate >= goal_wr else "#ff4444"
pnl_color = "#00ff88" if total_pnl >= 0 else "#ff4444"
rul_color = "#00ff88" if rules_pct >= 90 else ("#ffaa00" if rules_pct >= 70 else "#ff4444")

stat_card(ax_stats, "WIN RATE",  f"{win_rate:.0f}%",   f"goal {goal_wr}%",  wr_color,  0.04, 0.80)
stat_card(ax_stats, "TRADES",    f"{n}",                f"{wins}W / {losses}L", "#ffffff", 0.24, 0.80)
stat_card(ax_stats, "NET P&L",   f"${total_pnl:+.2f}", f"{net_pct:+.1f}% acct", pnl_color, 0.44, 0.80)
stat_card(ax_stats, "RULES %",   f"{rules_pct:.0f}%",  "all 6 followed",   rul_color, 0.64, 0.80)
stat_card(ax_stats, "ACCT END",  f"${acct_end:.2f}",   f"started ${acct_start:.2f}", "#ffffff", 0.78, 0.80)

# ── trade table ────────────────────────────────────────────────────────────
ax_tbl = fig.add_axes([0.04, 0.37, 0.92, 0.41])
ax_tbl.set_facecolor("#111111")
ax_tbl.axis("off")

headers = ["DATE", "TICKER", "ACCT", "ENTRY", "EXIT", "P&L %", "P&L $", "RULES", "EXIT REASON"]
col_x   = [0.01, 0.09, 0.17, 0.24, 0.32, 0.40, 0.50, 0.60, 0.72]
row_h   = 0.085
header_y = 0.92

for i, (h, x) in enumerate(zip(headers, col_x)):
    ax_tbl.text(x, header_y, h, fontsize=8, fontweight="bold",
                color="#ffaa00", fontfamily="monospace", transform=ax_tbl.transAxes)

ax_tbl.axhline(y=header_y - 0.04, color="#333333", linewidth=0.8)

max_rows = 9
display_trades = trades[:max_rows] if trades else []

# empty rows placeholder
if not display_trades:
    ax_tbl.text(0.5, 0.5, "No trades logged yet — add them to journal/weekly_log.json",
                ha="center", va="center", fontsize=10, color="#444444",
                fontfamily="monospace", transform=ax_tbl.transAxes)
else:
    for row_i, t in enumerate(display_trades):
        y = header_y - 0.06 - row_i * row_h
        bg_color = "#0d2b1a" if t["result"] == "win" else "#2b0d0d"
        ax_tbl.add_patch(FancyBboxPatch((0, y - 0.03), 1.0, row_h * 0.95,
            boxstyle="round,pad=0", facecolor=bg_color, linewidth=0,
            transform=ax_tbl.transAxes))

        pnl_pct_color = "#00ff88" if t["pnl_pct"] >= 0 else "#ff4444"
        rules_str = "✓ ALL" if t["all_rules_followed"] else "✗ BROKE"
        rules_color = "#00ff88" if t["all_rules_followed"] else "#ff4444"

        vals = [
            (t["date"], "#aaaaaa"),
            (t["ticker"], "#ffffff"),
            (t["account"].upper(), "#888888"),
            (f"${t['entry_price']:.2f}", "#ffffff"),
            (f"${t['exit_price']:.2f}", "#ffffff"),
            (f"{t['pnl_pct']:+.1f}%", pnl_pct_color),
            (f"${t['pnl_dollar']:+.2f}", pnl_pct_color),
            (rules_str, rules_color),
            (t["exit_reason"][:12], "#888888"),
        ]
        for (val, col), x in zip(vals, col_x):
            ax_tbl.text(x, y + 0.02, str(val), fontsize=8, color=col,
                        fontfamily="monospace", transform=ax_tbl.transAxes)

ax_tbl.set_title("TRADE LOG", color="#ffffff", fontsize=10,
                 fontfamily="monospace", pad=8, loc="left")

# ── rules checklist breakdown ──────────────────────────────────────────────
ax_rules = fig.add_axes([0.04, 0.19, 0.44, 0.16])
ax_rules.set_facecolor("#111111")
ax_rules.axis("off")
ax_rules.set_title("RULES FOLLOWED (per trade)", color="#ffffff",
                   fontsize=9, fontfamily="monospace", pad=6, loc="left")

rule_labels = {
    "stoch_rsi_cross_20": "Stoch RSI K cross 20",
    "sha_green":          "SHA candle green",
    "above_zlsma":        "Price > ZLSMA-50",
    "volume_1_5x":        "Volume ≥ 1.5×",
    "float_under_20m":    "Float < 20M",
    "session_4am_1030am": "Session 4am–10:30am",
}

for r_i, (key, label) in enumerate(rule_labels.items()):
    col_r = r_i % 2
    row_r = r_i // 2
    x_r = 0.02 + col_r * 0.50
    y_r = 0.75 - row_r * 0.28
    count = sum(1 for t in trades if t["rules"].get(key, False)) if trades else 0
    total_r = n if n else 1
    pct_r = count / total_r * 100
    bar_color = "#00ff88" if pct_r >= 90 else ("#ffaa00" if pct_r >= 70 else "#ff4444")
    ax_rules.barh(y_r, pct_r / 100 * 0.42, height=0.18, left=x_r + 0.06,
                  color=bar_color, alpha=0.7, transform=ax_rules.transAxes)
    ax_rules.text(x_r, y_r + 0.04, f"{label}", fontsize=7.5,
                  color="#aaaaaa", fontfamily="monospace", transform=ax_rules.transAxes)
    ax_rules.text(x_r + 0.49, y_r + 0.04, f"{pct_r:.0f}%", fontsize=7.5,
                  color=bar_color, fontfamily="monospace", ha="right",
                  transform=ax_rules.transAxes)

# ── weekly goals / reflection ──────────────────────────────────────────────
ax_goals = fig.add_axes([0.52, 0.19, 0.44, 0.16])
ax_goals.set_facecolor("#111111")
ax_goals.axis("off")
ax_goals.set_title("WEEKLY GOALS & REFLECTION", color="#ffffff",
                   fontsize=9, fontfamily="monospace", pad=6, loc="left")

goals = [
    ("Win rate ≥ 80%",         win_rate >= 80),
    ("Follow all 6 rules",     rules_pct >= 90),
    ("No revenge trades",      True),
    ("Paper trade only",       True),
    ("Log every trade",        n > 0),
    ("Review charts next day", False),
]

for g_i, (goal_txt, done) in enumerate(goals):
    col_g = g_i % 2
    row_g = g_i // 2
    x_g = 0.02 + col_g * 0.50
    y_g = 0.80 - row_g * 0.30
    icon  = "✓" if done else "○"
    color = "#00ff88" if done else "#555555"
    ax_goals.text(x_g, y_g, f"{icon}  {goal_txt}", fontsize=8,
                  color=color, fontfamily="monospace", transform=ax_goals.transAxes)

# ── lesson of the week ────────────────────────────────────────────────────
lesson = summary.get("lesson_of_the_week") or "Add your lesson to journal/weekly_log.json"
ax_lesson = fig.add_axes([0.04, 0.08, 0.92, 0.09])
ax_lesson.set_facecolor("#1a1a2e")
ax_lesson.axis("off")
ax_lesson.text(0.02, 0.72, "LESSON OF THE WEEK:", fontsize=9, fontweight="bold",
               color="#ffaa00", fontfamily="monospace", transform=ax_lesson.transAxes)
ax_lesson.text(0.02, 0.35, f'"{lesson}"', fontsize=10, color="#cccccc",
               fontfamily="monospace", transform=ax_lesson.transAxes, style="italic")

# ── milestone progress bar ────────────────────────────────────────────────
ax_mile = fig.add_axes([0.04, 0.03, 0.92, 0.04])
ax_mile.set_facecolor("#111111")
ax_mile.axis("off")

milestones = [173, 300, 500, 1000, 2500, 5000, 10000, 25000]
mile_labels = ["$173", "$300", "$500", "$1k", "$2.5k", "$5k", "$10k", "$25k"]
log_vals = [np.log10(m) for m in milestones]
log_min, log_max = log_vals[0], log_vals[-1]
log_current = np.log10(max(acct_end, 173))
progress = (log_current - log_min) / (log_max - log_min)

ax_mile.barh(0.5, 1.0, height=0.5, color="#222222", transform=ax_mile.transAxes)
ax_mile.barh(0.5, progress, height=0.5, color="#00ff88", alpha=0.6, transform=ax_mile.transAxes)

for m, lbl in zip(log_vals, mile_labels):
    xp = (m - log_min) / (log_max - log_min)
    ax_mile.axvline(x=xp, color="#333333", linewidth=1.5)
    ax_mile.text(xp, 1.15, lbl, ha="center", fontsize=7, color="#888888",
                 fontfamily="monospace", transform=ax_mile.transAxes)

ax_mile.text(0.0, -0.6, f"Current: ${acct_end:.2f}", fontsize=8, color="#00ff88",
             fontfamily="monospace", transform=ax_mile.transAxes)
ax_mile.text(1.0, -0.6, "Goal: $25,000", fontsize=8, color="#ffaa00",
             fontfamily="monospace", ha="right", transform=ax_mile.transAxes)

# ── save ──────────────────────────────────────────────────────────────────
out_path = os.path.join(os.path.dirname(__file__), "weekly_journal.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#0d0d0d")
print(f"Saved: {out_path}")
plt.close()
