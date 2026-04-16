#%% ---------------------------------------------------------------------------------------
# ------------------------Import packages----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import gaussian_kde

from code_file.py_code.py_config import s2_result, figures_loc



# Unified paper style: use your organized econ_pub_plot
from code_file.py_code.plot.tool_box import (
    set_econ_pub_style,
    new_figure,
    format_axes,
    add_vertical_line,
    add_zero_line,
    add_legend
)




#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
s2_loc = s2_result()
figure_loc = figures_loc()





#%% ---------------------------------------------------------------------------------------
# -----------------------Real income plot----------------------------------------------
# ----------------------------------------------------------------------------------------
# Read data
real_income = pd.read_stata(Path(s2_loc, "ols_income.dta"))

# Rename variables
shock_map = {
    'ru1':'upshock1',
    'ru2':'upshock2',
    'ru3':'upshock3',
    'ru4':'upshock4',
    'rd1':'downshock1',
    'rd2':'downshock2',
    'rd3':'downshock3',
    'rd4':'downshock4',
}
real_income['parm'] = real_income['parm'].map(shock_map)
real_income = real_income[real_income['parm'].isin(list(shock_map.values()))]

# Separate upstream and downstream
up_df   = real_income[real_income["parm"].str.contains("up")].copy()
down_df = real_income[real_income["parm"].str.contains("down")].copy()


# Extract level = 1,2,3,4
up_df["level"]   = up_df["parm"].str[-1].astype(int)
down_df["level"] = down_df["parm"].str[-1].astype(int)


# Plotting coefficients (numpy)
up_x    = up_df["level"].to_numpy()
up_y    = up_df["estimate"].to_numpy()
up_ci_l = up_df["min99"].to_numpy()
up_ci_h = up_df["max99"].to_numpy()

down_x    = down_df["level"].to_numpy()
down_y    = down_df["estimate"].to_numpy()
down_ci_l = down_df["min99"].to_numpy()
down_ci_h = down_df["max99"].to_numpy()

# Horizontal position offset
offset       = 0.03
up_x_shift   = up_x   - offset
down_x_shift = down_x + offset

# Plot
fig, ax = new_figure(width=6.0, height=3.5)

# Upstream: error bars (gray circles)
ax.errorbar(
    up_x_shift,
    up_y,
    yerr=[up_y - up_ci_l, up_ci_h - up_y],
    fmt="o-",
    color="0.5",
    capsize=2,
    markersize=3,
    linewidth=1.0,
    label="Upstream of Sanctioned Firms",
    zorder=2,
)

# Downstream: error bars (black squares)
ax.errorbar(
    down_x_shift,
    down_y,
    yerr=[down_y - down_ci_l, down_ci_h - down_y],
    fmt="s-",
    color="0.0",
    capsize=2,
    markersize=3,
    linewidth=1.0,
    label="Downstream of Sanctioned Firms",
    zorder=3,
)

# Estimated coefficient for sanctioned firms
itself_est = -0.1022
ax.axhline(
    y=itself_est,
    linestyle=":",      # Dotted line
    linewidth=1.0,
    color="0.5",        # Gray
    zorder=1,
)

# Add text annotation directly below the line: gray, italic, smaller font size
ax.text(
    x=2.5,   # Horizontal position, can be adjusted as needed
    y=itself_est+0.008,
    s=f"Estimated coefficient of sanctioned firms: {itself_est}",
    ha="center",
    va="top",
    color="0.5",        # Same gray as the line
    fontstyle="italic", # Italic
    fontsize=7,         # Slightly smaller than the global base_fontsize
)

# Horizontal reference line
add_zero_line(ax)

# X-axis ticks remain at integer positions
xticks       = np.array([1, 2, 3, 4])
xtick_labels = ["1–2", "3–4", "5–6", "7–8"]  
ax.set_xticks(xticks)
ax.set_xticklabels(xtick_labels)

# Axes and ranges
format_axes(
    ax,
    x_label=r"Distance from Sanctioned Firms",
    #y_label=r"Estimated Effect",
    xlim=(0.5, 4.5)
)
ymin, ymax = ax.get_ylim()
ax.set_ylim(-0.12, ymax)
# Legend
add_legend(ax, outside=True, ncol=2)

fig.tight_layout(pad=0.5)

# Save
outpath = Path(figure_loc, "f6.pdf")
fig.savefig(outpath, bbox_inches="tight",dpi=1000)





#%% ---------------------------------------------------------------------------------------
# -----------------------Fake income plot----------------------------------------------
# ----------------------------------------------------------------------------------------
fake_income = pd.read_stata(Path(s2_loc, "ols_income_fake.dta"))



# Separate upstream and downstream
up_df   = fake_income[fake_income["parm"].str.contains("up")].copy()
down_df = fake_income[fake_income["parm"].str.contains("down")].copy()


# Extract level = 1,2,3,4
up_df["level"]   = up_df["parm"].str[-1].astype(int)
down_df["level"] = down_df["parm"].str[-1].astype(int)


# Plotting coefficients (numpy)
up_x    = up_df["level"].to_numpy()
up_y    = up_df["estimate"].to_numpy()
up_ci_l = up_df["min99"].to_numpy()
up_ci_h = up_df["max99"].to_numpy()

down_x    = down_df["level"].to_numpy()
down_y    = down_df["estimate"].to_numpy()
down_ci_l = down_df["min99"].to_numpy()
down_ci_h = down_df["max99"].to_numpy()

# Horizontal position offset
offset       = 0.03
up_x_shift   = up_x   - offset
down_x_shift = down_x + offset

# Plot
fig, ax = new_figure(width=6.0, height=3.5)

# Upstream: error bars (gray circles)
ax.errorbar(
    up_x_shift,
    up_y,
    yerr=[up_y - up_ci_l, up_ci_h - up_y],
    fmt="o-",
    color="0.5",
    capsize=2,
    markersize=3,
    linewidth=1.0,
    label="Upstream of Sanctioned Firms",
    zorder=2,
)

# Downstream: error bars (black squares)
ax.errorbar(
    down_x_shift,
    down_y,
    yerr=[down_y - down_ci_l, down_ci_h - down_y],
    fmt="s-",
    color="0.0",
    capsize=2,
    markersize=3,
    linewidth=1.0,
    label="Downstream of Sanctioned Firms",
    zorder=3,
)

# Horizontal reference line
add_zero_line(ax)

# X-axis ticks remain at integer positions
xticks       = np.array([1, 2, 3, 4])
xtick_labels = ["1–2", "3–4", "5–6", "7–8"]  # Use en dash for a more publication-style look
ax.set_xticks(xticks)
ax.set_xticklabels(xtick_labels)

# Axes and ranges
format_axes(
    ax,
    x_label=r"Distance from Sanctioned Firms",
    #y_label=r"Estimated Effect",
    xlim=(0.5, 4.5),
)
ymin, ymax = ax.get_ylim()

# Legend
add_legend(ax, outside=True, ncol=2)

fig.tight_layout(pad=0.5)

# Save
outpath = Path(figure_loc, "f11_2.pdf")
fig.savefig(outpath, bbox_inches="tight",dpi=1000)









#%% ---------------------------------------------------------------------------------------
# -----------------------Real relationship break plot----------------------------------------------
# ----------------------------------------------------------------------------------------

# Read data
real_customer_break = pd.read_stata(f"{s2_loc}/ols_down_break.dta")
real_supply_break = pd.read_stata(f"{s2_loc}/ols_up_break.dta")

shock_map = {
    'ru1':'upshock1',
    'ru2':'upshock2',
    'ru3':'upshock3',
    'ru4':'upshock4',
    'rd1':'downshock1',
    'rd2':'downshock2',
    'rd3':'downshock3',
    'rd4':'downshock4',
}
real_customer_break['parm'] = real_customer_break['parm'].map(shock_map)
real_supply_break['parm'] = real_supply_break['parm'].map(shock_map)

real_supply_break = real_supply_break[real_supply_break['parm'].notna()]
real_customer_break = real_customer_break[real_customer_break['parm'].notna()]


up_break       = real_customer_break[real_customer_break["parm"].str.contains("up")].copy()
down_break   = real_supply_break[real_supply_break["parm"].str.contains("down")].copy()


# Extract level = 1,2,3,4
down_break["level"] = down_break["parm"].str[-1].astype(int)
up_break["level"]   = up_break["parm"].str[-1].astype(int)

# Plotting coefficients
down_break_x    = down_break["level"].to_numpy()
down_break_y    = down_break["estimate"].to_numpy()
down_break_ci_l = down_break["min99"].to_numpy()
down_break_ci_h = down_break["max99"].to_numpy()

up_break_x    = up_break["level"].to_numpy()
up_break_y    = up_break["estimate"].to_numpy()
up_break_ci_l = up_break["min99"].to_numpy()
up_break_ci_h = up_break["max99"].to_numpy()

# Horizontal position offset
offset       = 0.03
up_break_x_shift   = up_break_x   - offset
down_break_x_shift = down_break_x + offset

# Plot
fig, ax = new_figure(width=6.0, height=3.5)

# Downstream (down_break): error bars (black squares)
ax.errorbar(
    down_break_x_shift,
    down_break_y,
    yerr=[down_break_y - down_break_ci_l, down_break_ci_h - down_break_y],
    fmt="s-",
    color="0.0",
    capsize=2,
    markersize=3,
    linewidth=1.0,
    label="Downstream of Sanctioned Firms: Supplier Exit",
    zorder=3,
)

# Upstream (up_break): error bars (gray circles)
ax.errorbar(
    up_break_x_shift,
    up_break_y,
    yerr=[up_break_y - up_break_ci_l, up_break_ci_h - up_break_y],
    fmt="o-",
    color="0.5",
    capsize=2,
    markersize=3,
    linewidth=1.0,
    label="Upstream of Sanctioned Firms: Customer Exit",
    zorder=2,
)

# Horizontal reference line
add_zero_line(ax)

# X-axis ticks and labels
xticks       = np.array([1, 2, 3, 4])
xtick_labels = ["1–2", "3–4", "5–6", "7–8"]
ax.set_xticks(xticks)
ax.set_xticklabels(xtick_labels)

# Axes and ranges
format_axes(
    ax,
    x_label=r"Distance from Sanctioned Firms",
    #y_label=r"Estimated Effect",
    xlim=(0.5, 4.5),
    ylim=(-0.05, 0.25),
)

# Legend
add_legend(ax, outside=True, ncol=1)

fig.tight_layout(pad=0.5)

# Save
outpath = Path(figure_loc, "f5.pdf")
fig.savefig(outpath, bbox_inches="tight", dpi=1000)




#%% ---------------------------------------------------------------------------------------
# -----------------------Fake relationship break plot----------------------------------------------
# ----------------------------------------------------------------------------------------

# Read data
fake_customer_break = pd.read_stata(f"{s2_loc}/ols_down_break_fake.dta")
fake_supply_break = pd.read_stata(f"{s2_loc}/ols_up_break_fake.dta")


up_break       = fake_customer_break[fake_customer_break["parm"].str.contains("up")].copy()
down_break   = fake_supply_break[fake_supply_break["parm"].str.contains("down")].copy()

# Extract level = 1,2,3,4
down_break["level"] = down_break["parm"].str[-1].astype(int)
up_break["level"]   = up_break["parm"].str[-1].astype(int)

# Plotting coefficients
down_break_x    = down_break["level"].to_numpy()
down_break_y    = down_break["estimate"].to_numpy()
down_break_ci_l = down_break["min99"].to_numpy()
down_break_ci_h = down_break["max99"].to_numpy()

up_break_x    = up_break["level"].to_numpy()
up_break_y    = up_break["estimate"].to_numpy()
up_break_ci_l = up_break["min99"].to_numpy()
up_break_ci_h = up_break["max99"].to_numpy()

# Horizontal position offset
offset       = 0.03
up_break_x_shift   = up_break_x   - offset
down_break_x_shift = down_break_x + offset

# Plot
fig, ax = new_figure(width=6.0, height=3.5)

# Downstream (down_break): error bars (black squares)
ax.errorbar(
    down_break_x_shift,
    down_break_y,
    yerr=[down_break_y - down_break_ci_l, down_break_ci_h - down_break_y],
    fmt="s-",
    color="0.0",
    capsize=2,
    markersize=3,
    linewidth=1.0,
    label="Downstream of Sanctioned Firms: Supplier Exit",
    zorder=3,
)

# Upstream (up_break): error bars (gray circles)
ax.errorbar(
    up_break_x_shift,
    up_break_y,
    yerr=[up_break_y - up_break_ci_l, up_break_ci_h - up_break_y],
    fmt="o-",
    color="0.5",
    capsize=2,
    markersize=3,
    linewidth=1.0,
    label="Upstream of Sanctioned Firms: Customer Exit",
    zorder=2,
)

# Horizontal reference line
add_zero_line(ax)

# X-axis ticks and labels
xticks       = np.array([1, 2, 3, 4])
xtick_labels = ["1–2", "3–4", "5–6", "7–8"]
ax.set_xticks(xticks)
ax.set_xticklabels(xtick_labels)

# Axes and ranges
format_axes(
    ax,
    x_label=r"Distance from Sanctioned Firms",
    #y_label=r"Estimated Effect",
    xlim=(0.5, 4.5)
)
ymin, ymax = ax.get_ylim()
# Legend
add_legend(ax, outside=True, ncol=1)

fig.tight_layout(pad=0.5)

# Save
outpath = Path(figure_loc, "f11_1.pdf")
fig.savefig(outpath, bbox_inches="tight",dpi=1000)