#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import random
import string
from code_file.py_code.py_config import raw_data, processing_data




#%% ---------------------------------------------------------------------------------------
# ------------------------Get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc = raw_data()
processing_data_loc = processing_data()




#%% ---------------------------------------------------------------------------------------
# ------------------------read data----------------------------------------------
# ----------------------------------------------------------------------------------------
factset_df = pd.read_csv(
    f"{raw_data_loc}/factset/kh4r7uk0s9vw4x7a.csv",
    dtype={
        'source_company_id': str,
        'source_ticker': str,
        'source_isin': str,
        'target_company_id': str,
        'target_ticker': str,
        'target_isin': str
    }) 

balance_csmar = pd.read_csv(f"{raw_data_loc}/csmar/balance_sheet/FS_Combas.csv",dtype={'Stkcd': str})

sanction_list = pd.read_excel(f"{raw_data_loc}/sanction_list/sanctioned_company.xlsx",dtype={'stkcd': str, 'os_id': str })






#%% ---------------------------------------------------------------------------------------
# -----------------------Sort FactSet id----------------------------------------------
# ----------------------------------------------------------------------------------------
id_isin_ticker1 = factset_df[['source_company_id','source_ticker','source_isin']].drop_duplicates()
id_isin_ticker2 = factset_df[['target_company_id','target_ticker','target_isin']].drop_duplicates()

id_isin_ticker1.columns = id_isin_ticker1.columns.str.replace(r'^(source_|SOURCE_)', '',regex=True)
id_isin_ticker2.columns = id_isin_ticker2.columns.str.replace(r'^(target_|TARGET_)', '',regex=True)


id_df = pd.concat([id_isin_ticker1, id_isin_ticker2], axis=0).reset_index(drop=True).drop_duplicates()
id_df = id_df.rename(columns={'company_id': 'factset_id', 'ticker': 'stkcd'})








#%% ---------------------------------------------------------------------------------------
# -----------------------add sanctioned firm----------------------------------------------
# ----------------------------------------------------------------------------------------
# Delete Yue Power / Lutai（Regarding sanctoned A/B stocks）
del_list = ['000726','200726',
            '000539','200539']
sanction_list = sanction_list[~sanction_list['stkcd'].isin(del_list)] 



# sanctioned enterprises included in FactSet
id_df = id_df.merge(
    sanction_list[['stkcd','os_id']],
    on='stkcd',
    how='left'
)


# sanctioned enterprises not included
sanction_add_set = set(sanction_list['stkcd'].unique()) - set(id_df['stkcd'].unique())
sanction_add_df = sanction_list[sanction_list['stkcd'].isin(sanction_add_set)]
id_df = pd.concat([id_df, sanction_add_df[['stkcd','os_id']]], axis=0).reset_index(drop=True)
id_df['factset_id'] = id_df['factset_id'].fillna(id_df['os_id'])






#%% ---------------------------------------------------------------------------------------
# -----------------------firm in panel----------------------------------------------
# ----------------------------------------------------------------------------------------
# Delete Yue Power / Lutai（Regarding A/B stocks）
balance_csmar = balance_csmar[~balance_csmar['Stkcd'].isin(del_list)]


# csmar firm
csmar_set = set(balance_csmar['Stkcd'].unique())


# mark in panel
id_df['panel'] = 0
id_df.loc[id_df['stkcd'].isin(csmar_set), 'panel'] = 1




# repeated 
double_public = id_df[id_df['panel'] == 1]
stkcd_counts = double_public['stkcd'].value_counts()
valid_stkcds = stkcd_counts[stkcd_counts >= 2].index
double_public = double_public[double_public['stkcd'].isin(valid_stkcds)] # 178家
double_public_set = set(double_public['stkcd'].unique())
len(double_public_set)

id_df.loc[id_df['stkcd'].isin(double_public_set),'panel'] = 0                













#%% ---------------------------------------------------------------------------------------
# -----------------------Create ID mapping----------------------------------------------
# ----------------------------------------------------------------------------------------
id_set = set(id_df['factset_id'].unique())


charset = string.ascii_lowercase + string.digits
new_ids = set()
id_mapping = {}

random.seed(2025)
for original_id in sorted(id_set):
    while True:
        new_id = ''.join(random.choices(charset, k=5))
        if new_id not in new_ids:
            new_ids.add(new_id)
            id_mapping[original_id] = new_id
            break


id_df['id'] = id_df['factset_id'].map(id_mapping)








#%% ---------------------------------------------------------------------------------------
# -----------------------save data----------------------------------------------
# ----------------------------------------------------------------------------------------
id_df.to_parquet(f"{processing_data_loc}/id_map.parquet", index=False)

