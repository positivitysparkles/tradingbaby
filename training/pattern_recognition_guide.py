"""
W118 Curl if Flow — Pattern Recognition Training Guide
Generated from May 26, 2026 live trading session lessons.
Run this script to regenerate the PNG.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ── figure setup ──────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 22), facecolor='#0d1117')
fig.text(0.5, 0.977, 'W118 CURL IF FLOW — PATTERN RECOGNITION GUIDE',
         ha='center', fontsize=20, fontweight='bold',
         color='white', fontfamily='monospace')
fig.text(0.5, 0.962, 'Lessons from live trading  |  May 26, 2026  |  Study before every session',
         ha='center', fontsize=10, color='#666666', fontfamily='monospace')

BG      = '#0d1117'
CARD    = '#161b22'
GREEN   = '#3fb950'
RED     = '#f85149'
YELLOW  = '#FFD700'
BLUE    = '#58a6ff'
ORANGE  = '#ffaa00'
GRAY    = '#888888'
LGRAY   = '#cccccc'

def card_bg(ax):
    ax.set_facecolor(CARD)
    for spine in ax.spines.values():
        spine.set_color('#333333')
    ax.tick_params(colors='#555555')

def section_title(ax, text, color=ORANGE):
    ax.set_title(text, color=color, fontsize=11,
                 fontfamily='monospace', fontweight='bold', pad=8, loc='left')

def mini_candles(ax, pattern='runner'):
    """Draw simple candle shapes representing each pattern."""
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 10)
    ax.axis('off')

    if pattern == 'fade':
        # big spike then all day fade
        prices = [3,3.2,3.1,6.5,5.8,5.0,4.5,4.2,3.9,3.7,3.5,3.2,3.0,2.8,2.9]
        colors = [GREEN]+[RED]*13+[RED]
    elif pattern == 'runner':
        # spike, pullback, holds ZLSMA, another push
        prices = [3,3.1,5.0,4.5,4.2,4.3,4.5,4.4,4.6,4.8,5.2,5.5,5.3,5.6,5.8]
        colors = [GREEN,GREEN,GREEN,RED,RED,GREEN,GREEN,RED,GREEN,GREEN,GREEN,GREEN,RED,GREEN,GREEN]
    else:  # accumulation
        prices = [3,3.1,5.5,4.8,4.0,3.5,3.2,3.1,3.0,3.2,3.5,4.0,4.5,5.0,5.5]
        colors = [GREEN,GREEN,GREEN,RED,RED,RED,RED,RED,RED,GREEN,GREEN,GREEN,GREEN,GREEN,GREEN]

    xs = np.linspace(1, 19, len(prices))
    w = 0.7
    for i in range(1, len(prices)):
        lo = min(prices[i], prices[i-1])
        hi = max(prices[i], prices[i-1])
        h  = max(hi - lo, 0.15)
        ax.bar(xs[i], h, bottom=lo, width=w,
               color=colors[i], alpha=0.9, linewidth=0)

    # ZLSMA line
    zlsma_y = np.ones(len(xs)) * 3.8
    if pattern == 'runner':
        zlsma_y = np.array([3.0,3.1,3.5,3.8,3.9,4.0,4.1,4.1,4.2,4.3,4.4,4.5,4.5,4.6,4.7])
    elif pattern == 'accumulation':
        zlsma_y = np.array([3.0,3.1,3.4,3.7,3.8,3.7,3.6,3.5,3.4,3.4,3.5,3.6,3.8,4.0,4.2])
    ax.plot(xs, zlsma_y, color=YELLOW, linewidth=2.5, zorder=5, label='ZLSMA')

def stoch_mini(ax, k_vals, d_vals, color_k=BLUE, color_d=ORANGE):
    ax.set_xlim(0, len(k_vals))
    ax.set_ylim(-5, 105)
    ax.axis('off')
    xs = np.arange(len(k_vals))
    ax.axhline(y=20, color='white', linestyle='--', alpha=0.3, linewidth=1)
    ax.axhline(y=80, color='white', linestyle='--', alpha=0.2, linewidth=1)
    ax.fill_between(xs, 0, 20, alpha=0.15, color=GREEN)
    ax.plot(xs, k_vals, color=color_k, linewidth=2)
    ax.plot(xs, d_vals, color=color_d, linewidth=1.5, linestyle='--')

# ══════════════════════════════════════════════════════════════════════════════
# ROW 1 — THREE PATTERNS
# ══════════════════════════════════════════════════════════════════════════════

# Pattern A — FADE
ax_a = fig.add_axes([0.04, 0.76, 0.27, 0.17])
card_bg(ax_a)
mini_candles(ax_a, 'fade')
ax_a.set_title('PATTERN A  —  "FIRST RED DAY"  NO   AVOID',
               color=RED, fontsize=10, fontfamily='monospace',
               fontweight='bold', pad=6, loc='left')
fig.text(0.045, 0.756, '▸ Spikes at open → fades ALL day → closes near lows',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')
fig.text(0.045, 0.748, '▸ Price drops BELOW ZLSMA yellow line',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')
fig.text(0.045, 0.740, '▸ Smart money sold into the spike. Retail left holding.',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')
fig.text(0.045, 0.732, '▸ Tomorrow: likely fades more. Do NOT enter.',
         fontsize=8.5, color=RED, fontfamily='monospace', fontweight='bold')
fig.text(0.045, 0.724, '▸ Real example today: ARTL ($2.40 → $1.36 AH)',
         fontsize=8.5, color='#555555', fontfamily='monospace', style='italic')

# Pattern B — RUNNER
ax_b = fig.add_axes([0.37, 0.76, 0.27, 0.17])
card_bg(ax_b)
mini_candles(ax_b, 'runner')
ax_b.set_title('PATTERN B  —  "MULTI-DAY RUNNER"  ~~   WATCH',
               color=ORANGE, fontsize=10, fontfamily='monospace',
               fontweight='bold', pad=6, loc='left')
fig.text(0.375, 0.756, '▸ Big spike → pullback → HOLDS above ZLSMA at close',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')
fig.text(0.375, 0.748, '▸ Catalyst still live (real news, not just buzz)',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')
fig.text(0.375, 0.740, '▸ Stoch RSI resets overnight → BUY fires at premarket',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')
fig.text(0.375, 0.732, '▸ Tomorrow: wait for K < 20 curl → then enter',
         fontsize=8.5, color=ORANGE, fontfamily='monospace', fontweight='bold')
fig.text(0.375, 0.724, '▸ Real example today: YMAT (+203%), UZX (+72%)',
         fontsize=8.5, color='#555555', fontfamily='monospace', style='italic')

# Pattern C — ACCUMULATION
ax_c = fig.add_axes([0.70, 0.76, 0.27, 0.17])
card_bg(ax_c)
mini_candles(ax_c, 'accumulation')
ax_c.set_title('PATTERN C  —  "LATE ACCUMULATION"  #1   BEST',
               color=GREEN, fontsize=10, fontfamily='monospace',
               fontweight='bold', pad=6, loc='left')
fig.text(0.705, 0.756, '▸ Spikes → sells off all day → W118 BUY fires late/AH',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')
fig.text(0.705, 0.748, '▸ Stoch RSI FULLY reset (K near 0) by close',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')
fig.text(0.705, 0.740, '▸ Someone is buying intentionally into weakness',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')
fig.text(0.705, 0.732, '▸ Tomorrow: highest probability of clean premarket run',
         fontsize=8.5, color=GREEN, fontfamily='monospace', fontweight='bold')
fig.text(0.705, 0.724, '▸ Real example today: SNGX (K=7.85 at close!)',
         fontsize=8.5, color='#555555', fontfamily='monospace', style='italic')

# ══════════════════════════════════════════════════════════════════════════════
# ROW 2 — STOCH RSI GUIDE + ZLSMA GUIDE
# ══════════════════════════════════════════════════════════════════════════════

ax_stoch = fig.add_axes([0.04, 0.55, 0.56, 0.17])
card_bg(ax_stoch)
section_title(ax_stoch, 'STOCH RSI AT CLOSE → WHAT IT MEANS FOR TOMORROW')

# Draw multiple stoch scenarios side by side
scenarios = [
    ('K = 0–10\nat close', [8,6,4,3,2,1,0,2,5,10,18,25,35], 'PERFECT\nRESET', GREEN, '#1  Best setup\nFires by 4am premarket'),
    ('K = 10–25\nat close', [25,20,18,15,12,10,8,10,14,20,28,35,45], 'NEARLY\nRESET', ORANGE, ' OK Good setup\nMay fire at open'),
    ('K = 25–50\nat close', [50,45,40,38,35,32,30,32,35,40,45,50,55], 'PARTIAL\nRESET', ORANGE, ' ! Needs more\ncooling overnight'),
    ('K = 50–80\nat close', [70,68,65,62,60,58,56,57,60,65,68,72,75], 'NOT\nRESET', RED, 'NO  Do not enter\nWait for full reset'),
    ('K = 80–100\nat close', [90,88,85,83,80,78,76,78,80,83,86,88,90], 'OVERBOUGHT\nAVOID', RED, '!!  Way too high\nProbable reversal'),
]

panel_w = 0.09
for i, (label, k_vals, status, color, advice) in enumerate(scenarios):
    x0 = 0.07 + i * 0.105
    d_vals = np.convolve(k_vals, np.ones(3)/3, mode='same')
    ax_s = fig.add_axes([x0, 0.575, panel_w, 0.09])
    ax_s.set_facecolor('#0d1117')
    for sp in ax_s.spines.values():
        sp.set_color(color)
        sp.set_linewidth(1.5)
    stoch_mini(ax_s, k_vals, d_vals)
    ax_s.text(0.5, 1.18, label, ha='center', fontsize=6.5,
              color=LGRAY, fontfamily='monospace',
              transform=ax_s.transAxes)
    ax_s.text(0.5, -0.22, status, ha='center', fontsize=7,
              color=color, fontfamily='monospace', fontweight='bold',
              transform=ax_s.transAxes)
    ax_s.text(0.5, -0.52, advice, ha='center', fontsize=6,
              color=GRAY, fontfamily='monospace',
              transform=ax_s.transAxes)

# ══════════════════════════════════════════════════════════════════════════════
# ZLSMA position guide
ax_zlsma = fig.add_axes([0.64, 0.55, 0.33, 0.17])
card_bg(ax_zlsma)
section_title(ax_zlsma, 'ZLSMA POSITION RULES')
ax_zlsma.axis('off')

zlsma_rules = [
    (' OK', 'Price ABOVE ZLSMA',       'Buyers in control. W118 entries valid.',       GREEN),
    (' !', 'Price AT ZLSMA',          'Decision zone. Watch for bounce or break.',     ORANGE),
    ('!! ', 'Price BELOW ZLSMA',       'NEVER trade. Rule #3. Exit immediately.',       RED),
    ('#1 ', 'ZLSMA curving UP',        'Trend accelerating. Best entries here.',        GREEN),
    (' ~~', 'ZLSMA flat/curving DOWN', 'Momentum dying. Reduce size or avoid.',         GRAY),
]

for i, (icon, rule, desc, color) in enumerate(zlsma_rules):
    y = 0.82 - i * 0.19
    ax_zlsma.text(0.02, y, f'{icon}  {rule}', fontsize=9, color=color,
                  fontfamily='monospace', fontweight='bold',
                  transform=ax_zlsma.transAxes)
    ax_zlsma.text(0.07, y - 0.09, desc, fontsize=8, color=GRAY,
                  fontfamily='monospace', transform=ax_zlsma.transAxes)

# ══════════════════════════════════════════════════════════════════════════════
# ROW 3 — TONIGHT'S STOCKS GRADED
# ══════════════════════════════════════════════════════════════════════════════

ax_stocks = fig.add_axes([0.04, 0.38, 0.92, 0.14])
card_bg(ax_stocks)
section_title(ax_stocks, 'MAY 26 END-OF-DAY GRADES  →  TOMORROW PREDICTION')
ax_stocks.axis('off')

headers = ['TICKER', 'TODAY %', 'PATTERN', 'STOCH K\nAT CLOSE', 'ZLSMA\nPOSITION', 'REL VOL', 'TOMORROW\nPREDICTION', 'PRIORITY']
col_x = [0.01, 0.09, 0.18, 0.30, 0.41, 0.51, 0.60, 0.82]
hy = 0.88
for h, x in zip(headers, col_x):
    ax_stocks.text(x, hy, h, fontsize=8, fontweight='bold',
                   color=ORANGE, fontfamily='monospace',
                   transform=ax_stocks.transAxes)
ax_stocks.axhline(y=hy - 0.06, color='#333333', linewidth=0.8)

stocks = [
    ('SNGX',  '+31.50%', 'C — Late Accum.',  'K=7.85 #1 ',   'Above  OK',  '70x',  '$1.10–$1.20  (+24–35%)', '#1  #1 BEST'),
    ('UZX',   '+72.65%', 'B — Multi-Day',     'K=74.95  !',  'Above  OK',  '87x',  'Wait for K<20 first',    '~~  #2 WATCH'),
    ('YMAT',  '+203.16%','B — Multi-Day',     'K=50.23  !',  'Near  !',   '13x',  '$1.50–$1.65 if resets',  '~~  #3 WATCH'),
    ('ARTL',  '+43.70%', 'A — First Red Day', 'N/A',          'Below !! ',  '9x',   'Likely fades more',      'NO  AVOID'),
]

row_h = 0.20
for r, (ticker, pct, pat, stoch, zlsma, rvol, pred, priority) in enumerate(stocks):
    y = hy - 0.12 - r * row_h
    bg = '#0d2b1a' if '#1 ' in priority or '~~ ' in priority else '#2b0d0d'
    ax_stocks.add_patch(FancyBboxPatch((0, y - 0.05), 1.0, row_h * 0.88,
        boxstyle='round,pad=0', facecolor=bg, linewidth=0,
        transform=ax_stocks.transAxes))
    vals = [
        (ticker, '#ffffff'),
        (pct, GREEN if '+' in pct else RED),
        (pat, LGRAY),
        (stoch, GREEN if '#1 ' in stoch else (ORANGE if ' !' in stoch else GRAY)),
        (zlsma, GREEN if ' OK' in zlsma else (ORANGE if ' !' in zlsma else RED)),
        (rvol, BLUE),
        (pred, LGRAY),
        (priority, GREEN if '#1 ' in priority else (ORANGE if '~~ ' in priority else RED)),
    ]
    for (val, col), x in zip(vals, col_x):
        ax_stocks.text(x, y + 0.04, val, fontsize=8, color=col,
                       fontfamily='monospace', transform=ax_stocks.transAxes)

# ══════════════════════════════════════════════════════════════════════════════
# ROW 4 — ENTRY MISTAKE LESSON + RELATIVE VOLUME GUIDE
# ══════════════════════════════════════════════════════════════════════════════

ax_mistake = fig.add_axes([0.04, 0.21, 0.44, 0.14])
card_bg(ax_mistake)
section_title(ax_mistake, ' !  THE #1 ENTRY MISTAKE — DON\'T CHASE', RED)
ax_mistake.axis('off')

mistake_text = [
    ('WRONG NO ', 'W118 BUY fires at $1.37', 'You enter at $1.79  (+30% above signal)', RED),
    ('',         'You paid 30% premium',     'Stop hit immediately on any pullback',    RED),
    ('RIGHT  OK', 'W118 BUY fires at $1.37', 'You enter at $1.37–1.40  (within 2%)',    GREEN),
    ('',         'Full edge of the signal',  'Stop at $1.26  (-8%)  ← manageable',      GREEN),
]

for i, (tag, line1, line2, color) in enumerate(mistake_text):
    y = 0.82 - i * 0.22
    if tag:
        ax_mistake.text(0.01, y, tag, fontsize=9, color=color,
                        fontweight='bold', fontfamily='monospace',
                        transform=ax_mistake.transAxes)
    ax_mistake.text(0.18, y,      line1, fontsize=8.5, color=LGRAY,
                    fontfamily='monospace', transform=ax_mistake.transAxes)
    ax_mistake.text(0.18, y-0.10, line2, fontsize=8,   color=color,
                    fontfamily='monospace', transform=ax_mistake.transAxes)

ax_mistake.text(0.01, 0.04,
    '>>  RULE: If price is >3% above the BUY signal price → skip it. Wait for the next reset.',
    fontsize=8.5, color=ORANGE, fontfamily='monospace', fontweight='bold',
    transform=ax_mistake.transAxes)

# Relative volume guide
ax_rvol = fig.add_axes([0.54, 0.21, 0.43, 0.14])
card_bg(ax_rvol)
section_title(ax_rvol, '>>  RELATIVE VOLUME — HOW TO READ IT')
ax_rvol.axis('off')

rvol_data = [
    ('> 50x',   'EXTREME — algo/institution buying. High conviction.',  '#00ff88'),
    ('10–50x',  'HOT — strong retail + momentum. W118 ideal zone.',     GREEN),
    ('3–10x',   'WARM — worth watching. Set alert, wait for signal.',   ORANGE),
    ('1.5–3x',  'MINIMUM — W118 requires >1.5x. Borderline.',          '#888888'),
    ('< 1.5x',  'SKIP — not enough fuel for a momentum move.',          RED),
]

for i, (level, desc, color) in enumerate(rvol_data):
    y = 0.84 - i * 0.19
    ax_rvol.add_patch(FancyBboxPatch((0.01, y - 0.07), 0.13, 0.14,
        boxstyle='round,pad=0', facecolor=color+'33', linewidth=0,
        transform=ax_rvol.transAxes))
    ax_rvol.text(0.07, y, level, fontsize=8, color=color, fontweight='bold',
                 fontfamily='monospace', ha='center', transform=ax_rvol.transAxes)
    ax_rvol.text(0.17, y, desc, fontsize=8, color=LGRAY,
                 fontfamily='monospace', transform=ax_rvol.transAxes)

# ══════════════════════════════════════════════════════════════════════════════
# ROW 5 — 6 ENTRY CONDITIONS QUICK REFERENCE
# ══════════════════════════════════════════════════════════════════════════════

ax_rules = fig.add_axes([0.04, 0.05, 0.92, 0.13])
card_bg(ax_rules)
section_title(ax_rules, ' OK  THE 6 ENTRY CONDITIONS  —  ALL REQUIRED BEFORE ENTERING')
ax_rules.axis('off')

conditions = [
    ('1.', 'STOCH RSI', 'K crosses UP\nthrough 20\nK above D', '#58a6ff', 'CRITICAL'),
    ('2.', 'SHA CANDLE', 'Smoothed HA\ncandle is\nGREEN', GREEN, 'CRITICAL'),
    ('3.', 'ZLSMA-50', 'Price ABOVE\nyellow line\nNEVER below', YELLOW, 'CRITICAL'),
    ('4.', 'VOLUME', '≥ 1.5× the\n20-bar average\n(Rel Vol >1.5)', ORANGE, 'CONFIRMING'),
    ('5.', 'FLOAT', '< 20M shares\n$0.10–$15\nNASDAQ only', '#ff79c6', 'FILTER'),
    ('6.', 'CATALYST', 'Tier 1: FDA/merger\nTier 2: halt-resume\nTier 3: momentum', '#bd93f9', 'CONFIRMING'),
]

for i, (num, name, detail, color, weight) in enumerate(conditions):
    x = 0.01 + i * 0.163
    ax_rules.add_patch(FancyBboxPatch((x, 0.08), 0.15, 0.84,
        boxstyle='round,pad=0', facecolor=color+'1a', linewidth=1.5,
        edgecolor=color, transform=ax_rules.transAxes))
    ax_rules.text(x + 0.075, 0.85, num, ha='center', fontsize=14,
                  color=color, fontweight='bold', fontfamily='monospace',
                  transform=ax_rules.transAxes)
    ax_rules.text(x + 0.075, 0.70, name, ha='center', fontsize=8.5,
                  color='white', fontweight='bold', fontfamily='monospace',
                  transform=ax_rules.transAxes)
    ax_rules.text(x + 0.075, 0.40, detail, ha='center', fontsize=7.5,
                  color=LGRAY, fontfamily='monospace',
                  transform=ax_rules.transAxes)
    w_color = RED if weight == 'CRITICAL' else GRAY
    ax_rules.text(x + 0.075, 0.12, weight, ha='center', fontsize=7,
                  color=w_color, fontfamily='monospace', fontweight='bold',
                  transform=ax_rules.transAxes)

# ── footer ─────────────────────────────────────────────────────────────────────
fig.text(0.5, 0.025,
    'tradingbaby/training/  |  W118 "Curl if Flow" system  |  Paper trade 20+ times before going live',
    ha='center', fontsize=8, color='#333333', fontfamily='monospace')

# ── save ──────────────────────────────────────────────────────────────────────
out = '/home/user/tradingbaby/training/pattern_recognition_guide.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#0d1117')
print(f'Saved: {out}')
plt.close()
