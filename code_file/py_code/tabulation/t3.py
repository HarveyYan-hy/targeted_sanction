#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules---------------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from pathlib import Path
from code_file.py_code.py_config import tables_loc, s1_result





#%% ---------------------------------------------------------------------------------------
# ------------------------Get file locations-----------------------------------------------
# ----------------------------------------------------------------------------------------
table_loc = tables_loc()
s1_loc = s1_result()





#%% ---------------------------------------------------------------------------------------
# ------------------------Import regression results----------------------------------------
# ----------------------------------------------------------------------------------------
est_list = [
    'patent_low', 'patent_high', 'soe', 'nsoe',
    'cn_low', 'cn_high', 'eig_low', 'eig_high'
]

result_list = []

for est in est_list:
    # Read one regression result file
    est_df = pd.read_stata(Path(s1_loc, f'{est}.dta'))

    # Keep only the main explanatory variable
    est_df = est_df[est_df['parm'] == 'sanpost']

    # Extract the first-row values
    result_list.append(
        {
            'est': est,
            'coff': est_df['estimate'].iloc[0],
            'p': est_df['p'].iloc[0],
            'std': est_df['stderr'].iloc[0],
            'n': est_df['N'].iloc[0],
            'r2a': est_df['r2a'].iloc[0],
        }
    )

s1_het = pd.DataFrame(result_list)




#%% ---------------------------------------------------------------------------------------
# ------------------------Format regression outputs----------------------------------------
# ----------------------------------------------------------------------------------------

# Add significance stars
s1_het['star'] = ''
s1_het.loc[s1_het['p'] <= 0.1, 'star'] = '*'
s1_het.loc[s1_het['p'] <= 0.05, 'star'] = '**'
s1_het.loc[s1_het['p'] <= 0.01, 'star'] = '***'

# Format numeric columns to four decimals
des_cols = ['coff', 'p', 'std', 'r2a']
for col in des_cols:
    s1_het[col] = s1_het[col].round(4)
    s1_het[col] = s1_het[col].apply(lambda x: f'{x:.4f}')

# Format observations as integers
s1_het['n'] = s1_het['n'].apply(lambda x: f'{int(x)}')

# Append significance stars to coefficients
s1_het['coff'] = s1_het['coff'].astype(str) + s1_het['star']

# Convert all columns to string for LaTeX output
s1_het = s1_het.astype(str)


#%% ---------------------------------------------------------------------------------------
# ------------------------Add table metadata-----------------------------------------------
# ----------------------------------------------------------------------------------------

# Controls
control_dict = {
    'cn_low': 'Yes',
    'cn_high': 'Yes',
    'eig_low': 'Yes',
    'eig_high': 'Yes',
    'patent_low': 'Yes',
    'patent_high': 'Yes',
    'soe': 'Yes',
    'nsoe': 'Yes'
}
s1_het['control'] = s1_het['est'].map(control_dict)

# Firm fixed effects
firmfe_dict = {
    'cn_low': 'Yes',
    'cn_high': 'Yes',
    'eig_low': 'Yes',
    'eig_high': 'Yes',
    'patent_low': 'Yes',
    'patent_high': 'Yes',
    'soe': 'Yes',
    'nsoe': 'Yes'
}
s1_het['firmfe'] = s1_het['est'].map(firmfe_dict)

# Industry-by-time fixed effects
industrytime_dict = {
    'cn_low': 'Yes',
    'cn_high': 'Yes',
    'eig_low': 'Yes',
    'eig_high': 'Yes',
    'patent_low': 'Yes',
    'patent_high': 'Yes',
    'soe': 'Yes',
    'nsoe': 'Yes'
}
s1_het['industrytimefe'] = s1_het['est'].map(industrytime_dict)

# Province-by-time fixed effects
provincetime_dict = {
    'cn_low': 'No',
    'cn_high': 'No',
    'eig_low': 'No',
    'eig_high': 'No',
    'patent_low': 'No',
    'patent_high': 'No',
    'soe': 'No',
    'nsoe': 'No'
}
s1_het['provincetimefe'] = s1_het['est'].map(provincetime_dict)

# Whether flagged firms are dropped
st_dict = {
    'cn_low': 'No',
    'cn_high': 'No',
    'eig_low': 'No',
    'eig_high': 'No',
    'patent_low': 'No',
    'patent_high': 'No',
    'soe': 'No',
    'nsoe': 'No'
}
s1_het['Dropflaggedsample'] = s1_het['est'].map(st_dict)

# Parent group labels
parent_label = {
    'cn_low': 'Supplier Localization',
    'cn_high': 'Supplier Localization',
    'eig_low': 'Supplier Centrality',
    'eig_high': 'Supplier Centrality',
    'patent_low': 'Patent Num',
    'patent_high': 'Patent Num',
    'soe': 'Ownership',
    'nsoe': 'Ownership'
}
s1_het['parentlabel'] = s1_het['est'].map(parent_label)
s1_het['parentlabel'] = s1_het['parentlabel'].astype(str).str.replace('_', r'\_', regex=False)

# Column labels
col_labels = {
    'cn_low': 'Foreign',
    'cn_high': 'Domestic',
    'eig_low': 'Peripheral',
    'eig_high': 'Central',
    'patent_low': 'Low',
    'patent_high': 'High',
    'soe': 'SOE',
    'nsoe': 'NSOE'
}
s1_het['label'] = s1_het['est'].map(col_labels)
s1_het['label'] = s1_het['label'].astype(str).str.replace('_', r'\_', regex=False)


#%% ---------------------------------------------------------------------------------------
# ------------------------Reorder columns for LaTeX output--------------------------------
# ----------------------------------------------------------------------------------------
output_order = [
    'patent_low', 'patent_high', 'nsoe', 'soe',
    'cn_low', 'cn_high', 'eig_high', 'eig_low'
]

s1_het = s1_het.set_index('est').reindex(output_order).reset_index()


#%% ---------------------------------------------------------------------------------------
# ------------------------Build LaTeX table------------------------------------------------
# ----------------------------------------------------------------------------------------
TABLE_CAPTION = "Heterogeneity analysis"
TABLE_LABEL = "s1_het"
TABLE_WIDTH = r".95\linewidth"
TABLE_COLS = 9
TABLE_POS = "h"
TABLE_ARRAYSTRETCH = 1.3

latex_tpl = r"""
\begin{{table}}[width={table_width},cols={table_cols},pos={table_pos}]
\caption{{{caption}}}\label{{{label}}}
\footnotesize
\setlength{{\tabcolsep}}{{3pt}}
\renewcommand{{\arraystretch}}{{{arraystretch}}}
\begin{{tabular*}}{{\tblwidth}}{{@{{\extracolsep{{\fill}}}}lcccccccc@{{}}}}
\toprule
 & (1) & (2) & (3) & (4) & (5) & (6) & (7) & (8) \\
\cmidrule(lr){{2-9}}
 & \multicolumn{{2}}{{c}}{{{group_label1}}}
 & \multicolumn{{2}}{{c}}{{{group_label2}}}
 & \multicolumn{{2}}{{c}}{{{group_label3}}}
 & \multicolumn{{2}}{{c}}{{{group_label4}}} \\
\cmidrule(lr){{2-3}}\cmidrule(lr){{4-5}}\cmidrule(lr){{6-7}}\cmidrule(lr){{8-9}}
 & {col_label1} & {col_label2} & {col_label3} & {col_label4} & {col_label5} & {col_label6} & {col_label7} & {col_label8} \\
\midrule
{var_label} & {coeff1} & {coeff2} & {coeff3} & {coeff4} & {coeff5} & {coeff6} & {coeff7} & {coeff8} \\
 & ({se1}) & ({se2}) & ({se3}) & ({se4}) & ({se5}) & ({se6}) & ({se7}) & ({se8}) \\
Controls & {controls1} & {controls2} & {controls3} & {controls4} & {controls5} & {controls6} & {controls7} & {controls8} \\
Firm FE & {firm_fe1} & {firm_fe2} & {firm_fe3} & {firm_fe4} & {firm_fe5} & {firm_fe6} & {firm_fe7} & {firm_fe8} \\
Industry-by-time FE & {industry_time_fe1} & {industry_time_fe2} & {industry_time_fe3} & {industry_time_fe4} & {industry_time_fe5} & {industry_time_fe6} & {industry_time_fe7} & {industry_time_fe8} \\
Province-by-time FE & {province_time_fe1} & {province_time_fe2} & {province_time_fe3} & {province_time_fe4} & {province_time_fe5} & {province_time_fe6} & {province_time_fe7} & {province_time_fe8} \\
Drop Flagged Sample & {drop_flagged_sample1} & {drop_flagged_sample2} & {drop_flagged_sample3} & {drop_flagged_sample4} & {drop_flagged_sample5} & {drop_flagged_sample6} & {drop_flagged_sample7} & {drop_flagged_sample8} \\
Obs. & {obs1} & {obs2} & {obs3} & {obs4} & {obs5} & {obs6} & {obs7} & {obs8} \\
Adj. $R^2$ & {r2_1} & {r2_2} & {r2_3} & {r2_4} & {r2_5} & {r2_6} & {r2_7} & {r2_8} \\
\bottomrule
\end{{tabular*}}

\vspace{{2pt}}
\parbox{{\tblwidth}}{{\raggedright \footnotesize Notes: *$p<0.1$, **$p<0.05$, ***$p<0.01$. Standard errors are reported in parentheses.}}
\end{{table}}
""".strip()

var_label = r"Sanction $\times$ Post"

# Collect subgroup labels
col_labels_8 = s1_het["label"].tolist()
if len(col_labels_8) != 8:
    raise ValueError(f"Expected 8 column labels, got {len(col_labels_8)}")

parent_8 = s1_het["parentlabel"].tolist()
if len(parent_8) != 8:
    raise ValueError(f"Expected 8 parent labels, got {len(parent_8)}")

group_labels_4 = [parent_8[i] for i in [0, 2, 4, 6]]

fill_dict = {
    "table_width": TABLE_WIDTH,
    "table_cols": TABLE_COLS,
    "table_pos": TABLE_POS,
    "caption": TABLE_CAPTION,
    "label": TABLE_LABEL,
    "arraystretch": TABLE_ARRAYSTRETCH,
    "var_label": var_label,
    "group_label1": group_labels_4[0],
    "group_label2": group_labels_4[1],
    "group_label3": group_labels_4[2],
    "group_label4": group_labels_4[3],
}

# Fill column labels
for i in range(1, 9):
    fill_dict[f"col_label{i}"] = col_labels_8[i - 1]

# Fill coefficients and standard errors
for i in range(1, 9):
    fill_dict[f"coeff{i}"] = s1_het.loc[i - 1, "coff"]
    fill_dict[f"se{i}"] = s1_het.loc[i - 1, "std"]

# Fill controls and fixed effects
for i in range(1, 9):
    fill_dict[f"controls{i}"] = s1_het.loc[i - 1, "control"]
    fill_dict[f"firm_fe{i}"] = s1_het.loc[i - 1, "firmfe"]
    fill_dict[f"industry_time_fe{i}"] = s1_het.loc[i - 1, "industrytimefe"]
    fill_dict[f"province_time_fe{i}"] = s1_het.loc[i - 1, "provincetimefe"]
    fill_dict[f"drop_flagged_sample{i}"] = s1_het.loc[i - 1, "Dropflaggedsample"]

# Fill observations and adjusted R-squared
for i in range(1, 9):
    fill_dict[f"obs{i}"] = s1_het.loc[i - 1, "n"]
    fill_dict[f"r2_1" if i == 1 else f"r2_{i}"] = s1_het.loc[i - 1, "r2a"]

# Render and write LaTeX
latex_out = latex_tpl.format(**fill_dict)

out_path = Path(table_loc, "t3.tex")
out_path.write_text(latex_out, encoding="utf-8")

print(f"[OK] LaTeX table written to: {out_path}")