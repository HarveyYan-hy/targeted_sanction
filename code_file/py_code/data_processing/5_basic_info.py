#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from code_file.py_code.py_config import raw_data, processing_data






#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
py_data_loc = raw_data()
processing_data_loc = processing_data()








#%% ---------------------------------------------------------------------------------------
# -----------------------get data----------------------------------------------
# ----------------------------------------------------------------------------------------
basic_info_csmar = pd.read_excel(
        f"{py_data_loc}/csmar/basic_info/STK_LISTEDCOINFOANL.xlsx")

id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")






#%% ---------------------------------------------------------------------------------------
# -----------------------clean col----------------------------------------------
# ----------------------------------------------------------------------------------------

basic_info_csmar = basic_info_csmar.drop(columns=['RegisterCapital'])









#%% ---------------------------------------------------------------------------------------
# ------------------------Replace IDs----------------------------------------------
# ----------------------------------------------------------------------------------------
# Build mapping dict
id_dict = id_map[id_map['panel']==1].set_index('stkcd')['id'].to_dict()


# Apply mapping
basic_info_csmar['id'] = basic_info_csmar['Symbol'].map(id_dict)


# Remove rows with missing id
basic_info_csmar = basic_info_csmar[basic_info_csmar['id'].notna()]








#%% ---------------------------------------------------------------------------------------
# -----------------------Copy the basic information for the year 2024----------------------------------------------
# ----------------------------------------------------------------------------------------
basic_info_csmar['EndDate'] = pd.to_datetime(basic_info_csmar['EndDate'])
basic_info_csmar['year'] = basic_info_csmar['EndDate'].dt.year
basic_info_csmar['quarter'] = basic_info_csmar['EndDate'].dt.quarter

add_2025_df = basic_info_csmar[basic_info_csmar['year']==2024]
add_2025_df['year'] = 2025
basic_info_csmar = pd.concat([basic_info_csmar,add_2025_df], axis=0).reset_index(drop=True)
basic_info_csmar.drop(columns=['EndDate'],inplace=True)









#%% ---------------------------------------------------------------------------------------
# -----------------------save data----------------------------------------------
# ----------------------------------------------------------------------------------------
basic_info_csmar.to_parquet(
    f"{processing_data_loc}/basic_info_csmar.parquet",
    index=False
)
