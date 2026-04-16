#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from tqdm import tqdm
from code_file.py_code.py_config import stata_data, processing_data







#%% ---------------------------------------------------------------------------------------
# ------------------------Get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()
stata_data_loc = stata_data()









#%% ---------------------------------------------------------------------------------------
# ------------------------Load data----------------------------------------------
# ----------------------------------------------------------------------------------------
rival_df = pd.read_parquet(f"{processing_data_loc}/rival_rel.parquet")
panel_df = pd.read_parquet(f"{processing_data_loc}/stage2_ols.parquet")
sanction_info = pd.read_parquet(f"{processing_data_loc}/sanction_info.parquet")
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")







#%% ---------------------------------------------------------------------------------------
# ------------------------Get competitors of sanctioned firms----------------------------------------------
# ----------------------------------------------------------------------------------------
# Set of sanctioned firms
san_set = set(sanction_info['id'].unique())


# Rename columns
rival_df = rival_df.rename(columns={
    'source_company_id':'r1',
    'target_company_id':'r2'
})


# Keep only panel firms
panel_set = set(id_map[id_map['panel']==1]['id'].unique())
rival_df = rival_df[
    (rival_df['r1'].isin(panel_set)) & (rival_df['r2'].isin(panel_set))]


# Process time
rival_df['s_yq'] = rival_df['start_year']*4 + rival_df['start_quarter']
rival_df['e_yq'] = rival_df['end_year']*4 + rival_df['end_quarter']
rival_df = rival_df.drop(columns=['start_year','start_quarter','start_day','start_month',
                                  'end_year','end_quarter','end_day','end_month',
                                  'id','rel_type'])


# Shift relationship time earlier
rival_df['s_yq'] = rival_df['s_yq'] - 2


# Competitors of sanctioned firms
r1_san = rival_df[(rival_df['r1'].isin(san_set)) & (~rival_df['r2'].isin(san_set))]
r2_san = rival_df[(~rival_df['r1'].isin(san_set)) & (rival_df['r2'].isin(san_set))]




# Concatenate
r1_san.rename(columns={'r1':'id','r2':'rival'},inplace=True)
r2_san.rename(columns={'r2':'id','r1':'rival'},inplace=True)
rival_df = pd.concat([r1_san,r2_san],axis=0)
rival_df.drop_duplicates(inplace=True)





# Keep only the first sanction
sanction_info = sanction_info[sanction_info['san_date'].notna()]
sanction_info['san_yq'] = (sanction_info['san_date'].dt.year) * 4 + (sanction_info['san_date'].dt.quarter)
sanction_first = sanction_info.sort_values(['id','san_yq']).reset_index(drop=True)
sanction_first = sanction_first.loc[sanction_first.groupby("id")["san_yq"].idxmin()]



# Time of competitive benefit
rival_df = rival_df.merge(
    sanction_first[['id', 'san_yq']],
    on = 'id',
    how = 'left'
)


# Rivalry relationship must exist before the sanction
rival_df = rival_df[rival_df['s_yq']<=rival_df['san_yq']]



# Clean columns
rival_df = rival_df[['id','rival','san_yq']].drop_duplicates()
rival_df.reset_index(drop=True,inplace=True)




# First time receiving competitive benefit
rival_df = rival_df.loc[
    rival_df.groupby(['rival'])['san_yq'].idxmin()]




# Keep necessary columns
rival_df = rival_df[['rival','san_yq']]
rival_df.rename(columns={'rival':'id',
                        'san_yq':'rival_yq'},inplace=True)






# Merge into panel
panel_df = panel_df.merge(
    rival_df,
    on = 'id',
    how = 'left'
)





#%% ---------------------------------------------------------------------------------------
# ------------------------Save data----------------------------------------------
# ----------------------------------------------------------------------------------------
panel_df.to_stata(f"{stata_data_loc}/stage3_panel.dta", write_index=False)