"""
W118 Curl if Flow — Flashcard Deck Generator
Saves 13 individual study cards to training/flashcards/
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

OUT = os.path.dirname(__file__)

# ── colour palette ─────────────────────────────────────────────────────────
BG     = '#0d1117'
CARD   = '#161b22'
CARD2  = '#1c2128'
GREEN  = '#3fb950'
RED    = '#f85149'
YELLOW = '#FFD700'
BLUE   = '#58a6ff'
ORANGE = '#ffaa00'
PURPLE = '#bd93f9'
PINK   = '#ff79c6'
GRAY   = '#888888'
LGRAY  = '#cccccc'
WHITE  = '#ffffff'

def new_card(title, card_num, total=13, accent=ORANGE):
    fig = plt.figure(figsize=(11, 7), facecolor=BG)
    # card border
    fig.add_artist(mpatches.FancyBboxPatch(
        (0.01, 0.01), 0.98, 0.98,
        boxstyle='round,pad=0.01', linewidth=2,
        edgecolor=accent, facecolor='none',
        transform=fig.transFigure))
    # card number badge
    fig.text(0.97, 0.96, f'{card_num:02d}/{total}',
             ha='right', va='top', fontsize=9, color=accent,
             fontfamily='monospace', alpha=0.7)
    # title
    fig.text(0.05, 0.93, title, ha='left', va='top',
             fontsize=18, fontweight='bold', color=WHITE,
             fontfamily='monospace')
    # separator line
    line = plt.Line2D([0.05, 0.95], [0.885, 0.885],
                      transform=fig.transFigure,
                      color=accent, linewidth=1.5, alpha=0.6)
    fig.add_artist(line)
    # system tag bottom
    fig.text(0.05, 0.025, 'W118 CURL IF FLOW  |  tradingbaby/training/flashcards/',
             ha='left', fontsize=7, color='#333333', fontfamily='monospace')
    return fig

def save(fig, name):
    path = os.path.join(OUT, name)
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print(f'  Saved: {name}')

def rounded_box(ax, x, y, w, h, color, alpha=0.15, edge_alpha=0.8, lw=1.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle='round,pad=0.01', linewidth=lw,
        facecolor=color, edgecolor=color,
        alpha=alpha, transform=ax.transAxes, clip_on=False))
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle='round,pad=0.01', linewidth=lw,
        facecolor='none', edgecolor=color,
        alpha=edge_alpha, transform=ax.transAxes, clip_on=False))

# ══════════════════════════════════════════════════════════════════════════════
# CARD 01 — 6 Entry Conditions
# ══════════════════════════════════════════════════════════════════════════════
def card_01():
    fig = new_card('THE 6 ENTRY CONDITIONS  —  ALL REQUIRED', 1, accent=GREEN)
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.axis('off')

    conditions = [
        ('1', 'STOCH RSI',   'K crosses UP through 20\nK must be ABOVE D',        BLUE,   'CRITICAL'),
        ('2', 'SHA CANDLE',  'Smoothed Heikin Ashi\ncandle is GREEN',              GREEN,  'CRITICAL'),
        ('3', 'ZLSMA-50',    'Price ABOVE yellow line\nNEVER trade below it',      YELLOW, 'CRITICAL'),
        ('4', 'VOLUME',      'Rel Vol > 1.5x the\n20-bar average',                 ORANGE, 'CONFIRMING'),
        ('5', 'FLOAT/PRICE', 'Float < 20M shares\n$0.10-$15, NASDAQ only',         PINK,   'FILTER'),
        ('6', 'CATALYST',    'T1: FDA/merger\nT2: halt-resume  T3: momentum',      PURPLE, 'CONFIRMING'),
    ]
    positions = [(0.04,0.42),(0.37,0.42),(0.70,0.42),(0.04,0.08),(0.37,0.08),(0.70,0.08)]

    for (num, name, detail, color, weight), (px, py) in zip(conditions, positions):
        rounded_box(ax, px, py, 0.29, 0.34, color, alpha=0.08, lw=2)
        ax.text(px+0.06, py+0.27, num, fontsize=22, color=color,
                fontweight='bold', fontfamily='monospace', transform=ax.transAxes)
        ax.text(px+0.145, py+0.265, name, fontsize=11, color=WHITE,
                fontweight='bold', fontfamily='monospace', transform=ax.transAxes)
        ax.text(px+0.015, py+0.13, detail, fontsize=9, color=LGRAY,
                fontfamily='monospace', transform=ax.transAxes)
        w_col = RED if weight == 'CRITICAL' else (ORANGE if weight == 'CONFIRMING' else GRAY)
        ax.text(px+0.145, py+0.025, weight, fontsize=7.5, color=w_col,
                fontfamily='monospace', fontweight='bold', ha='center',
                transform=ax.transAxes)

    ax.text(0.5, 0.81, 'If even ONE condition is missing  ->  DO NOT ENTER',
            ha='center', fontsize=11, color=RED, fontfamily='monospace',
            fontweight='bold', transform=ax.transAxes)
    save(fig, 'card_01_entry_conditions.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 02 — Stoch RSI
# ══════════════════════════════════════════════════════════════════════════════
def card_02():
    fig = new_card('STOCH RSI  —  THE TRIGGER INDICATOR', 2, accent=BLUE)
    ax = fig.add_axes([0.05, 0.12, 0.50, 0.70])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color('#333333')

    t = np.linspace(0, 4*np.pi, 120)
    k = 50 + 48*np.sin(t - 0.3)
    d = 50 + 44*np.sin(t - 0.8)
    k = np.clip(k, 0, 100)
    d = np.clip(d, 0, 100)

    ax.plot(k, color=BLUE, linewidth=2.5, label='K (blue)')
    ax.plot(d, color=ORANGE, linewidth=2, linestyle='--', label='D (orange)')
    ax.axhline(20, color=WHITE, linestyle='--', alpha=0.4, linewidth=1)
    ax.axhline(80, color=WHITE, linestyle='--', alpha=0.2, linewidth=1)
    ax.fill_between(range(120), 0, 20, alpha=0.15, color=GREEN)
    ax.fill_between(range(120), 80, 100, alpha=0.08, color=RED)

    # mark the cross-up-through-20 moments
    for i in range(1, len(k)):
        if k[i] >= 20 and k[i-1] < 20 and k[i] > d[i]:
            ax.axvline(i, color=GREEN, alpha=0.6, linewidth=1.5, linestyle=':')
            ax.annotate('BUY\nSIGNAL', xy=(i, 22), fontsize=7.5,
                        color=GREEN, fontfamily='monospace', fontweight='bold',
                        ha='center')

    ax.set_ylim(-5, 105)
    ax.set_xlim(0, 120)
    ax.set_ylabel('Stoch RSI', color=GRAY, fontsize=9)
    ax.tick_params(colors='#555555', labelsize=8)
    ax.text(2, 22, '20', color=WHITE, fontsize=8, alpha=0.5)
    ax.text(2, 82, '80', color=WHITE, fontsize=8, alpha=0.4)
    ax.legend(loc='upper right', facecolor=CARD, edgecolor='#333333',
              labelcolor=WHITE, fontsize=8)

    ax2 = fig.add_axes([0.60, 0.12, 0.36, 0.70], frameon=False)
    ax2.axis('off')

    rules = [
        (GREEN,  'K < 20',           'Oversold zone. Stock beaten\ndown. Getting ready.'),
        (GREEN,  'K crosses UP 20',  'THE TRIGGER. Entry signal\nfires HERE. K must > D.'),
        (ORANGE, 'K in 20-80',       'Mid-range. Can hold position\nbut not ideal entry.'),
        (RED,    'K > 80',           'Overbought. DO NOT enter.\nExpect pullback soon.'),
        (RED,    'K crosses DOWN 20','EXIT signal. Momentum gone.\nGet out immediately.'),
    ]
    for i, (color, trigger, desc) in enumerate(rules):
        y = 0.88 - i * 0.195
        rounded_box(ax2, 0.0, y-0.08, 0.97, 0.175, color, alpha=0.08, lw=1)
        ax2.text(0.04, y+0.04, trigger, fontsize=10, color=color,
                 fontweight='bold', fontfamily='monospace', transform=ax2.transAxes)
        ax2.text(0.04, y-0.05, desc, fontsize=8.5, color=LGRAY,
                 fontfamily='monospace', transform=ax2.transAxes)

    ax2.text(0.5, -0.04,
             'Settings: RSI=14, Stoch=14, K=3, D=3, Source=Close',
             ha='center', fontsize=8, color=BLUE, fontfamily='monospace',
             fontweight='bold', transform=ax2.transAxes)
    save(fig, 'card_02_stoch_rsi.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 03 — ZLSMA Golden Rule
# ══════════════════════════════════════════════════════════════════════════════
def card_03():
    fig = new_card('ZLSMA-50  —  THE GOLDEN RULE', 3, accent=YELLOW)
    ax = fig.add_axes([0.05, 0.12, 0.50, 0.70])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color('#333333')

    t = np.arange(80)
    zlsma = 1.0 + 0.003*t + 0.1*np.sin(t/15)
    # price above, then crosses below, then recovers
    price = zlsma.copy()
    price[:35]  += 0.05 + 0.03*np.random.randn(35)
    price[35:50] = zlsma[35:50] - 0.06 - 0.02*np.random.randn(15)
    price[50:]  += 0.04 + 0.02*np.random.randn(30)

    ax.plot(t, zlsma, color=YELLOW, linewidth=3, label='ZLSMA-50', zorder=5)
    ax.fill_between(t, zlsma, price,
                    where=(price >= zlsma), color=GREEN, alpha=0.2, label='ABOVE = trade zone')
    ax.fill_between(t, zlsma, price,
                    where=(price < zlsma), color=RED, alpha=0.3, label='BELOW = NO TRADE')

    # candle bars
    for i in range(1, 80):
        lo = min(price[i], price[i-1])
        hi = max(price[i], price[i-1])
        col = GREEN if price[i] >= price[i-1] else RED
        ax.bar(i, max(hi-lo, 0.008), bottom=lo, width=0.6, color=col, alpha=0.85)

    ax.axvspan(35, 50, alpha=0.1, color=RED)
    ax.text(38, ax.get_ylim()[0]+0.01, 'NO TRADE\nZONE', fontsize=7,
            color=RED, fontfamily='monospace', fontweight='bold', ha='center')

    ax.set_xlim(0, 80)
    ax.tick_params(colors='#555555', labelsize=8)
    ax.legend(loc='upper left', facecolor=CARD, edgecolor='#333333',
              labelcolor=WHITE, fontsize=8)

    ax2 = fig.add_axes([0.60, 0.12, 0.36, 0.70], frameon=False)
    ax2.axis('off')

    rules = [
        (GREEN,  'Price ABOVE ZLSMA', 'Trend is up. Entries valid.\nThis is the trade zone.'),
        (ORANGE, 'Price AT ZLSMA',    'Watch carefully. Could\nbounce or break.'),
        (RED,    'Price BELOW ZLSMA', 'NEVER TRADE.\nRule #3. No exceptions.'),
        (YELLOW, 'ZLSMA curving UP',  'Best entries here. Trend\naccelerating. Full size.'),
        (GRAY,   'ZLSMA curving DOWN','Avoid or tiny size.\nMomentum dying.'),
    ]
    for i, (color, rule, desc) in enumerate(rules):
        y = 0.88 - i * 0.195
        rounded_box(ax2, 0.0, y-0.08, 0.97, 0.175, color, alpha=0.08, lw=1)
        ax2.text(0.04, y+0.04, rule, fontsize=10, color=color,
                 fontweight='bold', fontfamily='monospace', transform=ax2.transAxes)
        ax2.text(0.04, y-0.05, desc, fontsize=8.5, color=LGRAY,
                 fontfamily='monospace', transform=ax2.transAxes)

    ax2.text(0.5, -0.04, 'Formula: 2xEMA(50) - EMA(EMA(50))  |  Color: YELLOW',
             ha='center', fontsize=8, color=YELLOW, fontfamily='monospace',
             transform=ax2.transAxes)
    save(fig, 'card_03_zlsma.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 04 — Pattern A: Fade
# ══════════════════════════════════════════════════════════════════════════════
def card_04():
    fig = new_card('PATTERN A  —  "FIRST RED DAY"  ->  AVOID', 4, accent=RED)
    ax = fig.add_axes([0.05, 0.14, 0.52, 0.68])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color('#333333')

    prices = [1.0,1.05,1.02,2.20,2.05,1.90,1.75,1.65,1.58,1.50,1.42,1.35,1.28,1.20,1.18,1.22]
    zlsma  = [1.0,1.02,1.04,1.10,1.20,1.28,1.33,1.35,1.36,1.36,1.35,1.33,1.30,1.28,1.26,1.24]
    t = np.arange(len(prices))
    cols = [GREEN if i==0 or prices[i]>=prices[i-1] else RED for i in range(len(prices))]

    for i in range(1, len(prices)):
        lo = min(prices[i], prices[i-1])
        hi = max(prices[i], prices[i-1])
        ax.bar(i, max(hi-lo,0.015), bottom=lo, width=0.6, color=cols[i], alpha=0.9)

    ax.plot(t, zlsma, color=YELLOW, linewidth=2.5, zorder=5)
    ax.axhline(zlsma[-1], color=YELLOW, linestyle=':', alpha=0.3)

    # annotate
    ax.annotate('Open spike\n(trap!)', xy=(3, 2.20), xytext=(5, 2.30),
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.5),
                fontsize=8, color=RED, fontfamily='monospace')
    ax.annotate('Closes BELOW\nZLSMA', xy=(13, 1.20), xytext=(9, 1.05),
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.5),
                fontsize=8, color=RED, fontfamily='monospace')
    ax.text(1, 1.38, 'ZLSMA', color=YELLOW, fontsize=8, fontfamily='monospace')
    ax.set_xlim(0, 16); ax.set_ylim(0.85, 2.55)
    ax.tick_params(colors='#555555', labelsize=8)
    ax.set_title('AVOID THIS PATTERN', color=RED, fontsize=9, fontfamily='monospace')

    ax2 = fig.add_axes([0.61, 0.14, 0.36, 0.68], frameon=False)
    ax2.axis('off')
    signs = [
        ('HOW TO SPOT IT:', ORANGE, True),
        ('Spikes hard at open', LGRAY, False),
        ('Fades ALL day, no recovery', LGRAY, False),
        ('Closes at or below ZLSMA', LGRAY, False),
        ('Volume dries up by noon', LGRAY, False),
        ('', WHITE, False),
        ('WHAT HAPPENS NEXT:', ORANGE, True),
        ('Tomorrow likely fades more', LGRAY, False),
        ('Bag holders sell the bounce', LGRAY, False),
        ('No W118 re-entry signal fires', LGRAY, False),
        ('', WHITE, False),
        ('RULE: DO NOT ENTER', RED, True),
        ('Not today. Not tomorrow.', RED, False),
        ('Wait for the NEXT ticker.', RED, False),
        ('', WHITE, False),
        ('Real example: ARTL May 26', GRAY, False),
        ('$2.40 open -> $1.36 AH (-43%)', GRAY, False),
    ]
    for i, (text, color, bold) in enumerate(signs):
        y = 0.96 - i * 0.060
        prefix = '  ' if not bold else ''
        ax2.text(0.02, y, prefix + text, fontsize=8.5 if not bold else 9,
                 color=color, fontfamily='monospace',
                 fontweight='bold' if bold else 'normal',
                 transform=ax2.transAxes)
    save(fig, 'card_04_pattern_a_fade.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 05 — Pattern B: Multi-Day Runner
# ══════════════════════════════════════════════════════════════════════════════
def card_05():
    fig = new_card('PATTERN B  —  "MULTI-DAY RUNNER"  ->  WATCH', 5, accent=ORANGE)
    ax = fig.add_axes([0.05, 0.14, 0.52, 0.68])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color('#333333')

    prices = [1.0,1.05,1.80,1.65,1.55,1.50,1.48,1.50,1.52,1.55,1.58,1.60,1.63,1.68,1.72,1.78]
    zlsma  = [1.0,1.02,1.10,1.22,1.30,1.35,1.37,1.38,1.39,1.40,1.41,1.43,1.45,1.47,1.49,1.52]
    t = np.arange(len(prices))
    cols = [GREEN if i==0 or prices[i]>=prices[i-1] else RED for i in range(len(prices))]

    ax.fill_between(t, zlsma, prices,
                    where=[p >= z for p,z in zip(prices,zlsma)],
                    color=GREEN, alpha=0.1)
    for i in range(1, len(prices)):
        lo = min(prices[i], prices[i-1])
        hi = max(prices[i], prices[i-1])
        ax.bar(i, max(hi-lo,0.015), bottom=lo, width=0.6, color=cols[i], alpha=0.9)

    ax.plot(t, zlsma, color=YELLOW, linewidth=2.5, zorder=5)
    ax.annotate('Day 1 spike', xy=(2,1.80), xytext=(0.5,1.92),
                arrowprops=dict(arrowstyle='->', color=ORANGE, lw=1.5),
                fontsize=8, color=ORANGE, fontfamily='monospace')
    ax.annotate('Holds ABOVE\nZLSMA all day', xy=(6,1.48), xytext=(2,1.30),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5),
                fontsize=8, color=GREEN, fontfamily='monospace')
    ax.annotate('Day 2 run\nstarts here', xy=(14,1.72), xytext=(11,1.85),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5),
                fontsize=8, color=GREEN, fontfamily='monospace')
    ax.text(1, 1.42, 'ZLSMA', color=YELLOW, fontsize=8, fontfamily='monospace')
    ax.set_xlim(0,16); ax.set_ylim(0.85, 2.10)
    ax.tick_params(colors='#555555', labelsize=8)
    ax.set_title('WATCH FOR RE-ENTRY', color=ORANGE, fontsize=9, fontfamily='monospace')

    ax2 = fig.add_axes([0.61, 0.14, 0.36, 0.68], frameon=False)
    ax2.axis('off')
    signs = [
        ('HOW TO SPOT IT:', ORANGE, True),
        ('Big spike day 1', LGRAY, False),
        ('Pullback but HOLDS above ZLSMA', LGRAY, False),
        ('Catalyst still live (real news)', LGRAY, False),
        ('Volume stays above average', LGRAY, False),
        ('', WHITE, False),
        ('WHAT HAPPENS NEXT:', ORANGE, True),
        ('Stoch RSI resets overnight', LGRAY, False),
        ('W118 BUY fires premarket day 2', LGRAY, False),
        ('Second run: 20-40% more gain', LGRAY, False),
        ('', WHITE, False),
        ('RULE: WAIT FOR RESET', ORANGE, True),
        ('Stoch RSI K must go below 20', ORANGE, False),
        ('Then curl back up -> ENTER', ORANGE, False),
        ('', WHITE, False),
        ('Real example: YMAT May 26', GRAY, False),
        ('+203% day 1. Set alert for day 2.', GRAY, False),
    ]
    for i, (text, color, bold) in enumerate(signs):
        y = 0.96 - i * 0.060
        ax2.text(0.02, y, ('  ' if not bold else '') + text,
                 fontsize=8.5 if not bold else 9,
                 color=color, fontfamily='monospace',
                 fontweight='bold' if bold else 'normal',
                 transform=ax2.transAxes)
    save(fig, 'card_05_pattern_b_runner.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 06 — Pattern C: Late Accumulation
# ══════════════════════════════════════════════════════════════════════════════
def card_06():
    fig = new_card('PATTERN C  —  "LATE ACCUMULATION"  ->  BEST SETUP', 6, accent=GREEN)
    ax = fig.add_axes([0.05, 0.14, 0.52, 0.68])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color('#333333')

    prices = [0.40,0.42,1.20,1.05,0.90,0.78,0.72,0.68,0.65,0.66,0.70,0.78,0.85,0.92,1.00,1.10]
    zlsma  = [0.40,0.42,0.50,0.58,0.64,0.67,0.68,0.68,0.67,0.67,0.68,0.69,0.71,0.74,0.77,0.81]
    t = np.arange(len(prices))
    cols = [GREEN if i==0 or prices[i]>=prices[i-1] else RED for i in range(len(prices))]

    for i in range(1, len(prices)):
        lo = min(prices[i], prices[i-1])
        hi = max(prices[i], prices[i-1])
        ax.bar(i, max(hi-lo,0.012), bottom=lo, width=0.6, color=cols[i], alpha=0.9)

    ax.plot(t, zlsma, color=YELLOW, linewidth=2.5, zorder=5)

    # BUY signal in afternoon
    ax.annotate('', xy=(9, 0.67), xytext=(9, 0.55),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=2.5))
    ax.text(8.2, 0.52, 'W118 BUY\nfires here', fontsize=7.5,
            color=GREEN, fontfamily='monospace', fontweight='bold')
    ax.annotate('Open spike\nfades all day', xy=(3,1.05), xytext=(0.5,1.18),
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.5),
                fontsize=8, color=RED, fontfamily='monospace')
    ax.annotate('AH/next day\ncontinues up', xy=(14,1.0), xytext=(11,1.12),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5),
                fontsize=8, color=GREEN, fontfamily='monospace')
    ax.text(1, 0.71, 'ZLSMA', color=YELLOW, fontsize=8, fontfamily='monospace')
    ax.set_xlim(0,16); ax.set_ylim(0.35, 1.38)
    ax.tick_params(colors='#555555', labelsize=8)
    ax.set_title('HIGHEST PROBABILITY SETUP', color=GREEN, fontsize=9, fontfamily='monospace')

    ax2 = fig.add_axes([0.61, 0.14, 0.36, 0.68], frameon=False)
    ax2.axis('off')
    signs = [
        ('HOW TO SPOT IT:', GREEN, True),
        ('Spikes -> sells all day', LGRAY, False),
        ('Stoch RSI K near 0 at close', LGRAY, False),
        ('W118 BUY fires late/after hours', LGRAY, False),
        ('Someone buying into weakness', LGRAY, False),
        ('', WHITE, False),
        ('WHY THIS IS THE BEST:', GREEN, True),
        ('Full Stoch RSI reset complete', LGRAY, False),
        ('Smart money accumulated low', LGRAY, False),
        ('Less competition from chasers', LGRAY, False),
        ('Cleaner risk/reward ratio', LGRAY, False),
        ('', WHITE, False),
        ('RULE: SET ALERT TONIGHT', GREEN, True),
        ('Watch premarket for BUY fire', GREEN, False),
        ('Enter within 2-3% of signal', GREEN, False),
        ('', WHITE, False),
        ('Real example: SNGX May 26', GRAY, False),
        ('K=7.85 at close. Ready to pop.', GRAY, False),
    ]
    for i, (text, color, bold) in enumerate(signs):
        y = 0.96 - i * 0.060
        ax2.text(0.02, y, ('  ' if not bold else '') + text,
                 fontsize=8.5 if not bold else 9,
                 color=color, fontfamily='monospace',
                 fontweight='bold' if bold else 'normal',
                 transform=ax2.transAxes)
    save(fig, 'card_06_pattern_c_accumulation.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 07 — Exit Rules
# ══════════════════════════════════════════════════════════════════════════════
def card_07():
    fig = new_card('EXIT RULES  —  KNOW BEFORE YOU ENTER', 7, accent=RED)
    ax = fig.add_axes([0.05, 0.10, 0.52, 0.72])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color('#333333')
    ax.axis('off')

    # price ladder visual
    entry = 1.00
    levels = [
        (entry * 0.92, 'STOP  -8%',   RED,    'EXIT ALL. No exceptions.\nNever move stop down.'),
        (entry,        'ENTRY $1.00', WHITE,  ''),
        (entry * 1.15, 'T1  +15%',    BLUE,   'Sell 1/3. Move stop to\nbreakeven. You cannot lose.'),
        (entry * 1.30, 'T2  +30%',    ORANGE, 'Sell another 1/3.\nTrail stop 10% on rest.'),
        (entry * 1.60, 'T3  +60%',    GREEN,  'Trail 10% on final 1/3.\nLet it run. Never rush T3.'),
    ]
    for price, label, color, note in levels:
        y = (price - 0.85) / 0.90
        ax.axhline(y, color=color, linewidth=2 if label != 'ENTRY $1.00' else 3,
                   linestyle='-' if label == 'ENTRY $1.00' else '--', alpha=0.8)
        ax.text(0.02, y + 0.02, label, fontsize=11, color=color,
                fontweight='bold', fontfamily='monospace', transform=ax.transAxes)
        if note:
            ax.text(0.02, y - 0.06, note, fontsize=8, color=GRAY,
                    fontfamily='monospace', transform=ax.transAxes)

    ax.set_xlim(0,1); ax.set_ylim(-0.05, 1.05)

    ax2 = fig.add_axes([0.61, 0.10, 0.36, 0.72], frameon=False)
    ax2.axis('off')
    extra_exits = [
        ('SHA EXIT:', RED,    'If SHA candle turns RED\nfor 2+ consecutive bars\n-> EXIT immediately'),
        ('ZLSMA EXIT:', YELLOW,'If price CLOSES below\nthe yellow ZLSMA line\n-> EXIT immediately'),
        ('STOCH EXIT:', BLUE,  'If Stoch RSI K crosses\nback DOWN through 20\n-> EXIT immediately'),
        ('TIME EXIT:', GRAY,   'After 10:30am ET\nif not at T1 yet\n-> consider exiting'),
    ]
    for i, (label, color, desc) in enumerate(extra_exits):
        y = 0.90 - i * 0.245
        rounded_box(ax2, 0.0, y-0.14, 0.97, 0.22, color, alpha=0.08, lw=1)
        ax2.text(0.04, y+0.04, label, fontsize=10, color=color,
                 fontweight='bold', fontfamily='monospace', transform=ax2.transAxes)
        ax2.text(0.04, y-0.10, desc, fontsize=8, color=LGRAY,
                 fontfamily='monospace', transform=ax2.transAxes)
    save(fig, 'card_07_exit_rules.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 08 — The Stop Loss Rule
# ══════════════════════════════════════════════════════════════════════════════
def card_08():
    fig = new_card('THE STOP LOSS  —  YOUR ONLY PROTECTION', 8, accent=RED)
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.axis('off')

    ax.text(0.5, 0.75, '-8%', ha='center', fontsize=72, color=RED,
            fontweight='bold', fontfamily='monospace', transform=ax.transAxes)
    ax.text(0.5, 0.66, 'HARD STOP. NON-NEGOTIABLE. NO EXCEPTIONS.',
            ha='center', fontsize=13, color=RED, fontfamily='monospace',
            fontweight='bold', transform=ax.transAxes)

    cols_data = [
        ('Without stop:', [
            'Hope trade becomes -15%',
            '-15% becomes -30%',
            '-30% wipes weeks of gains',
            'You sell in panic at the bottom',
            'Stock bounces without you'
        ], RED),
        ('With stop:', [
            'Loss capped at -8% always',
            'Capital protected for next trade',
            '3 more trades to recover',
            'You stay in the game',
            'Next W118 signal = new chance'
        ], GREEN),
    ]
    for j, (title, items, color) in enumerate(cols_data):
        x = 0.08 + j * 0.50
        rounded_box(ax, x, 0.13, 0.40, 0.48, color, alpha=0.06, lw=2)
        ax.text(x + 0.20, 0.58, title, ha='center', fontsize=12,
                color=color, fontweight='bold', fontfamily='monospace',
                transform=ax.transAxes)
        for i, item in enumerate(items):
            ax.text(x + 0.03, 0.50 - i*0.08, ('X  ' if color==RED else 'OK ') + item,
                    fontsize=9, color=LGRAY, fontfamily='monospace',
                    transform=ax.transAxes)

    ax.text(0.5, 0.07,
            'Set your stop BEFORE you enter. If you cannot set a stop, do not trade.',
            ha='center', fontsize=10, color=ORANGE, fontfamily='monospace',
            fontweight='bold', transform=ax.transAxes)
    save(fig, 'card_08_stop_loss.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 09 — Re-Entry Rule
# ══════════════════════════════════════════════════════════════════════════════
def card_09():
    fig = new_card('RE-ENTRY RULE  —  PATIENCE IS THE EDGE', 9, accent=BLUE)
    ax = fig.add_axes([0.05, 0.13, 0.52, 0.70])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color('#333333')

    # stoch RSI showing full reset and curl
    k_full = [85,80,72,60,48,35,22,14,8,4,2,1,3,8,15,22,30,42,55,68,78,88,95]
    d_full = [82,78,72,64,55,44,34,25,17,11,7,4,3,5,9,15,22,32,44,57,68,78,87]
    t = np.arange(len(k_full))

    ax.plot(t, k_full, color=BLUE, linewidth=2.5, label='K')
    ax.plot(t, d_full, color=ORANGE, linewidth=2, linestyle='--', label='D')
    ax.axhline(20, color=WHITE, linestyle='--', alpha=0.4, linewidth=1.5)
    ax.fill_between(t, 0, 20, alpha=0.15, color=GREEN)

    # mark full reset
    ax.axvspan(10, 14, alpha=0.15, color=GREEN)
    ax.annotate('FULL RESET\nK near 0', xy=(11, 2), xytext=(3, 25),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5),
                fontsize=8, color=GREEN, fontfamily='monospace', fontweight='bold')

    # mark the entry
    entry_x = 15
    ax.axvline(entry_x, color=GREEN, linewidth=2, linestyle=':')
    ax.annotate('ENTRY\nK crosses 20\nK > D', xy=(entry_x, 22),
                xytext=(entry_x+2, 45),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=2),
                fontsize=8.5, color=GREEN, fontfamily='monospace', fontweight='bold')

    # mark WRONG entry (mid-range)
    ax.axvspan(5, 8, alpha=0.12, color=RED)
    ax.text(5.5, 55, 'WRONG\nnot reset\nenough', fontsize=7,
            color=RED, fontfamily='monospace', fontweight='bold', ha='center')

    ax.set_ylim(-5, 105)
    ax.set_xlim(0, len(k_full))
    ax.text(0.5, 22, '20 LINE', color=WHITE, fontsize=8, alpha=0.5)
    ax.legend(loc='upper right', facecolor=CARD, edgecolor='#333333',
              labelcolor=WHITE, fontsize=9)
    ax.tick_params(colors='#555555', labelsize=8)
    ax.set_title('5m STOCH RSI — FULL RESET REQUIRED', color=BLUE,
                 fontsize=9, fontfamily='monospace')

    ax2 = fig.add_axes([0.61, 0.13, 0.36, 0.70], frameon=False)
    ax2.axis('off')
    rules = [
        ('THE RE-ENTRY RULE:', BLUE, True),
        ('Stoch RSI K must drop', LGRAY, False),
        ('FULLY BELOW 20 first.', LGRAY, False),
        ('Not "near" 20. BELOW 20.', LGRAY, False),
        ('', WHITE, False),
        ('THEN wait for:', BLUE, True),
        ('K curls up from below 20', LGRAY, False),
        ('K crosses ABOVE D line', LGRAY, False),
        ('SHA candle turns GREEN', LGRAY, False),
        ('Price still above ZLSMA', LGRAY, False),
        ('', WHITE, False),
        ('WRONG re-entries:', RED, True),
        ('K at 30, "looks low enough"', RED, False),
        ('K at 25, "close to 20"', RED, False),
        ('Bouncing mid-range (50s)', RED, False),
        ('', WHITE, False),
        ('35% of W118 trades are', GRAY, False),
        ('re-entries. Patience pays.', GRAY, False),
    ]
    for i, (text, color, bold) in enumerate(rules):
        y = 0.96 - i * 0.058
        ax2.text(0.02, y, ('  ' if not bold else '') + text,
                 fontsize=8.5 if not bold else 9.5,
                 color=color, fontfamily='monospace',
                 fontweight='bold' if bold else 'normal',
                 transform=ax2.transAxes)
    save(fig, 'card_09_reentry_rule.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 10 — Session Times
# ══════════════════════════════════════════════════════════════════════════════
def card_10():
    fig = new_card('SESSION TIMES  —  WHEN TO TRADE / AVOID', 10, accent=ORANGE)
    ax = fig.add_axes([0.05, 0.30, 0.90, 0.52])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color('#333333')
    ax.axis('off')

    sessions = [
        (4,   9.5,  GREEN,   'PREMARKET\n4am-9:30am ET\n(2am-7:30am MT)',   'HIGHEST PRIORITY\n56% of W118 wins here\nBest setups fire here'),
        (9.5, 10.5, GREEN,   'OPEN\n9:30-10:30am ET\n(7:30-8:30am MT)',     'HIGH PRIORITY\nVolatile but valid\nWatch size at open'),
        (10.5,15,   RED,     'MIDDAY CHOP\n10:30am-3pm ET\n(8:30am-1pm MT)','AVOID\nChop kills momentum\nFake signals everywhere'),
        (15,  16,   ORANGE,  'POWER HOUR\n3-4pm ET\n(1-2pm MT)',             'SMALL SIZE ONLY\nEnd-of-day moves\nHalf normal position'),
    ]
    total_hours = 12
    for start, end, color, label, note in sessions:
        x0 = (start - 4) / total_hours
        w  = (end - start) / total_hours
        ax.add_patch(FancyBboxPatch((x0, 0.40), w-0.005, 0.45,
            boxstyle='round,pad=0.005', facecolor=color, alpha=0.25,
            edgecolor=color, linewidth=2, transform=ax.transAxes))
        cx = x0 + w/2
        parts = label.split('\n')
        ax.text(cx, 0.82, parts[0], ha='center', fontsize=9, color=color,
                fontweight='bold', fontfamily='monospace', transform=ax.transAxes)
        for k, part in enumerate(parts[1:]):
            ax.text(cx, 0.70 - k*0.12, part, ha='center', fontsize=7.5,
                    color=LGRAY, fontfamily='monospace', transform=ax.transAxes)
        for k, nline in enumerate(note.split('\n')):
            ax.text(cx, 0.32 - k*0.11, nline, ha='center', fontsize=7.5,
                    color=color, fontfamily='monospace', transform=ax.transAxes)

    hour_labels = ['4am','5am','6am','7am','8am','9am','10am','11am','12pm','1pm','2pm','3pm','4pm']
    for i, lbl in enumerate(hour_labels):
        x = i / total_hours
        ax.axvline(x, color='#333333', linewidth=0.8, alpha=0.5)
        ax.text(x, 0.04, lbl, fontsize=7, color=GRAY, ha='center',
                fontfamily='monospace', transform=ax.transAxes)

    ax_mt = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax_mt.axis('off')
    ax_mt.text(0.5, 0.22,
        'MOUNTAIN TIME (MT):  2am-7:30am = prime  |  7:30-8:30am = valid  |  8:30am-1pm = AVOID  |  1-2pm = caution',
        ha='center', fontsize=9, color=GRAY, fontfamily='monospace',
        transform=ax_mt.transAxes)
    ax_mt.text(0.5, 0.14,
        'W118 time gate is OFF by default — signals fire anytime. YOU must apply the time filter manually.',
        ha='center', fontsize=9, color=ORANGE, fontfamily='monospace',
        fontweight='bold', transform=ax_mt.transAxes)
    save(fig, 'card_10_session_times.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 11 — Don't Chase
# ══════════════════════════════════════════════════════════════════════════════
def card_11():
    fig = new_card('THE #1 MISTAKE  —  DO NOT CHASE', 11, accent=RED)
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.axis('off')

    # Wrong entry
    rounded_box(ax, 0.04, 0.14, 0.43, 0.68, RED, alpha=0.06, lw=2)
    ax.text(0.25, 0.79, 'WRONG  X', ha='center', fontsize=14, color=RED,
            fontweight='bold', fontfamily='monospace', transform=ax.transAxes)
    wrong = [
        ('W118 BUY fires at:',  '$1.37', WHITE),
        ('You see it, excited:', '', WHITE),
        ('You enter at:',       '$1.79  (+30% above!)', RED),
        ('Your stop (-8%):',    '$1.65', RED),
        ('Risk to stop:',       '-$0.14/share', RED),
        ('Reality:',            'Any normal pullback', RED),
        ('',                    'hits your stop.', RED),
        ('Outcome:',            'Stopped out -8%', RED),
        ('',                    'on a stock that', RED),
        ('',                    'eventually went up.', RED),
    ]
    for i, (label, value, color) in enumerate(wrong):
        y = 0.70 - i * 0.057
        ax.text(0.06, y, label, fontsize=8.5, color=GRAY,
                fontfamily='monospace', transform=ax.transAxes)
        ax.text(0.28, y, value, fontsize=8.5, color=color,
                fontfamily='monospace', fontweight='bold', transform=ax.transAxes)

    # Right entry
    rounded_box(ax, 0.53, 0.14, 0.43, 0.68, GREEN, alpha=0.06, lw=2)
    ax.text(0.745, 0.79, 'RIGHT  OK', ha='center', fontsize=14, color=GREEN,
            fontweight='bold', fontfamily='monospace', transform=ax.transAxes)
    right = [
        ('W118 BUY fires at:',  '$1.37', WHITE),
        ('You enter at:',       '$1.37-1.40', GREEN),
        ('Within signal by:',   '< 2%', GREEN),
        ('Your stop (-8%):',    '$1.26', GREEN),
        ('Risk to stop:',       '-$0.11/share', GREEN),
        ('T1 target (+15%):',   '$1.58', GREEN),
        ('T2 target (+30%):',   '$1.78', GREEN),
        ('Risk/reward:',        '1 : 3+', GREEN),
        ('Outcome:',            'Clean trade with', GREEN),
        ('',                    'full system edge.', GREEN),
    ]
    for i, (label, value, color) in enumerate(right):
        y = 0.70 - i * 0.057
        ax.text(0.55, y, label, fontsize=8.5, color=GRAY,
                fontfamily='monospace', transform=ax.transAxes)
        ax.text(0.77, y, value, fontsize=8.5, color=color,
                fontfamily='monospace', fontweight='bold', transform=ax.transAxes)

    ax.text(0.5, 0.07,
            'RULE: If price is more than 3% above the BUY signal -> SKIP IT. Wait for next reset.',
            ha='center', fontsize=10, color=ORANGE, fontfamily='monospace',
            fontweight='bold', transform=ax.transAxes)
    save(fig, 'card_11_dont_chase.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 12 — Relative Volume
# ══════════════════════════════════════════════════════════════════════════════
def card_12():
    fig = new_card('RELATIVE VOLUME  —  THE FUEL GAUGE', 12, accent=BLUE)
    ax = fig.add_axes([0.05, 0.14, 0.45, 0.72])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_color('#333333')

    levels = [1.2, 3, 8, 25, 70]
    colors = [RED, '#888888', ORANGE, GREEN, '#00ff88']
    labels = ['1.2x', '3x', '8x', '25x', '70x']

    bars = ax.barh(range(5), levels, color=colors, alpha=0.8, height=0.6)
    ax.set_xlim(0, 80)
    ax.set_yticks(range(5))
    ax.set_yticklabels(labels, fontsize=11, fontfamily='monospace', color=WHITE)
    ax.tick_params(colors='#555555', labelsize=9)
    ax.set_xlabel('Relative Volume (x normal)', color=GRAY, fontsize=9)
    for i, (bar, color) in enumerate(zip(bars, colors)):
        ax.text(levels[i] + 1, i, ['SKIP','WEAK','WATCH','HOT','EXTREME'][i],
                va='center', fontsize=10, color=color,
                fontweight='bold', fontfamily='monospace')
    ax.axvline(1.5, color=ORANGE, linestyle='--', linewidth=1.5, alpha=0.7)
    ax.text(1.6, 4.5, 'W118\nmin 1.5x', color=ORANGE, fontsize=7.5,
            fontfamily='monospace')

    ax2 = fig.add_axes([0.55, 0.14, 0.41, 0.72], frameon=False)
    ax2.axis('off')
    data = [
        ('> 50x', '#00ff88', 'EXTREME',
         'Algo/institution buying.\nHigh conviction move.\nExpect big range today.'),
        ('10-50x', GREEN, 'HOT',
         'Strong retail + momentum.\nIdeal W118 zone.\nSet alerts immediately.'),
        ('3-10x', ORANGE, 'WARM',
         'Worth watching.\nSet W118 alert.\nWait for clean signal.'),
        ('1.5-3x', GRAY, 'MINIMUM',
         'Barely qualifies.\nW118 requires >1.5x.\nSmaller size if entering.'),
        ('< 1.5x', RED, 'SKIP',
         'Not enough fuel.\nMomentum move unlikely.\nMove on to next ticker.'),
    ]
    for i, (level, color, label, desc) in enumerate(data):
        y = 0.92 - i * 0.20
        rounded_box(ax2, 0.0, y-0.10, 0.97, 0.18, color, alpha=0.08, lw=1)
        ax2.text(0.05, y+0.02, f'{level}  —  {label}', fontsize=9.5,
                 color=color, fontweight='bold', fontfamily='monospace',
                 transform=ax2.transAxes)
        ax2.text(0.05, y-0.07, desc, fontsize=7.5, color=LGRAY,
                 fontfamily='monospace', transform=ax2.transAxes)
    save(fig, 'card_12_relative_volume.png')

# ══════════════════════════════════════════════════════════════════════════════
# CARD 13 — THE A+ SETUP
# ══════════════════════════════════════════════════════════════════════════════
def card_13():
    fig = new_card('THE A+ SETUP  —  THE TRADE OF THE DAY', 13, accent='#00ff88')
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.axis('off')

    ax.text(0.5, 0.83,
            'When ALL of these align simultaneously -> FULL SIZE. MAX CONVICTION.',
            ha='center', fontsize=11, color=LGRAY, fontfamily='monospace',
            transform=ax.transAxes)

    checks = [
        ('#1', 'STOCH RSI K came from BELOW 10 (not just 20 — truly oversold)',    '#00ff88'),
        ('#2', 'K crosses 20 cleanly AND K is well above D (big spread)',           '#00ff88'),
        ('#3', 'SHA candle is GREEN and GROWING in size',                           '#00ff88'),
        ('#4', 'Price is ABOVE ZLSMA and ZLSMA is CURVING UP',                     YELLOW),
        ('#5', 'Volume is 10x+ normal (not just 1.5x — truly explosive)',           '#00ff88'),
        ('#6', 'Tier 1 catalyst: FDA approval / merger / halt-resume',              '#00ff88'),
        ('#7', 'Time is 4am-10am ET (premarket or early open)',                     BLUE),
        ('#8', 'Float is under 10M (not just 20M — truly tiny)',                   PINK),
        ('#9', 'Signal fires on BOTH 1m AND 5m charts simultaneously',             ORANGE),
    ]

    for i, (num, text, color) in enumerate(checks):
        col = i % 3
        row = i // 3
        x = 0.04 + col * 0.33
        y = 0.66 - row * 0.165
        rounded_box(ax, x, y-0.08, 0.30, 0.14, color, alpha=0.10, lw=1.5)
        ax.text(x+0.02, y+0.01, num, fontsize=10, color=color,
                fontweight='bold', fontfamily='monospace', transform=ax.transAxes)
        ax.text(x+0.07, y+0.01, text[:38], fontsize=7.5, color=LGRAY,
                fontfamily='monospace', transform=ax.transAxes)
        if len(text) > 38:
            ax.text(x+0.07, y-0.05, text[38:], fontsize=7.5, color=LGRAY,
                    fontfamily='monospace', transform=ax.transAxes)

    ax.text(0.5, 0.195,
            'A+ SETUP = position size 90% of account  |  hold through T1, T2, aim for T3',
            ha='center', fontsize=10, color='#00ff88', fontfamily='monospace',
            fontweight='bold', transform=ax.transAxes)

    ax.text(0.5, 0.135,
            'These happen 2-5 times per WEEK in W118\'s universe.',
            ha='center', fontsize=10, color=LGRAY, fontfamily='monospace',
            transform=ax.transAxes)

    ax.text(0.5, 0.075,
            'Historical A+ setup win rate: ~98%  |  Avg gain: +53%  |  Best: UGRO +692%',
            ha='center', fontsize=10, color=ORANGE, fontfamily='monospace',
            fontweight='bold', transform=ax.transAxes)

    # glow border for this special card
    for alpha, lw in [(0.15, 8), (0.25, 4), (0.5, 2)]:
        fig.add_artist(mpatches.FancyBboxPatch(
            (0.01, 0.01), 0.98, 0.98,
            boxstyle='round,pad=0.01', linewidth=lw,
            edgecolor='#00ff88', facecolor='none',
            alpha=alpha, transform=fig.transFigure))

    save(fig, 'card_13_aplus_setup.png')

# ══════════════════════════════════════════════════════════════════════════════
# RUN ALL
# ══════════════════════════════════════════════════════════════════════════════
print('Generating W118 flashcard deck...')
card_01(); card_02(); card_03(); card_04(); card_05(); card_06(); card_07()
card_08(); card_09(); card_10(); card_11(); card_12(); card_13()
print('Done! 13 cards saved to training/flashcards/')
