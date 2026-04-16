#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from pathlib import Path
from code_file.py_code.py_config import raw_data, stata_data, processing_data







#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc = raw_data()
processing_data_loc = processing_data()








#%% ---------------------------------------------------------------------------------------
# -----------------------Load data----------------------------------------------
# ----------------------------------------------------------------------------------------
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")
patent_df = pd.read_excel(Path(raw_data_loc, 'csmar', 'patent', 'PT_LCDOMFORAPPLY.xlsx'))





#%% ---------------------------------------------------------------------------------------
# -----------------------patent----------------------------------------------
# ----------------------------------------------------------------------------------------
# drop headline
patent_df = patent_df.drop(patent_df.index[[0,1]])




# handle time var
patent_df['EndDate'] = pd.to_datetime(patent_df['EndDate'])
patent_df['year'] = patent_df['EndDate'].dt.year
patent_df = patent_df.drop(columns=['EndDate'])


# Convert column names to lowercase
patent_df.columns = patent_df.columns.str.lower()



# Keep only consolidated financial statements
patent_df = patent_df[patent_df['statetypecode']==1]
patent_df = patent_df.drop(columns=['statetypecode'])


# Keep only domestic patents
patent_df = patent_df[patent_df['area']==1]
patent_df = patent_df.drop(columns=['area'])



# Keep only the cumulative total number of patents
patent_df = patent_df[patent_df['applytypecode']=='S5204']
drop_cols = ['source','applytypecode', 'applytype','utilitymodel', 'design', 'invention']
patent_df = patent_df.drop(columns=drop_cols)










#%% ---------------------------------------------------------------------------------------
# -----------------------replace id----------------------------------------------
# ----------------------------------------------------------------------------------------
# Build mapping dict
id_dict = id_map[id_map['panel']==1].set_index('stkcd')['id'].to_dict()


# Apply mapping
patent_df['id'] = patent_df['symbol'].map(id_dict)



# Remove rows with missing id
patent_df = patent_df[patent_df['id'].notna()]






#%% ---------------------------------------------------------------------------------------
# -----------------------save data----------------------------------------------
# ----------------------------------------------------------------------------------------
patent_df.to_parquet(f"{processing_data_loc}/patent_df.parquet", index=False)
