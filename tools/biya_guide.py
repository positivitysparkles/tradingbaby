import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                gridspec_kw={'height_ratios': [2, 1]},
                                facecolor='#0d1117')
fig.subplots_adjust(hspace=0.08)

for ax in [ax1, ax2]:
    ax.set_facecolor('#0d1117')
    ax.tick_params(colors='#555555')
    for spine in ax.spines.values():
        spine.set_color('#222222')

# ── simulate BIYA price data ───────────────────────────────────────────────
np.random.seed(42)
n = 80

# premarket run + pullback + potential re-entry
price = np.concatenate([
    np.linspace(0.65, 0.67, 8),                          # flat start
    np.linspace(0.67, 1.20, 20) + np.random.randn(20)*0.01,  # the big run
    np.linspace(1.20, 1.05, 15) + np.random.randn(15)*0.01,  # pullback
    np.linspace(1.05, 0.98, 12) + np.random.randn(12)*0.005, # continuing down
    np.linspace(0.98, 1.00, 10) + np.random.randn(10)*0.005, # base forming
    np.linspace(1.00, 1.08, 8) + np.random.randn(8)*0.005,   # potential re-curl
    np.linspace(1.08, 1.14, 7),                           # re-entry run
])
price = price[:n]
t = np.arange(n)

# zlsma - smoothed trend
zlsma = np.convolve(price, np.ones(12)/12, mode='same')
zlsma[:6] = price[:6]

# candle colors
colors = []
for i in range(n):
    if i == 0:
        colors.append('#3fb950')
    else:
        colors.append('#3fb950' if price[i] >= price[i-1] else '#f85149')

# ── price panel ────────────────────────────────────────────────────────────
bar_w = 0.6
for i in t:
    h = max(abs(price[i] - (price[i-1] if i>0 else price[i])), 0.008)
    low = min(price[i], price[i-1] if i>0 else price[i])
    ax1.bar(i, h, bottom=low, width=bar_w, color=colors[i], alpha=0.9)

ax1.plot(t, zlsma, color='#FFD700', linewidth=2.5, label='ZLSMA-50 (yellow line)', zorder=5)
ax1.set_xlim(-1, n+1)
ax1.set_ylim(0.55, 1.35)
ax1.set_ylabel('Price', color='#888888', fontsize=10)
ax1.yaxis.label.set_color('#888888')

# current price line
ax1.axhline(y=1.07, color='#ff4444', linestyle='--', alpha=0.5, linewidth=1)
ax1.text(n-1, 1.075, 'NOW $1.07', color='#ff4444', fontsize=8, ha='right')

# ── ZONE LABELS on price chart ─────────────────────────────────────────────
def label_box(ax, x, y, text, color, fontsize=8.5):
    ax.annotate(text, xy=(x, y), fontsize=fontsize, color='white',
                fontfamily='monospace', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=color,
                          edgecolor='none', alpha=0.92))

# zone 1: the big run (already happened)
ax1.axvspan(8, 28, alpha=0.08, color='#3fb950')
label_box(ax1, 12, 1.25, '① THE RUN\nW118 BUY fired at ~$0.83\nStoch curled from near 0\n+42% move', '#1a4a2e', fontsize=8)

# zone 2: current pullback
ax1.axvspan(28, 55, alpha=0.08, color='#ffaa00')
label_box(ax1, 31, 0.88, '② NOW — PULLBACK\nPrice cooling off\nStoch falling: 50→20\nDO NOT ENTER', '#4a3a00', fontsize=8)

# zone 3: re-entry zone
ax1.axvspan(55, n, alpha=0.12, color='#58a6ff')
label_box(ax1, 57, 1.18, '③ RE-ENTRY ZONE\nWait for Stoch curl\nfrom below 20\nTHIS is next entry', '#0a2a4a', fontsize=8)

# zlsma support arrow
ax1.annotate('', xy=(50, zlsma[50]), xytext=(50, zlsma[50]+0.08),
             arrowprops=dict(arrowstyle='->', color='#FFD700', lw=1.5))
ax1.text(51, zlsma[50]+0.09, 'ZLSMA must stay\nBELOW price', color='#FFD700', fontsize=7.5, fontfamily='monospace')

ax1.set_title('BIYA — W118 RE-ENTRY GUIDE  |  What to watch & when to enter',
              color='white', fontsize=12, fontfamily='monospace', pad=10, loc='left')
ax1.legend(loc='upper left', facecolor='#161b22', edgecolor='#333333',
           labelcolor='white', fontsize=9)

# ── stoch panel ────────────────────────────────────────────────────────────
# simulate stoch K matching the price story
stoch_k = np.concatenate([
    np.linspace(30, 15, 8),
    np.linspace(15, 95, 20),
    np.linspace(95, 50, 15),
    np.linspace(50, 18, 12),
    np.linspace(18, 10, 10),
    np.linspace(10, 32, 8),
    np.linspace(32, 72, 7),
])
stoch_k = stoch_k[:n]
stoch_d = np.convolve(stoch_k, np.ones(3)/3, mode='same')

ax2.plot(t, stoch_k, color='#58a6ff', linewidth=1.8, label='K (blue)')
ax2.plot(t, stoch_d, color='#ff8c00', linewidth=1.5, label='D (orange)', linestyle='--')
ax2.axhline(y=20, color='#ffffff', linestyle='--', alpha=0.3, linewidth=1)
ax2.axhline(y=80, color='#ffffff', linestyle='--', alpha=0.2, linewidth=1)
ax2.fill_between(t, 0, 20, alpha=0.1, color='#3fb950')  # buy zone

ax2.set_xlim(-1, n+1)
ax2.set_ylim(-5, 105)
ax2.set_ylabel('Stoch', color='#888888', fontsize=10)
ax2.yaxis.label.set_color('#888888')

# zone shading matching price
ax2.axvspan(8, 28, alpha=0.08, color='#3fb950')
ax2.axvspan(28, 55, alpha=0.08, color='#ffaa00')
ax2.axvspan(55, n, alpha=0.12, color='#58a6ff')

# stoch annotations
ax2.text(1, 22, '← 20 LINE', color='#ffffff', fontsize=7, alpha=0.5, fontfamily='monospace')
ax2.text(1, 82, '← 80 LINE', color='#ffffff', fontsize=7, alpha=0.4, fontfamily='monospace')

label_box(ax2, 10, 75, 'K curled from ~10\nthrough 20\nBUY fired here ✓', '#1a4a2e', fontsize=7.5)

label_box(ax2, 29, 55, 'K=50 now\nSTILL FALLING\nwait...', '#4a3a00', fontsize=7.5)

label_box(ax2, 56, 55, 'K drops below 20\nthen CURLS UP ↑\nK crosses above D\n= ENTRY SIGNAL ✓', '#0a2a4a', fontsize=7.5)

# entry arrow
ax2.annotate('', xy=(63, stoch_k[63]), xytext=(63, stoch_k[63]-18),
             arrowprops=dict(arrowstyle='->', color='#00ff88', lw=2))
ax2.text(64, stoch_k[63]-20, 'ENTER HERE\nif all 5 checks pass', color='#00ff88',
         fontsize=8, fontweight='bold', fontfamily='monospace')

ax2.legend(loc='upper right', facecolor='#161b22', edgecolor='#333333',
           labelcolor='white', fontsize=9)

# ── re-entry checklist box ─────────────────────────────────────────────────
checks = [
    '☐  5m Stoch K < 20 and curling UP',
    '☐  K crosses ABOVE D',
    '☐  SHA candle is GREEN',
    '☐  Price above yellow ZLSMA line',
    '☐  Volume picking back up',
]
checklist_text = 'RE-ENTRY CHECKLIST:\n' + '\n'.join(checks)
fig.text(0.72, 0.08, checklist_text, fontsize=8.5, color='#cccccc',
         fontfamily='monospace',
         bbox=dict(boxstyle='round,pad=0.7', facecolor='#161b22',
                   edgecolor='#58a6ff', alpha=0.95))

exit_text = ('IF ENTERED:\n'
             'Stop:  -8%  → EXIT immediately\n'
             'T1:   +15%  → sell 1/3, move stop to entry\n'
             'T2:   +30%  → sell 1/3 more\n'
             'T3:   +60%  → trail 10% on rest')
fig.text(0.72, 0.41, exit_text, fontsize=8.5, color='#cccccc',
         fontfamily='monospace',
         bbox=dict(boxstyle='round,pad=0.7', facecolor='#161b22',
                   edgecolor='#f85149', alpha=0.95))

out = '/home/user/tradingbaby/tools/biya_guide.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#0d1117')
print(f'Saved: {out}')
plt.close()
