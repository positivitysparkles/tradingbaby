"""
Card 14 — The Crowd Psychology Map
The chart translated into human emotion.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

OUT = os.path.join(os.path.dirname(__file__), 'card_14_crowd_psychology.png')

BG     = '#0d1117'
CARD   = '#161b22'
GREEN  = '#3fb950'
RED    = '#f85149'
YELLOW = '#FFD700'
BLUE   = '#58a6ff'
ORANGE = '#ffaa00'
PURPLE = '#bd93f9'
GRAY   = '#888888'
LGRAY  = '#cccccc'
WHITE  = '#ffffff'
TEAL   = '#00ff88'

fig = plt.figure(figsize=(11, 7), facecolor=BG)

# border
fig.add_artist(mpatches.FancyBboxPatch(
    (0.01, 0.01), 0.98, 0.98,
    boxstyle='round,pad=0.01', linewidth=2.5,
    edgecolor=PURPLE, facecolor='none',
    transform=fig.transFigure))

# card number
fig.text(0.97, 0.96, '14/14', ha='right', va='top', fontsize=9,
         color=PURPLE, fontfamily='monospace', alpha=0.7)

# title
fig.text(0.05, 0.93, 'THE CROWD PSYCHOLOGY MAP', ha='left', va='top',
         fontsize=18, fontweight='bold', color=WHITE, fontfamily='monospace')
fig.text(0.05, 0.865, 'You are not reading a chart. You are reading thousands of humans making emotional decisions simultaneously.',
         ha='left', fontsize=8.5, color=GRAY, fontfamily='monospace')

line = plt.Line2D([0.05, 0.95], [0.845, 0.845],
                  transform=fig.transFigure,
                  color=PURPLE, linewidth=1.5, alpha=0.6)
fig.add_artist(line)

# ── left column: the emotion map ──────────────────────────────────────────────
ax = fig.add_axes([0.03, 0.08, 0.56, 0.74], frameon=False)
ax.axis('off')

states = [
    # (indicator reading,         emotion word,    crowd story,                              color,  arrow)
    ('Stoch RSI K = 0-10',       'CAPITULATION',  'Every seller gave up.\nThe crowd is broken, exhausted.\nNo one left to sell.',                   TEAL,   True),
    ('K curls up from below 20', 'THE SHIFT',     'One quiet buyer stepped in.\nThe crowd starts to notice.\nPsychology tilting from fear to hope.', BLUE,   True),
    ('SHA candle turns GREEN',   'HOPE',          'Buyers are winning the\nminute-to-minute battle.\nCrowd mood flipping bullish.',                  GREEN,  True),
    ('Volume explodes 10x+',     'FRENZY',        'The whole city showed up.\nInstitutions, algos, retail — all\ncompeting at once. Fuel is here.',   ORANGE, True),
    ('Price holds above ZLSMA',  'BELIEF',        'Rational buyers keep defending\nthis exact level. They believe\nin the floor. Sellers can\'t break it.',YELLOW, True),
    ('W118 BUY fires',           'THE HELICOPTER','All systems green simultaneously.\nThis is the rescue. Act NOW.\nNo second-guessing. Get on.',      TEAL,   False),
    ('W118 SELL fires',          'PARTY IS OVER', 'Smart money leaving quietly.\nDon\'t be the last one holding.\nGet out WITH them, not after.',      RED,    False),
]

row_h = 0.127
for i, (indicator, emotion, story, color, has_arrow) in enumerate(states):
    y = 0.915 - i * row_h

    # emotion badge
    ax.add_patch(FancyBboxPatch((0.0, y-0.065), 0.22, 0.09,
        boxstyle='round,pad=0.01', facecolor=color+'22',
        edgecolor=color, linewidth=1.5, transform=ax.transAxes))
    ax.text(0.11, y-0.015, emotion, ha='center', fontsize=8.5,
            color=color, fontweight='bold', fontfamily='monospace',
            transform=ax.transAxes)

    # arrow between badge and indicator
    if has_arrow:
        ax.annotate('', xy=(0.255, y-0.015), xytext=(0.228, y-0.015),
                    arrowprops=dict(arrowstyle='->', color=color,
                                   lw=1.2, alpha=0.7),
                    xycoords='axes fraction', textcoords='axes fraction')

    # indicator text
    ax.text(0.265, y-0.005, indicator, fontsize=8.5, color=LGRAY,
            fontfamily='monospace', fontweight='bold', transform=ax.transAxes)
    ax.text(0.265, y-0.050, story, fontsize=7.2, color='#888888',
            fontfamily='monospace', transform=ax.transAxes)

# ── right column: the survival show parallel ──────────────────────────────────
ax2 = fig.add_axes([0.62, 0.08, 0.36, 0.74], frameon=False)
ax2.axis('off')

ax2.add_patch(FancyBboxPatch((0.0, 0.0), 1.0, 1.0,
    boxstyle='round,pad=0.01', facecolor='#1a1a2e',
    edgecolor='#333333', linewidth=1, transform=ax2.transAxes))

ax2.text(0.5, 0.95, 'YOUR SUPERPOWER:', ha='center', fontsize=10,
         color=PURPLE, fontweight='bold', fontfamily='monospace',
         transform=ax2.transAxes)
ax2.text(0.5, 0.885, 'You already watch humans\nmake emotional decisions\nunder extreme pressure.',
         ha='center', fontsize=8.5, color=LGRAY, fontfamily='monospace',
         transform=ax2.transAxes)

parallels = [
    ('Survivor in the wild',  'Retail trader at 9:30am',   ORANGE),
    ('Rescue almost spotted', 'K gets to 22, fades to 18', BLUE),
    ('Panic choice under stress','Chases stock up 40%',    RED),
    ('Follows strict protocol', 'Follows W118 rules',      GREEN),
    ('Helicopter appears',    'W118 BUY fires',            TEAL),
]

ax2.text(0.05, 0.73, 'I SHOULDN\'T BE ALIVE   =   CHART',
         fontsize=7.5, color='#555555', fontfamily='monospace',
         fontweight='bold', transform=ax2.transAxes)
ax2.axhline(y=0.70, color='#333333', linewidth=0.8,
            xmin=0.05, xmax=0.95)

for i, (show, trade, color) in enumerate(parallels):
    y = 0.655 - i * 0.135
    ax2.text(0.04, y,      show,  fontsize=7.5, color=color,
             fontfamily='monospace', transform=ax2.transAxes)
    ax2.text(0.04, y-0.06, trade, fontsize=7,   color=GRAY,
             fontfamily='monospace', transform=ax2.transAxes)
    if i < len(parallels)-1:
        ax2.axhline(y=y-0.075, color='#222222', linewidth=0.5,
                    xmin=0.03, xmax=0.97)

ax2.text(0.5, 0.04,
         '"Divine inspo" = your edge.\nWhen something feels wrong\nbefore the indicator confirms —\nthat feeling IS data. Trust it.',
         ha='center', fontsize=7.5, color=PURPLE, fontfamily='monospace',
         style='italic', transform=ax2.transAxes)

# footer
fig.text(0.05, 0.025, 'W118 CURL IF FLOW  |  tradingbaby/training/flashcards/',
         ha='left', fontsize=7, color='#333333', fontfamily='monospace')

plt.savefig(OUT, dpi=150, bbox_inches='tight', facecolor=BG)
print(f'Saved: {OUT}')
plt.close()
