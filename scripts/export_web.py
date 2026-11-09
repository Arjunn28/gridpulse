"""Write docs/data/*.json for the three interactive charts on the project page.

The numbers come from the notebook's own cells, run on data/snapshot/ in notebook order, so the page
shows what the notebook shows. Each cell that prints a table is also compared, character for character,
with the output stored in the notebook, and the script stops if anything differs.

Run from the repo root: python scripts/export_web.py
"""
import contextlib
import io
import json
import os
import re
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ["MPLBACKEND"] = "Agg"          # the chart cells are run, but nothing is drawn on screen

REPO = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO / "notebooks" / "GridPulse.ipynb"
OUT_DIR = REPO / "docs" / "data"
os.chdir(REPO)

CELLS = json.loads(NOTEBOOK.read_text())["cells"]


def find(marker):
    hits = [c for c in CELLS if c["cell_type"] == "code" and marker in "".join(c["source"])]
    assert len(hits) == 1, f"{marker!r} matched {len(hits)} cells"
    return hits[0]


def stored_text(cell):
    return "".join("".join(o["text"]) for o in cell.get("outputs", []) if o["output_type"] == "stream")


ns = {"__name__": "export_web"}
printed = {}                                # marker -> (text printed now, text stored in the notebook)


def run(marker, compare=False):
    cell = find(marker)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec("".join(cell["source"]), ns)
    if compare:
        printed[marker] = (buf.getvalue(), stored_text(cell))


# the notebook, in order, from the setup cell to the 8k zone tables
run("IN_COLAB = ")
ns["OUT"] = tempfile.mkdtemp()              # keep the parquet files out of data/processed
for marker in ("chart style, used by every figure", "def canon(d):", "ZONE_COORDS = {", "SUBREGION_",
               "INSTANT   = [", "def build_features(", "X_COLS = [c for c in feat.columns"):
    run(marker)
run("8c. Where does the net load error come from?", compare=True)
run("8d. Same analysis, demand as target", compare=True)
run('for tgt in ["wind_gen", "solar"]:\n    dd = feat', compare=True)
run("print(f\"{'fold':<5}{'solar_MW':>10}", compare=True)
run("WX_ONLY = [c for c in X_COLS", compare=True)
run("def fold_nmae(df, cols, target):")
run("8h. Weather response by year", compare=True)
run("8j. How sure are we?", compare=True)
run("8k. Which zones stopped following the weather?", compare=True)

mismatch = [m for m, (now, old) in printed.items() if now != old]
assert not mismatch, f"printed output differs from the notebook for: {mismatch}"
print(f"checked {len(printed)} cells: printed output identical to the notebook's stored output")

import pandas as pd

r = lambda x, n=4: round(float(x), n)

# ---- 08f: error by fold, and the solar fleet
test_end = ns["test_end"]
error_by_fold = {
    "test_end": test_end,
    "lines": {name: [r(x) for x in v[0]] for name, v in ns["lines"].items()},
    "solar": {"mean_mw": [r(x, 1) for x in ns["smean"]], "mae_mw": [r(x, 1) for x in ns["smae"]]},
}

# ---- 08j: cooling response per year with the block bootstrap interval
ci, early, late = ns["ci"], [2019, 2020, 2021], [2023, 2024, 2025]
cooling = {
    "years": [int(y) for y in ci.index],
    "cool_pct_per_c": [r(x) for x in ci["cool_pct_per_C"]],
    "ci_low": [r(x) for x in ci["ci_low"]],
    "ci_high": [r(x) for x in ci["ci_high"]],
    "late_minus_early": {"point": r(ns["point"]), "ci_low": r(ns["lo"]), "ci_high": r(ns["hi"])},
}

# ---- 08k: zone by year tables
names = {"COAS": "Coast", "EAST": "East", "FWES": "Far West", "NRTH": "North", "NCEN": "North Central",
         "SOUT": "South", "SCEN": "South Central", "WEST": "West"}
zones = list(ns["ZONES"])
tables = {key: pd.DataFrame(ns[key]).T for key in ("R2", "COOL", "FLAT")}
years = [int(y) for y in tables["R2"].columns]
zone_heatmaps = {
    "zones": zones, "zone_names": [names[z] for z in zones], "years": years,
    "r2": [[r(v) for v in row] for row in tables["R2"].loc[zones].values],
    "cooling_pct_per_c": [[r(v) for v in row] for row in tables["COOL"].loc[zones].values],
    "min_max_ratio": [[r(v) for v in row] for row in tables["FLAT"].loc[zones].values],
}

# ---- the chart values must agree with the tables the notebook printed (same rounding as the print)
d8c, d8d, d51 = (printed[m][0] for m in ("8c. Where does the net load error come from?",
                                          "8d. Same analysis, demand as target",
                                          "WX_ONLY = [c for c in X_COLS"))
nl_print = [float(x) for x in re.findall(r"^\d\s+\S+\s+\S+\s+[\d,]+\s+-?[\d,]+\s+([\d.]+)%", d8c, re.M)]
dm_print = [float(x) for x in re.findall(r"^\d\s+\S+\s+[\d,]+\s+-?[\d,]+\s+([\d.]+)%", d8d, re.M)]
wx_print = [float(x) for x in re.findall(r"nMAE\s+([\d.]+)%", d51)]
sol_rows = [l.split() for l in printed["print(f\"{'fold':<5}{'solar_MW':>10}"][0].splitlines()[1:]]
sol_mean_print = [float(x[1].replace(",", "")) for x in sol_rows]
sol_mae_print = [float(x[2].replace(",", "")) for x in sol_rows]

L = error_by_fold["lines"]
assert [round(x, 1) for x in L["demand, full model"]] == dm_print
assert [round(x, 1) for x in L["net load, full model"]] == nl_print
assert [round(x, 1) for x in L["demand, weather + calendar only"]] == wx_print
assert [round(x) for x in error_by_fold["solar"]["mean_mw"]] == sol_mean_print
assert [round(x) for x in error_by_fold["solar"]["mae_mw"]] == sol_mae_print
assert [round(x, 2) for row in zone_heatmaps["r2"] for x in row] == \
       [round(x, 2) for row in tables["R2"].loc[zones].values for x in row]
print("checked the exported chart values against the printed tables: they match")

OUT_DIR.mkdir(parents=True, exist_ok=True)
for name, obj in [("error_by_fold", error_by_fold), ("cooling_response", cooling), ("zone_heatmaps", zone_heatmaps)]:
    (OUT_DIR / f"{name}.json").write_text(json.dumps(obj, indent=1) + "\n")
    print("wrote", f"docs/data/{name}.json")
