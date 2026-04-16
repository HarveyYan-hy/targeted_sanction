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
* -------------------------------import the data----------------------------------------------
* -----------------------------------------------------------------------------------------
clear
use "$stata_data/stage3_panel.dta", clear




* %%--------------------------------------------------------------------------------------
* -------------------------------basic data processing----------------------------------------------
* -----------------------------------------------------------------------------------------
* Define panel
encode id, gen(id_code)   
tab yq,missing
xtset id_code yq



* Drop financial industry samples
drop if substr(industrycoded, 1, 1) == "J"



* Industry*time fixed effects
gen ind_sector = substr(industrycoded, 1, 1)
egen ind_time = group(ind_sector yq)




* Winsorize
winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace


* Drop sanctioned firms
tab san_yq,missing
keep if missing(san_yq)





* rivalpost
tab rival_yq,missing
gen rivalpost = 0
replace rivalpost = 1 if !missing(rival_yq) & yq >= rival_yq





* Define global variables
global con_var major_change top_hold_share i.debt_level i.cash_level i.asset_level downshock1 downshock2 downshock3 downshock4 upshock1 upshock2 upshock3 upshock4
global fixed_var id_code ind_time







* %%--------------------------------------------------------------------------------------
* -------------------------------baseline regression-----------------------------------------------
* -----------------------------------------------------------------------------------------


* With control variables
reghdfe total_income_q_yoy rivalpost $con_var, absorb($fixed_var) vce(cluster id_code)
est store income_control







* Save regression results
cap mkdir "${s3_result}/baseline"
local estlist income_control  

foreach est of local estlist {
    estimates restore `est'
    parmest, level(90) escal(N r2_a)  rename(es_1 N es_2 r2a) saving("${s3_result}/baseline/`est'.dta", replace)
}






* %%--------------------------------------------------------------------------------------
* ------------------------------set event window-----------------------------------------------
* -----------------------------------------------------------------------------------------
* Generate relative time
gen eventtime = yq - rival_yq


* Check the distribution of relative time
tab eventtime,missing


* Adjust relative time
replace eventtime = -12 if eventtime <= -12 & eventtime != .
replace eventtime = 8 if eventtime >= 8 & eventtime != .


* Generate relative-time dummy variables in a loop
forvalues i = 12(-1)1 {
    gen D_`i' = (eventtime == -`i')
}

gen D0 = (eventtime == 0)

forvalues i = 1/8 {
    gen D`i' = (eventtime == `i')
}






* %%--------------------------------------------------------------------------------------
* -------------------------------event study - total income--------------------------------
* -----------------------------------------------------------------------------------------
* Define dynamic DID variables
global d_did D_12 D_11 D_10 D_9 D_8 D_7 D_6 D_5 D_4 D_3 D_2 D0 D1 D2 D3 D4 D5 D6 D7 D8 D_1



* Income regression (main model)
reghdfe total_income_q_yoy $d_did $con_var, absorb($fixed_var) vce(cluster id_code)
est store income_event





* Save regression results
cap mkdir "${s3_result}"
local estlist income_event 


foreach est of local estlist {
    estimates restore `est'
    parmest, level(90) escal(N r2_a) rename(es_1 N es_2 r2a)  saving("${s3_result}/`est'.dta", replace)
}