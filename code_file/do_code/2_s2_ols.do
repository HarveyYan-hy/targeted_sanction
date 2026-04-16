* location-start
global stata_data "/your/project/directory/data/dta"
global s1_result "/your/project/directory/data/result/s1"
global s2_result "/your/project/directory/data/result/s2"
global s3_result "/your/project/directory/data/result/s3"
global figures_loc "/your/project/directory/figures"
global tables_loc "/your/project/directory/tables"
global code_loc "/Volumes/T7/phd/research/sanction_publication/code_file"
* location-end
* %%--------------------------------------------------------------------------------------
* -------------------------------Open data----------------------------------------------
* -----------------------------------------------------------------------------------------
clear
use "$stata_data/stage2_ols.dta", clear






* %%--------------------------------------------------------------------------------------
* -------------------------------Basic data processing-------------------------------------
* -----------------------------------------------------------------------------------------
* Define panel
encode id, gen(id_code)   
xtset id_code yq



* Drop financial industry samples
drop if substr(industrycoded, 1, 1) == "J"



* Industry*time fixed effects
gen ind_sector = substr(industrycoded, 1, 1)
egen ind_time = group(ind_sector yq)




* Winsorize
winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace






* Define global variables
global con_var major_change top_hold_share i.debt_level i.cash_level i.asset_level
global fixed_var id_code ind_time 









* %%--------------------------------------------------------------------------------------
* -------------------------------Real exposure---------------------------------------------
* -----------------------------------------------------------------------------------------

tab upexpected,missing
forvalues i = 1/4 {
    gen ru`i' = upshock`i'
    replace ru`i' = 0 if upexpected == 1
    tab ru`i' upshock`i'
}

tab downexpected,missing
forvalues i = 1/4 {
    gen rd`i' = downshock`i'
    replace rd`i' = 0 if downexpected == 1
    tab rd`i' downshock`i'
}




global real_exp ru1 ru2 ru3 ru4 rd1 rd2 rd3 rd4



* Income
reghdfe total_income_q_yoy $real_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_income

reghdfe total_income_q_yoy_asset $real_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_income_asset

reghdfe total_income_ihs_d $real_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_income_ihs

* Upstream break
reghdfe up_break $real_exp $con_var, absorb($fixed_var) vce(cluster id_code) 
est store ols_up_break


* Downstream break
reghdfe down_break $real_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_down_break






* %%--------------------------------------------------------------------------------------
* -------------------------------Fake exposure---------------------------------------------
* -----------------------------------------------------------------------------------------
tab upexpected,missing
drop if upexpected==0
tab downexpected,missing
drop if downexpected==0

global fake_exp upshock1 upshock2 upshock3 upshock4 downshock1 downshock2 downshock3 downshock4


* Income
reghdfe total_income_q_yoy $fake_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_income_fake

reghdfe total_income_q_yoy_asset $fake_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_income_asset_fake

reghdfe total_income_ihs_d $fake_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_income_ihs_fake

* Upstream break
reghdfe up_break $fake_exp $con_var, absorb($fixed_var) vce(cluster id_code) 
est store ols_up_break_fake



* Downstream break
reghdfe down_break $fake_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_down_break_fake






* %%--------------------------------------------------------------------------------------
* -------------------------------Save results----------------------------------------------
* -----------------------------------------------------------------------------------------
cap mkdir "${s2_result}"
local estlist ols_income ols_up_break ols_down_break ols_income_fake ols_up_break_fake ols_down_break_fake

foreach est of local estlist {
    estimates restore `est'
    parmest, level(99) escal(N r2_a)  rename(es_1 N es_2 r2a) saving("${s2_result}/`est'.dta", replace)
}













* %%--------------------------------------------------------------------------------------
* -------------------------------Random----------------------------------------------
* -----------------------------------------------------------------------------------------
clear
use "$stata_data/stage2_ols_random.dta", clear





* Define panel
encode id, gen(id_code)   
xtset id_code yq



* Drop financial industry samples
drop if substr(industrycoded, 1, 1) == "J"



* Industry*time fixed effects
gen ind_sector = substr(industrycoded, 1, 1)
egen ind_time = group(ind_sector yq)




* Winsorize
winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace






* Define global variables
global con_var major_change top_hold_share i.debt_level i.cash_level i.asset_level
global fixed_var id_code ind_time 








tab upexpected,missing
forvalues i = 1/4 {
    gen ru`i' = upshock`i'
    replace ru`i' = 0 if upexpected == 1
    tab ru`i' upshock`i'
}

tab downexpected,missing
forvalues i = 1/4 {
    gen rd`i' = downshock`i'
    replace rd`i' = 0 if downexpected == 1
    tab rd`i' downshock`i'
}




global real_exp ru1 ru2 ru3 ru4 rd1 rd2 rd3 rd4



* Income
reghdfe total_income_q_yoy $real_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_income_random



* Upstream break
reghdfe up_break $real_exp $con_var, absorb($fixed_var) vce(cluster id_code) 
est store ols_up_break_random


* Downstream break
reghdfe down_break $real_exp $con_var, absorb($fixed_var) vce(cluster id_code)
est store ols_down_break_random




cap mkdir "${s2_result}"
local estlist ols_income_random ols_up_break_random ols_down_break_random 

foreach est of local estlist {
    estimates restore `est'
    parmest, level(99) escal(N r2_a)  rename(es_1 N es_2 r2a) saving("${s2_result}/`est'.dta", replace)
}