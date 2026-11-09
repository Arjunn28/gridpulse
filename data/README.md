# Data

All inputs are public and need no API key.

| Folder | Contents | In git |
|---|---|---|
| `raw/` | 16 EIA-930 BALANCE and 16 SUBREGION six-month CSVs (2019 to 2026) and 8 Open-Meteo weather CSVs in `raw/weather/` | No |
| `processed/` | Parquet and CSV files written by the notebook | No |
| `snapshot/` | ERCO-only rows of the raw files behind the Oct 30, 2026 run, compressed, with SHA256 checksums | Yes |

## Snapshot

The snapshot is what makes the results reproducible. EIA revises its "Adjusted" series and Open-Meteo
revises recent months, so a fresh download can differ slightly from the files I used.

```
snapshot/eia_balance_erco/     16 files, EIA930_BALANCE_<year>_<half>.csv.gz
snapshot/eia_subregion_erco/   16 files, EIA930_SUBREGION_<year>_<half>.csv.gz
snapshot/weather/              8 files, one per ERCOT weather zone (COAS, EAST, FWES, NCEN, NRTH, SCEN, SOUT, WEST)
snapshot/SHA256SUMS            checksum of each of the 40 files
```

- **Window.** 2019-01-01 to 2026-09-19 05:00 UTC (hour ending). The notebook sets `START_UTC` and
  `END_UTC` and cuts every input to this window, so later hours in a fresh download are ignored.
- **How it was built.** `scripts/build_snapshot.py` reads the raw files from my Google Drive cache, keeps
  the rows with `Balancing Authority == "ERCO"` and every original column (values are copied as text, so
  nothing is rounded) and writes gzip files. The weather files are copied as they are. The script never
  downloads anything.
- **Size.** About 12 MB in total.
- **Checksums.** `snapshot/SHA256SUMS` lists one SHA256 per file. `tests/test_pipeline.py` checks them.
  To check by hand: `cd data/snapshot && shasum -a 256 -c SHA256SUMS`.
- **How the notebook uses it.** Each loading cell looks in `snapshot/` first, then in the raw cache
  (`raw/`, or Google Drive in Colab), and downloads only if both are missing.

Sources: EIA-930 Hourly Electric Grid Monitor (https://www.eia.gov/electricity/gridmonitor/) and
Open-Meteo Historical Weather API, ERA5 reanalysis (https://open-meteo.com/en/docs/historical-weather-api).
