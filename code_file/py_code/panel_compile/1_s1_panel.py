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
# ------------------------Get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()
stata_data_loc = stata_data()






#%% ---------------------------------------------------------------------------------------
# ------------------------Import data----------------------------------------------
# ----------------------------------------------------------------------------------------
panel_df = pd.read_parquet(f"{processing_data_loc}/basic_panel.parquet")
sanction_df = pd.read_parquet(f"{processing_data_loc}/sanction_info.parquet")
heterogeneity_df = pd.read_parquet(f"{processing_data_loc}/heterogeneity_df.parquet")







#%% ---------------------------------------------------------------------------------------
# ------------------------Sanction data processing----------------------------------------------
# ----------------------------------------------------------------------------------------

# Non-missing sanction dates
sanction_df = sanction_df[sanction_df['san_date'].notna()]


# Sanction time series
sanction_df['san_yq'] = (sanction_df['san_date'].dt.year) * 4 + (sanction_df['san_date'].dt.quarter)



# Keep only the first sanction
sanction_first = sanction_df.sort_values(['id','san_yq']).reset_index(drop=True)
sanction_first = sanction_first.loc[sanction_first.groupby("id")["san_yq"].idxmin()]



# Get the second sanction
result_list = []
for san_id in tqdm(sanction_df['id'].unique()):

    tmp = sanction_df[sanction_df['id']==san_id].sort_values(['san_yq']).reset_index(drop=True)

    yq_set = set(tmp['san_yq'].unique())

    if len(yq_set) > 1:
        second_san = sorted(yq_set)[1] 
    else:
        second_san = 999999

    result_list.append({
        'id': san_id,
        'second_san': second_san
    })

second_df = pd.DataFrame(result_list)
sanction_first = sanction_first.merge(
    second_df,
    on = 'id',
    how = 'left'
)




#%% ---------------------------------------------------------------------------------------
# ------------------------Merge data----------------------------------------------
# ----------------------------------------------------------------------------------------

# Sanctioned firms
panel_df = panel_df.merge(
    sanction_first[['id','san_yq','second_san']],
    on = 'id',
    how = 'left'
)


# Heterogeneity
panel_df = panel_df.merge(
    heterogeneity_df,
    on = 'id',
    how = 'left'
)








#%% ---------------------------------------------------------------------------------------
# ------------------------Save data----------------------------------------------
# ----------------------------------------------------------------------------------------

# Save as a parquet file without index
panel_df.to_parquet(f"{processing_data_loc}/stage1_panel.parquet", index=False)

# Save as a Stata file without index
panel_df.to_stata(f"{stata_data_loc}/stage1_panel.dta", write_index=False)