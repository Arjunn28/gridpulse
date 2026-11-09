"""Build data/snapshot/ from the raw files behind the Oct 30, 2026 reference run.

EIA files are cut down to the ERCO rows (every original column kept). Weather files are copied as they are.
Everything is written as .csv.gz with a fixed timestamp so the checksums are stable.
Run from the repo root: python scripts/build_snapshot.py
"""
import gzip
import hashlib
import io
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SNAP = ROOT / "data" / "snapshot"


def write_gz(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0, compresslevel=9) as g:
        g.write(data)


def build_eia(kind):
    for src in sorted(RAW.glob(f"EIA930_{kind.upper()}_*.csv")):
        # read everything as text so the values are written back exactly as EIA published them
        d = pd.read_csv(src, dtype=str, keep_default_na=False)
        d = d[d["Balancing Authority"] == "ERCO"]
        buf = io.StringIO()
        d.to_csv(buf, index=False, lineterminator="\n")
        write_gz(SNAP / f"eia_{kind}_erco" / f"{src.name}.gz", buf.getvalue().encode())
        print(f"{src.name}: {len(d)} ERCO rows")


def build_weather():
    for src in sorted((RAW / "weather").glob("*.csv")):
        write_gz(SNAP / "weather" / f"{src.name}.gz", src.read_bytes())
        print(f"{src.name}: copied")


def write_checksums():
    lines = []
    for p in sorted(SNAP.rglob("*.csv.gz")):
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(SNAP).as_posix()}")
    (SNAP / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    return len(lines)


if __name__ == "__main__":
    build_eia("balance")
    build_eia("subregion")
    build_weather()
    n = write_checksums()
    size = sum(p.stat().st_size for p in SNAP.rglob("*") if p.is_file())
    print(f"\n{n} files, {size / 1e6:.1f} MB total")
