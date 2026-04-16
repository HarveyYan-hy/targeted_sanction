#%% ---------------------------------------------------------------------------------------
# ------------------------import module----------------------------------------------
# ----------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from tqdm import tqdm
import json
from matplotlib_venn import venn3
from datetime import date
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from code_file.py_code.py_config import figures_loc, raw_data, processing_data
from code_file.py_code.plot.tool_box import (
    set_econ_pub_style,
    new_figure,
    format_axes,
    add_legend
)
set_econ_pub_style(use_tex=True, font_serif=["Times New Roman"])







#%% ---------------------------------------------------------------------------------------
# ------------------------get the location----------------------------------------------
# ----------------------------------------------------------------------------------------
raw_data_loc = raw_data()
processing_data_loc = processing_data()
figure_loc = figures_loc()






#%% ---------------------------------------------------------------------------------------
# ------------------------get the data----------------------------------------------
# ----------------------------------------------------------------------------------------
sanctioned_company = pd.read_excel(f"{raw_data_loc}/sanction_list/sanctioned_company.xlsx",
                                dtype={'os_id': str, 'stkcd': str})
id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")







#%% ---------------------------------------------------------------------------------------
# ------------------------load json----------------------------------------------
# ----------------------------------------------------------------------------------------
# consolidation
file_path = f"{raw_data_loc}/opensanction/con_ftm.json"
con_san = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue 
        if obj.get("schema") == "Sanction":   
            con_san.append(obj)

con_ftm_df = pd.DataFrame(con_san)



# default
file_path = f"{raw_data_loc}/opensanction/default_ftm.json"
def_san = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue  
        if obj.get("schema") == "Sanction":   
            def_san.append(obj)

default_ftm_df = pd.DataFrame(def_san)





# mark debarred/sanction
con_ftm_df['type'] = 1
sanction_df = default_ftm_df.merge(
    con_ftm_df[['id','type']],
    on='id',
    how='left'
)
sanction_df['type'] = sanction_df['type'].fillna(0).astype(int)  





# clean columns
sanction_df['san_id'] = sanction_df['id']
sanction_df['san_properties'] = sanction_df['properties']

sanction_df = sanction_df.drop(
                        columns=[
                            "id","properties","referents", "first_seen", "last_seen", 
                            "schema", "last_change","target","origin"
                            ])





# get sanctioned entity 
sanction_df['entity'] = sanction_df['san_properties'].apply(lambda x: x.get('entity') if isinstance(x, dict) else None)
sanction_df = sanction_df[~sanction_df['entity'].isna()]
sanction_df['entity_num'] = sanction_df['entity'].apply(lambda x: len(x))
sanction_df['entity'] = sanction_df['entity'].apply(lambda x: x[0])
sanction_df.drop(columns=['entity_num'],inplace=True)







#%% ---------------------------------------------------------------------------------------
# -------------------------sanction info---------------------------------------------
# ----------------------------------------------------------------------------------------

sanction_df['os_id'] = sanction_df['entity']
sanction_df['san_datasets'] = sanction_df['datasets']

sanction_info = sanction_df[['os_id','san_id','type','san_datasets','san_properties']].merge(
    sanctioned_company,
    on='os_id',
    how='left'
)
sanction_info = sanction_info[sanction_info['stkcd'].notna()]
sanction_info = sanction_info.sort_values(by=['os_id','stkcd']).reset_index(drop=True)






# sanction info
sanction_info['listdate'] = sanction_info['san_properties'].apply(lambda x: x.get('listingDate') if isinstance(x, dict) else None) 
sanction_info['startdate'] = sanction_info['san_properties'].apply(lambda x: x.get('startDate') if isinstance(x, dict) else None) 
sanction_info['authority'] = sanction_info['san_properties'].apply(lambda x: x.get('authority') if isinstance(x, dict) else None) 
sanction_info['program_link'] = sanction_info['san_properties'].apply(lambda x: x.get('programUrl') if isinstance(x, dict) else None) 
sanction_info['program'] = sanction_info['san_properties'].apply(lambda x: x.get('program') if isinstance(x, dict) else None) 

sanction_info = sanction_info.drop(columns=['san_properties'])















#%% ---------------------------------------------------------------------------------------
# ------------------------['RUSSIA-EO14024']----------------------------------------------
# ----------------------------------------------------------------------------------------

mask1 = sanction_info['program'].apply(lambda x: isinstance(x, list) and ('RUSSIA-EO14024' in x))

targets = {
    '欧科亿688308': '2025-01-15',
    '瓦轴B200706': '2025-01-15',
    'ST天喻300205': '2024-06-12',
    '动力源600405': '2024-10-30',
    '华中数控300161': '2024-10-30',
    '浙海德曼688577': '2024-10-30',
    '安联锐视301042': '2024-10-30',
}

for sname, dt in targets.items():
    mask2 = (sanction_info['stkcd_sname'] == sname)
    idx = (mask1 & mask2).idxmax()
    sanction_info.at[idx, 'startdate'] = [dt]








#%% ---------------------------------------------------------------------------------------
# ------------------------BIS----------------------------------------------
# ----------------------------------------------------------------------------------------

mask1 = sanction_info['san_datasets'].apply(lambda x: isinstance(x, list) and ('us_trade_csl' in x))

targets = {
    '中瓷电子003031': '2018-08-01',
    '同惠电子833509': '2018-08-01',
}

for sname, dt in targets.items():
    mask2 = (sanction_info['stkcd_sname'] == sname)
    idx = (mask1 & mask2).idxmax()
    sanction_info.at[idx, 'startdate'] = [dt]



# The effective date for 华力创通300045 is missing in EL
# 立航科技603261 and 新晨科技300542 are UV, with no date







#%% ---------------------------------------------------------------------------------------
# ------------------------John S. McCain National Defense Authorization Act for Fiscal Year 2019 (Public Law 115-232)------------------
# ----------------------------------------------------------------------------------------
# The John S. McCain National Defense Authorization Act for Fiscal Year 2019 (Public Law 115-232) was signed into law on August 13, 2018
mask1 = sanction_info['program'].apply(
    lambda x: ('Section 889 of the John S. McCain National Defense Authorization Act for Fiscal Year 2019 (Public Law 115 - 232)' in x) 
    if isinstance(x, list) else False
)

for i in sanction_info.index[mask1]:
    sanction_info.at[i, 'startdate'] = ['2018-08-13']










#%% ---------------------------------------------------------------------------------------
# -----------------------Delete Yue Power / Lutai（Regarding A/B stocks）----------------------------------------------
# ----------------------------------------------------------------------------------------
del_stkcd = ['鲁泰B200726','鲁泰A000726','粤电力A000539','粤电力B200539']
sanction_info = sanction_info[~sanction_info['stkcd_sname'].isin(del_stkcd)]











#%% ---------------------------------------------------------------------------------------
# ------------------------earliest timestamp----------------------------------------------
# ----------------------------------------------------------------------------------------
result_list = [] 

for index, row in tqdm(sanction_info.iterrows(), total=sanction_info.shape[0], desc="Processing", leave=True):
    row_dict = row.to_dict()

    # Process listing date
    list_date_list = row_dict.get('listdate') or []
    list_date_list = [d for d in list_date_list if d]           
    list_date = min(list_date_list) if list_date_list else None

    # Process start date
    start_date_list = row_dict.get('startdate') or []
    start_date_list = [d for d in start_date_list if d]
    start_date = min(start_date_list) if start_date_list else None

    # Effective date = the earlier non-null date between the two
    candidates = [d for d in (list_date, start_date) if d]    
    row_dict['san_date'] = min(candidates) if candidates else None

    # Append to list
    result_list.append(row_dict)
    

sanction_info = pd.DataFrame(result_list)




# Adjust the time format
sanction_info['san_date'] = pd.to_datetime(sanction_info['san_date'])
sanction_info = sanction_info[sanction_info['san_date'].notna()]




# Extract year/quarter
sanction_info['year'] = sanction_info['san_date'].dt.year
sanction_info['quarter'] = sanction_info['san_date'].dt.quarter
sanction_info['san_yq'] = sanction_info['year']*4 + sanction_info['quarter']





# sample period
SAMPLE_PERIOD_START = 2015 * 4 + 1
SAMPLE_PERIOD_END = 2025 * 4 + 3







#%% ---------------------------------------------------------------------------------------
# ------------------------venn----------------------------------------------
# ----------------------------------------------------------------------------------------
firm_auth = sanction_info[['stkcd_sname','authority']]
dep_dict = {
    (
        'Department of the Commerce - International Trade Administration',
        'Entity List (EL) - Bureau of Industry and Security'
    ): ['Department of the Commerce'],

    (
        'Department of the Commerce - International Trade Administration',
        'Military End User (MEU) List - Bureau of Industry and Security'
    ): ['Department of the Commerce'],

    ('Department of the Commerce - International Trade Administration', 
    'Nonproliferation Sanctions (ISN) - State Department',):['Department of the Commerce'],

    ('TREAS-OFAC',): ['Department of the Treasury'],
    ('Office of Foreign Assets Control',): ['Department of the Treasury'],
}

firm_auth['authority'] = firm_auth['authority'].apply(
    lambda x: dep_dict.get(tuple(x), x)
)

firm_auth['num'] = firm_auth['authority'].str.len()
firm_auth = firm_auth[firm_auth['num']==1]
firm_auth['authority'] = firm_auth['authority'].str[0]
firm_auth['authority'].value_counts()


# 先筛选出3类 authority
firm_auth = firm_auth[firm_auth['authority'].isin([
    'Department of the Commerce',
    'Department of the Treasury',
    'Department of Defense'
])]

# 只保留作图需要的列，并去重
df_plot = firm_auth[['stkcd_sname', 'authority']].drop_duplicates().copy()

# 分别构造三个集合
commerce = set(df_plot.loc[
    df_plot['authority'] == 'Department of the Commerce', 'stkcd_sname'
])

treasury = set(df_plot.loc[
    df_plot['authority'] == 'Department of the Treasury', 'stkcd_sname'
])

defense = set(df_plot.loc[
    df_plot['authority'] == 'Department of Defense', 'stkcd_sname'
])


# 绘图
fig, ax = new_figure(width=6.0, height=6)

v = venn3(
    [commerce, treasury, defense],
    set_labels=('', '', ''),   # 不在图中直接显示标签
    set_colors=('#245532', '#447542', '#649552'),
    alpha=0.6,
    ax=ax
)
# 放大维恩图中的数字
for text in v.subset_labels:
    if text is not None:
        text.set_fontsize(12)     # 改成你想要的大小
        text.set_fontweight('bold')   # 需要加粗的话取消注释
# 自定义图例
legend_handles = [
    Patch(facecolor='#245532', edgecolor='black', alpha=0.6, label='Department of the Commerce'),
    Patch(facecolor='#447542', edgecolor='black', alpha=0.6, label='Department of the Treasury'),
    Patch(facecolor='#649552', edgecolor='black', alpha=0.6, label='Department of Defense')
]

ax.legend(
    handles=legend_handles,
    loc='lower center',
    bbox_to_anchor=(0.5, -0.15),   
    ncol=1,                       
    frameon=False,
    fontsize=12
    
)

plt.tight_layout()



fig.savefig(f"{figure_loc}/f3.pdf",dpi=1000)








#%% ---------------------------------------------------------------------------------------
# ------------------------Plot: cumulative number of firms & cumulative number of sanctions------------------------------------
# ----------------------------------------------------------------------------------------

# Count firms (keep only the first sanctioned quarter for each firm)
firm_count = sanction_info[['stkcd_sname', 'san_yq']].copy()
firm_count = firm_count.groupby('stkcd_sname', as_index=False)['san_yq'].min()

# Count sanctions (keep every sanction record)
san_count = sanction_info[['san_id', 'san_yq']].copy()

# Count the cumulative number of effective firms and sanctions by period
result = []
for i in range(SAMPLE_PERIOD_START, SAMPLE_PERIOD_END + 1):
    n_firm = (firm_count['san_yq'] <= i).sum()
    n_san = (san_count['san_yq'] <= i).sum()
    result.append([i, n_firm, n_san])

result_df = pd.DataFrame(result, columns=['san_yq', 'n_firm', 'n_san'])

# Convert to year and quarter
result_df['year'] = (result_df['san_yq'] - 1) // 4
result_df['quarter'] = (result_df['san_yq'] - 1) % 4 + 1
result_df['yq_label'] = result_df['year'].astype(int).astype(str) + 'Q' + result_df['quarter'].astype(int).astype(str)

# Prepare data for plotting
x = result_df['san_yq'].to_numpy()
y_firm = result_df['n_firm'].to_numpy()
y_san = result_df['n_san'].to_numpy()

fig, ax = new_figure(width=6.0, height=3.5)

# Number of firms: light gray shaded area
ax.fill_between(
    x,
    y_firm,
    0,
    color='0.7',
    alpha=0.25,
    linewidth=0.0,
    label=r"Cumulative number of sanctioned firms",
    zorder=1
)

# Number of sanctions: black line
ax.plot(
    x,
    y_san,
    color='0.0',
    linewidth=1.0,
    label=r"Cumulative number of sanctions",
    zorder=2
)

# x-axis ticks: show once per year at Q1
mask_q1 = result_df['quarter'] == 1
tick_pos = result_df.loc[mask_q1, 'san_yq'].to_numpy()
tick_labels = result_df.loc[mask_q1, 'yq_label'].to_list()

ax.set_xticks(tick_pos)
ax.set_xticklabels(tick_labels, rotation=45, ha='right')

# Axis limits
x_min, x_max = x.min(), x.max()
y_max = max(y_firm.max(), y_san.max())
x_pad = 0.5

format_axes(
    ax,
    #x_label=r"Quarter",
    #y_label=r"Count",
    xlim=(x_min - x_pad, x_max + x_pad),
    ylim=(0, y_max * 1.05),
    inward_ticks=True
)

# Legend
add_legend(ax, ncol=2, outside=True)

fig.tight_layout(pad=0.5)



# Save: pdf for LaTeX, png for preview
fig.savefig(f"{figure_loc}/f2.pdf",dpi=1000)