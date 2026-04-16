#%% ---------------------------------------------------------------------------------------
# ------------------------Import packages----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from tqdm import tqdm
import re
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from scipy.stats import gaussian_kde
from code_file.py_code.py_config import figures_loc, raw_data
from code_file.py_code.plot.tool_box import (
    set_econ_pub_style,
    new_figure,
    format_axes,
    plot_descriptive_line,
    add_legend
)


set_econ_pub_style(use_tex=True, font_serif=["Times New Roman"], base_fontsize=9)



#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc  = raw_data()
figure_loc  = figures_loc()





#%% ---------------------------------------------------------------------------------------
# ------------------------Read data----------------------------------------------
# ----------------------------------------------------------------------------------------
cols = ['year','Approved%']
exp_df = pd.read_excel(Path(raw_data_loc,'bis_report','bis_china_report.xlsx'),sheet_name='exp',usecols=cols)
deemed_df = pd.read_excel(Path(raw_data_loc,'bis_report','bis_china_report.xlsx'),sheet_name='deemed',usecols=cols)
value_df = pd.read_excel(Path(raw_data_loc,'bis_report','bis_china_report.xlsx'),sheet_name='value',usecols=cols)





#%% ---------------------------------------------------------------------------------------
# ------------------------Plotting----------------------------------------------
# ----------------------------------------------------------------------------------------
fig, ax = new_figure(width=6.0, height=3.5)

x = exp_df["year"].to_numpy()

series = {
    "Export/Re-export (Count)": exp_df["Approved%"].to_numpy(),
    "Export/Re-export (Value)": value_df["Approved%"].to_numpy(),
    "Deemed Export (Count)": deemed_df["Approved%"].to_numpy()
}

# Distinguish the three lines using line styles/markers (default colors are all grayscale 0.0)
styles = {
    "Export/Re-export (Count)": {"linestyle": "-",  "marker": "o", "markersize": 3},
    "Export/Re-export (Value)": {"linestyle": "--", "marker": "s", "markersize": 3},
    "Deemed Export (Count)":    {"linestyle": ":",  "marker": "^", "markersize": 3},
}

plot_descriptive_line(ax, x=x, series=series, styles=styles)

format_axes(ax)
ax.set_xticks(x)



ax.set_ylim(0.2, 1.0)  # Confirm that the data range is 0-1
ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
add_legend(ax, ncol=3, outside=True)

fig.subplots_adjust(bottom=0.22)  # Leave space below for the legend




fig.savefig(Path(figure_loc, "f1.pdf"), bbox_inches="tight",dpi=1000)