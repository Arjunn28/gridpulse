"""Compare an executed notebook with the Oct 30, 2026 reference numbers.

Usage: python scripts/check_results.py [build/GridPulse.executed.ipynb]
Exit code 0 if every number matches to the printed precision, 1 otherwise.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "build" / "GridPulse.executed.ipynb"
cells = json.loads(path.read_text())["cells"]


def output_of(marker):
    """Printed text of the one code cell whose source contains marker."""
    hits = [c for c in cells if c["cell_type"] == "code" and marker in "".join(c["source"])]
    assert len(hits) == 1, f"{marker!r} matched {len(hits)} cells"
    return "".join("".join(o["text"]) for o in hits[0].get("outputs", []) if o["output_type"] == "stream")


def one(text, pattern, group=1):
    m = re.search(pattern, text, re.M)
    return m.group(group) if m else None


def many(text, pattern):
    return re.findall(pattern, text, re.M)


def row(text, label, col):
    """Whitespace-split column `col` of the first line that starts with `label`."""
    for line in text.splitlines():
        if line.split()[:1] == [label]:
            return line.split()[col]
    return None


def table_row(text, after, label, col):
    """Same as row(), but only looks after the heading `after`."""
    return row(text[text.index(after):], label, col)


checks = []   # (name, expected, found)


def check(name, expected, found):
    checks.append((name, expected, found))


a = output_of("X_COLS = [c for c in feat.columns")
check("modelling rows", "66,438", one(a, r"modelling rows: ([\d,]+)"))
check("features", "39", one(a, r"features: (\d+)"))
check("net load persistence MAE (MW)", "5,059", one(a, r"persistence\s+MAE\s+([\d,]+) MW"))
check("net load OLS MAE (MW)", "4093.72", row(a, "OLS", 1))
check("net load Ridge MAE (MW)", "4100.81", row(a, "Ridge", 1))
check("net load Lasso MAE (MW)", "4141.21", row(a, "Lasso", 1))

b = output_of("random k-fold vs rolling-origin")
check("random k-fold MAE (MW)", "3,550", one(b, r"random k-fold  MAE :\s+([\d,]+) MW"))
check("rolling-origin MAE (MW)", "4,101", one(b, r"rolling-origin MAE :\s+([\d,]+) MW"))
check("optimism", "15.5%", one(b, r"optimism\s+:\s+([\d.]+%)"))

c = output_of("8d. Same analysis, demand as target")
check("demand Ridge nMAE by fold", "3.2 3.5 3.4 3.0 2.8",
      " ".join(many(c, r"^\d\s+\S+\s+[\d,]+\s+-?[\d,]+\s+([\d.]+)%")))

d = output_of("WX_ONLY = [c for c in X_COLS")
check("weather + calendar only, by fold", "6.9 9.2 11.6 13.2 13.5", " ".join(many(d, r"nMAE\s+([\d.]+)%")))

e = output_of("8g. Is the missing piece")
line = next((l for l in e.splitlines() if l.startswith("weather+calendar+baseload")), "")
check("+ baseload, by fold", "5.2 5.2 5.2 4.3 4.4", " ".join(many(line, r"([\d.]+)% \(")))

f = output_of("8h. Weather response by year")
check("cooling response 2019 (% per C)", "5.83", row(f, "2019", 4))
check("cooling response 2025 (% per C)", "4.61", row(f, "2025", 4))

h = output_of("8j. How sure are we")
m = re.search(r"late minus early, cool %/C: (-?[\d.]+)\s+95% CI \[(-?[\d.]+), (-?[\d.]+)\]", h)
check("late minus early, 95% block CI", "-0.701 -0.958 -0.454", " ".join(m.groups()) if m else None)

g = output_of("8i. Are the model errors independent")
check("Durbin-Watson", "0.11", one(g, r"Durbin-Watson: ([\d.]+)"))
check("lag-1 autocorrelation", "0.94", one(g, r"\{1: ([\d.]+)"))

i = output_of("8k. Which zones stopped following the weather")
check("FWES R2 2019", "0.65", row(i, "FWES", 1))
check("FWES R2 2025", "0.21", row(i, "FWES", 7))

k = output_of("9d. Gradient boosting vs Ridge")
check("Ridge mean demand nMAE (%)", "3.18", row(k.split("model  nMAE_pct")[-1], "Ridge", 1))
check("HGB mean demand nMAE (%)", "3.32", row(k.split("model  nMAE_pct")[-1], "HGB", 1))
check("RF mean demand nMAE (%)", "4.21", one(output_of("from sklearn.ensemble import RandomForestRegressor"),
                                             r"RF nMAE ([\d.]+)%"))

m91 = many(output_of('for name, mdl in [("Ridge"'), r"top-5% hours\s+([\d,]+) MW")
check("final fold top-5% hours, Ridge", "1,567", m91[0] if len(m91) > 0 else None)
check("final fold top-5% hours, RF", "5,240", m91[1] if len(m91) > 1 else None)

j = output_of("9c. Bias-variance trade-off")
check("KNN best K, test nMAE", "5 5.78", " ".join(one(j, r"best K = (\d+), test nMAE ([\d.]+)%", g) or "" for g in (1, 2)).strip())

n = output_of("10a. Stress labels")
check("stress rate, net load label", "5.9", one(n, r"stress_nl\s+rate\s+([\d.]+)%"))

o = output_of("10b. Stress classification")
nl = [l.split() for l in o.splitlines() if l.startswith("stress_nl") and len(l.split()) == 7]
auc = {r[1]: r[5] for r in nl}
check("net load AUC-PR, Persistence", "0.746", auc.get("Persistence"))
check("net load AUC-PR, SVM-RBF", "0.767", auc.get("SVM-RBF"))
check("net load AUC-PR, HGB", "0.752", auc.get("HGB"))

p = output_of("km = KMeans(n_clusters=K")
check("summer days in cluster 1, 2019", "8.2", table_row(p, "summer days only", "2019", 2))
check("summer days in cluster 1, 2025", "22.1", table_row(p, "summer days only", "2025", 2))

errors = [c for cell in cells if cell["cell_type"] == "code" for c in cell.get("outputs", []) if c["output_type"] == "error"]

bad = 0
for name, expected, found in checks:
    ok = found == expected
    bad += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name:<38} reference {expected:<22} this run {found}")
print(f"\n{len(checks) - bad} of {len(checks)} checks match" + (f", {len(errors)} cell error(s)" if errors else ""))
sys.exit(1 if bad or errors else 0)
