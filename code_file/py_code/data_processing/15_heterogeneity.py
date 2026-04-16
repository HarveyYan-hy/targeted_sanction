#%% ---------------------------------------------------------------------------------------
# ------------------------导入模块----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
from code_file.py_code.py_config import stata_data, processing_data







#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
processing_data_loc = processing_data()
stata_data_loc = stata_data()







#%% ---------------------------------------------------------------------------------------
# ------------------------load data----------------------------------------------
# ----------------------------------------------------------------------------------------
sanction_df = pd.read_parquet(f"{processing_data_loc}/sanction_info.parquet")
cn_rate = pd.read_parquet(f"{processing_data_loc}/rel_cn_rate.parquet")
eigvec_df = pd.read_parquet(f"{processing_data_loc}/eig_panel.parquet")
patent_df = pd.read_parquet(f"{processing_data_loc}/patent_df.parquet")






#%% ---------------------------------------------------------------------------------------
# ------------------------处理制裁数据----------------------------------------------
# ----------------------------------------------------------------------------------------

# fist san
sanction_first = sanction_df[sanction_df['san_date'].notna()]
sanction_first = sanction_first.sort_values(['id','san_date']).reset_index(drop=True)
sanction_first = sanction_first.loc[sanction_first.groupby("id")["san_date"].idxmin()]


# sanctiined set
san_set = set(sanction_first['id'].unique())


# san_yq
sanction_first['san_yq'] = (sanction_first['san_date'].dt.year) * 4 + (sanction_first['san_date'].dt.quarter)



# clean col
sanction_first = sanction_first[['id','san_yq','stkcd_sname']]




#%% ---------------------------------------------------------------------------------------
# ------------------------eig cn_rate----------------------------------------------
# ----------------------------------------------------------------------------------------

# keep sanctioned related
eigvec_df = eigvec_df[eigvec_df['id'].isin(san_set)]
cn_rate = cn_rate[cn_rate['id'].isin(san_set)]

eigvec_df = eigvec_df.merge(
    sanction_first[['id','san_yq']],
    on = 'id',
    how = 'left')
cn_rate = cn_rate.merge(
    sanction_first[['id','san_yq']],
    on = 'id',
    how = 'left')


# rel_time
eigvec_df['rel_time'] = eigvec_df['yq'] - eigvec_df['san_yq']
cn_rate['rel_time'] = cn_rate['yq'] - cn_rate['san_yq']




# cn_rate average
down_cols = [col for col in cn_rate.columns if col.startswith('down_cn_rate_')]
up_cols   = [col for col in cn_rate.columns if col.startswith('up_cn_rate_')]
cn_rate['down_cn_rate'] = cn_rate[down_cols].mean(axis=1).round(4)
cn_rate['up_cn_rate']   = cn_rate[up_cols].mean(axis=1).round(4)
cn_rate = cn_rate[['id', 'yq','rel_time', 'down_cn_rate', 'up_cn_rate']]







# Keep the last issue in advance or the first issue after the event.
eigvec_df = eigvec_df.groupby('id', group_keys=False).apply(
    lambda g: g[g['rel_time'] <= 0].loc[[g[g['rel_time'] <= 0]['rel_time'].idxmax()]]
    if (g['rel_time'] <= 0).any()
    else g.loc[[g['rel_time'].idxmin()]]
).reset_index(drop=True)

cn_rate = cn_rate.groupby('id', group_keys=False).apply(
    lambda g: g[g['rel_time'] <= 0].loc[[g[g['rel_time'] <= 0]['rel_time'].idxmax()]]
    if (g['rel_time'] <= 0).any()
    else g.loc[[g['rel_time'].idxmin()]]
).reset_index(drop=True)



# group
eigvec_df['in_median'] = eigvec_df['eigin_rank'].median()
eigvec_df['out_median'] = eigvec_df['eigout_rank'].median()
cn_rate['down_median'] = cn_rate['down_cn_rate'].median()
cn_rate['up_median']   = cn_rate['up_cn_rate'].median()


eigvec_df.loc[eigvec_df['eigin_rank'] >= eigvec_df['in_median'], 'eigin_group'] = 2
eigvec_df.loc[eigvec_df['eigin_rank'] < eigvec_df['in_median'], 'eigin_group'] = 1

eigvec_df.loc[eigvec_df['eigout_rank'] >= eigvec_df['out_median'], 'eigout_group'] = 2
eigvec_df.loc[eigvec_df['eigout_rank'] < eigvec_df['out_median'], 'eigout_group'] = 1

cn_rate.loc[cn_rate['down_cn_rate'] >= cn_rate['down_median'], 'down_group'] = 2
cn_rate.loc[cn_rate['down_cn_rate'] < cn_rate['down_median'], 'down_group'] = 1

cn_rate.loc[cn_rate['up_cn_rate'] >= cn_rate['up_median'], 'up_group'] = 2
cn_rate.loc[cn_rate['up_cn_rate'] < cn_rate['up_median'], 'up_group'] = 1



# clean col
eigvec_df = eigvec_df[['id', 'eigin_group', 'eigout_group']]
cn_rate = cn_rate[['id', 'down_group', 'up_group']]






#%% ---------------------------------------------------------------------------------------
# ------------------------专利与研发----------------------------------------------
# ----------------------------------------------------------------------------------------
patent_df = patent_df[patent_df['patents'].notna()]

patent_df = patent_df[patent_df['id'].isin(san_set)]

patent_df = patent_df.merge(
    sanction_first,
    on=['id'],
    how='left'
)


# regarded as the quarterly end data Q4
patent_df['yq'] = patent_df['year'] * 4 + 4



# rel_time
patent_df['rel_time'] = patent_df['yq'] - patent_df['san_yq']




# Keep the last issue in advance or the first issue after the event
patent_df = patent_df.groupby('id', group_keys=False).apply(
    lambda g: g[g['rel_time'] <= 0].loc[[g[g['rel_time'] <= 0]['rel_time'].idxmax()]]
    if (g['rel_time'] <= 0).any()
    else g.loc[[g['rel_time'].idxmin()]]
).reset_index(drop=True)






# group
patent_df['median'] = patent_df['patents'].median()
patent_df.loc[patent_df['patents'] >= patent_df['median'], 'group'] = 2
patent_df.loc[patent_df['patents'] < patent_df['median'], 'group'] = 1


# clean col
patent_df = patent_df[['id', 'group']]


# rename
patent_df   = patent_df.rename(columns={'group': 'patent_group'})




#%% ---------------------------------------------------------------------------------------
# ------------------------combine----------------------------------------------
# ----------------------------------------------------------------------------------------
heterogeneity_df = pd.DataFrame({'id': sorted(san_set)})

heterogeneity_df = heterogeneity_df.merge(
    eigvec_df,
    on=['id'],
    how='left'
)
heterogeneity_df = heterogeneity_df.merge(
    cn_rate,
    on=['id'],
    how='left'
)
heterogeneity_df = heterogeneity_df.merge(
    patent_df,
    on=['id'],
    how='left'
)


heterogeneity_df.to_parquet(
    f"{processing_data_loc}/heterogeneity_df.parquet",
    index=False
)
