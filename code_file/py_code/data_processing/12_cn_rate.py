#%% ---------------------------------------------------------------------------------------
# ------------------------import module----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from tqdm import tqdm
import networkx as nx
import pickle
import os
from code_file.py_code.py_config import processing_data






#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()






#%% ---------------------------------------------------------------------------------------
# ------------------------load data----------------------------------------------
# ----------------------------------------------------------------------------------------
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")



# sample period
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3






#%% ---------------------------------------------------------------------------------------
# ------------------------load network----------------------------------------------
# ----------------------------------------------------------------------------------------
G_dict = {}
Grev_dict = {}
for plot_yearseason in tqdm(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1), desc='Quarter'): 

    g_path    = os.path.join(f"{processing_data_loc}/network_plot", f"G_{plot_yearseason}.pkl")

    with open(g_path, "rb") as f:
        G = pickle.load(f)
        G_dict[plot_yearseason] = G

        Grev = G.reverse(copy=False)
        Grev_dict[plot_yearseason] = Grev








#%% ---------------------------------------------------------------------------------------
# ------------------------cn firm----------------------------------------------
# ----------------------------------------------------------------------------------------
cne_set = set(id_map[id_map['isin'].str.startswith('CNE', na=False)]['id'].unique())

for y in range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1):
    G = G_dict[y]
    Grev = Grev_dict[y]
    for node in G.nodes():
        G.nodes[node]['cn'] = (node in cne_set)
    for node in Grev.nodes():
        Grev.nodes[node]['cn'] = (node in cne_set)








#%% ---------------------------------------------------------------------------------------
# ------------------------获取各级上下游----------------------------------------------
# ----------------------------------------------------------------------------------------
# panel firm
panel_set = set(id_map[id_map['panel']==1]['id'].unique())



max_depth  = 2 

cn_rate_list = [] 

for plot_yearseason in tqdm(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1), desc='Quarter'): 

    G = G_dict[plot_yearseason]
    Grev = Grev_dict[plot_yearseason]

    targets = panel_set & set(G.nodes())

    for target_id in targets:

        row_dict = {'yq': plot_yearseason, 'id': target_id}

        # 获取上下游距离字典
        down_dist = nx.single_source_shortest_path_length(G, target_id, cutoff=max_depth)
        up_dist   = nx.single_source_shortest_path_length(Grev, target_id, cutoff=max_depth)

        # 初始化计数器
        for d in range(1, max_depth + 1):
            row_dict[f'down_cn_rate_{d}'] = 0.0
            row_dict[f'up_cn_rate_{d}'] = 0.0

            down_nodes = [node for node, dist in down_dist.items() if dist == d]
            up_nodes   = [node for node, dist in up_dist.items() if dist == d]

            # 计算中国节点比例
            if down_nodes:
                cn_count = sum(G.nodes[n].get('cn', False) for n in down_nodes)
                row_dict[f'down_cn_rate_{d}'] = cn_count / len(down_nodes)

            if up_nodes:
                cn_count = sum(Grev.nodes[n].get('cn', False) for n in up_nodes)
                row_dict[f'up_cn_rate_{d}'] = cn_count / len(up_nodes)

        cn_rate_list.append(row_dict)


cn_rate_df = pd.DataFrame(cn_rate_list)









# save data
cn_rate_df.to_parquet(
    f"{processing_data_loc}/rel_cn_rate.parquet",
    index=False
)