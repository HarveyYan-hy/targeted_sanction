#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules---------------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from pathlib import Path
from code_file.py_code.py_config import tables_loc, s1_result





#%% ---------------------------------------------------------------------------------------
# ------------------------Get the location-------------------------------------------------
# ----------------------------------------------------------------------------------------
table_loc = tables_loc()
s1_loc = s1_result()





#%% ---------------------------------------------------------------------------------------
# ------------------------Import data------------------------------------------------------
# ----------------------------------------------------------------------------------------
des_df = pd.read_stata(Path(s1_loc, 'descriptive_statistics.dta'))







#%% ---------------------------------------------------------------------------------------
# ------------------------Construct descriptive statistics table---------------------------
# ----------------------------------------------------------------------------------------

# Rename variables
rename_dict = {
    'year': 'Year',
    'quarter': 'Quarter',
    'st_sample': 'ST_Sample',
    'exit_sample': 'Exit_Sample',
    'total_income_q_yoy': 'Inc_YoY',
    'total_income_q_yoy_asset': 'Inc_YoY_A',
    'total_income_ihs_d': 'Inc_IHS_d',
    'major_change': 'Major_Change',
    'top_hold_share': 'Top_Share',
    'up_break': 'Supplier_Exit',
    'down_break': 'Customer_Exit'
}
des_df = des_df.rename(columns=rename_dict)
des_df = des_df[list(rename_dict.values())]



# Descriptive statistics
stats = des_df.describe().loc[['count', 'mean', 'std', 'min', 'max']]
stats = stats.rename(index={
    'count': 'Obs',
    'mean': 'Mean',
    'std': 'SD',
    'min': 'Min',
    'max': 'Max'
})
stats_table = stats.T.reset_index().rename(columns={'index': 'Variable'})


# Format numbers
stats_table['Obs'] = stats_table['Obs'].round(0).astype(int)
des_cols = ['Mean', 'SD', 'Min', 'Max']
for col in des_cols:
    stats_table[col] = stats_table[col].round(3).map(lambda x: f'{x:.3f}')




#%% ---------------------------------------------------------------------------------------
# ------------------------LaTeX table settings---------------------------------------------
# ----------------------------------------------------------------------------------------

# Width of the Description column
DESC_COL_WIDTH = "5.2cm"

# Row spacing in the table
TABULAR_ARRAYSTRETCH = 1.2
INTER_VAR_SPACE = r"[0.15\baselineskip]"

# Spacing inside multi-line Description cells
CELL_BASELINESKIP = r"0.95\baselineskip"
CELL_SPLIT_GAP = r"[-0.8ex]"





#%% ---------------------------------------------------------------------------------------
# ------------------------Variable descriptions--------------------------------------------
# ----------------------------------------------------------------------------------------
intro_dict = {
    'Year': '',
    'Quarter': '',
    'ST_Sample': 'Flag high-risk stocks',
    'Exit_Sample': 'Flag stocks entering delisting',
    'Inc_YoY': r'$(Income_{i,t} - Income_{i,t-4}) / Income_{i,t-4}$',
    'Inc_YoY_A': r'$(Income_{i,t} - Income_{i,t-4}) / Asset_{i,t-4}$',
    'Inc_IHS_d': r'$\operatorname{asinh}(Income_{i,t}) - \operatorname{asinh}(Income_{i,t-4})$',
    'Major_Change': 'Indicator of significant changes',
    'Top_Share': "Largest shareholder's equity ratio",
    'Supplier_Exit': 'Suppl. rel. end (t+1)',
    'Customer_Exit': 'Cust. rel. end (t+1)'
}
stats_table['Description'] = stats_table['Variable'].map(intro_dict)





#%% ---------------------------------------------------------------------------------------
# ------------------------Helper functions-------------------------------------------------
# ----------------------------------------------------------------------------------------
def escape_latex_text(s: str) -> str:
    """
    Escape LaTeX special characters for plain text only.
    Do not use this for math expressions.
    """
    repl = {
        '&': r'\&',
        '%': r'\%',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\{',
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    return s




def split_by_at(desc: str):
    """
    Return (desc1, desc2, is_split)

    Rules:
    - If there is no @, do not split.
    - If the whole string is wrapped in $...$, and contains @,
      split it into two independent math expressions.
    """
    if desc is None or (isinstance(desc, float) and pd.isna(desc)) or desc == '':
        return '', '', False

    desc = str(desc)

    if '@' not in desc:
        return desc, '', False

    stripped = desc.strip()

    if stripped.startswith('$') and stripped.endswith('$'):
        inner = stripped[1:-1]
        left_inner, right_inner = inner.split('@', 1)
        return f"${left_inner.strip()}$", f"${right_inner.strip()}$", True

    left, right = desc.split('@', 1)
    return left.strip(), right.strip(), True


def make_desc_cell(desc1: str, desc2: str, is_split: bool) -> str:
    """
    Build the LaTeX content for the Description cell.
    The second column itself is already p{...}, so no need for \parbox here.
    """
    cell_preamble = rf"\setlength{{\baselineskip}}{{{CELL_BASELINESKIP}}}\selectfont "

    if is_split:
        return rf"{cell_preamble}{desc1}\\{CELL_SPLIT_GAP}{desc2}"
    return rf"{cell_preamble}{desc1}"






#%% ---------------------------------------------------------------------------------------
# ------------------------Generate LaTeX rows----------------------------------------------
# ----------------------------------------------------------------------------------------
latex_rows = []
n_rows = len(stats_table)

for idx, row in stats_table.iterrows():
    var = row['Variable']
    desc = row['Description']

    # Escape underscores in variable names
    var = '' if pd.isna(var) else str(var).replace('_', r'\_')

    # Split description at @ if needed
    desc1, desc2, is_split = split_by_at(desc)

    # Escape only plain text; leave LaTeX math untouched
    if '$' not in str(desc1):
        desc1 = escape_latex_text(str(desc1))
    if '$' not in str(desc2):
        desc2 = escape_latex_text(str(desc2))

    desc_cell = make_desc_cell(desc1, desc2, is_split)

    obs = row['Obs']
    mean = row['Mean']
    sd = row['SD']
    min_val = row['Min']
    max_val = row['Max']

    end_space = "" if idx == n_rows - 1 else INTER_VAR_SPACE

    latex_rows.append(
        f"{var} & {desc_cell} & {obs} & {mean} & {sd} & {min_val} & {max_val} \\\\{end_space}"
    )

latex_content = "\n".join(latex_rows)







#%% ---------------------------------------------------------------------------------------
# ------------------------Generate full LaTeX table----------------------------------------
# ----------------------------------------------------------------------------------------
latex_template = rf"""
\begin{{table}}[width=.95\linewidth,cols=7,pos=h]
\caption{{Summary statistics}}
\label{{tab_descriptive_statistics}}
\footnotesize
\setlength{{\tabcolsep}}{{3.5pt}}
\renewcommand{{\arraystretch}}{{{TABULAR_ARRAYSTRETCH}}}
\begin{{tabular*}}{{\tblwidth}}{{@{{\extracolsep{{\fill}}}}l p{{{DESC_COL_WIDTH}}} c c c c c@{{}}}}
\toprule
Variables & Description & Obs & Mean & SD & Min & Max \\
\midrule
{latex_content}
\bottomrule
\end{{tabular*}}
\end{{table}}
"""

print(latex_template)

output_path = Path(table_loc, 't1.tex')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(latex_template)

print(f"LaTeX table saved to: {output_path}")