#%% ---------------------------------------------------------------------------------------
# ------------------------import module----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from tqdm import tqdm
import os, pickle, gc
import networkx as nx
from code_file.py_code.py_config import processing_data








#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()






#%% ---------------------------------------------------------------------------------------
# ------------------------load data---------------------------------------------
# ----------------------------------------------------------------------------------------
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")




# sample period
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3







#%% ---------------------------------------------------------------------------------------
# ------------------------cal eig----------------------------------------------
# ----------------------------------------------------------------------------------------

results = []

for plot_yearseason in tqdm(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1), desc='Quarter'): 
    
    g_path = os.path.join(f"{processing_data_loc}/network_plot", f"G_{plot_yearseason}.pkl")
    
    with open(g_path, "rb") as f:
        G = pickle.load(f)
        Grev = G.reverse(copy=False)


    # 统一节点集合
    nodes = sorted(set(G.nodes()) | set(Grev.nodes()))


    # ---- 出向：下游影响力（在 G 上算 A x = λx）----
    try:
        eig_out = nx.eigenvector_centrality(G, max_iter=500, tol=1e-6, weight=None)
        out_failed = False
    except nx.PowerIterationFailedConvergence:
        eig_out = {}
        out_failed = True


    # ---- 入向：上游依赖（在 Grev 上算 A^T x = λx 等价于对 Grev 的右特征向量）----
    try:
        eig_in = nx.eigenvector_centrality(Grev, max_iter=500, tol=1e-6, weight=None)
        in_failed = False
    except nx.PowerIterationFailedConvergence:
        eig_in = {}
        in_failed = True


    # 收敛失败或缺失节点时，按要求填充 'misconvergence'
    def fill_vec(d, failed):
        if failed:
            return ['misconvergence'] * len(nodes)
        return [d.get(n, 'misconvergence') for n in nodes]

    df = pd.DataFrame({
        "id": nodes,
        "eigvec_out": fill_vec(eig_out, out_failed),   # 出向/下游影响力
        "eigvec_in":  fill_vec(eig_in,  in_failed),    # 入向/上游依赖
        "yq": plot_yearseason
    })
    results.append(df)

    del G, Grev, df, eig_in, eig_out
    gc.collect()

eig_panel = pd.concat(results, ignore_index=True)






#%% ---------------------------------------------------------------------------------------
# ------------------------trim----------------------------------------------
# ----------------------------------------------------------------------------------------

# keep node in panel
panel_set = set(id_map[id_map['panel']==1]['id'].unique())
eig_panel = eig_panel[eig_panel['id'].isin(panel_set)]




# rank
eig_panel['eigin_rank'] = (
    eig_panel.groupby('yq')['eigvec_in']
    .rank(method='average', ascending=True, pct=True)
    .round(4))

eig_panel['eigout_rank'] = (
    eig_panel.groupby('yq')['eigvec_out']
    .rank(method='average', ascending=True, pct=True)
    .round(4))
eig_panel['eigin_rank'] = eig_panel['eigin_rank']*100
eig_panel['eigout_rank'] = eig_panel['eigout_rank']*100



# clean col
eig_panel.drop(columns=['eigvec_in', 'eigvec_out'], inplace=True)










#%% ---------------------------------------------------------------------------------------
# ------------------------save data----------------------------------------------
# ----------------------------------------------------------------------------------------
eig_panel.to_parquet(
    f"{processing_data_loc}/eig_panel.parquet",
    index=False
)