# 11. Building it: architecture and a roadmap for this repo

This repo's stated goal is **PV power forecasting from weather data using public DWD/Open-Meteo data**. This chapter turns the research into a concrete plan.

## Reference architecture

```
                 +-------------------- scheduler (cron / GitHub Actions / Airflow) ---------------------+
                 |  triggers aligned to NWP availability: e.g. every hour + after 00/06/12/18 UTC runs   |
                 +----------------------------------------------------------------------------------------+
   INGEST                         STORE                    MODEL                         SERVE / USE
   ------                         -----                    -----                         -----------
   Open-Meteo APIs   --+                                   physical model (pvlib)  --+
   DWD ICON-D2/EU    --+--> raw (GRIB/JSON, as received)    ML correction (LightGBM)  +--> forecasts table (UTC, 15 min,
   DWD MOSMIX        --+    -> tidy (Parquet / Zarr,        quantile models           |    quantiles, run_time, version)
   ECMWF open data   --+       with issue_time + lead)      blending                  +--> dashboard (Streamlit/Grafana)
   SMARD/ENTSO-E     --+    -> features table               evaluation jobs           +--> CSV/API for others
   DWD CDC obs       --+    -> measurements (QC flags)                                +--> alerts (bad data, big errors)
   plant SCADA       --+
```

Design principles:
- **Keep the raw data as received** (immutable), then derive tidy tables. You will find bugs and want to reprocess.
- **Every forecast row carries `issue_time` (run time), `valid_time`, `lead_time`, `source`, `model_version`.** This is what makes honest backtests possible.
- **UTC everywhere**, documented interval convention per source.
- **Formats**: GRIB2 for raw NWP, NetCDF/Zarr for gridded archives (xarray), Parquet for tabular time series, DuckDB or PostgreSQL/TimescaleDB for querying.
- **Idempotent jobs**: rerunning a day produces the same result.

## Roadmap for this repo

### Phase 0: choose a target you can actually measure
Without your own plant data, good free targets are:
1. **German national PV generation** (SMARD / ENTSO-E, 15 min) with the **TSO day-ahead solar forecast** on ENTSO-E as the benchmark to beat.
2. **One TSO control area** (netztransparenz.de extrapolations).
3. **Measured irradiance at DWD stations** (CDC 10-min global radiation): forecast GHI first, which is the hardest part of PV forecasting anyway.
4. **Open PV system data** (Open Climate Fix UK PV, PVOutput) if a single-site target is wanted.

If plant SCADA data becomes available (e.g. from work), the same pipeline applies per site.

### Phase 1: data ingestion
- [ ] Open-Meteo **Historical Forecast** and **Previous Runs** APIs for ICON-D2, ICON-EU, ECMWF IFS/AIFS, GFS: GHI, direct/diffuse, cloud cover (low/mid/high), temperature, wind, snow.
- [ ] Open-Meteo **Satellite Radiation API** as a near-real-time "truth" for irradiance.
- [ ] DWD **MOSMIX** station forecasts (via `wetterdienst`) as a strong free baseline.
- [ ] **Start archiving** DWD ICON-D2 radiation fields and MOSMIX daily (files disappear after ~24 h).
- [ ] Target data: SMARD/ENTSO-E PV generation and TSO forecasts; DWD CDC station radiation.
- [ ] Note the Open-Meteo free API is non-commercial; for work use plan a subscription or go direct to DWD/ECMWF.

### Phase 2: physical baseline
- [ ] pvlib chain: solar position, clear sky, decomposition (if only GHI), Perez transposition, Faiman temperature, PVWatts DC, inverter clipping.
- [ ] For the national target: model the German fleet as a capacity-weighted set of representative sites (orientations/tilts), scaled by installed capacity (Energy-Charts / Marktstammdatenregister give capacity).
- [ ] Baselines: smart persistence, climatology, single-model physical forecast.

### Phase 3: ML post-processing
- [ ] Features: multi-model irradiance and clouds, clear-sky GHI and clear-sky index, solar angles, temperature, snow, lead time, cyclical calendar, physical-model output.
- [ ] Target normalised by capacity (or clear-sky power).
- [ ] LightGBM point model, then quantile models (P10/P50/P90); sort quantiles to avoid crossing.
- [ ] Walk-forward backtest, evaluation by lead time and regime (chapter 9).

### Phase 4: probabilistic and evaluation suite
- [ ] Pinball loss, CRPS, reliability diagram, PIT histogram, coverage.
- [ ] Skill vs smart persistence and vs TSO forecast.
- [ ] "Worst days" report (fog, snow, dust events).

### Phase 5: automation and visualisation
- [ ] Scheduled runs (GitHub Actions cron is free for public repos; or a small VM with cron).
- [ ] Streamlit dashboard: fan chart vs actuals, run-to-run comparison, error by lead time, map of input fields.
- [ ] Data freshness monitoring and alerts.

### Phase 6: extensions (pick based on interest)
- **Nowcasting**: satellite-radiation-based intraday updates, blending with live data.
- **Price layer**: day-ahead price model from residual-load forecasts; solar capture rate and negative-price-hour forecasts.
- **Lost-energy calculator**: expected vs actual with satellite irradiance when sensors fail; Redispatch Ausfallarbeit comparison.
- **Wind**: add a wind model (windpowerlib) for a combined residual-load view; Kelmarsh/Penmanshiel SCADA for testing.
- **AI weather models**: add AIFS/AIGFS as extra blend members; compare skill.
- **Aerosols**: CAMS AOD/dust as features for Saharan dust days.

## Suggested repo layout

```
energy-weather-forecasting/
  research/                papers in the house format (see research/README.md)
  src/ewf/
    ingest/                openmeteo.py, dwd.py, ecmwf.py, smard.py, entsoe.py
    qc/                    quality control of measurements
    features/              solar geometry, clear sky, NWP de-accumulation, feature tables
    models/                physical.py (pvlib), ml.py (lightgbm), quantiles.py, blend.py
    evaluate/              metrics.py, backtest.py, plots.py
    serve/                 dashboard (streamlit), export
  data/                    raw/, tidy/, features/  (git-ignored)
  notebooks/               exploration
  tests/                   unit tests (timestamps, accumulations, pvlib chain)
  pyproject.toml
```

## Python stack

| Area | Packages |
|---|---|
| Data access | `openmeteo-requests`, `wetterdienst`, `ecmwf-opendata`, `herbie`, `cdsapi`, `entsoe-py`, `requests` |
| Gridded data | `xarray`, `cfgrib`/`eccodes`, `zarr`, `dask`, `earthkit` |
| Tables | `pandas` or `polars`, `pyarrow`, `duckdb` |
| PV / wind physics | `pvlib`, `windpowerlib`, `PyWake` |
| ML | `scikit-learn`, `lightgbm`, `xgboost`, `catboost`, `ngboost`, `mapie` (conformal) |
| Time series | `statsmodels`, `sktime`, `darts`, `statsforecast`, `neuralforecast` |
| Scoring | `scoringrules` / `properscoring`, `xskillscore` |
| Optimisation (BESS, bids) | `pyomo`, `linopy`, `cvxpy` |
| Viz | `plotly`, `matplotlib`, `cartopy`, `streamlit`, `grafana` |
| Orchestration | cron, GitHub Actions, Prefect, Airflow, Dagster |

## Minimal first milestone (one weekend)

1. Pull 2 years of Open-Meteo historical forecasts (ICON + ECMWF) of GHI/cloud/temperature for ~10 representative German locations.
2. Pull SMARD German PV generation (15 min) and installed capacity.
3. pvlib physical model → national PV estimate; compare with SMARD actuals and the ENTSO-E TSO day-ahead solar forecast.
4. Train a LightGBM correction on year 1, test on year 2.
5. Plot error by lead time and month; write down the worst 10 days and why they failed.

That alone teaches most of what matters: timestamps, normalisation, NWP differences, aggregation and the weather regimes that drive errors.
