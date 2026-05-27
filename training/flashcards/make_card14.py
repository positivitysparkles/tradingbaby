"""
Card 14 — The Crowd Psychology Map (v2 - clean layout)
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np, os

OUT = os.path.join(os.path.dirname(__file__), 'card_14_crowd_psychology.png')

BG=('#0d1117'); CARD=('#161b22'); GREEN=('#3fb950'); RED=('#f85149')
YELLOW=('#FFD700'); BLUE=('#58a6ff'); ORANGE=('#ffaa00')
PURPLE=('#bd93f9'); GRAY=('#888888'); LGRAY=('#cccccc')
WHITE=('#ffffff'); TEAL=('#00ff88')

fig = plt.figure(figsize=(13, 8), facecolor=BG)

fig.add_artist(mpatches.FancyBboxPatch(
    (0.01,0.01),0.98,0.98, boxstyle='round,pad=0.01',
    linewidth=2.5, edgecolor=PURPLE, facecolor='none',
    transform=fig.transFigure))

fig.text(0.97,0.96,'14/14',ha='right',va='top',fontsize=9,
         color=PURPLE,fontfamily='monospace',alpha=0.7)
fig.text(0.05,0.93,'THE CROWD PSYCHOLOGY MAP',ha='left',va='top',
         fontsize=19,fontweight='bold',color=WHITE,fontfamily='monospace')
fig.text(0.05,0.875,
         'You are not reading a chart — you are reading thousands of humans making emotional decisions.',
         ha='left',fontsize=9,color=GRAY,fontfamily='monospace')

fig.add_artist(plt.Line2D([0.05,0.95],[0.855,0.855],
    transform=fig.transFigure, color=PURPLE,linewidth=1.5,alpha=0.5))

# ── LEFT: emotion ladder ───────────────────────────────────────────────────────
states = [
    ('Stoch RSI  K = 0-10',       'CAPITULATION',    'Last sellers gave up. Nobody left to sell.',     TEAL),
    ('K curls UP through 20',     'THE SHIFT',       'One quiet buyer stepped in. Crowd notices.',     BLUE),
    ('SHA candle turns GREEN',    'HOPE',            'Buyers winning the minute-to-minute battle.',    GREEN),
    ('Volume explodes 10x+',      'FRENZY',          'The whole city showed up. Fuel is here.',        ORANGE),
    ('Price holds above ZLSMA',   'BELIEF',          'Rational buyers defending the floor.',           YELLOW),
    ('W118 BUY label fires',      'THE HELICOPTER',  'All systems green. Act NOW. No hesitation.',     TEAL),
    ('W118 SELL label fires',     'PARTY IS OVER',   'Smart money leaving. Get out WITH them.',        RED),
]

top = 0.80; row = 0.103
for i,(indicator, emotion, story, color) in enumerate(states):
    y = top - i*row

    # colored pill
    ax_pill = fig.add_axes([0.05, y-0.025, 0.18, 0.068], frameon=False)
    ax_pill.set_facecolor(color+'22')
    for sp in ax_pill.spines.values():
        sp.set_color(color); sp.set_linewidth(1.5)
    ax_pill.axis('off')
    ax_pill.text(0.5,0.5, emotion, ha='center',va='center',
                 fontsize=9, color=color, fontweight='bold',
                 fontfamily='monospace', transform=ax_pill.transAxes)

    # arrow + text to the right
    fig.text(0.245, y+0.022, '->  ' + indicator,
             fontsize=9, color=LGRAY, fontfamily='monospace',
             fontweight='bold', va='top')
    fig.text(0.245, y-0.008, '     ' + story,
             fontsize=8, color=GRAY, fontfamily='monospace', va='top')

# ── RIGHT: survival show parallel ─────────────────────────────────────────────
rx = 0.665
fig.add_artist(mpatches.FancyBboxPatch(
    (rx,0.08),0.305,0.755, boxstyle='round,pad=0.01',
    linewidth=1, edgecolor='#333333', facecolor='#161b22',
    transform=fig.transFigure))

fig.text(rx+0.152, 0.805, 'YOUR SUPERPOWER', ha='center',
         fontsize=10, color=PURPLE, fontweight='bold',
         fontfamily='monospace')

fig.text(rx+0.015, 0.768,
         'You watch humans make emotional\n'
         'decisions under extreme pressure.\n'
         'Trading IS that same show.',
         fontsize=8.5, color=LGRAY, fontfamily='monospace')

fig.text(rx+0.015, 0.680,
         'I SHOULDN\'T BE ALIVE  =  YOUR CHART',
         fontsize=8, color='#555555', fontweight='bold',
         fontfamily='monospace')

parallels = [
    ('Survivor panics, bad choice',  'Retail chases +40% move',      RED),
    ('Rescue almost spotted, miss',  'K=22 then fades — no entry',   BLUE),
    ('Follows strict protocol',      'Follows W118 6 rules',         GREEN),
    ('Helicopter appears',           'W118 BUY fires — GET ON',      TEAL),
    ('"One more try" loop',          '"Maybe it\'ll come back" loop', ORANGE),
]

py = 0.650
for show, trade, color in parallels:
    fig.text(rx+0.015, py,      '> ' + show,  fontsize=8,   color=color,
             fontfamily='monospace', fontweight='bold')
    fig.text(rx+0.015, py-0.030,'  ' + trade, fontsize=7.5, color=GRAY,
             fontfamily='monospace')
    py -= 0.082

fig.text(rx+0.152, 0.115,
         '"Divine inspo" = real data.\n'
         'When something feels wrong\n'
         'before the indicator confirms —\n'
         'THAT FEELING IS YOUR EDGE.',
         ha='center', fontsize=8, color=PURPLE,
         fontfamily='monospace', style='italic')

fig.text(0.05,0.025,
         'W118 CURL IF FLOW  |  tradingbaby/training/flashcards/',
         ha='left',fontsize=7,color='#333333',fontfamily='monospace')

plt.savefig(OUT,dpi=150,bbox_inches='tight',facecolor=BG)
print(f'Saved: {OUT}')
plt.close()
