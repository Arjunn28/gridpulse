#!/usr/bin/env bash
# Run the notebook headlessly and write the executed copy to build/ (not tracked by git).
# Usage: scripts/run_notebook.sh [output_name]     (default: GridPulse.executed)
set -euo pipefail
cd "$(dirname "$0")/.."

OUT_NAME="${1:-GridPulse.executed}"
mkdir -p build

jupyter nbconvert --to notebook --execute notebooks/GridPulse.ipynb \
  --output "$OUT_NAME" --output-dir build \
  --ExecutePreprocessor.timeout=3600 --ExecutePreprocessor.kernel_name=python3

echo "executed copy: build/$OUT_NAME.ipynb"
