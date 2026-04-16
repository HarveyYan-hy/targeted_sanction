* location-start
global stata_data "/your/project/directory/data/dta"
global s1_result "/your/project/directory/data/result/s1"
global s2_result "/your/project/directory/data/result/s2"
global s3_result "/your/project/directory/data/result/s3"
global figures_loc "/your/project/directory/figures"
global tables_loc "/your/project/directory/tables"
global code_loc "/Volumes/T7/phd/research/sanction_publication/code_file"
* location-end
* one-by-one
clear


do "${code_loc}/do_code/1_s1.do"
clear
do "${code_loc}/do_code/2_s2_ols.do"
clear
do "${code_loc}/do_code/3_s2_stacked.do"
clear
do "${code_loc}/do_code/4_s2_group.do"
clear
do "${code_loc}/do_code/5_s3_further.do"
