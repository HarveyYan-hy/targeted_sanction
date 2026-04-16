#%% ---------------------------------------------------------------------------------------
# ------------------------ Import modules -------------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from tqdm import tqdm
import re
import os
from collections import Counter
import matplotlib.pyplot as plt

from code_file.py_code.py_config import stata_data, figures_loc, s2_result


from code_file.py_code.plot.tool_box import (
    make_eventstudy_df,
    set_econ_pub_style,
    new_figure,
    format_axes,
    plot_reg_with_errorbar,
    plot_reg_with_band,
    add_zero_line,
    add_vertical_line,
)

# Set a unified plotting style (call once for the entire project)
set_econ_pub_style(use_tex=True, font_serif=["Times New Roman"], base_fontsize=9)


#%% ---------------------------------------------------------------------------------------
# ------------------------ get the location ----------------------------------------------
# ----------------------------------------------------------------------------------------
stata_data_loc   = stata_data()
figure_loc = figures_loc()
s2_loc           = s2_result()
reg_result_loc   = f"{s2_loc}"





#%% ---------------------------------------------------------------------------------------
# ------------------------ Plot upstream groups sequentially ------------------------------
# ----------------------------------------------------------------------------------------
# Define group types
group_list = ['up1', 'up2', 'up3', 'up4']

# Define the regression result list
result_list = ['group_iw_down_break']

for result in result_list:
    for i, group in enumerate(group_list, start=1):

        # Read regression results
        result_df = pd.read_stata(f"{reg_result_loc}/{group}/{result}.dta")

        # Convert format
        df_plot = make_eventstudy_df(
            result_df,
            pre_periods=12,
            post_periods=8,
            base_period=-1
        )

        x      = df_plot['event_time'].to_numpy()
        y      = df_plot['estimate'].to_numpy()
        ci_low = df_plot['min90'].to_numpy()
        ci_high= df_plot['max90'].to_numpy()


        # Create a journal-style canvas
        fig, ax = new_figure(width=4.0, height=3.5)

        # Error bars
        plot_reg_with_errorbar(
            ax,
            x=x,
            beta=y,
            ci_low=ci_low,
            ci_high=ci_high,
            label=None,
            marker="s"
        )

        # Reference lines: y=0 and t=-1
        add_zero_line(ax)
        add_vertical_line(ax, x=-1.0)

        # x-axis ticks: all event times (integers)
        x_int = np.unique(np.round(x).astype(int))
        x_even = x_int[x_int % 2 == 0]     # Keep only even numbers
        ax.set_xticks(x_even)

        # Leave a little blank space at both ends of the x-axis
        ax.set_xlim(x_int.min() - 0.5, x_int.max() + 0.5)

        # Distinguish upstream and downstream in the title
        if group.startswith('up'):
            title_prefix = "Upstream"
        else:
            title_prefix = "Downstream"

        # Distinguish hierarchy levels in the title
        level = int(group[-1])
        label = f"({level * 2 - 1}-{level * 2})"

        # Title suffix (keep your original naming)
        map_dict = {
            'group_iw_income':    'Income Yoy',
            'group_iw_up_break':  'Supplier Exit',
            'group_iw_down_break':'Customer Exit',
        }
        title_suffix = map_dict[result]

        # Combine title
        plot_title = f"{title_prefix} {label}: {title_suffix}"


        # Axes & title
        format_axes(
            ax,
            x_label=r"Quarters Relative to Exposure",
            y_label=r"Estimated Effect",
            ylim=(-0.15,0.45),
        )
        ax.set_title(plot_title)

        fig.tight_layout(pad=0.5)


        # Save
        file_title = f"f13_{i}"
        fig.savefig(f"{figure_loc}/{file_title}.pdf", dpi=1000)




#%% ---------------------------------------------------------------------------------------
# ------------------------ Plot downstream groups sequentially ----------------------------
# ----------------------------------------------------------------------------------------
# Define group types
group_list = ['down1', 'down2', 'down3','down4']

# Define the regression result list
result_list = ['group_iw_up_break']

for result in result_list:
    for i, group in enumerate(group_list, start=5):

        # Read regression results
        result_df = pd.read_stata(f"{reg_result_loc}/{group}/{result}.dta")

        # Convert format
        df_plot = make_eventstudy_df(
            result_df,
            pre_periods=12,
            post_periods=8,
            base_period=-1
        )

        x      = df_plot['event_time'].to_numpy()
        y      = df_plot['estimate'].to_numpy()
        ci_low = df_plot['min90'].to_numpy()
        ci_high= df_plot['max90'].to_numpy()


        # Create a journal-style canvas
        fig, ax = new_figure(width=4.0, height=3.5)

        # Error bars
        plot_reg_with_errorbar(
            ax,
            x=x,
            beta=y,
            ci_low=ci_low,
            ci_high=ci_high,
            label=None,
            marker="s"
        )

        # Reference lines: y=0 and t=-1
        add_zero_line(ax)
        add_vertical_line(ax, x=-1.0)

        # x-axis ticks: all event times (integers)
        x_int = np.unique(np.round(x).astype(int))
        x_even = x_int[x_int % 2 == 0]     # Keep only even numbers
        ax.set_xticks(x_even)

        # Leave a little blank space at both ends of the x-axis
        ax.set_xlim(x_int.min() - 0.5, x_int.max() + 0.5)

        # Distinguish upstream and downstream in the title
        if group.startswith('up'):
            title_prefix = "Upstream"
        else:
            title_prefix = "Downstream"

        # Distinguish hierarchy levels in the title
        level = int(group[-1])
        label = f"({level * 2 - 1}-{level * 2})"

        # Title suffix (keep your original naming)
        map_dict = {
            'group_iw_income':    'Income Yoy',
            'group_iw_up_break':  'Supplier Exit',
            'group_iw_down_break':'Customer Exit',
        }
        title_suffix = map_dict[result]

        # Combine title
        plot_title = f"{title_prefix} {label}: {title_suffix}"



        # Axes & title
        format_axes(
            ax,
            x_label=r"Quarters Relative to Exposure",
            #y_label=r"Estimated Effect",
            ylim=(-0.15,0.55),
        )
        ax.set_title(plot_title)

        fig.tight_layout(pad=0.5)


        # Save
        file_title = f"f13_{i}"
        fig.savefig(f"{figure_loc}/{file_title}.pdf", dpi=1000)