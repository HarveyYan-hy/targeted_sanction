#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from code_file.py_code.py_config import raw_data, processing_data










#%% ---------------------------------------------------------------------------------------
# ------------------------Get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc = raw_data()
processing_data_loc = processing_data()










#%% ---------------------------------------------------------------------------------------
# ------------------------Load data----------------------------------------------
# ----------------------------------------------------------------------------------------
factset_df = pd.read_csv(
    f"{raw_data_loc}/factset/kh4r7uk0s9vw4x7a.csv",
    dtype={
        'source_company_id': str,
        'SOURCE_ticker': str,
        'SOURCE_isin': str,
        'target_company_id': str,
        'TARGET_ticker': str,
        'TARGET_isin': str
    }
) 
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")







#%% ---------------------------------------------------------------------------------------
# ------------------------Basic----------------------------------------------
# ----------------------------------------------------------------------------------------
# clean col
del_list = [ 'subsidiaries', 'revenue_percent','percent_estimated', 
    'source_company_subsidiaries','target_company_subsidiaries', 
    'source_name', 'source_ticker','source_cusip','source_isin', 'source_sedol', 
    'target_name', 'target_ticker','target_cusip', 'target_isin', 'target_sedol', 
    'source_company_keyword','target_company_keyword', 
    'keyword1', 'keyword2', 'keyword3','keyword4', 'keyword5', 'keyword6', 'keyword7', 
    'keyword8', 'keyword9','keyword10']
factset_df = factset_df.drop(columns=del_list)



# replace id
id_dict = id_map.set_index('factset_id')['id'].to_dict()
factset_df['source_company_id'] = factset_df['source_company_id'].map(id_dict)
factset_df['target_company_id'] = factset_df['target_company_id'].map(id_dict)





# adjust time format
factset_df['start_year'] = factset_df['start_'].str[:4].astype(int) 
factset_df['end_year'] = factset_df['end_'].str[:4].astype(int) 

factset_df['start_month'] = factset_df['start_'].str[5:7].astype(int) 
factset_df['end_month'] = factset_df['end_'].str[5:7].astype(int) 

factset_df['start_day'] = factset_df['start_'].str[8:10].astype(int)
factset_df['end_day'] = factset_df['end_'].str[8:10].astype(int)

factset_df['start_quarter'] = (factset_df['start_month'] - 1) //3 + 1
factset_df['end_quarter'] = (factset_df['end_month'] - 1) //3 + 1


factset_df = factset_df.drop(columns=['start_', 'end_'])


# Lowercase column names
factset_df.columns = factset_df.columns.str.lower()








#%% ---------------------------------------------------------------------------------------
# ------------------------rival----------------------------------------------
# ----------------------------------------------------------------------------------------
rival_df = factset_df[factset_df['rel_type']=='COMPETITOR']
rival_df.to_parquet(f"{processing_data_loc}/rival_rel.parquet", index=False)








#%% ---------------------------------------------------------------------------------------
# ------------------------supply-customer----------------------------------------------
# ----------------------------------------------------------------------------------------

# filter
factset_df = factset_df[
    (factset_df['rel_type']=='SUPPLIER') |
    (factset_df['rel_type']=='CUSTOMER')] 




# Separate processing for supplier/customer relationships
factset_df_supplier = factset_df[factset_df['rel_type']=='SUPPLIER']
factset_df_customer = factset_df[factset_df['rel_type']=='CUSTOMER']



# Rename columns
factset_df_customer.columns = factset_df_customer.columns.str.replace('source_', 'supplier_', regex=False)
factset_df_customer.columns = factset_df_customer.columns.str.replace('target_', 'customer_', regex=False)

factset_df_supplier.columns = factset_df_supplier.columns.str.replace('source_', 'customer_', regex=False)
factset_df_supplier.columns = factset_df_supplier.columns.str.replace('target_', 'supplier_', regex=False)


# Combine
factset_df_customer = factset_df_customer.drop(columns=['rel_type'])
factset_df_supplier = factset_df_supplier.drop(columns=['rel_type'])

factset_adjust = pd.concat([factset_df_customer, factset_df_supplier], axis=0).reset_index(drop=True)










#%% ---------------------------------------------------------------------------------------
# ------------------------handel rel period----------------------------------------------
# ----------------------------------------------------------------------------------------
# going on rel-2027
factset_adjust['end_year'] = factset_adjust['end_year'].replace(4000,2027)


# end before 2015
factset_adjust = factset_adjust[factset_adjust['end_year']>=2015]


# period yq
factset_adjust['s_date'] = pd.to_datetime(
    dict(year = factset_adjust['start_year'], 
         month = factset_adjust['start_month'], 
         day = factset_adjust['start_day']))

factset_adjust['e_date'] = pd.to_datetime(
    dict(year = factset_adjust['end_year'],
         month = factset_adjust['end_month'],
         day = factset_adjust['end_day']))

factset_adjust['s_yq'] = factset_adjust['start_year']*4 + factset_adjust['start_quarter']
factset_adjust['e_yq'] = factset_adjust['end_year']*4 + factset_adjust['end_quarter']

factset_adjust = factset_adjust.drop(columns=['start_year', 'start_month', 'start_day', 'start_quarter',
                                              'end_year', 'end_month', 'end_day','end_quarter'])


# adjust start yp
factset_adjust['s_yq'] = factset_adjust['s_yq'] - 2





#%% ---------------------------------------------------------------------------------------
# ------------------------save data----------------------------------------------
# ----------------------------------------------------------------------------------------
factset_adjust.to_parquet(f"{processing_data_loc}/factset_rel.parquet", index=False)

















