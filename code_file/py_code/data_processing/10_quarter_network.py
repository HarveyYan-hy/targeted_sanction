#%% ---------------------------------------------------------------------------------------
# ------------------------导入模块----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import networkx as nx 
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
factset_df = pd.read_parquet(f"{processing_data_loc}/factset_rel.parquet")










#%% ---------------------------------------------------------------------------------------
# ------------------------plot----------------------------------------------
# ----------------------------------------------------------------------------------------
# sample period
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3





# save dir
save_dir = f"{processing_data_loc}/network_plot"
os.makedirs(save_dir, exist_ok=True)





for plot_yearseason in tqdm(range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+2), desc='Quarter'): 
    
    # 筛选出有效关系
    factset_plot = factset_df[
        (factset_df['s_yq'] <= plot_yearseason)& (factset_df['e_yq'] >= plot_yearseason)
        ][['supplier_company_id', 'customer_company_id']].drop_duplicates()

    # 创建有向图
    G = nx.from_pandas_edgelist(
        factset_plot,
        source='supplier_company_id',
        target='customer_company_id',
        create_using=nx.DiGraph()
    )


    # ----------  Pickle（ ----------
    with open(os.path.join(save_dir, f"G_{plot_yearseason}.pkl"), "wb") as f:
        pickle.dump(G, f)


    # ---------- GEXF ----------
    nx.write_gexf(G, os.path.join(save_dir, f"G_{plot_yearseason}.gexf"))


