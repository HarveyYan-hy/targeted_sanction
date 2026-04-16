#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from tqdm import tqdm
import re
import random
import os, pickle, gc
import networkx as nx
import numpy as np
from code_file.py_code.py_config import processing_data




#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()






#%% ---------------------------------------------------------------------------------------
# ------------------------Load data----------------------------------------------
# ----------------------------------------------------------------------------------------
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")
factset_df = pd.read_parquet(f"{processing_data_loc}/factset_rel.parquet")



# Sample period
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3





#%% ---------------------------------------------------------------------------------------
# -----------------------ID permutation----------------------------------------------
# ----------------------------------------------------------------------------------------
ids = sorted(id_map['id'].unique())
rnd = random.Random(2025)
perm = ids[:]
rnd.shuffle(perm)
perm_dict = dict(zip(ids, perm))

factset_df['supplier_company_id'] = factset_df['supplier_company_id'].map(perm_dict)
factset_df['customer_company_id'] = factset_df['customer_company_id'].map(perm_dict)
factset_df.to_parquet(factset_df.to_parquet(f"{processing_data_loc}/factset_rel_random.parquet", index=False))





#%% ---------------------------------------------------------------------------------------
# -----------------------Plotting----------------------------------------------
# ----------------------------------------------------------------------------------------

# Save directory
save_dir = f"{processing_data_loc}/network_plot/random"
os.makedirs(save_dir, exist_ok=True)




# Loop for plotting
for plot_yearseason in tqdm(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+2), desc='Quarter'): 
    
    # Filter valid relationships
    factset_plot = factset_df[
        (factset_df['s_yq'] <= plot_yearseason)& (factset_df['e_yq'] >= plot_yearseason)
        ][['supplier_company_id', 'customer_company_id']].drop_duplicates()

    # Create directed graph
    G = nx.from_pandas_edgelist(
        factset_plot,
        source='supplier_company_id',
        target='customer_company_id',
        create_using=nx.DiGraph()
    )




    # ---------- Save Pickle (fast loading in Python) ----------
    with open(os.path.join(save_dir, f"G_{plot_yearseason}.pkl"), "wb") as f:
        pickle.dump(G, f)