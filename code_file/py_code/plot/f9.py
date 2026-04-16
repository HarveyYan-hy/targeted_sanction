#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from code_file.py_code.py_config import stata_data, figures_loc, s3_result, s1_result

from code_file.py_code.plot.tool_box import (
    make_eventstudy_df,
    set_econ_pub_style,
    new_figure,
    format_axes,
    plot_event_study,
)

# Set publication-style plotting format (only needs to be called once for the whole paper)
set_econ_pub_style(use_tex=True, font_serif=["Times New Roman"], base_fontsize=9)












#%% ---------------------------------------------------------------------------------------
# ------------------------Paths----------------------------------------------
# ----------------------------------------------------------------------------------------
stata_data_loc   = stata_data()
latex_figure_loc = figures_loc()
s3_result        = s3_result()
reg_result_loc   = f"{s3_result}"

os.makedirs(latex_figure_loc, exist_ok=True)


#%% ---------------------------------------------------------------------------------------
# ------------------------Baseline regression event-study plot----------------------------------------------
# ----------------------------------------------------------------------------------------
result_list = ["income_event"]

for result in result_list:

    result_df = pd.read_stata(f"{reg_result_loc}/{result}.dta")

    df_plot = make_eventstudy_df(
        result_df,
        pre_periods=12,
        post_periods=8,
        base_period=-1,
    )

    x       = df_plot["event_time"].to_numpy()
    y       = df_plot["estimate"].to_numpy()
    ci_low  = df_plot["min90"].to_numpy()
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
    # Estimated coefficient of sanctioned firms
    itself_est = -0.1022
    ax.axhline(
        y=itself_est,
        linestyle=":",      # dotted line
        linewidth=1.0,
        color="0.5",        # gray
        zorder=1,
    )

    # Add annotation directly below the line: gray, italic, and smaller font size
    ax.text(
        x=-7,   # horizontal position, can be fine-tuned as needed
        y=itself_est-0.02 ,  
        s=f"Estimated coefficient of sanctioned firms: {itself_est}",
        ha="center",
        va="top",
        color="0.5",        # same gray as the line
        fontstyle="italic", # italic
        fontsize=7,         # slightly smaller than the global base_fontsize
    )

    # ---- Force x-axis ticks to be even integers ----
    x_int = np.round(x).astype(int)
    even_ticks = np.arange(x_int.min(), x_int.max() + 1, 2)
    ax.set_xticks(even_ticks)

    # Also slightly extend both ends of the x-axis to avoid clipping at the boundaries
    ax.set_xlim(x_int.min() - 0.5, x_int.max() + 0.5)

    # Axis formatting
    format_axes(
        ax,
        x_label=r"Quarters relative to sanction",
        #y_label=r"Estimated effect",
        ylim=(-0.35, 0.4),
    )

    fig.tight_layout(pad=0.5)

    fig.savefig(f"{latex_figure_loc}/f9.pdf",dpi=1000)