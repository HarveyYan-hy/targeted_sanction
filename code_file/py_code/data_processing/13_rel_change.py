#%% ---------------------------------------------------------------------------------------
# ------------------------import module----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from tqdm import tqdm
import os
import pickle
from code_file.py_code.py_config import processing_data




#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()




#%% ---------------------------------------------------------------------------------------
# ------------------------load data----------------------------------------------
# ----------------------------------------------------------------------------------------
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")









#%% ---------------------------------------------------------------------------------------
# ------------------------direct partner----------------------------------------------
# ----------------------------------------------------------------------------------------

# 样本区间
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3


# panel fimr
panel_set = set(id_map[id_map['panel']==1]['id'].unique())


# cn firm
cne_set = set(id_map[id_map['isin'].str.startswith('CNE', na=False)]['id'].unique())



records = []  
for plot_yearseason in tqdm(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1), desc='Quarter'): 
    
    # load network
    with open(os.path.join(f"{processing_data_loc}/network_plot", f"G_{plot_yearseason}.pkl"), "rb") as f:
        G = pickle.load(f)

    # 本期有效节点
    effective_set = set(G.nodes) & panel_set

    for target_id in effective_set:

        down_set = set(G.successors(target_id))
        up_set = set(G.predecessors(target_id))


        # 添加结果
        records.append({
            "yq": plot_yearseason,
            "id": target_id,
            "up": up_set,         
            "down": down_set
        })

# to df
rel_panel = pd.DataFrame(records)
rel_panel = rel_panel.sort_values(["id", "yq"]).reset_index(drop=True)
rel_panel = rel_panel.sort_values(["id", "yq"]).reset_index(drop=True)





# balanced panel
id_set = panel_set
rel_info = rel_panel
periods = list(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1))
panel_index = pd.MultiIndex.from_product(
    [sorted(id_set), periods], 
    names=['id', 'yq']
)
rel_panel = pd.DataFrame(index=panel_index).reset_index()
rel_panel = rel_panel.merge(rel_info, on=['id', 'yq'], how='left')






# Fill the missing 
fill_cols = ['up','down']
for col in fill_cols:
    rel_panel[col] = rel_panel[col].apply(lambda x: x if isinstance(x, set) else set())












#%% ---------------------------------------------------------------------------------------
# ------------------------rel change----------------------------------------------
# ----------------------------------------------------------------------------------------
# sort
rel_panel = rel_panel.sort_values(["id", "yq"]).reset_index(drop=True)



# Obtain the rel between the current period and the previous period
set_cols = ['up', 'down']
g = rel_panel.groupby('id', sort=False)
for c in set_cols:
    rel_panel[f'{c}_before'] = g[c].shift(1)   # 上一期
    rel_panel[f'{c}_next']   = g[c].shift(-1)  # 下一期




# Remove the beginning and ending periods
rel_panel = rel_panel[rel_panel['yq'] != SAMPLE_PERIOD_START-1].reset_index(drop=True)
rel_panel = rel_panel[rel_panel['yq'] != SAMPLE_PERIOD_END+1].reset_index(drop=True)





# 确定新建和结束关系
for c in ['up', 'down']:
    rel_panel[f'{c}_build'] = rel_panel[c].map(set) - rel_panel[f'{c}_before'].map(set)
    rel_panel[f'{c}_break'] = rel_panel[c].map(set) - rel_panel[f'{c}_next'].map(set)

rel_panel.drop(columns=['up_before','up_next', 'down_before','down_next'], inplace=True)














#%% ---------------------------------------------------------------------------------------
# ------------------------dummy var----------------------------------------------
# ----------------------------------------------------------------------------------------
target_cols = ['up_build','down_build',
                'up_break','down_break']

for c in target_cols:
    rel_panel[c] = rel_panel[c].map(lambda s: int(len(s) > 0))

rel_panel = rel_panel[['id','yq']+target_cols]








#%% ---------------------------------------------------------------------------------------
# -----------------------save data----------------------------------------------
# ----------------------------------------------------------------------------------------
rel_panel.to_parquet(
    f"{processing_data_loc}/rel_change.parquet",
    index=False
)
