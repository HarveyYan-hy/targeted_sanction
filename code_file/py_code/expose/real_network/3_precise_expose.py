#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import re
import os
import networkx as nx
import json
from code_file.py_code.py_config import raw_data, stata_data, processing_data






#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()
stata_data_loc = stata_data()






#%% ---------------------------------------------------------------------------------------
# ------------------------Load data----------------------------------------------
# ----------------------------------------------------------------------------------------
factset_adjust = pd.read_parquet(f"{processing_data_loc}/factset_rel.parquet")
path_df = pd.read_parquet(f"{processing_data_loc}/expose_path.parquet")
panel_df = pd.read_parquet(f"{processing_data_loc}/basic_panel.parquet",columns=['id','yq'])
full_up = pd.read_parquet(f"{processing_data_loc}/full_expose_up.parquet")
full_down = pd.read_parquet(f"{processing_data_loc}/full_expose_down.parquet")





# Sample period
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3



#%% ---------------------------------------------------------------------------------------
# ------------------------Calculate relationship coverage periods----------------------------------------------
# ----------------------------------------------------------------------------------------

# Convert to tuples
factset_adjust['pair'] = list(zip(factset_adjust['supplier_company_id'], factset_adjust['customer_company_id']))
factset_adjust = factset_adjust.drop(columns=['supplier_company_id','customer_company_id','id'])




# Generate coverage sets
factset_adjust['period'] = factset_adjust.apply(lambda row: set(range(row['s_yq'], row['e_yq'] + 1)), axis=1)
factset_adjust = factset_adjust.drop(columns=['s_date','e_date','s_yq','e_yq'])


# Merge relationship coverage periods
factset_group = factset_adjust.groupby('pair')['period'].agg(lambda periods: set.union(*periods) if len(periods) > 0 else set()).reset_index()



# Convert to a dictionary for lookup
rel_dict = dict(zip(factset_group['pair'], factset_group['period']))







#%% ---------------------------------------------------------------------------------------
# ------------------------Process paths----------------------------------------------
# ----------------------------------------------------------------------------------------
# Convert paths to nested lists
path_df['paths'] = path_df['paths'].apply(lambda x: json.loads(x) if x else [])


# Number of paths
path_df['path_num'] = path_df['paths'].apply(lambda a: len(a))


# Expand by path
path_df = path_df.explode('paths', ignore_index=True)


# Split into steps
max_elems  = 9              # path has at most 9 elements
max_pairs  = max_elems - 1  # at most 8 pairs
stp_cols   = [f'stp{i}' for i in range(1, max_pairs+1)]
path_df[stp_cols] = pd.DataFrame(
    path_df['paths'].apply(
        lambda L: (list(map(tuple, zip(L, L[1:]))) +            # adjacent pairs [('a','b'), ('b','c'), ...]
                   [pd.NA] * max(0, max_pairs - max(0, len(L)-1)))[:max_pairs]  # pad to 8
    ).tolist(),
    index=path_df.index)



# Calculate covered periods for each stp
stp_cols = [f'stp{i}' for i in range(1, max_elems)] 
for stp in stp_cols:
    periods_col = f'{stp}_periods'
    path_df[periods_col] = path_df[stp].apply(
        lambda p: rel_dict.get(p, set()) if pd.notna(p) else set()
    )



# Take intersection
def compute_path_period(row):
    periods = [row[f'{stp}_periods'] for stp in stp_cols if pd.notna(row[stp])]
    if not periods:
        return set()
    return set.intersection(*periods)

path_df['path_period'] = path_df.apply(compute_path_period, axis=1)


# Clean columns
stp_columns = [col for col in path_df.columns if col.startswith('stp')]
path_df.drop(columns=stp_columns, inplace=True)




# Get exposure start and end periods
path_df['exp_start'] = path_df['yq']

def find_max_continuous_end(start, periods):
    if not periods or start not in periods:
        return None  # If the set is empty or start is not in the set, return None (can be adjusted to start - 1 or others as needed)
    end = start
    while end + 1 in periods:
        end += 1
    return end
path_df['exp_end'] = path_df.apply(lambda row: find_max_continuous_end(row['exp_start'], row['path_period']), axis=1)


# Clean columns
path_df.drop(columns=['paths','path_period','path_num','yq'], inplace=True)






#%% ---------------------------------------------------------------------------------------
# ------------------------Process full exposure----------------------------------------------
# ----------------------------------------------------------------------------------------

full_up = full_up.drop(columns=['san_yq','san_node'])
full_down = full_down.drop(columns=['san_yq','san_node'])

full_up['dist'] = (full_up['dist'] - 1) // 2 + 1
full_down['dist'] = (full_down['dist'] - 1) // 2 + 1

full_up = full_up.drop_duplicates().sort_values(['id','yq','dist']).reset_index(drop=True)
full_down = full_down.drop_duplicates().sort_values(['id','yq','dist']).reset_index(drop=True)

full_up = full_up.loc[full_up.groupby(['id', 'yq'])['dist'].idxmin()].drop_duplicates().reset_index(drop=True)
full_down = full_down.loc[full_down.groupby(['id', 'yq'])['dist'].idxmin()].drop_duplicates().reset_index(drop=True)

full_up = full_up[full_up['yq']<=SAMPLE_PERIOD_END]
full_down = full_down[full_down['yq']<=SAMPLE_PERIOD_END]






#%% ---------------------------------------------------------------------------------------
# ------------------------Distinguish two types of exposure----------------------------------------------
# ----------------------------------------------------------------------------------------
# Separate upstream and downstream
up_df = path_df[path_df['san_node'] == path_df['down_node']]
up_df = up_df.drop(columns=['down_node','san_node'])
up_df = up_df.rename(columns={'up_node':'id'})

down_df = path_df[path_df['san_node'] == path_df['up_node']]
down_df = down_df.drop(columns=['up_node','san_node'])
down_df = down_df.rename(columns={'down_node':'id'})





# Expand to period-by-period
up_df['exp_period'] = up_df.apply(lambda row: list(range(row['exp_start'], row['exp_end'] + 1)), axis=1)
down_df['exp_period'] = down_df.apply(lambda row: list(range(row['exp_start'], row['exp_end'] + 1)), axis=1)

up_df = up_df.explode('exp_period', ignore_index=True)
down_df = down_df.explode('exp_period', ignore_index=True)

up_df = up_df.drop(columns=['exp_start','exp_end'])
down_df = down_df.drop(columns=['exp_start','exp_end'])

up_df = up_df.rename(columns={'exp_period':'yq'})
down_df = down_df.rename(columns={'exp_period':'yq'})
up_df['yq'] = up_df['yq'].astype('Int64')
down_df['yq'] = down_df['yq'].astype('Int64')


# Truncate sample period
up_df = up_df[up_df['yq']<=SAMPLE_PERIOD_END]
down_df = down_df[down_df['yq']<=SAMPLE_PERIOD_END]




# Deduplicate
up_df = up_df.drop_duplicates().sort_values(['id','yq','dist']).reset_index(drop=True)
down_df = down_df.drop_duplicates().sort_values(['id','yq','dist']).reset_index(drop=True)


# Collapse levels
up_df['dist'] = (up_df['dist'] - 1) // 2 + 1
down_df['dist'] = (down_df['dist'] - 1) // 2 + 1




# Minimum-level rule
up_df = up_df.loc[up_df.groupby(['id', 'yq'])['dist'].idxmin()].drop_duplicates().reset_index(drop=True)
down_df = down_df.loc[down_df.groupby(['id', 'yq'])['dist'].idxmin()].drop_duplicates().reset_index(drop=True)




# Mark
up_df['upexpected'] = 0
down_df['downexpected'] = 0

full_up = full_up.merge(up_df[['id','yq','upexpected']],on=['id','yq'],how='left')
full_up['upexpected'] = full_up['upexpected'].fillna(1)

full_down = full_down.merge(down_df[['id','yq','downexpected']],on=['id','yq'],how='left')
full_down['downexpected'] = full_down['downexpected'].fillna(1)




#%% ---------------------------------------------------------------------------------------
# ------------------------Merge into panel data----------------------------------------------
# ----------------------------------------------------------------------------------------

# Rename columns
full_up.rename(columns={"dist": "up_dist"}, inplace=True)
full_down.rename(columns={"dist": "down_dist"}, inplace=True)




# Merge exposure relations into the panel
panel_df = panel_df.merge(full_up, on=["id", "yq"], how="left")
panel_df = panel_df.merge(full_down, on=["id", "yq"], how="left")



# Convert to integers
panel_df['down_dist'] = pd.to_numeric(panel_df['down_dist'], errors='coerce').astype('Int64')
panel_df['up_dist']   = pd.to_numeric(panel_df['up_dist'],   errors='coerce').astype('Int64')



# Assign dummy variables
for i in range(1, 5):
    panel_df[f'downshock{i}'] = (panel_df['down_dist'] == i).fillna(False).astype('int8')

for i in range(1, 5):
    panel_df[f'upshock{i}'] = (panel_df['up_dist'] == i).fillna(False).astype('int8')




#%% ---------------------------------------------------------------------------------------
# ------------------------Save data----------------------------------------------
# ----------------------------------------------------------------------------------------
panel_df.to_parquet(f"{processing_data_loc}/exp_panel.parquet", index=False)