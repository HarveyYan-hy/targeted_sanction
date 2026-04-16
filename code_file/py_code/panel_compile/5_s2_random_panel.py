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
exp_panel = pd.read_parquet(f"{processing_data_loc}/exp_panel_random.parquet")
raw_panle = pd.read_parquet(f"{processing_data_loc}/stage1_panel.parquet")
sanction_df = pd.read_parquet(f"{processing_data_loc}/sanction_info.parquet")







#%% ---------------------------------------------------------------------------------------
# ------------------------OLS panel----------------------------------------------
# ----------------------------------------------------------------------------------------
# Merge exposure data
panel_df = panel_df.merge(exp_panel,on=['id','yq'],how='left')


# Remove sanctioned firms themselves
san_set = set(sanction_df['id'].unique())
panel_df = panel_df[~panel_df['id'].isin(san_set)]


# Save
panel_df.to_stata(f"{stata_data_loc}/stage2_ols_random.dta", write_index=False)