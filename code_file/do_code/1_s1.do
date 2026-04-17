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
* -------------------------------Load data----------------------------------------------
* -----------------------------------------------------------------------------------------
use "$stata_data/stage1_panel.dta", clear






* %%--------------------------------------------------------------------------------------
* -------------------------------Basic data processing----------------------------------------------
* -----------------------------------------------------------------------------------------
* Define panel
encode id, gen(id_code)   
tab yq,missing
xtset id_code yq



* Drop financial industry samples
drop if substr(industrycoded, 1, 1) == "J"



* Industry * time fixed effects
gen ind_sector = substr(industrycoded, 1, 1)
egen ind_time = group(ind_sector yq)




* Winsorize
winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace



* sanpost
tab san_yq,missing
tab san_yq second_san, missing
gen sanpost = 0
replace sanpost = 1 if (!missing(san_yq)) & (yq >= san_yq) 



* Define global variables
global con_var major_change top_hold_share i.debt_level i.cash_level i.asset_level
global fixed_var id_code ind_time



* Drop samples after the second sanction
drop if yq >= second_san



* %%--------------------------------------------------------------------------------------
* -------------------------------Descriptive statistics-----------------------------------------------
* -----------------------------------------------------------------------------------------
estpost summarize
save "$s1_result/descriptive_statistics.dta", replace








* %%--------------------------------------------------------------------------------------
* ------------------------------Set window-----------------------------------------------
* -----------------------------------------------------------------------------------------
* Generate relative time
gen eventtime = yq - san_yq
tab eventtime,missing


* Adjust relative time
replace eventtime = -12 if eventtime <= -12 & eventtime != .
replace eventtime = 8 if eventtime >= 8 & eventtime != .


* Generate dummy 
forvalues i = 12(-1)1 {
    gen D_`i' = (eventtime == -`i')
}

gen D0 = (eventtime == 0)

forvalues i = 1/8 {
    gen D`i' = (eventtime == `i')
}


* Define dynamic DID variables
global d_did D_12 D_11 D_10 D_9 D_8 D_7 D_6 D_5 D_4 D_3 D_2 D0 D1 D2 D3 D4 D5 D6 D7 D8 D_1













* %%--------------------------------------------------------------------------------------
* -------------------------------Baseline regressions-----------------------------------------------
* -----------------------------------------------------------------------------------------
* Without control variables
reghdfe total_income_q_yoy sanpost, absorb($fixed_var) vce(cluster id_code)
estimates store no_control


* With control variables
reghdfe total_income_q_yoy sanpost $con_var, absorb($fixed_var) vce(cluster id_code)
estimates store baseline



* Event study
reghdfe total_income_q_yoy $d_did $con_var, absorb($fixed_var) vce(cluster id_code)
estimates store eventstudy

coefplot, ///
    keep(D_12 D_11 D_10 D_9 D_8 D_7 D_6 D_5 D_4 D_3 D_2 D0 D1 D2 D3 D4 D5 D6 D7 D8) ///
    vertical yline(0) ///
    ciopts(lwidth(thin)) msymbol(O) msize(small) ///
    xlabel(, angle(0)) ///
    legend(off)




* %%--------------------------------------------------------------------------------------
* -------------------------------cn_rate heterogeneity-----------------------------------------------
* -----------------------------------------------------------------------------------------
* Set the control group to 0
tab up_group,missing
replace up_group = 0 if missing(up_group)



* Upstream low domestic content
reghdfe total_income_q_yoy sanpost $con_var if up_group==0 | up_group==1, absorb($fixed_var) vce(cluster id_code)
estimates store cn_low



* Upstream high domestic content
reghdfe total_income_q_yoy sanpost $con_var if up_group==0 | up_group==2, absorb($fixed_var) vce(cluster id_code)
estimates store cn_high










* %%--------------------------------------------------------------------------------------
* -------------------------------eig heterogeneity-----------------------------------------------
* -----------------------------------------------------------------------------------------
tab eigin_group,missing
replace eigin_group = 0 if missing(eigin_group)


* Low indegree
reghdfe total_income_q_yoy sanpost $con_var if eigin_group==0 | eigin_group==1, absorb($fixed_var) vce(cluster id_code)
estimates store eig_low



* High indegree
reghdfe total_income_q_yoy sanpost $con_var if eigin_group==0 | eigin_group==2, absorb($fixed_var) vce(cluster id_code)
estimates store eig_high








* %%--------------------------------------------------------------------------------------
* -------------------------------Patent heterogeneity-----------------------------------------------
* -----------------------------------------------------------------------------------------
tab patent_group,missing
replace patent_group = 0 if missing(patent_group)


* Low patents
reghdfe total_income_q_yoy sanpost $con_var if patent_group==0 | patent_group==1, absorb($fixed_var) vce(cluster id_code)
estimates store patent_low



* High patents
reghdfe total_income_q_yoy sanpost $con_var if patent_group==0 | patent_group==2, absorb($fixed_var) vce(cluster id_code)
estimates store patent_high






* %%--------------------------------------------------------------------------------------
* -------------------------------soe heterogeneity-----------------------------------------------
* -----------------------------------------------------------------------------------------
* Check distribution
tab top_hold_nature 
tab top_hold_nature if !missing(san_yq)

* Mark state ownership
gen natioanl_hold = 0
replace natioanl_hold = 1 if (top_hold_nature==4) | (top_hold_nature==6)
tab natioanl_hold
tab natioanl_hold if !missing(san_yq)




* State-owned
reghdfe total_income_q_yoy sanpost $con_var if missing(san_yq) | (!missing(san_yq) & natioanl_hold==1), absorb($fixed_var) vce(cluster id_code)
estimates store soe


* Non-state-owned
reghdfe total_income_q_yoy sanpost $con_var if missing(san_yq) | (!missing(san_yq) & natioanl_hold==0), absorb($fixed_var) vce(cluster id_code)
estimates store nsoe







* %%--------------------------------------------------------------------------------------
* -------------------------------alternative Y-----------------------------------------------
* -----------------------------------------------------------------------------------------
reghdfe total_income_q_yoy_asset sanpost $con_var, absorb($fixed_var) vce(cluster id_code)
estimates store robust_asset

reghdfe total_income_ihs_d sanpost $con_var, absorb($fixed_var) vce(cluster id_code)
estimates store robust_ihs





* %%--------------------------------------------------------------------------------------
* -------------------------------ST-related-----------------------------------------------
* -----------------------------------------------------------------------------------------
tab st_sample,missing
tab exit_sample,missing

reghdfe total_income_q_yoy sanpost $con_var if (st_sample==0) & (exit_sample==0), absorb($fixed_var) vce(cluster id_code)
estimates store robust_st

* %%--------------------------------------------------------------------------------------
* -------------------------------COVID-related -----------------------------------------------
* -----------------------------------------------------------------------------------------

* Province * time fixed effects
egen province_time = group(provincecode yq)


reghdfe total_income_q_yoy sanpost $con_var, absorb($fixed_var province_time) vce(cluster id_code)
estimates store robust_province



* %%--------------------------------------------------------------------------------------
* -------------------------------placebo test-----------------------------------------------
* -----------------------------------------------------------------------------------------
* Number of placebo iterations
global pla_num = 500

* Matrices for storing results
mat b_matrix  = J($pla_num, 1, .)
mat se_matrix = J($pla_num, 1, .)
mat p_matrix  = J($pla_num, 1, .)


* Number of treated units
quietly levelsof id_code if !missing(san_yq), local(real_treated_ids)
global N_targeted : word count `real_treated_ids'



* Eligible for sampling: id_code with at least 2 periods of observations
preserve
    keep id_code yq
    duplicates drop id_code yq, force    // Prevent repeated id-yq pairs from causing interference
    quietly bysort id_code: gen long nT = _N
    keep if nT >= 2
    keep id_code
    duplicates drop
    tempfile id_universe_eligible
    save `id_universe_eligible', replace

    count
    local N_eligible = r(N)
restore



* Loop sampling
forval i = 1/$pla_num {

    * Random seed
    set seed `=2025 + `i''

    * Draw treated group
    preserve
        use `id_universe_eligible', clear
        quietly sample $N_targeted, count
        gen byte pseudo_group = 1
        tempfile pseudo_ids
        quietly save `pseudo_ids', replace
    restore


    * Draw treatment timing
    preserve
        keep id_code yq
        quietly duplicates drop id_code yq, force

        * Keep only the sampled pseudo-treated group
        quietly merge m:1 id_code using `pseudo_ids', keep(match) nogenerate

        * Exclude the first-period observation for each individual
        bysort id_code (yq): drop if _n==1

        * Randomly draw 1 yq from the remaining periods
        gen double u = runiform()
        quietly bysort id_code (u): keep if _n==1

        rename yq pseudo_start_yq
        keep id_code pseudo_start_yq

        * Strict check: whether there are exactly N_targeted ids
        quietly count
        if (r(N) != $N_targeted) {
            di as err "ERROR in loop `i': pseudo timing ids != N_targeted"
            exit 459
        }

        tempfile pseudo_timing
        quietly save `pseudo_timing', replace
    restore


    * Merge into panel data
    cap drop pseudo_start_yq
    cap drop pseudo_treat_it

    quietly merge m:1 id_code using `pseudo_timing', keep(master match) nogenerate

    gen byte pseudo_treat_it = (!missing(pseudo_start_yq) & yq >= pseudo_start_yq)
	
	* Regression analysis
    quietly reghdfe total_income_q_yoy pseudo_treat_it $con_var, absorb($fixed_var) vce(cluster id_code)

    tempname b se
    scalar `b'  = _b[pseudo_treat_it]
    scalar `se' = _se[pseudo_treat_it]

    mat b_matrix[`i',1]  = `b'
    mat se_matrix[`i',1] = `se'
    mat p_matrix[`i',1]  = 2*ttail(e(df_r), abs(`b'/`se'))

    * Clean up
    quietly drop pseudo_start_yq pseudo_treat_it
}



* Save data
preserve
    clear

    * Matrix -> variables (one column for each matrix)
    svmat b_matrix,  names(b)
    svmat se_matrix, names(se)
    svmat p_matrix,  names(p)

    rename b1  b_hat
    rename se1 se_hat
    rename p1  p_val

    * Optional: add an iteration index for traceability
    gen int iter = _n
    order iter b_hat se_hat p_val


    * Save to disk (modify the path yourself if needed)
    save "${s1_result}/pla_test.dta", replace
restore



* %%--------------------------------------------------------------------------------------
* -------------------------------Save baseline and robustness-----------------------
* -----------------------------------------------------------------------------------------
cap mkdir "${s1_result}"
local estlist no_control baseline robust_asset robust_ihs robust_province robust_st

foreach est of local estlist {
    estimates restore `est'
    parmest, level(90) escal(N r2_a)  rename(es_1 N es_2 r2a) saving("${s1_result}/`est'.dta", replace)
}







* %%--------------------------------------------------------------------------------------
* -------------------------------Save heterogeneity results-----------------------------------------------
* -----------------------------------------------------------------------------------------
cap mkdir "${s1_result}"
local estlist cn_low cn_high eig_low eig_high patent_low patent_high soe nsoe

foreach est of local estlist {
    estimates restore `est'
    parmest, level(90) escal(N r2_a)  rename(es_1 N es_2 r2a) saving("${s1_result}/`est'.dta", replace)
}




* %%--------------------------------------------------------------------------------------
* -------------------------------Save event-study results-----------------------------------------------
* -----------------------------------------------------------------------------------------
cap mkdir "${s1_result}"
local estlist eventstudy

foreach est of local estlist {
    estimates restore `est'
    parmest, level(90) escal(N r2_a)  rename(es_1 N es_2 r2a) saving("${s1_result}/`est'.dta", replace)
}





* %%--------------------------------------------------------------------------------------
* -------------------------------did_imputation-----------------------------------------------
* -----------------------------------------------------------------------------------------
clear
use "$stata_data/stage1_panel.dta", clear


* Define panel
encode id, gen(id_code)   
tab yq,missing
xtset id_code yq



* Drop financial industry samples
drop if substr(industrycoded, 1, 1) == "J"



* Industry * time fixed effects
gen ind_sector = substr(industrycoded, 1, 1)
egen ind_time = group(ind_sector yq)




* Winsorize
winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace



* sanpost
tab san_yq,missing
tab san_yq second_san, missing
gen sanpost = 0
replace sanpost = 1 if (!missing(san_yq)) & (yq >= san_yq) 



* Define global variables
global con_var major_change top_hold_share i.debt_level i.cash_level i.asset_level
global fixed_var id_code ind_time



* Drop samples after the second sanction
drop if yq >= second_san


* Generate financial dummy variables
tab debt_level, gen(d_debt)
tab cash_level, gen(d_cash)
tab asset_level, gen(d_asset)


did_imputation total_income_q_yoy id_code yq san_yq, horizons(0/8) pretrend(12) autosample controls(major_change top_hold_share d_debt2 d_debt3 d_debt4 d_cash2 d_cash3 d_cash4 d_asset2 d_asset3 d_asset4) fe(id_code ind_time) cluster(id_code) tol(1) maxit(100)
estimates store did_imputation


* Store regression results
local estlist did_imputation
foreach est of local estlist {
    estimates restore `est'
    parmest, level(90) escal(N r2_a)  rename(es_1 N es_2 r2a) saving("${s1_result}/`est'.dta", replace)
}





* %%--------------------------------------------------------------------------------------
* -------------------------------stackedev-----------------------------------------------
* -----------------------------------------------------------------------------------------
clear
use "$stata_data/stage1_panel.dta", clear



* Define panel
encode id, gen(id_code)   
tab yq,missing
xtset id_code yq



* Drop financial industry samples
drop if substr(industrycoded, 1, 1) == "J"



* Industry * time fixed effects
gen ind_sector = substr(industrycoded, 1, 1)
egen ind_time = group(ind_sector yq)




* Winsorize
winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace



* sanpost
tab san_yq,missing
tab san_yq second_san, missing
gen sanpost = 0
replace sanpost = 1 if (!missing(san_yq)) & (yq >= san_yq) 



* Define global variables
global con_var major_change top_hold_share i.debt_level i.cash_level i.asset_level
global fixed_var id_code ind_time



* Drop samples after the second sanction
drop if yq >= second_san


* Generate control-group indicator
gen never_san = 0
replace never_san = 1 if missing(san_yq)



* Generate relative time
gen eventtime = yq - san_yq


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

global d_did D_12 D_11 D_10 D_9 D_8 D_7 D_6 D_5 D_4 D_3 D_2 D0 D1 D2 D3 D4 D5 D6 D7 D8 D_1 



stackedev total_income_q_yoy $d_did, cohort(san_yq) time(yq) never_treat(never_san) unit_fe(id_code) clust_unit(id_code) covariates($con_var)
estimates store stackedev

* Store regression results
local estlist stackedev

foreach est of local estlist {
    estimates restore `est'
    parmest, level(90) escal(N r2_a)  rename(es_1 N es_2 r2a) saving("${s1_result}/`est'.dta", replace)
}






* %%--------------------------------------------------------------------------------------
* -------------------------------eventstudyinteract-----------------------------------------------
* -----------------------------------------------------------------------------------------
clear
use "$stata_data/stage1_panel.dta", clear



* Define panel
encode id, gen(id_code)   
tab yq,missing
xtset id_code yq



* Drop financial industry samples
drop if substr(industrycoded, 1, 1) == "J"



* Industry * time fixed effects
gen ind_sector = substr(industrycoded, 1, 1)
egen ind_time = group(ind_sector yq)




* Winsorize
winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace



* sanpost
tab san_yq,missing
tab san_yq second_san, missing
gen sanpost = 0
replace sanpost = 1 if (!missing(san_yq)) & (yq >= san_yq) 



* Define global variables
global con_var major_change top_hold_share i.debt_level i.cash_level i.asset_level
global fixed_var id_code ind_time



* Drop samples after the second sanction
drop if yq >= second_san


* Generate control-group indicator
gen never_san = 0
replace never_san = 1 if missing(san_yq)



* Generate relative time
gen eventtime = yq - san_yq


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

global d_did D_12 D_11 D_10 D_9 D_8 D_7 D_6 D_5 D_4 D_3 D_2 D0 D1 D2 D3 D4 D5 D6 D7 D8 D_1 


* Regression
eventstudyinteract total_income_q_yoy $d_did, cohort(san_yq) control_cohort(never_san) covariates(major_change top_hold_share i.debt_level i.cash_level i.asset_level) absorb(id_code ind_time) vce(cluster id_code)

estimates store es_raw

* Repost the IW results to e(b)/e(V)
matrix b_iw = e(b_iw)
matrix V_iw = e(V_iw)
erepost b=b_iw V=V_iw
estimates store eventstudyinteract
estimates replay eventstudyinteract



* Store regression results
local estlist eventstudyinteract

foreach est of local estlist {
    estimates restore `est'
    parmest, level(90) escal(N r2_a)  rename(es_1 N es_2 r2a) saving("${s1_result}/`est'.dta", replace)
}