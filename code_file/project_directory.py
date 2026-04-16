#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import os
import re
from pathlib import Path








#%% ---------------------------------------------------------------------------------------
# ------------------------Set Location----------------------------------------------
# ----------------------------------------------------------------------------------------
project_location = '/your/project/directory'
stata_location = "/Applications/Stata"
stata_version = 'se'






#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
# l1 folder
code_dir = os.path.join(project_location, "code_file")
code_dir = '/Volumes/T7/phd/research/sanction_publication/code_file'
figures_dir = os.path.join(project_location, "figures")
tables_dir = os.path.join(project_location, "tables")
data_dir = os.path.join(project_location, "data")


# sub-data
dta_dir = os.path.join(data_dir, "dta")
raw_data_dir = os.path.join(data_dir, "raw_data")
processing_dir = os.path.join(data_dir, "processing")
result_dir = os.path.join(data_dir, "result")


# sub-result
s1_dir = os.path.join(result_dir, "s1")
s2_dir = os.path.join(result_dir, "s2")
s3_dir = os.path.join(result_dir, "s3")


# create folders
dirs_to_create = [
    figures_dir,
    tables_dir,
    data_dir,
    dta_dir,
    raw_data_dir,
    processing_dir,
    s1_dir,
    s2_dir,
    s3_dir,
]
for d in dirs_to_create:
    os.makedirs(d, exist_ok=True)

print("The directory structure has been created successfully")







#%% ---------------------------------------------------------------------------------------
# ------------------------Create py_config.py----------------------------------------------
# ----------------------------------------------------------------------------------------
py_config_path = os.path.join(code_dir, "py_code", "py_config.py")

with open(py_config_path, "w", encoding="utf-8") as f:
    f.write("# Auto-generated path configuration file\n")
    f.write("import os\n\n")


    f.write(f'project_root = r"{project_location}"\n')
    f.write(f'codes_dir = r"{code_dir}"\n')
    f.write(f'figures_dir = r"{figures_dir}"\n')
    f.write(f'tables_dir = r"{tables_dir}"\n')
    f.write(f'data_dir = r"{data_dir}"\n')
    f.write(f'dta_dir = r"{dta_dir}"\n')
    f.write(f'raw_data_dir = r"{raw_data_dir}"\n')
    f.write(f'processing_dir = r"{processing_dir}"\n')
    f.write(f'result_dir = r"{result_dir}"\n')
    f.write(f's1_dir = r"{s1_dir}"\n')
    f.write(f's2_dir = r"{s2_dir}"\n')
    f.write(f's3_dir = r"{s3_dir}"\n\n')

    # path dict
    f.write("paths = {\n")
    f.write('    "project_root": project_root,\n')
    f.write('    "codes_dir": codes_dir,\n')
    f.write('    "figures_dir": figures_dir,\n')
    f.write('    "tables_dir": tables_dir,\n')
    f.write('    "data_dir": data_dir,\n')
    f.write('    "dta_dir": dta_dir,\n')
    f.write('    "raw_data_dir": raw_data_dir,\n')
    f.write('    "processing_dir": processing_dir,\n')
    f.write('    "result_dir": result_dir,\n')
    f.write('    "s1_dir": s1_dir,\n')
    f.write('    "s2_dir": s2_dir,\n')
    f.write('    "s3_dir": s3_dir,\n')
    f.write("}\n\n")

    # define function
    f.write("def raw_data():\n")
    f.write('    return paths.get("raw_data_dir", "")\n\n')

    f.write("def stata_data():\n")
    f.write('    return paths.get("dta_dir", "")\n\n')

    f.write("def processing_data():\n")
    f.write('    return paths.get("processing_dir", "")\n\n')

    f.write("def figures_loc():\n")
    f.write('    return paths.get("figures_dir", "")\n\n')

    f.write("def tables_loc():\n")
    f.write('    return paths.get("tables_dir", "")\n\n')

    f.write("def s1_result():\n")
    f.write('    return paths.get("s1_dir", "")\n\n')

    f.write("def s2_result():\n")
    f.write('    return paths.get("s2_dir", "")\n\n')

    f.write("def s3_result():\n")
    f.write('    return paths.get("s3_dir", "")\n\n')

print(f"py_config.py has been created successfully: {py_config_path}")






#%% ---------------------------------------------------------------------------------------
# ------------------------stata global location----------------------------------------------
# ----------------------------------------------------------------------------------------
do_code_path = os.path.join(code_dir, "do_code")

# global command
new_block = (
    "* location-start\n"
    f'global stata_data "{dta_dir}"\n'
    f'global s1_result "{s1_dir}"\n'
    f'global s2_result "{s2_dir}"\n'
    f'global s3_result "{s3_dir}"\n'
    f'global figures_loc "{figures_dir}"\n'
    f'global tables_loc "{tables_dir}"\n'
    f'global code_loc "{code_dir}"\n'
    "* location-end"
)


pattern = re.compile(
    r"^\* location-start\s*$.*?^\* location-end\s*$",
    re.DOTALL | re.MULTILINE
)

for do_file in Path(do_code_path).glob("*.do"):
    with open(do_file, "r", encoding="utf-8") as f:
        content = f.read()

    if not re.search(r"^\* location-start\s*$", content, re.MULTILINE):
        print(f"Skip {do_file.name}: do not find * location-start")
        continue

    if not re.search(r"^\* location-end\s*$", content, re.MULTILINE):
        print(f"Skip {do_file.name}: do not find * location-end")
        continue

    new_content, n_replaced = pattern.subn(new_block, content, count=1)
    print("replace obsoleting global")

    if n_replaced == 0:
        print(f"Skip {do_file.name}: do not replace location block")
        continue

    with open(do_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated: {do_file.name}")









#%% ---------------------------------------------------------------------------------------
# ------------------------Create run_all.py----------------------------------------------
# ----------------------------------------------------------------------------------------
current_script_dir = Path(__file__).resolve().parent
run_all_path = current_script_dir / "run_all.py"

run_all_content = f'''
import os
import sys
import subprocess
from pathlib import Path


# ----------------------------------------------------------------------------------------
# Set location
# ----------------------------------------------------------------------------------------
project_location = r"{project_location}"
stata_location = r"{stata_location}"
stata_version = r"{stata_version}"


# ----------------------------------------------------------------------------------------
# Master files (edit file names here if needed)
# ----------------------------------------------------------------------------------------
python_masters_before_stata = [
    ("py_code/data_processing", "process_master.py"),
    ("py_code/expose", "expose_master.py"),
    ("py_code/panel_compile", "compile_master.py"),
]

stata_master = ("do_code", "do_master.do")

python_masters_after_stata = [
    ("py_code/plot", "plot_master.py"),
    ("py_code/tabulation", "tabulation_master.py"),
]


# ----------------------------------------------------------------------------------------
# Derived paths
# ----------------------------------------------------------------------------------------
project_root = Path(project_location)
code_dir = project_root / "code_file"

env = os.environ.copy()
old_pythonpath = env.get("PYTHONPATH", "")
env["PYTHONPATH"] = (
    str(project_root)
    if not old_pythonpath
    else str(project_root) + os.pathsep + old_pythonpath
)


def run_python_script(script_path: Path):
    print(f"\\n[Python] Running: {{script_path}}")

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(script_path.parent),
        env=env,
        check=True
    )

    print(f"[Python] Finished: {{script_path.name}}")


def run_stata_do(do_path: Path):
    print(f"\\n[Stata] Running: {{do_path}}")

    try:
        import stata_setup
        stata_setup.config(stata_location, stata_version)
        from pystata import stata
    except Exception as e:
        raise RuntimeError(
            "Failed to initialize pystata. Please check:\\n"
            "1. pystata/stata_setup is installed in this Python environment\\n"
            "2. stata_location is correct\\n"
            "3. stata_version is one of mp / se / be\\n"
            f"Original error: {{e}}"
        )

    do_path_str = str(do_path.resolve()).replace("\\\\", "/")
    stata.run(f'do "{{do_path_str}}"', quietly=False)

    print(f"[Stata] Finished: {{do_path.name}}")


def main():
    # 1. Python masters before Stata
    for rel_folder, file_name in python_masters_before_stata:
        script_path = code_dir / rel_folder / file_name
        if not script_path.exists():
            raise FileNotFoundError(f"Python master file not found: {{script_path}}")
        run_python_script(script_path)

    # 2. Stata master
    stata_folder, stata_file = stata_master
    do_path = code_dir / stata_folder / stata_file
    if not do_path.exists():
        raise FileNotFoundError(f"Stata do file not found: {{do_path}}")
    run_stata_do(do_path)

    # 3. Python masters after Stata
    for rel_folder, file_name in python_masters_after_stata:
        script_path = code_dir / rel_folder / file_name
        if not script_path.exists():
            raise FileNotFoundError(f"Python master file not found: {{script_path}}")
        run_python_script(script_path)

    print("\\nAll tasks finished successfully.")


if __name__ == "__main__":
    main()
'''

with open(run_all_path, "w", encoding="utf-8") as f:
    f.write(run_all_content)

print(f"run_all.py has been created successfully: {{run_all_path}}")