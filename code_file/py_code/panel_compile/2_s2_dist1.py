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
# ------------------------OLS panel----------------------------------------------
# ----------------------------------------------------------------------------------------
# Merge exposure data
panel_df = panel_df.merge(exp_panel,on=['id','yq'],how='left')


# Drop sanctioned firms themselves
san_set = set(sanction_df['id'].unique())
panel_df = panel_df[~panel_df['id'].isin(san_set)]



# Save
panel_df.to_stata(f"{stata_data_loc}/stage2_ols.dta", write_index=False)
panel_df.to_parquet(f"{processing_data_loc}/stage2_ols.parquet", index=False)





#%% ---------------------------------------------------------------------------------------
# ------------------------stacked type----------------------------------------------
# ----------------------------------------------------------------------------------------
ignore_dist = 1




#%% ---------------------------------------------------------------------------------------
# ------------------------Reset exposure indicators----------------------------------------------
# ----------------------------------------------------------------------------------------

# Keep only essential columns
exp_panel = exp_panel[['id','yq','up_dist','down_dist','upexpected','downexpected']]


# Keep only true pre-exposure observations
exp_panel.loc[exp_panel['upexpected']==1,'up_dist'] = np.nan
exp_panel.loc[exp_panel['downexpected']==1, 'down_dist'] = np.nan



# Ignore distant layers
exp_panel.loc[exp_panel['up_dist']>ignore_dist,'up_dist'] = np.nan
exp_panel.loc[exp_panel['down_dist']>ignore_dist,'down_dist'] = np.nan



# Set exposure direction
exp_panel.loc[exp_panel['down_dist'].notna() & exp_panel['up_dist'].notna(), 'direction'] = 'double_exp'
exp_panel.loc[exp_panel['down_dist'].notna() & exp_panel['up_dist'].isna(), 'direction'] = 'down'
exp_panel.loc[exp_panel['down_dist'].isna() & exp_panel['up_dist'].notna(), 'direction'] = 'up'
exp_panel.loc[exp_panel['down_dist'].isna() & exp_panel['up_dist'].isna(), 'direction'] = 'no_exp'





# Mark continuous exposure segments for splitting
exp_panel.loc[exp_panel['direction']=='no_exp','exposed'] = 0
exp_panel.loc[exp_panel['direction']!='no_exp','exposed'] = 1
exp_panel['exposed'] = exp_panel['exposed'].astype('Int64')




# Set exposure distance
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
# ------------------------Split individuals----------------------------------------------
# ----------------------------------------------------------------------------------------
# Handle entry and exit issues using fake_id
result_list = []

for gid, id_group in exp_panel.groupby('id', sort=False):
    
    # Sort
    id_group = id_group.sort_values('yq').copy()


    # Set split points
    first_val = id_group['exposed'].iloc[0]
    changed = id_group['exposed'].ne(
        id_group['exposed'].shift(fill_value=first_val))
    id_group['seg_id'] = changed.cumsum()


    # Split segments
    sub_control = [] # Blank segments
    sub_treat = [] # Single-direction exposure segments
    sub_double = [] # Double-exposure segments
    for k, seg in id_group.groupby('seg_id', sort=False):
        if seg['direction'].eq('no_exp').all(): # This segment is a blank period
            sub_control.append(seg)
        elif 'double_exp' in set(seg['direction'].unique()): # Contains double exposure
            sub_double.append(seg)
        else: # This segment is a single-exposure period
            sub_treat.append(seg)



    # Combine control segments into one DataFrame
    control_df = (pd.concat(sub_control, ignore_index=True) if sub_control else id_group.head(0).copy())



    # Add the control group to each treated segment
    fake_df_list = []
    for treat_df in sub_treat:
        treat_df = treat_df.reset_index(drop=True)
        treat_df = pd.concat([control_df, treat_df], axis=0).sort_values('yq').reset_index(drop=True)
        fake_df_list.append(treat_df)



    # Process each fake_df one by one
    for fake_df in fake_df_list:

        # Sort
        fake_df = fake_df.sort_values('yq').reset_index(drop=True)

        # Get the exposure start and end periods
        exp_start = fake_df[fake_df['direction'] != "no_exp"]['yq'].min()
        exp_end = fake_df[fake_df['direction'] != "no_exp"]['yq'].max()
        fake_df['exp_start'] = exp_start
        fake_df['exp_end'] = exp_end


        # Drop samples after the end of exposure
        # (part of the control group may be merged in after exposure, which would turn this into an entry-exit DID)
        fake_df = fake_df[fake_df['yq'] <= exp_end]


        # Exposure direction
        fake_df = fake_df.sort_values('yq').reset_index(drop=True)
        exp_direction = fake_df[fake_df['yq'] == exp_start]['direction'].iloc[0]
        

        # Exposure distance
        exp_dist = 1


        # Combine into exposure type
        exp_type = f"{exp_direction}{exp_dist}"
        fake_df['exp_type'] = exp_type


        # Create fake individual id
        fake_df['fake_id'] = f"{exp_type}_" +  fake_df['id'] + f"_{exp_start}"


        # Add fake_df to result_list
        result_list.append(fake_df)

# Convert to DataFrame
exp_reset = pd.concat(result_list, ignore_index=True)



# Keep only essential columns
exp_reset = exp_reset[['fake_id','yq','exp_start','exp_end','exp_type','id']]




# Calculate relative time
exp_reset['rel_time'] = exp_reset['yq'] - exp_reset['exp_start']



# Samples without pre/post periods
noafter_ids = exp_reset.groupby('id')['rel_time'].apply(lambda x: all(x < 0)).loc[lambda x: x].index.tolist()
print('no after',len(noafter_ids))
nobefore_ids = exp_reset.groupby('id')['rel_time'].apply(lambda x: all(x > 0)).loc[lambda x: x].index.tolist()
print('no before',len(nobefore_ids))






#%% ---------------------------------------------------------------------------------------
# ------------------------Stacked sample---------------------------------------------
# ----------------------------------------------------------------------------------------

# Never-exposed sample
clean_df = panel_df[panel_df['id'].isin(clean_set)][['id','yq']]
clean_df['fake_id'] = clean_df['id']



# Batch list (true sanction effective time)
batch_list = list(exp_reset['exp_start'].unique())
len(batch_list)





# Exposure type list
direction_list = ['up','down']
max_dist = 1
type_list = [f"{direction}{i}" for direction in direction_list for i in range(1, max_dist + 1)]




# Set window
before_window = -12
after_window = 8




# Organize by cohort
result_list = []

for batch in batch_list:

    for exp_type in type_list:

        # Define cohort
        cohort = str(batch) + '_' + exp_type

        # Get the treated group in this batch
        cohort_treat = exp_reset[
            (exp_reset['exp_start']== batch) # Exposure in this batch
            &
            (exp_reset['exp_type'] == exp_type) # This exposure type
        ]
        cohort_treat['treated'] = 1


        # Never-exposed control group
        never_exp = clean_df.copy()


        # Exposed control group
        exp_control = exp_reset[exp_reset['exp_start'] > batch] # First, must be a later batch
        exp_control = exp_control[exp_control['rel_time'] < 0] # Then, must be observations before exposure


        # Combine control groups
        cohort_control = pd.concat([exp_control, never_exp], ignore_index=True)

        


        # Process the control group
        cohort_control['treated'] = 0
        cohort_control[['exp_start','exp_end','exp_type','rel_time']] = np.nan


        # Merge treated and control groups
        cohort_df = pd.concat([cohort_treat, cohort_control], ignore_index=True)
        

        # Truncate the time window
        cohort_df = cohort_df[cohort_df['yq'] >= batch + before_window]
        cohort_df = cohort_df[cohort_df['yq'] <= batch + after_window]


        # Add labels
        cohort_df['cohort'] = cohort
        cohort_df['group'] = exp_type

        # Save
        if cohort_df['treated'].sum() > 0:
            result_list.append(cohort_df)


cohort_combine = pd.concat(result_list, ignore_index=True)






# Define prefixes and event time
prefixes   = type_list
rel_values = range(before_window, after_window + 1)  


# Suffix
rel2suf = {}
for t in range(before_window, 0):
    rel2suf[t] = f"_D_{-t}"
for t in range(0, after_window+1):
    rel2suf[t] = f"_D{t}"


# Generate all dummy variable names and initialize them to 0
dummy_cols = [f"{pre}{rel2suf[t]}" for pre in prefixes for t in rel_values]
cohort_combine[dummy_cols] = 0




# Set exp_type and rel_time to 1
for pre in prefixes:
    mask_pre = cohort_combine['exp_type'] == pre
    for t in rel_values:
        col = f"{pre}{rel2suf[t]}"
        mask_t = cohort_combine['rel_time'] == t
        cohort_combine.loc[mask_pre & mask_t, col] = 1





# Merge financial data
cohort_combine = cohort_combine.merge(
    raw_panle,
    on=['id','yq'],
    how='left'
)






#%% ---------------------------------------------------------------------------------------
# ------------------------Save data---------------------------------------------
# ----------------------------------------------------------------------------------------
if ignore_dist==1:

    cohort_combine.to_stata(f"{stata_data_loc}/stage2_stacked_income.dta", write_index=False)

else:
    cohort_combine.to_stata(f"{stata_data_loc}/stage2_stacked_break.dta", write_index=False)