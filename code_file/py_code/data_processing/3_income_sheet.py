#%% ---------------------------------------------------------------------------------------
# ------------------------import module----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from code_file.py_code.py_config import raw_data, processing_data









#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc = raw_data()
processing_data_loc = processing_data()









#%% ---------------------------------------------------------------------------------------
# -----------------------get data----------------------------------------------
# ----------------------------------------------------------------------------------------
income_csmar = pd.read_csv(
    f"{raw_data_loc}/csmar/income_sheet/FS_Comins.csv",
    dtype={'Stkcd': str}  
)
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")
balance_csmar = pd.read_parquet(f"{processing_data_loc}/balance_sheet.parquet")








#%% ---------------------------------------------------------------------------------------
# -----------------------basic process----------------------------------------------
# ----------------------------------------------------------------------------------------
# Keep only consolidated statements
income_csmar = income_csmar[income_csmar['Typrep'] == 'A']

# handle time var
income_csmar['Accper'] = pd.to_datetime(income_csmar['Accper'])
income_csmar['year'] = income_csmar['Accper'].dt.year
income_csmar['quarter'] = income_csmar['Accper'].dt.quarter
income_csmar['month'] = income_csmar['Accper'].dt.month
income_csmar = income_csmar[income_csmar['month'] != 1]  # 删去一月份的数据





# Keep only specified accounts 
keep_cols = {
    'B001100000': 'total_income',
    'B002000000': 'total_profit'
}

income_csmar = income_csmar.rename(columns= keep_cols)
income_csmar = income_csmar[['Stkcd', 'ShortName', 'year', 'quarter'] + list(keep_cols.values())]

# Convert column names to lowercase
income_csmar.columns = income_csmar.columns.str.lower()  # 转小写









#%% ---------------------------------------------------------------------------------------
# -----------------------Adjust quarterly accumulation----------------------------------------------
# ----------------------------------------------------------------------------------------
# create yq
income_csmar['yq'] = income_csmar['year']*4 + income_csmar['quarter']


# sort
income_csmar = income_csmar.sort_values(['stkcd','yq']).reset_index(drop=True)


# Determine continuity
income_csmar['yq_last'] = income_csmar.groupby('stkcd')['yq'].shift(1)
income_csmar['continue'] = 0
income_csmar.loc[income_csmar['yq'] == income_csmar['yq_last'] + 1, 'continue'] = 1
income_csmar.loc[income_csmar['yq_last'].isna(), 'continue'] = 1



# financial figures of the previous period
fin_var = list(keep_cols.values())
for var in fin_var:
    income_csmar[f'{var}_last'] = income_csmar.groupby('stkcd')[var].shift(1)


# Differential 
for var in fin_var:
    income_csmar.loc[income_csmar['continue']==1,f'{var}_q'] = income_csmar[var] - income_csmar[f'{var}_last']


# handle Q1
for var in fin_var:
    income_csmar.loc[income_csmar['quarter']==1,f'{var}_q'] = income_csmar[var]



# clean col
drop_cols = ['yq_last','continue'] + [f'{var}_last' for var in fin_var]
income_csmar = income_csmar.drop(columns=drop_cols)




#%% ---------------------------------------------------------------------------------------
# ------------------------Replace IDs----------------------------------------------
# ----------------------------------------------------------------------------------------
# Build mapping dict
id_dict = id_map[id_map['panel'] == 1].set_index('stkcd')['id'].to_dict()

# Apply mapping
income_csmar['id'] = income_csmar['stkcd'].map(id_dict)


# Remove rows with missing id
income_csmar = income_csmar[income_csmar['id'].notna()]










#%% ---------------------------------------------------------------------------------------
# -----------------------yoy----------------------------------------------
# ----------------------------------------------------------------------------------------
# add asset
print(income_csmar.shape)
income_csmar = income_csmar.merge(
    balance_csmar[['id','year','quarter','asset']],
    on=['id','year','quarter'],
    how='left'
)
print(income_csmar.shape)


# sort
income_csmar = income_csmar.sort_values(['stkcd','yq']).reset_index(drop=True)



# Last year in the corresponding quarter
base_cols = ['stkcd', 'yq'] + [f'{v}_q' for v in fin_var] + ['asset']
tmp = income_csmar[base_cols].copy()
tmp['yq'] = tmp['yq'] + 4
tmp = tmp.rename(columns={f'{v}_q': f'{v}_q_last4' for v in fin_var})
tmp = tmp.rename(columns={'asset': 'asset_last4'})

print(income_csmar.shape)
income_csmar = income_csmar.merge(tmp, on=['stkcd','yq'], how='left')
print(income_csmar.shape)



# IHS
for v in fin_var:
    income_csmar[f'{v}_ihs'] = np.arcsinh(income_csmar[f'{v}_q'])
    income_csmar[f'{v}_ihs_last4'] = np.arcsinh(income_csmar[f'{v}_q_last4'])



# income growth
for v in fin_var:
    # just yoy
    m1 = income_csmar[f'{v}_q_last4'].notna() & (income_csmar[f'{v}_q_last4'] > 0) & income_csmar[f'{v}_q'].notna()
    income_csmar.loc[m1, f'{v}_q_yoy'] = (
        income_csmar.loc[m1, f'{v}_q'] / income_csmar.loc[m1, f'{v}_q_last4'] - 1
    ).round(4)

    # yoy asset
    m2 = income_csmar['asset_last4'].notna() & (income_csmar['asset_last4'] > 0) & income_csmar[f'{v}_q'].notna() & income_csmar[f'{v}_q_last4'].notna()
    income_csmar.loc[m2, f'{v}_q_yoy_asset'] = (
        (income_csmar.loc[m2, f'{v}_q'] - income_csmar.loc[m2, f'{v}_q_last4']) / income_csmar.loc[m2, 'asset_last4']
    ).round(4)

    # IHS delta
    income_csmar[f'{v}_ihs_d'] = (income_csmar[f'{v}_ihs'] - income_csmar[f'{v}_ihs_last4']).round(4)





# clean col
income_csmar.columns
income_csmar = income_csmar[['id', 'year', 'quarter', 'yq',
    'total_income_q_yoy','total_income_q_yoy_asset', 'total_income_ihs_d', 
    'total_profit_q_yoy', 'total_profit_q_yoy_asset', 'total_profit_ihs_d']]














#%% ---------------------------------------------------------------------------------------
# ----------------------- save data---------------------------------------------
# ----------------------------------------------------------------------------------------
income_csmar = income_csmar.drop(columns=['yq'])

income_csmar.to_parquet(
    f"{processing_data_loc}/income_sheet.parquet",
    index=False
)




