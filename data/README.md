# Data

All inputs are public and need no API key.

| Folder | Contents | In git |
|---|---|---|
| `raw/` | 16 EIA-930 BALANCE and 16 SUBREGION six-month CSVs (2019 to 2026), 8 Open-Meteo weather CSVs | No |
| `processed/` | Parquet files written by the notebook | No |
| `snapshot/` | ERCO-only rows of the raw files used by the Oct 30, 2026 run, compressed, with SHA256 checksums | Yes (coming next) |

Window: 2019-01-01 to 2026-09-19 UTC. EIA revises its "Adjusted" series and Open-Meteo revises recent
months, so a fresh download can differ slightly. The snapshot is what makes results reproducible.

Sources: EIA-930 Hourly Electric Grid Monitor (https://www.eia.gov/electricity/gridmonitor/) and
Open-Meteo Historical Weather API, ERA5 reanalysis (https://open-meteo.com/en/docs/historical-weather-api).
