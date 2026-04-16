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
top_holder1 = pd.read_csv(
    f"{raw_data_loc}/csmar/top10_holder/HLD_Shareholders.csv",
    dtype={'Stkcd': str} # Store stock codes as strings
)


top_holder2 = pd.read_csv(
        f"{raw_data_loc}/csmar/top10_holder/HLD_Shareholders1.csv",
        dtype={'Stkcd': str} # Store stock codes as strings
)

top_holder3 = pd.read_csv(
        f"{raw_data_loc}/csmar/top10_holder/HLD_Shareholders2.csv",
        dtype={'Stkcd': str} # Store stock codes as strings
)
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")





# Merge the three tables
top_holder = pd.concat([top_holder1, top_holder2, top_holder3], axis=0, ignore_index=True)






#%% ---------------------------------------------------------------------------------------
# -----------------------Basic processing----------------------------------------------
# ----------------------------------------------------------------------------------------
# Adjust date format
top_holder['date'] =pd.to_datetime(top_holder['Reptdt'])
top_holder['year'] = top_holder['date'].dt.year
top_holder['quarter'] = top_holder['date'].dt.quarter




# Keep only the largest (No.1) shareholder
top_holder = top_holder[top_holder['S0306a']==1]




# Keep only relevant columns
top_holder['top_hold'] = top_holder['S0301a']
top_holder['top_hold_share'] = top_holder['S0304a']
top_holder['stkcd'] = top_holder['Stkcd']
top_holder['top_hold_nature'] = top_holder['ShareholderNature']
top_holder = top_holder[['stkcd','top_hold','top_hold_share','top_hold_nature','year','quarter']]




# top1 nature
mapping = { 
    '其他': 1,
    '境内非国有法人': 2,
    '境外法人': 3,
    '国家': 4,
    '境内自然人': 5,
    '国有法人': 6,
    '境内自然人,境内非国有法人': 7,
    '境外自然人': 8
    # 缺失值保持 NaN
}

top_holder['top_hold_nature'] = top_holder['top_hold_nature'].map(mapping)













#%% ---------------------------------------------------------------------------------------
# ------------------------Replace IDs----------------------------------------------
# ----------------------------------------------------------------------------------------
# Build mapping dict
id_dict = id_map[id_map['panel']==1].set_index('stkcd')['id'].to_dict()


# Apply mapping
top_holder['id'] = top_holder['stkcd'].map(id_dict)


# Remove rows with missing id
top_holder = top_holder[top_holder['id'].notna()]














#%% ---------------------------------------------------------------------------------------
# -----------------------Save data----------------------------------------------
# ----------------------------------------------------------------------------------------
top_holder = top_holder[['id','year','quarter','top_hold_share','top_hold_nature']]

top_holder.to_parquet(f"{processing_data_loc}/top_holder.parquet", index=False)
