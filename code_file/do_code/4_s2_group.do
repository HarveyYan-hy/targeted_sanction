* location-start
global stata_data "/your/project/directory/data/dta"
global s1_result "/your/project/directory/data/result/s1"
global s2_result "/your/project/directory/data/result/s2"
global s3_result "/your/project/directory/data/result/s3"
global figures_loc "/your/project/directory/figures"
global tables_loc "/your/project/directory/tables"
global code_loc "/your/project/directory/code_file"
* location-end
* %%--------------------------------------------------------------------------------------
* -------------------------------IW----------------------------------------------
* -----------------------------------------------------------------------------------------

* ----------------------------------up----------------------------------------------------
clear


* Regression result location
cap mkdir "${s2_result}"

* Loop over each group
local group_list up1 up2 up3 up4 


foreach group of local group_list {
    

    use "$stata_data/stage2_`group'.dta", clear


    * Set id
    encode id,      gen(id_code)
    encode fake_id, gen(fake_id_code)

    * Drop financial industry samples
    drop if substr(industrycoded, 1, 1) == "J"

    * Industry * time fixed effects
    gen  ind_sector = substr(industrycoded, 1, 1)
    egen ind_time   = group(ind_sector yq)


    * Winsorize
    winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace


    * Generate dummy variables: multi-category level controls
    tab debt_level,  gen(d_debt)
    tab cash_level,  gen(d_cash)
    tab asset_level, gen(d_asset)


    * Control group variable
    gen never = 0
    replace never = 1 if treated ==0
	tab treated never,missing
    

    * Define global variables
    global con_var  major_change top_hold_share i.debt_level i.cash_level i.asset_level
    global fixed_var fake_id_code ind_time 
    global did D_12 D_11 D_10 D_9 D_8 D_7 D_6 D_5 D_4 D_3 D_2 D0 D1 D2 D3 D4 D5 D6 D7 D8 D_1



    eventstudyinteract down_break $did , cohort(exp_start) control_cohort(never) covariates($con_var)  absorb($fixed_var) vce(cluster id_code)
    estimates store down_break_raw

    matrix b_iw = e(b_iw)
    matrix V_iw = e(V_iw)
    erepost b=b_iw V=V_iw
    estimates store group_iw_down_break


    cap mkdir "${s2_result}/`group'"
	local estlist group_iw_down_break 

    foreach est of local estlist {
        estimates restore `est'
        parmest, norestore level(90)
		
        save "${s2_result}/`group'/`est'.dta", replace
    }

}



* ----------------------------------down----------------------------------------------------

clear


* Regression result location
cap mkdir "${s2_result}"

* Loop over each group
local group_list down1 down2 down3 down4


foreach group of local group_list {
    


    use "$stata_data/stage2_`group'.dta", clear


    * Set id
    encode id,      gen(id_code)
    encode fake_id, gen(fake_id_code)

    * Drop financial industry samples
    drop if substr(industrycoded, 1, 1) == "J"

    * Industry * time fixed effects
    gen  ind_sector = substr(industrycoded, 1, 1)
    egen ind_time   = group(ind_sector yq)


    * Winsorize
    winsor2 top_hold_share total_income_q_yoy total_income_q_yoy_asset total_income_ihs_d, cuts(1 99) replace


    * Generate dummy variables: multi-category level controls
    tab debt_level,  gen(d_debt)
    tab cash_level,  gen(d_cash)
    tab asset_level, gen(d_asset)


    * Control group variable
    gen never = 0
    replace never = 1 if treated ==0
	tab treated never,missing
    

    * Define global variables
    global con_var  major_change top_hold_share i.debt_level i.cash_level i.asset_level
    global fixed_var fake_id_code ind_time 
    global did D_12 D_11 D_10 D_9 D_8 D_7 D_6 D_5 D_4 D_3 D_2 D0 D1 D2 D3 D4 D5 D6 D7 D8 D_1



    eventstudyinteract up_break $did , cohort(exp_start) control_cohort(never) covariates($con_var)  absorb($fixed_var) vce(cluster id_code)
    estimates store up_break_raw

    matrix b_iw = e(b_iw)
    matrix V_iw = e(V_iw)
    erepost b=b_iw V=V_iw
    estimates store group_iw_up_break



    cap mkdir "${s2_result}/`group'"
	local estlist group_iw_up_break

    foreach est of local estlist {
        estimates restore `est'
        parmest, norestore level(90)
		
        save "${s2_result}/`group'/`est'.dta", replace
    }

}