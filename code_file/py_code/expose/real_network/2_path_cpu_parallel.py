#%% ---------------------------------------------------------------------------------------
# ------------------------Import modules----------------------------------------------
# ----------------------------------------------------------------------------------------
import os
import re
import json
import pickle
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
import numpy as np
import networkx as nx
from tqdm import tqdm

from code_file.py_code.py_config import processing_data



#%% ---------------------------------------------------------------------------------------
# ------------------------Globals: for multiprocessing workers--------------------------------
# ----------------------------------------------------------------------------------------
_PD_LOC = None
_SAN_BY_YQ = None
_PANEL_SET = None
_MAX_DEPTH = None

_PD_LOC2 = None


def _init_stage1(processing_data_loc, sanctions_by_yq, panel_ids, max_depth):
    """stage1: initialize worker global variables (to avoid repeatedly pickling large objects for each task)"""
    global _PD_LOC, _SAN_BY_YQ, _PANEL_SET, _MAX_DEPTH
    _PD_LOC = processing_data_loc
    _SAN_BY_YQ = sanctions_by_yq
    _PANEL_SET = set(panel_ids)
    _MAX_DEPTH = int(max_depth)


def _stage1_quarter(yq):
    """
    For a single quarter:
      - read graph G_yq
      - find sanctioned nodes in the current period (and present in the graph)
      - for each sanctioned node, find upstream and downstream nodes with cutoff=_MAX_DEPTH
      - keep only nodes in panel_set
    Returns:
      up_rows   : (yq, san_node, other_id, dist)  other_id=upstream node
      down_rows : (yq, san_node, other_id, dist)  other_id=downstream node
    """
    # Whether there are sanction events in the current period
    san_list = _SAN_BY_YQ.get(yq, None)
    if not san_list:
        return [], []

    g_path = os.path.join(_PD_LOC, "network_plot", f"G_{yq}.pkl")
    with open(g_path, "rb") as f:
        G = pickle.load(f)
    Grev = G.reverse(copy=False)

    up_rows = []
    down_rows = []

    for target_id in san_list:
        if target_id not in G:
            continue

        # Downstream (along the original graph direction)
        down_dist = nx.single_source_shortest_path_length(G, target_id, cutoff=_MAX_DEPTH)
        # Upstream (along the reversed graph direction)
        up_dist = nx.single_source_shortest_path_length(Grev, target_id, cutoff=_MAX_DEPTH)

        down_dist.pop(target_id, None)
        up_dist.pop(target_id, None)

        # Keep only panel_set
        for node, dist in down_dist.items():
            if node in _PANEL_SET:
                down_rows.append((yq, target_id, node, dist))

        for node, dist in up_dist.items():
            if node in _PANEL_SET:
                up_rows.append((yq, target_id, node, dist))

    return up_rows, down_rows


def _init_stage2(processing_data_loc):
    """stage2: only processing_data_loc is needed"""
    global _PD_LOC2
    _PD_LOC2 = processing_data_loc


def _stage2_quarter(args):
    """
    args = (yq, pairs)
    pairs: [(idx, up_node, down_node), ...]
    Returns: [(idx, packed_paths_json), ...]
    """
    yq, pairs = args
    if not pairs:
        return []

    g_path = os.path.join(_PD_LOC2, "network_plot", f"G_{yq}.pkl")
    with open(g_path, "rb") as f:
        G = pickle.load(f)

    out = []
    for idx, up_node, down_node in pairs:
        try:
            named_paths = [list(p) for p in nx.all_shortest_paths(G, source=up_node, target=down_node)]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            named_paths = []
        out.append((idx, json.dumps(named_paths, ensure_ascii=False)))
    return out




#%% ---------------------------------------------------------------------------------------
# ------------------------Main workflow----------------------------------------------
# ----------------------------------------------------------------------------------------
def main(n_jobs=None, max_depth=8):
    # macOS: use spawn; must run under __main__ (see the end of the file)
    if n_jobs is None:
        n_jobs = os.cpu_count() or 1
    n_jobs = max(1, int(n_jobs))

    #%% get the location
    processing_data_loc = processing_data()

    #%% Load data
    sanction_df = pd.read_parquet(f"{processing_data_loc}/sanction_info.parquet")
    id_map = pd.read_parquet(f"{processing_data_loc}/id_map.parquet")

    # Sample period
    SAMPLE_PERIOD_START = 2015 * 4 + 1
    SAMPLE_PERIOD_END = 2025 * 4 + 3

    #%% Process sanction data: organize events
    sanction_df = sanction_df[sanction_df["san_date"].notna()][["id", "san_date"]].copy()
    sanction_df["san_yq"] = (sanction_df["san_date"].dt.year) * 4 + (sanction_df["san_date"].dt.quarter)
    sanction_df = (
        sanction_df.drop(columns="san_date")
        .drop_duplicates()
        .sort_values(["id", "san_yq"])
        .reset_index(drop=True)
    )

    # Package the list of sanctioned firms by quarter (for workers)
    sanctions_by_yq = sanction_df.groupby("san_yq")["id"].apply(list).to_dict()

    # Panel firm set (for workers)
    panel_ids = list(set(id_map[id_map['panel']==1]['id'].unique()))

    # Quarter sequence to run: equivalent to your original range(SAMPLE_PERIOD_START-1, SAMPLE_PERIOD_END+1+1)
    yqs = list(range(SAMPLE_PERIOD_START - 1, SAMPLE_PERIOD_END + 2))

    #%% -----------------------------------------------------------------------------------
    # ------------------------Stage 1: parallel computation of upstream/downstream exposure---------------------------------
    # -----------------------------------------------------------------------------------
    up_all = []
    down_all = []

    ctx = mp.get_context("spawn")  # macOS-friendly
    with ProcessPoolExecutor(
        max_workers=n_jobs,
        mp_context=ctx,
        initializer=_init_stage1,
        initargs=(processing_data_loc, sanctions_by_yq, panel_ids, max_depth),
    ) as ex:
        futs = {ex.submit(_stage1_quarter, yq): yq for yq in yqs}

        for fut in tqdm(as_completed(futs), total=len(futs), desc="Quarter (exposure)"):
            yq = futs[fut]
            try:
                up_rows, down_rows = fut.result()
            except Exception as e:
                raise RuntimeError(f"Stage1 failed at yq={yq}") from e

            if up_rows:
                up_all.extend(up_rows)
            if down_rows:
                down_all.extend(down_rows)

    # Convert results to DataFrame (same as your original structure)
    up_df = pd.DataFrame(up_all, columns=["yq", "san_node", "id", "dist"])
    down_df = pd.DataFrame(down_all, columns=["yq", "san_node", "id", "dist"])

    up_df["up_node"] = up_df["id"]
    up_df["down_node"] = up_df["san_node"]
    up_df = up_df.drop(columns="id")

    down_df["down_node"] = down_df["id"]
    down_df["up_node"] = down_df["san_node"]
    down_df = down_df.drop(columns="id")

    expose_df = (
        pd.concat([up_df, down_df], axis=0, ignore_index=True)
        .sort_values(["yq", "san_node", "dist", "up_node", "down_node"])
        .reset_index(drop=True)
    )

    #%% -----------------------------------------------------------------------------------
    # ------------------------Stage 2: parallel computation of shortest path sets---------------------------------
    # -----------------------------------------------------------------------------------
    expose_df["paths"] = None

    # Package (idx, up_node, down_node) for each quarter
    tasks = []
    for yq in yqs:
        effect = expose_df.loc[expose_df["yq"] == yq, ["up_node", "down_node"]]
        if effect.empty:
            continue
        pairs = [(row.Index, row.up_node, row.down_node) for row in effect.itertuples()]
        tasks.append((yq, pairs))

    with ProcessPoolExecutor(
        max_workers=n_jobs,
        mp_context=ctx,
        initializer=_init_stage2,
        initargs=(processing_data_loc,),
    ) as ex:
        futs = {ex.submit(_stage2_quarter, t): t[0] for t in tasks}

        for fut in tqdm(as_completed(futs), total=len(futs), desc="Quarter (paths)"):
            yq = futs[fut]
            try:
                out = fut.result()  # [(idx, packed_json), ...]
            except Exception as e:
                raise RuntimeError(f"Stage2 failed at yq={yq}") from e

            if out:
                idxs, packed = zip(*out)
                expose_df.loc[list(idxs), "paths"] = list(packed)

    #%% -----------------------------------------------------------------------------------
    # ------------------------Save data-----------------------------------------------------
    # -----------------------------------------------------------------------------------
    expose_df.to_parquet(f"{processing_data_loc}/expose_path.parquet", index=False)





#%% ---------------------------------------------------------------------------------------
# ------------------------Entry point: macOS multiprocessing must be written this way----------------------------
# ---------------------------------------------------------------------------------------
if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    # Specify number of cores:
    N_JOBS = 8  
    MAX_DEPTH = 8

    main(n_jobs=N_JOBS, max_depth=MAX_DEPTH)