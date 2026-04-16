# -----------------------------------------------------------------------------
# This script is the single-threaded version of 2_path_cpu_parallel.py.
# It keeps the same core logic but runs without multiprocessing.
# -------------------------------------------------------------------------



#%% ---------------------------------------------------------------------------------------
# ------------------------导入模块----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from tqdm import tqdm
import re
import json
import os
import pickle
import networkx as nx
from code_file.py_code.py_config import raw_data, stata_data, processing_data







#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()







#%% ---------------------------------------------------------------------------------------
# ------------------------导入数据----------------------------------------------
# ----------------------------------------------------------------------------------------
sanction_df = pd.read_parquet(f"{processing_data_loc}/sanction_info.parquet")
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")





# 样本区间
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3







#%% ---------------------------------------------------------------------------------------
# ------------------------处理制裁数据----------------------------------------------
# ----------------------------------------------------------------------------------------

# 整理出事件
sanction_df = sanction_df[sanction_df['san_date'].notna()][['id','san_date']]
sanction_df['san_yq'] = (sanction_df['san_date'].dt.year) * 4 + (sanction_df['san_date'].dt.quarter)
sanction_df = sanction_df.drop(columns='san_date').drop_duplicates().sort_values(['id','san_yq']).reset_index(drop=True)






#%% ---------------------------------------------------------------------------------------
# ------------------------制裁当期所有的暴露----------------------------------------------
# ----------------------------------------------------------------------------------------
# 面板公司集合
panel_set = set(id_map[id_map['panel']==1]['id'].unique())

# 设置查询层级
max_depth  = 8

up_list = [] # 储存制裁企业的上游
down_list = [] # 储存制裁企业的下游

for plot_yearseason in tqdm(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1), desc='Quarter'): 

    # 读取关系图
    g_path = os.path.join(f"{processing_data_loc}/network_plot", f"G_{plot_yearseason}.pkl")
    with open(g_path, "rb") as f:
        G = pickle.load(f)

    Grev = G.reverse(copy=False)


    # 筛选节点
    san_set = set(sanction_df[sanction_df['san_yq']==plot_yearseason]['id'].unique())
    effective_set = san_set & G.nodes

    
    # 依次查找制裁企业的上下游
    for target_id in effective_set:
        

        # 下游（沿原图方向）
        down_dist = nx.single_source_shortest_path_length(G, target_id, cutoff=max_depth)
        # 上游（沿反向图方向）
        up_dist   = nx.single_source_shortest_path_length(Grev, target_id, cutoff=max_depth)


        # 删除自己距离自己
        down_dist.pop(target_id, None)
        up_dist.pop(target_id, None)


        # 只保留键在面板中的项
        down_dist = {node: dist for node, dist in down_dist.items() if node in panel_set}
        up_dist   = {node: dist for node, dist in up_dist.items() if node in panel_set}


        # 追加到列表（保持你指定的嵌套结构）
        up_list.append({plot_yearseason: {target_id: up_dist}})
        down_list.append({plot_yearseason: {target_id: down_dist}})






# 结果转成dataframe
rows = []
for item in up_list:  # 每个 item 是 {plot_yearseason: {target_id: up_dist}}
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


# 上下游合并
up_df['up_node'] = up_df['id']
up_df['down_node'] = up_df['san_node']
up_df = up_df.drop(columns='id')

down_df['down_node'] = down_df['id']
down_df['up_node'] = down_df['san_node']
down_df = down_df.drop(columns='id')

expose_df = pd.concat([up_df, down_df], axis=0).sort_values(['yq','san_node','dist','up_node','down_node']).reset_index(drop=True)








#%% ---------------------------------------------------------------------------------------
# ------------------------逐批次查询路径----------------------------------------------
# ----------------------------------------------------------------------------------------
# 初始化
expose_df['paths'] = None


for plot_yearseason in tqdm(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1), desc='find path'): 


    # 读取关系图
    g_path = os.path.join(f"{processing_data_loc}/network_plot", f"G_{plot_yearseason}.pkl")
    with open(g_path, "rb") as f:
        G = pickle.load(f)

    Grev = G.reverse(copy=False)

    # 这一批的暴露数据（
    effect_expose = expose_df.loc[expose_df['yq'] == plot_yearseason].copy()

    packed_paths = []  # 与 effect_expose 行顺序一一对应

    for r in effect_expose.itertuples(index=False):
        up_node = r.up_node
        down_node = r.down_node

        try:
            # 所有最短路径
            named_paths = [list(p) for p in nx.all_shortest_paths(G, source=up_node, target=down_node)]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            named_paths = []

        # “打包到一行”：存成 JSON 字符串（一个 cell 一条记录）
        packed_paths.append(json.dumps(named_paths, ensure_ascii=False))

    # 写回原 expose_df
    idx = effect_expose.index
    expose_df.loc[idx, 'paths'] = packed_paths





#%% ---------------------------------------------------------------------------------------
# ------------------------保存数据----------------------------------------------
# ----------------------------------------------------------------------------------------
expose_df.to_parquet(f"{processing_data_loc}/expose_path.parquet", index=False)