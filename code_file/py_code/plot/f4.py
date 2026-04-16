#%% ---------------------------------------------------------------------------------------
# ------------------------Import packages----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import gaussian_kde

from code_file.py_code.py_config import s1_result, figures_loc

# Unified paper style: use your refined econ_pub_plot
from code_file.py_code.plot.tool_box import (
    set_econ_pub_style,
    new_figure,
    format_axes,
    add_vertical_line,
)





#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
s1_loc = s1_result()
figure_loc = figures_loc()

#%% ---------------------------------------------------------------------------------------
# -----------------------Import data----------------------------------------------
# ----------------------------------------------------------------------------------------
pla_df = pd.read_stata(Path(s1_loc, "pla_test.dta"))

#%% ---------------------------------------------------------------------------------------
# -----------------------Plot: left axis KDE (coefficient distribution) + right axis scatter (p-value) ----------------------
# ----------------------------------------------------------------------------------------

# 1) Global style (recommended to call only once for the whole project; put it here if this script runs independently)
set_econ_pub_style(use_tex=True, base_fontsize=9)

# Baseline estimate (vertical line)
rel_est = -0.1042

# p-value threshold (optional horizontal line, right axis)
min_p = 0.1

# Data
b = pla_df["b_hat"].dropna().to_numpy()
p = pla_df.loc[pla_df["b_hat"].notna(), "p_val"].to_numpy()

# 2) Canvas (use unified size; your original 8×4.5 is closer to a horizontal single plot, so it can be specified explicitly)
fig, ax = new_figure(width=6.0, height=3.5)

# ---------------- Left y-axis: KDE ----------------
kde = gaussian_kde(b)
x_min, x_max = float(np.min(b)), float(np.max(b))
xpad = 0.05 * (x_max - x_min) if x_max > x_min else 1e-6

x = np.linspace(x_min - xpad, x_max + xpad, 600)
y = kde(x)

# KDE line (grayscale + thinner line width, consistent with econ_pub_plot line width)
ax.plot(x, y, color="0.0", linewidth=1.0, label="KDE")

# Baseline vertical line (use unified helper)
add_vertical_line(ax, rel_est, linewidth=0.8, color="0.4", linestyle="--")
# If you want it to appear in the legend as well, you need to manually add a "proxy artist";
# the simplest way is to draw another vline with a label:
ax.axvline(rel_est, color="0.4", linestyle="--", linewidth=0.8, label="Baseline estimate")

# Left axis range (as requested: minimum value -2)
ax.set_ylim(-2, float(np.max(y)) * 1.15)

# x-axis range
ax.set_xlim(x_min - xpad, x_max + xpad)

# Left axis format (keep only left/bottom spines + inward ticks)
format_axes(
    ax,
    x_label="Coefficient",
    y_label="Kernel Density",
    inward_ticks=True,
)

# ---------------- Right y-axis: p-values scatter ----------------
ax2 = ax.twinx()

ax2.scatter(
    b, p,
    s=18,
    facecolors="none",     # hollow markers
    edgecolors="0.0",
    linewidths=0.7,
    label="P value",
    zorder=3,
)

# Uncomment if you need the p-value threshold line (it was originally commented out)
# ax2.axhline(min_p, color="0.4", linestyle="--", linewidth=0.8, label=f"p = {min_p}")

ax2.set_ylabel("P Value")
ax2.set_ylim(-0.2, 1.2)

# Apply "paper style" to the right axis spines/ticks as well: keep only the right spine (because of the right y-axis)
ax2.spines["top"].set_visible(False)
ax2.spines["left"].set_visible(False)
ax2.spines["bottom"].set_visible(False)
ax2.spines["right"].set_visible(True)
ax2.spines["right"].set_linewidth(0.8)

ax2.tick_params(
    axis="y",
    direction="in",
    length=3,
    width=0.8,
    left=False,
    right=True,
)
# Do not duplicate x-axis ticks/labels on the twin axis
ax2.tick_params(axis="x", bottom=False, labelbottom=False)

# ---------------- Legend: merge both axes ----------------
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
fig.legend(
    h1 + h2,
    l1 + l2,
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.005),
    ncol=3,
    handlelength=2,
)

# Tighten layout (leave some space for the bottom legend)
fig.tight_layout()

# Save
outpath = Path(figure_loc, "f4.pdf")
fig.savefig(outpath, bbox_inches="tight",dpi=1000)