**Haiwen Yan** College of Public Finance and Investment, Shanghai University of Finance and Economics  
**Jiaojiao Yang** College of Public Finance and Investment, Shanghai University of Finance and Economics  

---

# Overview

This repository integrates **Python** and **Stata** code for:

- Raw data processing
- Production-network construction
- Panel-data compilation
- Empirical analysis
- Figure generation
- Table production

---

# Repository Structure

```text
.
├── README.md
├── code_files/
│   ├── project_directory.py
│   ├── py_code/
│   │   ├── data_processing/
│   │   ├── expose/
│   │   ├── panel_compile/
│   │   ├── plot/
│   │   └── tabulation/
│   └── do_code/
└── raw_data/
    ├── bis_report/
    ├── csmar/
    │   ├── balance_sheet/
    │   ├── basic_info/
    │   ├── income_sheet/
    │   ├── major_change/
    │   ├── patent/
    │   └── top10_holder/
    ├── factset/
    ├── opensanction/
    └── sanction_list/
```

---

# Folder and File Description

## `README.md`
This file provides an overview of the repository structure, data sources, software requirements, and replication procedures.

## `code_files/`
This folder contains all scripts used in the replication, including both Python and Stata code.

### `project_directory.py`
This script initializes the replication environment. Specifically, it:

- generates `py_config.py` for managing relative paths across Python scripts;
- updates path settings in all Stata `.do` files; and
- generates `run_all.py` for one-click execution of the full replication workflow.

### `py_code/`
This folder contains all Python scripts used in the project.

- **`data_processing/`**  
  Scripts for cleaning, standardizing, and preprocessing raw data from multiple sources.

- **`expose/`**  
  Scripts for constructing the production network using `networkx` and identifying upstream and downstream firms connected to sanctioned firms.

- **`panel_compile/`**  
  Scripts for merging processed datasets and compiling the final panel dataset used in the empirical analysis.

- **`plot/`**  
  Scripts for producing figures for the paper and appendix. File names generally correspond to figure numbering in the manuscript.

- **`tabulation/`**  
  Scripts for generating summary statistics tables, regression tables, and other output tables. File names generally correspond to table numbering in the manuscript.

### `do_code/`
This folder contains all Stata `.do` files used to generate the empirical results reported in the paper.

## `raw_data/`
This folder stores all raw input data used in the project. These files should remain in their original form and should **not** be modified manually.

- **`bis_report/`**  
  Data on China-related approval rates compiled from the annual country licensing and trade analysis reports published by the U.S. Bureau of Industry and Security (BIS).

- **`csmar/`**  
  Raw firm-level and financial data obtained from the CSMAR database.

- **`factset/`**  
  Raw firm-level business relationship data obtained from FactSet.

- **`opensanction/`**  
  `entities.ftm.json` files from both the *Consolidated Sanctions* dataset and the *OpenSanctions Default* dataset.

- **`sanction_list/`**  
  The list of sanctioned Chinese listed firms used in this project.

---

# Software Requirements

Replication requires only **Python** and **Stata**.

## Python

The Python code was tested with **Python 3.13.5** using **conda** on **macOS**.

In addition to common packages for data processing and scientific computing, the replication also requires:

- `networkx`
- `igraph`
- `matplotlib-venn`
- `venn`
- `stata_setup`

## Stata

The Stata code requires Stata 17 or later and several user-written packages used by commands such as `reghdfe`, `stackedev`, and other DID-related procedures called in the `.do` files.

---

# Replication Instructions

## Step 1. Initialize the project structure

Run `project_directory.py` first. In that script, fill in the following parameters:

- **`project_location`**: the root folder where the replication project will be stored
- **`stata_location`**: the location of the Stata executable used by `run_all.py`
- **`stata_version`**: the version of Stata installed on your machine

After running `project_directory.py`, the following working structure will be created:

```text
project_location/
├── README.md
├── code_files/
│   ├── project_directory.py
│   ├── run_all.py
│   ├── py_code/
│   │   ├── py_config.py
│   │   ├── data_processing/
│   │   ├── expose/
│   │   ├── panel_compile/
│   │   ├── plot/
│   │   └── tabulation/
│   └── do_code/
├── data/
│   ├── raw_data/
│   ├── processing/
│   ├── dta/
│   └── result/
│       ├── s1/
│       ├── s2/
│       └── s3_further/
├── figures/
└── tables/
```

> **Note**  
> The structure shown above is the working directory created after initialization. It is slightly different from the repository layout shown at the beginning of this README.

## Step 2. Run the scripts

After initialization, run the scripts in the following order:

1. `py_code/data_processing/`
2. `py_code/expose/`
3. `py_code/panel_compile/`
4. `do_code/`
5. `py_code/plot/`
6. `py_code/tabulation/`

Within each folder, you may either:

- run the scripts sequentially based on their file names; or
- run the corresponding `master` script, which executes all scripts in that folder in order.

## Recommended option

The recommended approach is to run:

```python
project_directory.py
run_all.py
```

This script executes the master scripts across all folders in the correct order.

---

# Data Availability

Some core datasets used in this project—especially those in `csmar/` and `factset/`—are proprietary commercial datasets and therefore cannot be distributed as part of this replication package.

After obtaining these datasets through the appropriate commercial channels, users only need to place the extracted raw files into the corresponding `raw_data/` subfolders. No additional manual preprocessing is required before running the replication code.

OpenSanctions data can be obtained from the official OpenSanctions website, subject to its terms of use.

---

# Replication Notes

- Please keep all raw data files in their original format.
- Do not manually rename intermediate folders generated by the scripts.
