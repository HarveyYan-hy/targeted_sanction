#%% ---------------------------------------------------------------------------------------
# ------------------------import module----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from tqdm import tqdm
import json
from datetime import date
from code_file.py_code.py_config import raw_data, processing_data








#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc = raw_data()
processing_data_loc = processing_data()







#%% ---------------------------------------------------------------------------------------
# ------------------------get the data----------------------------------------------
# ----------------------------------------------------------------------------------------
sanctioned_company = pd.read_excel(f"{raw_data_loc}/sanction_list/sanctioned_company.xlsx",
                                dtype={'os_id': str, 'stkcd': str})
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")







#%% ---------------------------------------------------------------------------------------
# ------------------------load json----------------------------------------------
# ----------------------------------------------------------------------------------------
# consolidation
file_path = f"{raw_data_loc}/opensanction/con_ftm.json"
con_san = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue 
        if obj.get("schema") == "Sanction":   
            con_san.append(obj)

con_ftm_df = pd.DataFrame(con_san)



# default
file_path = f"{raw_data_loc}/opensanction/default_ftm.json"
def_san = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue  
        if obj.get("schema") == "Sanction":   
            def_san.append(obj)

default_ftm_df = pd.DataFrame(def_san)





# mark debarred/sanction
con_ftm_df['type'] = 1
sanction_df = default_ftm_df.merge(
    con_ftm_df[['id','type']],
    on='id',
    how='left'
)
sanction_df['type'] = sanction_df['type'].fillna(0).astype(int)  





# clean col
sanction_df['san_id'] = sanction_df['id']
sanction_df['san_properties'] = sanction_df['properties']

sanction_df = sanction_df.drop(
                        columns=[
                            "id","properties","referents", "first_seen", "last_seen", 
                            "schema", "last_change","target","origin"
                            ])





# get sanctioned entity 
sanction_df['entity'] = sanction_df['san_properties'].apply(lambda x: x.get('entity') if isinstance(x, dict) else None)
sanction_df = sanction_df[~sanction_df['entity'].isna()]
sanction_df['entity_num'] = sanction_df['entity'].apply(lambda x: len(x))
sanction_df['entity'] = sanction_df['entity'].apply(lambda x: x[0])
sanction_df.drop(columns=['entity_num'],inplace=True)







#%% ---------------------------------------------------------------------------------------
# -------------------------sanction info---------------------------------------------
# ----------------------------------------------------------------------------------------

sanction_df['os_id'] = sanction_df['entity']
sanction_df['san_datasets'] = sanction_df['datasets']

sanction_info = sanction_df[['os_id','san_id','type','san_datasets','san_properties']].merge(
    sanctioned_company,
    on='os_id',
    how='left'
)
sanction_info = sanction_info[sanction_info['stkcd'].notna()]
sanction_info = sanction_info.sort_values(by=['os_id','stkcd']).reset_index(drop=True)






# sanction info
sanction_info['listdate'] = sanction_info['san_properties'].apply(lambda x: x.get('listingDate') if isinstance(x, dict) else None) 
sanction_info['startdate'] = sanction_info['san_properties'].apply(lambda x: x.get('startDate') if isinstance(x, dict) else None) 
sanction_info['authority'] = sanction_info['san_properties'].apply(lambda x: x.get('authority') if isinstance(x, dict) else None) 
sanction_info['program_link'] = sanction_info['san_properties'].apply(lambda x: x.get('programUrl') if isinstance(x, dict) else None) 
sanction_info['program'] = sanction_info['san_properties'].apply(lambda x: x.get('program') if isinstance(x, dict) else None) 

sanction_info = sanction_info.drop(columns=['san_properties'])















#%% ---------------------------------------------------------------------------------------
# ------------------------['RUSSIA-EO14024']----------------------------------------------
# ----------------------------------------------------------------------------------------

mask1 = sanction_info['program'].apply(lambda x: isinstance(x, list) and ('RUSSIA-EO14024' in x))

targets = {
    '欧科亿688308': '2025-01-15',
    '瓦轴B200706': '2025-01-15',
    'ST天喻300205': '2024-06-12',
    '动力源600405': '2024-10-30',
    '华中数控300161': '2024-10-30',
    '浙海德曼688577': '2024-10-30',
    '安联锐视301042': '2024-10-30',
}

for sname, dt in targets.items():
    mask2 = (sanction_info['stkcd_sname'] == sname)
    idx = (mask1 & mask2).idxmax()
    sanction_info.at[idx, 'startdate'] = [dt]








#%% ---------------------------------------------------------------------------------------
# ------------------------BIS----------------------------------------------
# ----------------------------------------------------------------------------------------

mask1 = sanction_info['san_datasets'].apply(lambda x: isinstance(x, list) and ('us_trade_csl' in x))

targets = {
    '中瓷电子003031': '2018-08-01',
    '同惠电子833509': '2018-08-01',
}

for sname, dt in targets.items():
    mask2 = (sanction_info['stkcd_sname'] == sname)
    idx = (mask1 & mask2).idxmax()
    sanction_info.at[idx, 'startdate'] = [dt]



# 华力创通300045的生效时间在EL上缺失
# 立航科技603261和新晨科技300542是UV，没有时间







#%% ---------------------------------------------------------------------------------------
# ------------------------《约翰·麦凯恩2019财年国防授权法案》（Public Law 115-232）------------------
# ----------------------------------------------------------------------------------------
# 《约翰·麦凯恩2019财年国防授权法案》（Public Law 115-232）于 2018 年 8 月 13 日 签署成法
mask1 = sanction_info['program'].apply(
    lambda x: ('Section 889 of the John S. McCain National Defense Authorization Act for Fiscal Year 2019 (Public Law 115 - 232)' in x) 
    if isinstance(x, list) else False
)

for i in sanction_info.index[mask1]:
    sanction_info.at[i, 'startdate'] = ['2018-08-13']










#%% ---------------------------------------------------------------------------------------
# -----------------------Delete Yue Power / Lutai（Regarding A/B stocks）----------------------------------------------
# ----------------------------------------------------------------------------------------
del_stkcd = ['鲁泰B200726','鲁泰A000726','粤电力A000539','粤电力B200539']
sanction_info = sanction_info[~sanction_info['stkcd_sname'].isin(del_stkcd)]











#%% ---------------------------------------------------------------------------------------
# ------------------------earliest timestamp----------------------------------------------
# ----------------------------------------------------------------------------------------
result_list = [] 

for index, row in tqdm(sanction_info.iterrows(), total=sanction_info.shape[0], desc="Processing", leave=True):
    row_dict = row.to_dict()

    # 处理公布时间
    list_date_list = row_dict.get('listdate') or []
    list_date_list = [d for d in list_date_list if d]           
    list_date = min(list_date_list) if list_date_list else None

    # 处理开始时间
    start_date_list = row_dict.get('startdate') or []
    start_date_list = [d for d in start_date_list if d]
    start_date = min(start_date_list) if start_date_list else None

    # 有效时间 = 两者中更早的非空日期
    candidates = [d for d in (list_date, start_date) if d]    
    row_dict['san_date'] = min(candidates) if candidates else None

    # 添加到列表
    result_list.append(row_dict)
    

sanction_info = pd.DataFrame(result_list)




# Adjust the time format
sanction_info['san_date'] = pd.to_datetime(sanction_info['san_date'])





sanction_info['san_datasets'].value_counts()








#%% ---------------------------------------------------------------------------------------
# ------------------------Replace IDs----------------------------------------------
# ----------------------------------------------------------------------------------------
# Build mapping dict
id_dict = id_map[id_map['panel']==1].set_index('stkcd')['id'].to_dict()


# Apply mapping
sanction_info['id'] = sanction_info['stkcd'].map(id_dict)


# Remove rows with missing id
sanction_info = sanction_info[sanction_info['id'].notna()]







#%% ---------------------------------------------------------------------------------------
# ------------------------save data---------------------------------------------
# ----------------------------------------------------------------------------------------
drop_cols = ['authority', 'program_link', 'program','stkcd']
sanction_info = sanction_info.drop(columns=drop_cols)


sanction_info.to_parquet(
    f"{processing_data_loc}/sanction_info.parquet",
    index=False
)
