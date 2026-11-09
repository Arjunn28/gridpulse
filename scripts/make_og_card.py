"""Draw docs/figures/og-card.png (1200 x 630), the link preview image for the project page.

Run from the repo root: python scripts/make_og_card.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

OUT = Path(__file__).resolve().parents[1] / "docs" / "figures" / "og-card.png"
NAVY, BLUE, ORANGE = "#0f1b2d", "#4d94e8", "#f0793f"
plt.rcParams["font.family"] = ["Arial", "Helvetica", "DejaVu Sans"]

fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=NAVY)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1200); ax.set_ylim(630, 0); ax.axis("off")

# faint grid
for x in range(0, 1201, 40):
    ax.plot([x, x], [0, 630], color="white", alpha=0.045, lw=0.8)
for y in range(0, 631, 40):
    ax.plot([0, 1200], [y, y], color="white", alpha=0.045, lw=0.8)

# faint load curve: a daily wave on a rising floor
x = np.linspace(0, 1200, 400)
y = 318 - 0.05 * x - 22 * np.sin(x / 1200 * 2 * np.pi * 7) - 10 * np.sin(x / 1200 * 2 * np.pi * 21)
ax.plot(x, y, color=BLUE, alpha=0.2, lw=2)

ax.text(60, 62, "GRIDPULSE", color=BLUE, fontsize=13, fontweight="bold", va="center")
ax.text(60, 128, "Has AI data center growth made Texas\nelectricity harder to predict?", color="white",
        fontsize=31, fontweight="bold", va="center", linespacing=1.18)
ax.text(60, 250, "Not for demand. But a shrinking share of Texas\ndemand follows the weather.", color="#c3cbd8",
        fontsize=17.5, va="center", linespacing=1.4)

stats = [("About 3%", "Demand forecast error in every year", BLUE),
         ("0.65 to 0.21", "Far West weather R2, 2019 to 2025", ORANGE),
         ("-0.70 points", "Cooling response, 95% CI -0.96 to -0.45", BLUE)]
for i, (big, small, col) in enumerate(stats):
    x0 = 60 + i * 370
    ax.add_patch(Rectangle((x0, 360), 340, 150, facecolor="white", alpha=0.07, lw=0))
    ax.add_patch(Rectangle((x0, 360), 340, 5, facecolor=col, lw=0))
    ax.text(x0 + 24, 424, big, color="white", fontsize=25, fontweight="bold", va="center")
    ax.text(x0 + 24, 472, small, color="#aeb8c8", fontsize=11.5, va="center")

ax.text(60, 578, "Arjun Abbimutt Nagendra Kumar", color="#c3cbd8", fontsize=13, va="center")
ax.text(1140, 578, "arjunn28.github.io/gridpulse", color="#7f8da3", fontsize=12, va="center", ha="right")

fig.savefig(OUT, dpi=100, facecolor=NAVY)
print("wrote", OUT)
