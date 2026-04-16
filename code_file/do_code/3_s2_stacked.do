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
* -------------------------------break----------------------------------------------
* -----------------------------------------------------------------------------------------
clear
use "$stata_data/stage2_stacked_break.dta", clear



* Check sample
count


* Set id
encode id,      gen(id_code)
encode fake_id,      gen(fake_id_code)


* Drop financial industry samples
drop if substr(industrycoded, 1, 1) == "J"



* Industry*time fixed effects
gen  ind_sector = substr(industrycoded, 1, 1)
egen ind_time   = group(ind_sector yq)


* id*cohort fixed effects
egen long idcohort = group(fake_id_code cohort)


* Winsorization
winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace



* Define global variables
global con_var   major_change top_hold_share i.debt_level i.cash_level i.asset_level
global fixed_var idcohort ind_time 





* All window dummy variables
local vars up1 down1
local suffixes _D_12 _D_11 _D_10 _D_9 _D_8 _D_7 _D_6 _D_5 _D_4 _D_3 _D_2 _D0 _D1 _D2 _D3 _D4 _D5 _D6 _D7 _D8 _D_1

global net_var
foreach v of local vars {
    foreach s of local suffixes {
        global net_var $net_var `v'`s'
    }
}


* Break
reghdfe up_break $net_var $con_var, absorb($fixed_var) vce(cluster id_code)
estimates store stacked_up_break

reghdfe down_break $net_var $con_var, absorb($fixed_var) vce(cluster id_code)
estimates store stacked_down_break




* Save regression results
cap mkdir "${s2_result}"
local estlist  stacked_up_break stacked_down_break 

    foreach est of local estlist {
        estimates restore `est'
        parmest, norestore level(90)
		
        save "${s2_result}/`est'.dta", replace
    }









* %%--------------------------------------------------------------------------------------
* -------------------------------income----------------------------------------------
* -----------------------------------------------------------------------------------------
clear
use "$stata_data/stage2_stacked_income.dta", clear



* Check sample
count


* Set id
encode id,      gen(id_code)
encode fake_id,      gen(fake_id_code)


* Drop financial industry samples
drop if substr(industrycoded, 1, 1) == "J"



* Industry*time fixed effects
gen  ind_sector = substr(industrycoded, 1, 1)
egen ind_time   = group(ind_sector yq)


* id*cohort fixed effects
egen long idcohort = group(fake_id_code cohort)


* Winsorization
winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace



* Define global variables
global con_var   major_change top_hold_share i.debt_level i.cash_level i.asset_level
global fixed_var idcohort ind_time 




* All window dummy variables
local vars up1 down1
local suffixes _D_12 _D_11 _D_10 _D_9 _D_8 _D_7 _D_6 _D_5 _D_4 _D_3 _D_2 _D0 _D1 _D2 _D3 _D4 _D5 _D6 _D7 _D8 _D_1

global net_var
foreach v of local vars {
    foreach s of local suffixes {
        global net_var $net_var `v'`s'
    }
}


* Income
reghdfe total_income_q_yoy $net_var $con_var, absorb($fixed_var) vce(cluster id_code)
est store stacked_income




cap mkdir "${s2_result}"
local estlist  stacked_income 

    foreach est of local estlist {
        estimates restore `est'
        parmest, norestore level(90)
		
        save "${s2_result}/`est'.dta", replace
    }