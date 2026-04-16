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
est_list = ['no_control', 'baseline', 'robust_asset', 'robust_ihs', 'robust_province', 'robust_st']

result_list = []
for est in est_list:
    # Read the regression result file
    est_df = pd.read_stata(Path(s1_loc, f'{est}.dta'))

    # Keep only the core explanatory variable
    est_df = est_df[est_df['parm'] == 'sanpost']

    # Extract the first row
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

s1_df = pd.DataFrame(result_list)


#%% ---------------------------------------------------------------------------------------
# ------------------------Process table content--------------------------------------------
# ----------------------------------------------------------------------------------------

# Add significance stars
s1_df['star'] = ''
s1_df.loc[s1_df['p'] <= 0.1, 'star'] = '*'
s1_df.loc[s1_df['p'] <= 0.05, 'star'] = '**'
s1_df.loc[s1_df['p'] <= 0.01, 'star'] = '***'

# Round numeric columns
for col in ['coff', 'p', 'std', 'r2a']:
    s1_df[col] = s1_df[col].round(4)

# Format numeric columns for LaTeX output
s1_df['coff'] = s1_df['coff'].apply(lambda x: f'{x:.4f}')
s1_df['std'] = s1_df['std'].apply(lambda x: f'{x:.4f}')
s1_df['r2a'] = s1_df['r2a'].apply(lambda x: f'{x:.4f}')
s1_df['n'] = s1_df['n'].apply(lambda x: f'{int(x):,}')

# Append significance stars to coefficients
s1_df['coff'] = s1_df['coff'] + s1_df['star']

# Map control variables
control_dict = {
    'no_control': 'No',
    'baseline': 'Yes',
    'robust_asset': 'Yes',
    'robust_ihs': 'Yes',
    'robust_province': 'Yes',
    'robust_st': 'Yes'
}
s1_df['control'] = s1_df['est'].map(control_dict)

# Map firm fixed effects
firmfe_dict = {
    'no_control': 'No',
    'baseline': 'Yes',
    'robust_asset': 'Yes',
    'robust_ihs': 'Yes',
    'robust_province': 'Yes',
    'robust_st': 'Yes'
}
s1_df['firmfe'] = s1_df['est'].map(firmfe_dict)

# Map industry-by-time fixed effects
industrytime_dict = {
    'no_control': 'No',
    'baseline': 'Yes',
    'robust_asset': 'Yes',
    'robust_ihs': 'Yes',
    'robust_province': 'Yes',
    'robust_st': 'Yes'
}
s1_df['industrytimefe'] = s1_df['est'].map(industrytime_dict)

# Map province-by-time fixed effects
provincetime_dict = {
    'no_control': 'No',
    'baseline': 'No',
    'robust_asset': 'No',
    'robust_ihs': 'No',
    'robust_province': 'Yes',
    'robust_st': 'No'
}
s1_df['provincetimefe'] = s1_df['est'].map(provincetime_dict)

# Map whether the flagged sample is dropped
st_dict = {
    'no_control': 'No',
    'baseline': 'No',
    'robust_asset': 'No',
    'robust_ihs': 'No',
    'robust_province': 'No',
    'robust_st': 'Yes'
}
s1_df['Dropflaggedsample'] = s1_df['est'].map(st_dict)

# Map column labels
col_labels = {
    'no_control': 'No Controls',
    'baseline': 'Baseline',
    'robust_asset': 'Inc_YoY_A',
    'robust_ihs': 'Inc_IHS_d',
    'robust_province': 'COVID-19',
    'robust_st': 'Drop Flagged'
}
s1_df['label'] = s1_df['est'].map(col_labels)

# Escape underscores for LaTeX
s1_df['label'] = s1_df['label'].astype(str).str.replace('_', r'\_', regex=False)

# Reorder rows
s1_df = s1_df.set_index('est').reindex(est_list).reset_index()


#%% ---------------------------------------------------------------------------------------
# ------------------------Write LaTeX table-----------------------------------------------
# ----------------------------------------------------------------------------------------
TABLE_WIDTH = r'.95\linewidth'
TABLE_COLS = 7
TABLE_POS = 'h'
TABLE_ARRAYSTRETCH = 1.2
TABLE_CAPTION = 'Baseline and robustness results'
TABLE_LABEL = 'tab:s1_baseline_robust'
VAR_LABEL = r'Sanction $\times$ Post'

latex_tpl = r"""
\begin{{table}}[width={table_width},cols={table_cols},pos={table_pos}]
\caption{{{caption}}}\label{{{label}}}
\footnotesize
\renewcommand{{\arraystretch}}{{{arraystretch}}}
\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular*}}{{\tblwidth}}{{@{{\extracolsep{{\fill}}}}lcccccc@{{}}}}
\toprule
 & (1) & (2) & (3) & (4) & (5) & (6) \\
 & {col_label1} & {col_label2} & {col_label3} & {col_label4} & {col_label5} & {col_label6} \\
\midrule
{var_label} & {coeff1} & {coeff2} & {coeff3} & {coeff4} & {coeff5} & {coeff6} \\
 & ({se1}) & ({se2}) & ({se3}) & ({se4}) & ({se5}) & ({se6}) \\
Controls & {controls1} & {controls2} & {controls3} & {controls4} & {controls5} & {controls6} \\
Firm FE & {firm_fe1} & {firm_fe2} & {firm_fe3} & {firm_fe4} & {firm_fe5} & {firm_fe6} \\
Industry-by-time FE & {industry_time_fe1} & {industry_time_fe2} & {industry_time_fe3} & {industry_time_fe4} & {industry_time_fe5} & {industry_time_fe6} \\
Province-by-time FE & {province_time_fe1} & {province_time_fe2} & {province_time_fe3} & {province_time_fe4} & {province_time_fe5} & {province_time_fe6} \\
Drop Flagged Sample & {drop_flagged_sample1} & {drop_flagged_sample2} & {drop_flagged_sample3} & {drop_flagged_sample4} & {drop_flagged_sample5} & {drop_flagged_sample6} \\
Obs. & {obs1} & {obs2} & {obs3} & {obs4} & {obs5} & {obs6} \\
Adj. $R^2$ & {r21} & {r22} & {r23} & {r24} & {r25} & {r26} \\
\bottomrule
\end{{tabular*}}

\par\vspace{{0.5em}}
\noindent\parbox{{\tblwidth}}{{\footnotesize Notes: *$p<0.1$, **$p<0.05$, ***$p<0.01$. Standard errors are in parentheses.}}
\end{{table}}
""".strip()

fill = {
    'table_width': TABLE_WIDTH,
    'table_cols': TABLE_COLS,
    'table_pos': TABLE_POS,
    'caption': TABLE_CAPTION,
    'label': TABLE_LABEL,
    'arraystretch': TABLE_ARRAYSTRETCH,
    'var_label': VAR_LABEL
}

for j, row in enumerate(s1_df.itertuples(index=False), start=1):
    fill[f'col_label{j}'] = str(getattr(row, 'label'))
    fill[f'coeff{j}'] = str(getattr(row, 'coff'))
    fill[f'se{j}'] = str(getattr(row, 'std'))
    fill[f'controls{j}'] = str(getattr(row, 'control'))
    fill[f'firm_fe{j}'] = str(getattr(row, 'firmfe'))
    fill[f'industry_time_fe{j}'] = str(getattr(row, 'industrytimefe'))
    fill[f'province_time_fe{j}'] = str(getattr(row, 'provincetimefe'))
    fill[f'drop_flagged_sample{j}'] = str(getattr(row, 'Dropflaggedsample'))
    fill[f'obs{j}'] = str(getattr(row, 'n'))
    fill[f'r2{j}'] = str(getattr(row, 'r2a'))

latex_out = latex_tpl.format(**fill)

print(latex_out)

# Save the LaTeX table
out_path = Path(table_loc, 't2.tex')
out_path.write_text(latex_out, encoding='utf-8')