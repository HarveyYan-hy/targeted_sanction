#%% ---------------------------------------------------------------------------------------
# ------------------------ Import modules -------------------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from pathlib import Path

from code_file.py_code.py_config import stata_data, figures_loc, s2_result


from code_file.py_code.plot.tool_box import (
    make_eventstudy_df,
    set_econ_pub_style,
    new_figure,
    format_axes,
    plot_reg_with_errorbar,
    add_zero_line,
    add_vertical_line,
    add_legend,
    plot_band_only,      
)

# Set a unified plotting style (only needs to be called once for the whole project)
set_econ_pub_style(use_tex=True, font_serif=["Times New Roman"], base_fontsize=9)


#%% ---------------------------------------------------------------------------------------
# ------------------------ Paths ----------------------------------------------------------
# ----------------------------------------------------------------------------------------
figure_loc = figures_loc()
s2_loc     = s2_result()

os.makedirs(figure_loc, exist_ok=True)


#%% ---------------------------------------------------------------------------------------
# ------------------------ Income: Upstream and Downstream ---------------------------------------------------
# ----------------------------------------------------------------------------------------

# Read data
income_df = pd.read_stata(f"{s2_loc}/stacked_income.dta")

# Separate upstream and downstream
up_df   = income_df[income_df["parm"].str.contains("up1")]
down_df = income_df[income_df["parm"].str.contains("down1")]

# Transform format
up_plot   = make_eventstudy_df(up_df,   pre_periods=12, post_periods=8, base_period=-1)
down_plot = make_eventstudy_df(down_df, pre_periods=12, post_periods=8, base_period=-1)

# Plotting data
up_x    = up_plot["event_time"].to_numpy()
up_low  = up_plot["min90"].to_numpy()
up_high = up_plot["max90"].to_numpy()

down_x    = down_plot["event_time"].to_numpy()
down_y    = down_plot["estimate"].to_numpy()
down_low  = down_plot["min90"].to_numpy()
down_high = down_plot["max90"].to_numpy()

# Plot
fig, ax = new_figure(width=6.0, height=3.5)

# Upstream: shaded band only (without solid line)
plot_band_only(
    ax,
    x=up_x,
    ci_low=up_low,
    ci_high=up_high,
    label=r"Upstream of Sanctioned Firms: Income YoY",
)

# Downstream: error bars (with solid line)
plot_reg_with_errorbar(
    ax,
    x=down_x,
    beta=down_y,
    ci_low=down_low,
    ci_high=down_high,
    label=r"Downstream of Sanctioned Firms: Income YoY",
    marker="s",
)

# Reference lines
add_zero_line(ax)
add_vertical_line(ax, x=-1.0)

# X-axis ticks: even integers
x_all = np.concatenate([up_x, down_x])
x_int = np.unique(np.round(x_all).astype(int))
even_ticks = np.arange(x_int.min(), x_int.max() + 1, 2)
ax.set_xticks(even_ticks)

# X-axis range
ax.set_xlim(x_int.min() - 0.5, x_int.max() + 0.5)

# Axis formatting
format_axes(
    ax,
    #x_label=r"Quarters Relative to Exposure",
    #y_label=r"Estimated Effect",
    ylim=(-0.30, 0.15),
)

# Legend
add_legend(ax, outside=True, ncol=2)

fig.tight_layout(pad=0.5)

# Save
outpath = Path(figure_loc, "f8.pdf")
fig.savefig(outpath, bbox_inches="tight",dpi=1000)







#%% ---------------------------------------------------------------------------------------
# ------------------------ Relationship Break: Upstream and Downstream ------------------------------------------------
# ----------------------------------------------------------------------------------------

# Read data
down_break = pd.read_stata(f"{s2_loc}/stacked_down_break.dta")
up_break   = pd.read_stata(f"{s2_loc}/stacked_up_break.dta")

# Filter direction (note the up/down correspondence in the original code)
down_break = down_break[down_break["parm"].str.contains("up1")]
up_break   = up_break[up_break["parm"].str.contains("down1")]

# Transform format
down_break_plot = make_eventstudy_df(down_break, pre_periods=12, post_periods=8, base_period=-1)
up_break_plot   = make_eventstudy_df(up_break,   pre_periods=12, post_periods=8, base_period=-1)

# Plotting data
down_break_x    = down_break_plot["event_time"].to_numpy()
down_break_low  = down_break_plot["min90"].to_numpy()
down_break_high = down_break_plot["max90"].to_numpy()

up_break_x    = up_break_plot["event_time"].to_numpy()
up_break_y    = up_break_plot["estimate"].to_numpy()
up_break_low  = up_break_plot["min90"].to_numpy()
up_break_high = up_break_plot["max90"].to_numpy()

# Plot
fig, ax = new_figure(width=6.0, height=3.5)

# Upstream (down_break): shaded band
plot_band_only(
    ax,
    x=down_break_x,
    ci_low=down_break_low,
    ci_high=down_break_high,
    label=r"Upstream of Sanctioned Firms: Customer Exit",
)

# Downstream (up_break): error bars
plot_reg_with_errorbar(
    ax,
    x=up_break_x,
    beta=up_break_y,
    ci_low=up_break_low,
    ci_high=up_break_high,
    label=r"Downstream of Sanctioned Firms: Supplier Exit",
    marker="s",
)

# Reference lines
add_zero_line(ax)
add_vertical_line(ax, x=-1.0)

# X-axis ticks
x_all_break = np.concatenate([down_break_x, up_break_x])
x_int_break = np.unique(np.round(x_all_break).astype(int))
even_ticks_break = np.arange(x_int_break.min(), x_int_break.max() + 1, 2)
ax.set_xticks(even_ticks_break)

# X-axis range
ax.set_xlim(x_int_break.min() - 0.5, x_int_break.max() + 0.5)

# Y-axis range
format_axes(
    ax,
    #x_label=r"Quarters Relative to Exposure",
    #y_label=r"Estimated Effect",
    ylim=(-0.05, 0.35),
)

# Legend
add_legend(ax, outside=True, ncol=2)

fig.tight_layout(pad=0.5)


# Save
outpath = Path(figure_loc, "f7.pdf")
fig.savefig(outpath, bbox_inches="tight",dpi=1000)