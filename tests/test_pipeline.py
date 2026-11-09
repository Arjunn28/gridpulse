"""Pipeline checks against the frozen snapshot. Run from anywhere: pytest -q

The notebook cells are executed as they are (no copy of the logic here), so these tests fail if a loading
or feature cell drifts away from the Oct 30, 2026 reference run.
"""
import hashlib
import json
import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO / "notebooks" / "GridPulse.ipynb"
SNAP = REPO / "data" / "snapshot"


def cell_with(marker):
    cells = json.loads(NOTEBOOK.read_text())["cells"]
    hits = [("".join(c["source"])) for c in cells if c["cell_type"] == "code" and marker in "".join(c["source"])]
    assert len(hits) == 1, f"{marker!r} matched {len(hits)} cells"
    return hits[0]


@pytest.fixture(scope="module")
def nb(tmp_path_factory):
    """Run setup, EIA, weather, zone weights, merge and feature cells in one namespace."""
    os.chdir(REPO)
    ns = {"__name__": "gridpulse_test"}
    exec(cell_with("IN_COLAB = "), ns)
    ns["OUT"] = str(tmp_path_factory.mktemp("processed"))      # keep test output out of data/processed
    for marker in ("def canon(d):", "ZONE_COORDS = {", "SUBREGION_", "INSTANT   = [", "def build_features("):
        exec(cell_with(marker), ns)
    # X_COLS is defined at the top of the baseline-models cell, before any model is fitted
    exec(cell_with("X_COLS = [c for c in feat.columns").split("d = feat.dropna")[0], ns)
    return ns


def test_checksums_match():
    lines = (SNAP / "SHA256SUMS").read_text().strip().splitlines()
    assert len(lines) == 40
    for line in lines:
        digest, name = line.split("  ", 1)
        assert hashlib.sha256((SNAP / name).read_bytes()).hexdigest() == digest, name


def test_hourly_rows_after_cutoff(nb):
    df = nb["df"]
    assert len(df) == 67631
    assert str(df["ts"].min()) == "2019-01-01 07:00:00+00:00"
    assert str(df["ts"].max()) == "2026-09-19 05:00:00+00:00"


def test_net_load_nulls(nb):
    assert nb["df"]["net_load"].isna().sum() == 48


def test_solar_and_radiation_peak_at_hour_14(nb):
    g = nb["m"].groupby("hr_ct")
    assert g["solar"].mean().idxmax() == 14
    assert g["shortwave_radiation_SCEN"].mean().idxmax() == 14


def test_lag0_correlation(nb):
    m = nb["m"]
    t = m[m["ts"].dt.year == 2025].dropna(subset=["solar", "shortwave_radiation_SCEN"])
    assert round(t["solar"].corr(t["shortwave_radiation_SCEN"]), 4) == 0.9202


def test_feature_list(nb):
    x = nb["X_COLS"]
    assert len(x) == 39
    banned = set(nb["GEN"]) | {"demand_fcst", "net_load"}
    assert not banned & set(x)
