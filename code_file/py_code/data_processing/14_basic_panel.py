#%% ---------------------------------------------------------------------------------------
# ------------------------import module----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from code_file.py_code.py_config import raw_data, processing_data







#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc = raw_data()
processing_data_loc = processing_data()








#%% ---------------------------------------------------------------------------------------
# ------------------------load data----------------------------------------------
# ----------------------------------------------------------------------------------------
balance_sheet = pd.read_csv(
        f"{raw_data_loc}/csmar/balance_sheet/FS_Combas.csv",
        dtype={'Stkcd': str}
        )
basic_info_csmar = pd.read_parquet(f"{processing_data_loc}/basic_info_csmar.parquet")
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")
balance_csmar = pd.read_parquet(f"{processing_data_loc}/balance_sheet.parquet")
income_csmar = pd.read_parquet(f"{processing_data_loc}/income_sheet.parquet")
major_change = pd.read_parquet(f"{processing_data_loc}/major_change.parquet")
top_holder = pd.read_parquet(f"{processing_data_loc}/top_holder.parquet")
rel_panel = pd.read_parquet(f"{processing_data_loc}/rel_change.parquet")







#%% ---------------------------------------------------------------------------------------
# ------------------------create panel---------------------------------------------
# ----------------------------------------------------------------------------------------
# keep consolidated
panel_df = balance_sheet[balance_sheet['Typrep']=='A'][['Stkcd','ShortName','Accper','Typrep']]   
panel_df = panel_df.drop(columns='Typrep')


# handle time var
panel_df['Accper'] = pd.to_datetime(panel_df['Accper'])
panel_df = panel_df[panel_df['Accper'].dt.month != 1]
panel_df['year'] = panel_df['Accper'].dt.year
panel_df['quarter'] = panel_df['Accper'].dt.quarter
panel_df['yq'] = panel_df['year']*4 + panel_df['quarter']



# sample period
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3

panel_df = panel_df[
    (panel_df['yq']>=SAMPLE_PERIOD_START)
    &(panel_df['yq']<=SAMPLE_PERIOD_END)
]


# rename var
panel_df = panel_df.rename(columns={
    'Stkcd': 'stkcd',
    'ShortName': 'sname',
    'Accper': 'full_time'
})



# get id
id_dict = id_map[id_map['panel']==1].set_index('stkcd')['id'].to_dict()
panel_df['id'] = panel_df['stkcd'].map(id_dict)
panel_df = panel_df[panel_df['id'].notna()]




# add basic info
basic_info_csmar = basic_info_csmar.rename(columns={
    'Symbol': 'stkcd',
    'ShortName': 'sname',
})
basic_info_csmar.columns = basic_info_csmar.columns.str.lower() 
info_col= ['stkcd','industrycoded', 'provincecode','year']

print(panel_df.shape)
panel_df = panel_df.merge(basic_info_csmar[info_col],on=['year','stkcd'],how='left')
print(panel_df.shape)












#%% ---------------------------------------------------------------------------------------
# -----------------------st&exit----------------------------------------------
# ----------------------------------------------------------------------------------------

# st
panel_df['st_sample'] = 0
panel_df.loc[
    panel_df['sname'].astype(str).str.contains('st', case=False, na=False),
    'st_sample'
] = 1
panel_df['st_sample'] = panel_df['st_sample'].astype(int)

# exit
panel_df['exit_sample'] = 0
panel_df.loc[
    panel_df['sname'].astype(str).str.contains('退', case=False, na=False),
    'exit_sample'
] = 1
panel_df['exit_sample'] = panel_df['exit_sample'].astype(int)


















#%% ---------------------------------------------------------------------------------------
# -----------------------combine----------------------------------------------
# ----------------------------------------------------------------------------------------
# balance
balance_csmar['yq'] = balance_csmar['year']*4 + balance_csmar['quarter']
print(panel_df.shape)
panel_df = panel_df.merge(
        balance_csmar,
        on=['id','year','quarter','yq'],
        how='left')
print(panel_df.shape)


# income
panel_df = panel_df.merge(
        income_csmar,
        on=['id','year','quarter'],
        how='left')
print(panel_df.shape)


# change
panel_df = panel_df.merge(
        major_change[['id','year','quarter','major_change']],
        on=['id','year','quarter'],
        how='left')
panel_df['major_change'] = panel_df['major_change'].fillna(0)
print(panel_df.shape)



# holder
panel_df = panel_df.merge(
        top_holder,
        on=['id','year','quarter'],
        how='left')
print(panel_df.shape)




# rel change
panel_df = panel_df.merge(
        rel_panel,
        on=['id','yq'],
        how='left')
print(panel_df.shape)





# clen col
name_cols = ['sname']
panel_df = panel_df.drop(columns = name_cols)





#%% ---------------------------------------------------------------------------------------
# ------------------------save data----------------------------------------------
# ----------------------------------------------------------------------------------------
panel_df.to_parquet(
    f"{processing_data_loc}/basic_panel.parquet",
    index=False
)
