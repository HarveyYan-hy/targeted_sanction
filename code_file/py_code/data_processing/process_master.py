from pathlib import Path
import subprocess
import sys
import os
import time


# Directory where 0_master.py is located
SCRIPT_DIR = Path(__file__).resolve().parent

# Project root directory
# Current structure: project_root / code_file / py_code / data_processing / 0_master.py
PROJECT_ROOT = SCRIPT_DIR.parents[2]

scripts = [
    "1_id_map.py",
    "2_balance_sheet.py",
    "3_income_sheet.py",
    "4_major_change.py",
    "5_basic_info.py",
    "6_top_holders.py",
    "7_patent.py",
    "8_sanction_info.py",
    "9_factset_rel.py",
    "10_quarter_network.py",
    "11_eigvec.py",
    "12_cn_rate.py",
    "13_rel_change.py",
    "14_basic_panel.py",
    "15_heterogeneity.py",
]

# Allow child scripts to import modules from the project root
env = os.environ.copy()
old_pythonpath = env.get("PYTHONPATH", "")
env["PYTHONPATH"] = (
    str(PROJECT_ROOT) if not old_pythonpath
    else str(PROJECT_ROOT) + os.pathsep + old_pythonpath
)


def format_seconds(seconds):
    """Convert seconds to a readable string."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours >= 1:
        return f"{int(hours)}h {int(minutes)}m {secs:.2f}s"
    if minutes >= 1:
        return f"{int(minutes)}m {secs:.2f}s"
    return f"{secs:.2f}s"


script_times = {}
master_start = time.perf_counter()

for script in scripts:
    script_path = SCRIPT_DIR / script

    print(f"Script path : {script_path}")

    script_start = time.perf_counter()

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True
    )

    script_end = time.perf_counter()
    elapsed = script_end - script_start
    script_times[script] = elapsed

    if result.returncode != 0:
        print(f"\nError in {script}:")
        print(result.stderr)
        print(f"Elapsed time before failure: {format_seconds(elapsed)}")
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd=result.args
        )

master_end = time.perf_counter()
total_time = master_end - master_start

longest_script = max(script_times, key=script_times.get)
longest_time = script_times[longest_script]

print("\nAll scripts finished successfully.")
print(f"Total running time: {format_seconds(total_time)}")
print(f"Longest-running script: {longest_script}")
print(f"Time used by longest-running script: {format_seconds(longest_time)}")