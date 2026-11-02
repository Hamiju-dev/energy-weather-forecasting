# Analysis code: paper 01

Seven scripts, numbered in the order they run. All settings (study period, models, lead times, stations, bias-correction window, turbine, PV plant) are in [`config.py`](config.py); every script lists its inputs and outputs in its header.

| Step | Script | Reads | Writes | Paper |
|---|---|---|---|---|
| 1 | `01_fetch_station_observations.py` | NOAA ISD on AWS | station candidates, observations 2025, climatology 2020-2024, download manifest | Sec. 10.1 |
| 2 | `02_fetch_model_forecasts.py` | ECMWF open data and GFS on Google Cloud (GRIB2 byte ranges) | forecast values at the stations, download manifest | Sec. 10.1 |
| 3 | `03_build_verification_pairs.py` | steps 1 and 2 | matched forecast-observation pairs, station list | Sec. 10.1 |
| 4 | `04_skill_by_lead_time.py` | step 3 | skill by lead time, bias-corrected forecasts, Table 7, combination check | Fig. 5, Table 7, Prop. 3 |
| 5 | `05_spatial_aggregation.py` | step 4 | error correlation by distance, portfolio error vs size | Fig. 6, Prop. 2 |
| 6 | `06_wind_power_and_bidding.py` | step 4, windpowerlib power curve | elasticity, power errors, bidding costs | Fig. 7, Props. 1 and 4 |
| 7 | `07_pv_clear_sky_chain.py` | step 1, pvlib | clear-sky PV chain for one day | Fig. 3 |

Helpers: [`common.py`](common.py) (HTTP with retries, SHA-256 download log, distances, LaTeX macro writer).

## Run

```bash
pip install -r requirements.txt
```

```bash
cd .. && make fetch analysis
```

`make fetch` reads about 12 GB from the public archives (only the needed GRIB2 messages are requested) and keeps a few MB; it takes 20-30 minutes and is resumable. `make analysis` takes about a minute.

## Method notes

- **Interpolation:** bilinear from the 0.25° grid to the station.
- **Observation matching:** nearest report within ±30 minutes of the valid time, per variable; stations need ≥ 90 % availability.
- **Bias correction:** for each model, station and lead time, subtract the mean error of the previous 30 runs whose observations were available when the run started (no look-ahead; at least 10 past errors).
- **Climatology:** 2020-2024 station mean for the same month and hour (out of sample).
- **Intervals:** 1,000 bootstrap resamples of whole runs (block bootstrap); Diebold-Mariano tests on daily mean squared errors with a Newey-West variance.
- **Pseudo power:** 10 m wind × (120/10)^(1/7) through the V126/3450 power curve, applied identically to forecast and observation.
