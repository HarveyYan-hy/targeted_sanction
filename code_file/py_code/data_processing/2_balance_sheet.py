#%% ---------------------------------------------------------------------------------------
# ------------------------Importing Modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from code_file.py_code.py_config import raw_data, processing_data







#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc = raw_data()
processing_data_loc = processing_data()






#%% ---------------------------------------------------------------------------------------
# -----------------------get the data----------------------------------------------
# ----------------------------------------------------------------------------------------
balance_csmar = pd.read_csv(
        f"{raw_data_loc}/csmar/balance_sheet/FS_Combas.csv",
        dtype={'Stkcd': str}
        )

id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")





#%% ---------------------------------------------------------------------------------------
# -----------------------processing----------------------------------------------
# ----------------------------------------------------------------------------------------
# Keep only consolidated statements
balance_csmar = balance_csmar[balance_csmar['Typrep'] == 'A']
balance_csmar = balance_csmar.drop(columns='Typrep')


# Process time
balance_csmar['Accper'] = pd.to_datetime(balance_csmar['Accper'])
balance_csmar['year'] = balance_csmar['Accper'].dt.year
balance_csmar['quarter'] = balance_csmar['Accper'].dt.quarter
balance_csmar['month'] = balance_csmar['Accper'].dt.month
balance_csmar = balance_csmar[balance_csmar['month'] != 1]





# Keep only specified accounts 
keep_cols = {
    'A002000000':'liability',
    'A001000000':'asset',
    'A001200000':'illiquid_asset',
    'A001101000':'currency'

}
balance_csmar = balance_csmar.rename(columns=keep_cols)

balance_csmar = balance_csmar[['Stkcd', 'ShortName','year','quarter','month',
                            'liability', 'asset', 'illiquid_asset', 'currency']]



# Convert column names to lowercase
balance_csmar.columns = balance_csmar.columns.str.lower() 




'''

#%% ---------------------------------------------------------------------------------------
# -----------------------查看数据分布----------------------------------------------
# ----------------------------------------------------------------------------------------
# 描述性统计信息
desc_list = []

fin_var_list = list(keep_cols.values())

for var in fin_var_list:
    s = balance_csmar[var].dropna()

    # 描述性统计
    desc = pd.Series({
        "var": var,
        "N": s.size,
        "missing": balance_csmar[var].isna().sum(),
        "mean": s.mean(),
        "std": s.std(),
        "min": s.min(),
        "p1": s.quantile(0.01),
        "p5": s.quantile(0.05),
        "p25": s.quantile(0.25),
        "median": s.median(),
        "p75": s.quantile(0.75),
        "p95": s.quantile(0.95),
        "p99": s.quantile(0.99),
        "max": s.max(),
    })
    desc_list.append(desc)


# 汇总输出描述性统计表
desc_df = pd.DataFrame(desc_list).set_index("var")
print(desc_df)

'''

















#%% ---------------------------------------------------------------------------------------
# -----------------------Compute relative levels----------------------------------------------
# ----------------------------------------------------------------------------------------

# Debt ratio
balance_csmar['debt_rate'] = (balance_csmar['liability'] / balance_csmar['asset']).round(4)


grp = balance_csmar.groupby(['year', 'quarter'])['debt_rate']
balance_csmar['debt_rate_25'] = grp.transform(lambda s: s.quantile(0.25))
balance_csmar['debt_rate_50'] = grp.transform(lambda s: s.quantile(0.50))  
balance_csmar['debt_rate_75'] = grp.transform(lambda s: s.quantile(0.75))


d  = balance_csmar['debt_rate']
q25 = balance_csmar['debt_rate_25']
q50 = balance_csmar['debt_rate_50']
q75 = balance_csmar['debt_rate_75']
level = np.full(len(balance_csmar), np.nan, dtype=float)
level = np.where(d < q25, 1, level)
level = np.where((d >= q25) & (d < q50), 2, level)
level = np.where((d >= q50) & (d < q75), 3, level)
level = np.where(d >= q75, 4, level)

balance_csmar['debt_level'] = pd.Series(level, index=balance_csmar.index).astype('Int64')
balance_csmar = balance_csmar.drop(columns=['debt_rate','debt_rate_25','debt_rate_50','debt_rate_75'])



# Cash ratio
balance_csmar['cash_rate'] = balance_csmar['currency'] / balance_csmar['asset']
grp_cash = balance_csmar.groupby(['year', 'quarter'])['cash_rate']
balance_csmar['cash_rate_25'] = grp_cash.transform(lambda s: s.quantile(0.25))
balance_csmar['cash_rate_50'] = grp_cash.transform(lambda s: s.quantile(0.50)) 
balance_csmar['cash_rate_75'] = grp_cash.transform(lambda s: s.quantile(0.75))

c   = balance_csmar['cash_rate']
cq25 = balance_csmar['cash_rate_25']
cq50 = balance_csmar['cash_rate_50']
cq75 = balance_csmar['cash_rate_75']

cash_level = np.full(len(balance_csmar), np.nan, dtype=float)
cash_level = np.where(c < cq25, 1, cash_level)
cash_level = np.where((c >= cq25) & (c < cq50), 2, cash_level)
cash_level = np.where((c >= cq50) & (c < cq75), 3, cash_level)
cash_level = np.where(c >= cq75, 4, cash_level)

balance_csmar['cash_level'] = pd.Series(cash_level, index=balance_csmar.index).astype('Int64')
balance_csmar = balance_csmar.drop(columns=['cash_rate','cash_rate_25','cash_rate_50','cash_rate_75']) 



# Asset level
grp_asset = balance_csmar.groupby(['year', 'quarter'])['asset']
balance_csmar['asset_25'] = grp_asset.transform(lambda s: s.quantile(0.25))
balance_csmar['asset_50'] = grp_asset.transform(lambda s: s.quantile(0.50)) 
balance_csmar['asset_75'] = grp_asset.transform(lambda s: s.quantile(0.75))

a    = balance_csmar['asset']
a25  = balance_csmar['asset_25']
a50  = balance_csmar['asset_50']
a75  = balance_csmar['asset_75']

asset_level = np.full(len(balance_csmar), np.nan, dtype=float)
asset_level = np.where(a < a25, 1, asset_level)
asset_level = np.where((a >= a25) & (a < a50), 2, asset_level)
asset_level = np.where((a >= a50) & (a < a75), 3, asset_level)
asset_level = np.where(a >= a75, 4, asset_level)

balance_csmar['asset_level'] = pd.Series(asset_level, index=balance_csmar.index).astype('Int64')
balance_csmar = balance_csmar.drop(columns=['asset_25','asset_50','asset_75'])







#%% ---------------------------------------------------------------------------------------
# ------------------------Replace IDs----------------------------------------------
# ----------------------------------------------------------------------------------------
# Build mapping dict
id_dict = id_map[id_map['panel']==1].set_index('stkcd')['id'].to_dict()


# Apply mapping
balance_csmar['id'] = balance_csmar['stkcd'].map(id_dict)


# Remove rows with missing id
balance_csmar = balance_csmar[balance_csmar['id'].notna()]







#%% ---------------------------------------------------------------------------------------
# -----------------------Save data----------------------------------------------
# ----------------------------------------------------------------------------------------

balance_csmar = balance_csmar[['id','year','quarter','debt_level','asset_level','cash_level','asset']]


balance_csmar.to_parquet(
    f"{processing_data_loc}/balance_sheet.parquet",
    index=False
)
