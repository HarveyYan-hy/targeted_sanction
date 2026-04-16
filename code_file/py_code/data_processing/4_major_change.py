#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from code_file.py_code.py_config import raw_data, processing_data








#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc = raw_data()
processing_data_loc = processing_data()







#%% ---------------------------------------------------------------------------------------
# -----------------------Load data----------------------------------------------
# ----------------------------------------------------------------------------------------
major_change = pd.read_csv(
        f"{raw_data_loc}/csmar/major_change/STK_LISTEDCOINFOCHG.csv",
        dtype={'Symbol': str},
        usecols=[0, 1, 2, 3, 4, 5])

id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")







#%% ---------------------------------------------------------------------------------------
# -----------------------Major changes----------------------------------------------
# ----------------------------------------------------------------------------------------
# Filter major change types
major_change['ChangedItem'].unique()
changed_item = ['公司经营性质', '注册地址', '总经理','法人代表', '注册资本', '多交易所上市', '公司经营范围', '主营业务', '所属城市', '所属省份','上市板块']
major_change = major_change[major_change['ChangedItem'].isin(changed_item)]


# Add year/quarter/month
major_change['ImplementDate'] = pd.to_datetime(major_change['ImplementDate'])
major_change['year'] = major_change['ImplementDate'].dt.year
major_change['quarter'] = major_change['ImplementDate'].dt.quarter



# Create dummy variable
major_change= major_change.drop_duplicates(subset=['Symbol', 'year', 'quarter'])
major_change['major_change'] = 1


# Rename columns
major_change = major_change.rename(columns={'Symbol': 'stkcd'})








#%% ---------------------------------------------------------------------------------------
# ------------------------Replace IDs----------------------------------------------
# ----------------------------------------------------------------------------------------
# Build mapping dict
id_dict = id_map[id_map['panel']==1].set_index('stkcd')['id'].to_dict()


# Apply mapping
major_change['id'] = major_change['stkcd'].map(id_dict)


# Remove rows with missing id
major_change = major_change[major_change['id'].notna()]








#%% ---------------------------------------------------------------------------------------
# -----------------------Save data----------------------------------------------
# ----------------------------------------------------------------------------------------
major_change = major_change[['id','year','quarter','major_change']]


major_change.to_parquet(
        f"{processing_data_loc}/major_change.parquet",
        index=False
)
