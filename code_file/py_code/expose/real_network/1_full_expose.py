#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from tqdm import tqdm
import re
import os
import pickle
import networkx as nx
from code_file.py_code.py_config import raw_data, stata_data, processing_data







#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()





#%% ---------------------------------------------------------------------------------------
# ------------------------Load data----------------------------------------------
# ----------------------------------------------------------------------------------------
sanction_df = pd.read_parquet(f"{processing_data_loc}/sanction_info.parquet")
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")




# Sample period
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3





#%% ---------------------------------------------------------------------------------------
# ------------------------Get the sets to query----------------------------------------------
# ----------------------------------------------------------------------------------------
# Set of sanctioned firms
san_set = set(sanction_df['id'].unique())


# Set of panel firms
panel_set = set(id_map[id_map['panel']==1]['id'].unique())





#%% ---------------------------------------------------------------------------------------
# ------------------------Loop query----------------------------------------------
# ----------------------------------------------------------------------------------------

# Set search depth
max_depth  = 8

up_list = [] # Store the upstream of sanctioned firms
down_list = [] # Store the downstream of sanctioned firms

for plot_yearseason in tqdm(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1), desc='Quarter'): 

    # Load the relationship graph
    g_path = os.path.join(f"{processing_data_loc}/network_plot", f"G_{plot_yearseason}.pkl")
    with open(g_path, "rb") as f:
        G = pickle.load(f)

    Grev = G.reverse(copy=False)


    # Filter nodes
    effective_set = san_set & G.nodes

    
    # Find the upstream and downstream of sanctioned firms one by one
    for target_id in effective_set:
        

        # Downstream (along the original graph direction)
        down_dist = nx.single_source_shortest_path_length(G, target_id, cutoff=max_depth)
        # Upstream (along the reverse graph direction)
        up_dist   = nx.single_source_shortest_path_length(Grev, target_id, cutoff=max_depth)


        # Remove the distance from itself to itself
        down_dist.pop(target_id, None)
        up_dist.pop(target_id, None)


        # Keep only items whose keys are in the panel set
        down_dist = {node: dist for node, dist in down_dist.items() if node in panel_set}
        up_dist   = {node: dist for node, dist in up_dist.items() if node in panel_set}


        # Append to the list (keeping your specified nested structure)
        up_list.append({plot_yearseason: {target_id: up_dist}})
        down_list.append({plot_yearseason: {target_id: down_dist}})






# Convert results to dataframe
rows = []
for item in up_list:  # Each item is {plot_yearseason: {target_id: up_dist}}
    for yq, target_dict in item.items():
        for target_id, up_dist in target_dict.items():
            for up_node, dist in up_dist.items():
                rows.append((yq, target_id, up_node, dist))

up_df = pd.DataFrame(rows, columns=['yq', 'san_node', 'id', 'dist'])

rows = []
for item in down_list:
    for yq, target_dict in item.items():
        for target_id, down_dist in target_dict.items():
            for down_node, dist in down_dist.items():
                rows.append((yq, target_id, down_node, dist))

down_df = pd.DataFrame(rows, columns=['yq', 'san_node', 'id', 'dist'])






#%% ---------------------------------------------------------------------------------------
# ------------------------Keep only post-sanction exposure----------------------------------------------
# ----------------------------------------------------------------------------------------

# Keep only the first sanction
sanction_first = sanction_df[sanction_df['san_date'].notna()]
sanction_first = sanction_first[['id','san_date']].sort_values(['id','san_date']).reset_index(drop=True)
sanction_first = sanction_first.loc[sanction_first.groupby("id")["san_date"].idxmin()]
sanction_first['san_yq'] = sanction_first['san_date'].dt.year*4 + sanction_first['san_date'].dt.quarter
sanction_first = sanction_first.drop(columns='san_date')




# Add sanction time to upstream and downstream exposure
sanction_first = sanction_first.rename(columns={'id':'san_node'})
up_df = up_df.merge(sanction_first, on='san_node', how='left')
down_df = down_df.merge(sanction_first, on='san_node', how='left')





# Keep post-sanction data
up_df = up_df[up_df['yq'] >= up_df['san_yq']]
down_df = down_df[down_df['yq'] >= down_df['san_yq']]







#%% ---------------------------------------------------------------------------------------
# ------------------------Save data----------------------------------------------
# ----------------------------------------------------------------------------------------
up_df.to_parquet(f"{processing_data_loc}/full_expose_up.parquet", index=False)
down_df.to_parquet(f"{processing_data_loc}/full_expose_down.parquet", index=False)