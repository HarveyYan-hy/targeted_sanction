#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from tqdm import tqdm
import re
from collections import Counter
from code_file.py_code.py_config import stata_data, processing_data





#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()
stata_data_loc = stata_data()






#%% ---------------------------------------------------------------------------------------
# ------------------------Import data----------------------------------------------
# ----------------------------------------------------------------------------------------
panel_df = pd.read_parquet(f"{processing_data_loc}/stage1_panel.parquet")
exp_panel = pd.read_parquet(f"{processing_data_loc}/exp_panel.parquet")
raw_panle = pd.read_parquet(f"{processing_data_loc}/stage1_panel.parquet")
sanction_df = pd.read_parquet(f"{processing_data_loc}/sanction_info.parquet")






#%% ---------------------------------------------------------------------------------------
# ------------------------Reset exposure indicators----------------------------------------------
# ----------------------------------------------------------------------------------------

# Keep only necessary columns
exp_panel = exp_panel[['id','yq','up_dist','down_dist','upexpected','downexpected']]


# Keep only pre-event actual exposure
exp_panel.loc[exp_panel['upexpected']==1,'up_dist'] = np.nan
exp_panel.loc[exp_panel['downexpected']==1, 'down_dist'] = np.nan
exp_panel = exp_panel.drop(columns=['upexpected','downexpected'])



# Set exposure direction
exp_panel.loc[exp_panel['down_dist'].notna() & exp_panel['up_dist'].notna(), 'direction'] = 'double_exp'
exp_panel.loc[exp_panel['down_dist'].notna() & exp_panel['up_dist'].isna(), 'direction'] = 'down'
exp_panel.loc[exp_panel['down_dist'].isna() & exp_panel['up_dist'].notna(), 'direction'] = 'up'
exp_panel.loc[exp_panel['down_dist'].isna() & exp_panel['up_dist'].isna(), 'direction'] = 'no_exp'





# Mark continuous exposure for segmentation
exp_panel.loc[exp_panel['direction']=='no_exp','exposed'] = 0
exp_panel.loc[exp_panel['direction']!='no_exp','exposed'] = 1
exp_panel['exposed'] = exp_panel['exposed'].astype('Int64')




# Set exposure level
exp_panel.loc[exp_panel['direction']=='down','dist'] = exp_panel['down_dist']
exp_panel.loc[exp_panel['direction']=='up','dist'] = exp_panel['up_dist']
exp_panel.drop(columns=['down_dist','up_dist'],inplace=True)





#%% ---------------------------------------------------------------------------------------
# ------------------------Firm classification----------------------------------------------
# ----------------------------------------------------------------------------------------
# Sanctioned firms
san_set = set(sanction_df['id'].unique())
print('san_set',len(san_set))




# Exposed firms
dirty_set = set(
    exp_panel[exp_panel['direction'] != 'no_exp']['id'].unique()
)
dirty_set = dirty_set - san_set
print('dirty_set',len(dirty_set))



# Clean firms
clean_set = set(exp_panel['id'].unique())
clean_set = clean_set - dirty_set
clean_set = clean_set - san_set
print('clean set',len(clean_set))



# Keep only dirty firms in the exposure panel
exp_panel = exp_panel[exp_panel['id'].isin(dirty_set)]






#%% ---------------------------------------------------------------------------------------
# ------------------------Process each exposure episode---------------------------------------------
# ----------------------------------------------------------------------------------------

# End time of the first exposure
df_sorted = exp_panel.sort_values(["id", "yq"]).copy()
next_exposed = df_sorted.groupby("id")["exposed"].shift(-1)
next_exposed = next_exposed.fillna(0)
mask = (df_sorted["exposed"] == 1) & (next_exposed == 0)
exp_end_df = (
    df_sorted.loc[mask]
    .groupby("id")["yq"]
    .apply(lambda s: sorted(set(s)))  
    .reset_index(name="yq_set")
)
exp_end_df['first_end'] = exp_end_df['yq_set'].apply(lambda x: min(x))



# Keep only the first exposure
exp_panel = exp_panel.merge(exp_end_df[['id','first_end']], on=['id'], how='left')
exp_panel = exp_panel[exp_panel['yq'] <= exp_panel['first_end']]



# Drop firms with double exposure
double_exp_panel = exp_panel[exp_panel['direction'] == 'double_exp']
double_exp_set = set(double_exp_panel['id'].unique())
exp_panel = exp_panel[~exp_panel['id'].isin(double_exp_set)]








#%% ---------------------------------------------------------------------------------------
# ------------------------Process each exposure type one by one---------------------------------------------
# ----------------------------------------------------------------------------------------
result_list = []

for gid, id_group in exp_panel.groupby('id', sort=False):
    
    # Sort
    id_group = id_group.sort_values('yq').copy()

    # Exposure start time
    id_group['exp_start'] = id_group[id_group['exposed'] == 1]['yq'].min()

    # Exposure end time 
    id_group['exp_end'] = id_group[id_group['exposed'] == 1]['yq'].max()


    # Exposure level
    #exp_dist = id_group[id_group['exposed'] == 1]['dist'].min()
    exp_dist = id_group[id_group['exposed'] == 1]['dist'].iloc[0]

    # Exposure direction
    exp_direction = id_group[id_group['exposed'] == 1]['direction'].iloc[0]


    # Combine into exposure type
    id_group['exp_type'] = exp_direction + str(exp_dist)


    # Append to list
    result_list.append(id_group)


# Combine into a dataframe
exp_panel = pd.concat(result_list, ignore_index=True)


# Drop irrelevant columns
exp_panel.drop(columns=['dist','direction','exposed','first_end'],inplace=True)




# Calculate relative time
exp_panel['rel_time'] = exp_panel['yq'] - exp_panel['exp_start']


# Distribution of exposure types
exp_panel['exp_type'].value_counts()











#%% ---------------------------------------------------------------------------------------
# ------------------------Grouping----------------------------------------------
# ----------------------------------------------------------------------------------------

# Never-exposed sample
clean_df = panel_df[panel_df['id'].isin(clean_set)][['id','yq']]





# Set window
before_window = -12
after_window = 8


# Exposure types
group_type_list = list(exp_panel['exp_type'].unique())



for group_type in group_type_list: 

    # ---------------- Treatment group ----------------
    group_treat = exp_panel[exp_panel['exp_type'] == group_type].copy()
    group_treat['treated'] = 1

    # Collapse window
    group_treat.loc[group_treat['rel_time'] <= before_window, 'rel_time'] = before_window
    group_treat.loc[group_treat['rel_time'] >= after_window, 'rel_time'] = after_window  


    # Add dummy variables
    vals = group_treat['rel_time'].to_numpy(copy=False)
    dummy_cols = []  
    for v in range(before_window, after_window+1):  
        name = f"D_{abs(v)}" if v < 0 else f"D{v}"
        group_treat[name] = (vals == v).astype('int8')
        dummy_cols.append(name)




    # ---------------- Control group ----------------
    group_control = exp_panel[exp_panel['exp_type'] != group_type].copy()
    group_control = group_control[group_control['rel_time'] < 0]  # Pre-treatment periods

    #group_control = pd.concat([group_control, clean_df]).reset_index(drop=True)
    group_control = clean_df.copy().reset_index(drop=True)
    
    group_control['treated'] = 0
    group_control[['exp_start','exp_end','exp_type','rel_time']] = np.nan


    # Merge 
    group_df = pd.concat([group_treat, group_control]).reset_index(drop=True)


    # Fill missing values of all event dummies in this group with 0
    group_df[dummy_cols] = group_df[dummy_cols].fillna(0).astype('int8')


    # Add financial variables
    group_df = group_df.merge(raw_panle, on=['id', 'yq'], how='left')
    group_df['fake_id'] = group_df['id']
    
    print(group_type,group_df.shape)
    
    # Save
    group_df.to_stata(f"{stata_data_loc}/stage2_{group_type}.dta", write_index=False)