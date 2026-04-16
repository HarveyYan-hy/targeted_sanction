#%% ---------------------------------------------------------------------------------------
# ------------------------Import packages----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from tqdm import tqdm
import re
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from code_file.py_code.py_config import s1_result, figures_loc
from code_file.py_code.plot.tool_box import (
    make_eventstudy_df,
    set_econ_pub_style,
    new_figure,
    format_axes,
    plot_event_study,
)


set_econ_pub_style(use_tex=True, font_serif=["Times New Roman"], base_fontsize=9)



#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
s1_loc = s1_result()
figure_loc  = figures_loc()




#%% ---------------------------------------------------------------------------------------
# -----------------------twfe----------------------------------------------
# ----------------------------------------------------------------------------------------
result_df = pd.read_stata(f"{s1_loc}/eventstudy.dta")


df_plot = make_eventstudy_df(
    result_df,
    pre_periods=12,
    post_periods=8,
    base_period=-1,
)

# Extract data
x = df_plot["event_time"].to_numpy()
y = df_plot["estimate"].to_numpy()
ci_low = df_plot["min90"].to_numpy()
ci_high = df_plot["max90"].to_numpy()


fig, ax = new_figure(width=6.0, height=3.5)

# Event study: error bars
plot_event_study(
    ax,
    x=x,
    beta=y,
    ci_low=ci_low,
    ci_high=ci_high,
    treat_time=-1,
    use_errorbar=True,
    marker="s",
    )

# Force x-axis ticks to be even integers
x_int = np.round(x).astype(int)
even_ticks = np.arange(x_int.min(), x_int.max() + 1, 2)
ax.set_xticks(even_ticks)

# Slightly widen the x-axis limits to avoid clipping at the endpoints
ax.set_xlim(x_int.min() - 0.5, x_int.max() + 0.5)

# Axis format
format_axes(
    ax,
    x_label=r"Quarters relative to sanction",
    #y_label=r"Estimated effect",
    ylim=(-0.35, 0.4),
    )

fig.tight_layout(pad=0.5)


fig.savefig(f"{figure_loc}/f10_1.pdf",dpi=1000)






#%% ---------------------------------------------------------------------------------------
# -----------------------didimputation----------------------------------------------
# ----------------------------------------------------------------------------------------
imputation_df = pd.read_stata(f"{s1_loc}/did_imputation.dta")


# Rename dummy variables
def rename_parm(s: str) -> str:
    """
    tau0..tau8 -> D0..D8
    pre1..pre9 -> D_1..D_9
    """
    s = str(s)

    m_tau = re.fullmatch(r"tau(\d+)", s)
    if m_tau:
        return f"D{m_tau.group(1)}"      # D0, D1, ...

    m_pre = re.fullmatch(r"pre(\d+)", s)
    if m_pre:
        return f"D_{m_pre.group(1)}"     # D_1, D_2, ...
    return s


imputation_df["parm"] = imputation_df["parm"].astype(str).map(rename_parm)



df_plot = make_eventstudy_df(
    imputation_df,
    pre_periods=12,
    post_periods=8,
    base_period="nobase"   # Keep your original setting
)

x       = df_plot["event_time"].to_numpy()
y       = df_plot["estimate"].to_numpy()
ci_low  = df_plot["min90"].to_numpy()
ci_high = df_plot["max90"].to_numpy()

# Create a new journal-style figure
fig, ax = new_figure(width=6.0, height=3.5)

# Event study: error bars + treatment timing vertical line (here treatment is at 0)
plot_event_study(
    ax,
    x=x,
    beta=y,
    ci_low=ci_low,
    ci_high=ci_high,
    treat_time=0,          # The vertical line in your original figure is drawn at 0
    use_errorbar=True,
    marker="s",
)

# Force x-axis ticks to be even integers
x_int = np.round(x).astype(int)
even_ticks = np.arange(x_int.min(), x_int.max() + 1, 2)
ax.set_xticks(even_ticks)

# Leave some space at both ends of the x-axis to avoid clipping
ax.set_xlim(x_int.min() - 0.5, x_int.max() + 0.5)

# Axis format
format_axes(
    ax,
    x_label=r"Quarters relative to Sanction",
    #y_label=r"Estimated effect",
    ylim=(-0.35, 0.4),
)

fig.tight_layout(pad=0.5)

# Save: pdf for LaTeX, png for preview
fig.savefig(f"{figure_loc}/f10_2.pdf",dpi=1000)





#%% ---------------------------------------------------------------------------------------
# -----------------------stackedev----------------------------------------------
# ----------------------------------------------------------------------------------------
stackedev_df = pd.read_stata(f"{s1_loc}/stackedev.dta")

df_plot = make_eventstudy_df(
    stackedev_df,
    pre_periods=12,
    post_periods=8,
    base_period=-1
)

x       = df_plot["event_time"].to_numpy()
y       = df_plot["estimate"].to_numpy()
ci_low  = df_plot["min90"].to_numpy()
ci_high = df_plot["max90"].to_numpy()


fig, ax = new_figure(width=6.0, height=3.5)

# Event study: error bars + reference line
plot_event_study(
    ax,
    x=x,
    beta=y,
    ci_low=ci_low,
    ci_high=ci_high,
    treat_time=-1,
    use_errorbar=True,
    marker="s",
)

# X-axis: force even integer ticks
x_int = np.round(x).astype(int)
even_ticks = np.arange(x_int.min(), x_int.max() + 1, 2)
ax.set_xticks(even_ticks)

# Leave some space at both ends of the x-axis to avoid clipping
ax.set_xlim(x_int.min() - 0.5, x_int.max() + 0.5)

# Axis format and y-axis range
format_axes(
    ax,
    x_label=r"Quarters relative to sanction",
    #y_label=r"Estimated effect",
    ylim=(-0.35, 0.4),
)

fig.tight_layout(pad=0.5)

# Save: pdf for LaTeX, png for preview
fig.savefig(f"{figure_loc}/f10_3.pdf",dpi=1000)




#%% ---------------------------------------------------------------------------------------
# -----------------------eventstudyinteract----------------------------------------------
# ----------------------------------------------------------------------------------------
eventstudyinteract_df = pd.read_stata(f"{s1_loc}/eventstudyinteract.dta")



df_plot = make_eventstudy_df(
    eventstudyinteract_df,
    pre_periods=12,
    post_periods=8,
    base_period=-1
)

x       = df_plot["event_time"].to_numpy()
y       = df_plot["estimate"].to_numpy()
ci_low  = df_plot["min90"].to_numpy()
ci_high = df_plot["max90"].to_numpy()


fig, ax = new_figure(width=6.0, height=3.5)

# Event study: error bars + reference line
plot_event_study(
    ax,
    x=x,
    beta=y,
    ci_low=ci_low,
    ci_high=ci_high,
    treat_time=-1,
    use_errorbar=True,
    marker="s",
)

# X-axis: force even integer ticks
x_int = np.round(x).astype(int)
even_ticks = np.arange(x_int.min(), x_int.max() + 1, 2)
ax.set_xticks(even_ticks)

# Leave some space at both ends of the x-axis to avoid clipping
ax.set_xlim(x_int.min() - 0.5, x_int.max() + 0.5)

# Axis format and y-axis range
format_axes(
    ax,
    x_label=r"Quarters relative to sanction",
    #y_label=r"Estimated effect",
    ylim=(-0.35, 0.4),
)

fig.tight_layout(pad=0.5)

# Save: pdf for LaTeX, png for preview
fig.savefig(f"{figure_loc}/f10_4.pdf",dpi=1000)