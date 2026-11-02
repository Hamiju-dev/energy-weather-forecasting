# Data catalogue: paper 01

All data are public. Times are UTC. Every download is logged with its URL, byte range, size and SHA-256 hash in `raw/`.

## Folder overview

| Folder | Content | Versioned |
|---|---|---|
| `raw/` | download manifests and small raw files, exactly as received | yes |
| `cache/` | large downloads (NOAA station files, per-run forecast extracts); re-created by `make fetch` and checkable against the manifests | no |
| `interim/` | parsed observations, forecast values at the stations, matched pairs | yes |
| `processed/` | one CSV per figure and table of the paper (the numbers behind every chart) | yes |
| `literature/` | facts and tables taken from publications, one row per item, with source key and URL | yes |

## Sources and licences

| Source | Provider | Used for | Licence |
|---|---|---|---|
| ECMWF open data (IFS and AIFS Single, 0.25°), Google Cloud mirror `storage.googleapis.com/ecmwf-open-data` | ECMWF | forecasts, 00 UTC runs 1 May to 31 July 2025 | CC-BY-4.0, © ECMWF |
| GFS 0.25°, NOAA Open Data Dissemination on Google Cloud `storage.googleapis.com/global-forecast-system` | NOAA NCEP | forecasts, same runs | public domain |
| Integrated Surface Database (ISD), AWS Open Data `noaa-isd-pds` | NOAA NCEI | hourly station observations 2020-2025 | public domain |
| OpenEnergy turbine library, bundled with windpowerlib 0.2.2 | oemof / OpenEnergy Platform | V126/3450 power curve | see windpowerlib (MIT) and the OpenEnergy Platform terms |
| Linke turbidity climatology, bundled with pvlib 0.16.1 | pvlib / SoDa | clear-sky irradiance | BSD-3 (pvlib) |
| Publications and web pages listed in `literature/` | various | market facts, accuracy benchmarks, model and data inventories | cited, not redistributed |

The ISD archive on AWS ends in August 2025, which is why the study covers May to July 2025.

## raw/

| File | Description |
|---|---|
| `forecast-download-manifest.csv.gz` | one row per GRIB2 message read: `retrieved_utc, url, byte_start, byte_end, bytes, sha256, note` (note = model, variable, lead time) |
| `noaa-isd-download-manifest.csv` | one row per station file and the station catalogue, same columns |
| `turbine-power-curves/oedb_power_curves_windpowerlib-0.2.2.csv` | the OpenEnergy turbine power curves as shipped with windpowerlib; columns are wind speeds in m/s, values in W |

## interim/

| File | Columns | Description |
|---|---|---|
| `station_candidates.csv` | `station_id, name, icao, latitude, longitude, elevation_m` | German ISD stations below 600 m, active 2020 to August 2025 |
| `station_observations_2025.csv.gz` | `station_id, time_utc, report_type, wind_speed_10m_ms, temperature_2m_c` | all reports from 29 April to 12 August 2025 that passed ISD quality control |
| `station_climatology_2020_2024.csv` | `station_id, month, hour, wind_mean, wind_n, t2m_mean, t2m_n` | mean 10 m wind (m/s) and 2 m temperature (°C) at 00 and 12 UTC for May to August 2020-2024 |
| `observations_at_valid_times.csv.gz` | `valid_time_utc, wind_obs, t2m_obs, station_id` | report nearest to each 00/12 UTC valid time within ±30 min |
| `forecast_point_values_<model>.csv.gz` | `model, init_time_utc, step_h, station_id, u10, v10, t2m` | model values interpolated bilinearly to the stations; wind components in m/s, temperature in °C |
| `verification_pairs.csv.gz` | `model, init_time_utc, step_h, valid_time_utc, station_id, wind_fc, wind_obs, t2m_fc, t2m_obs` | forecast and observation side by side (long format) |
| `verification_wide.csv.gz` | `init_time_utc, step_h, valid_time_utc, station_id, wind_fc_<src>, t2m_fc_<src>, wind_obs, t2m_obs, hour, month` | all forecasts per case; `<src>` = `ifs, aifs, gfs, mmm` and their bias-corrected `_bc` versions, `persistence`, `climatology` |

## processed/ (figure and table data)

| File | Used in | Key columns |
|---|---|---|
| `fig03_pv_chain_clear_day.csv` | Figure 3 | `hour_utc`, irradiance `ghi_wm2, dni_wm2, dhi_wm2, poa_global_wm2`, `air_temperature_c, cell_temperature_c`, power `p_dc_mw, p_dc_at_25c_mw, p_ac_mw` |
| `fig05_skill_by_lead_wind.csv`, `fig05_skill_by_lead_t2m.csv` | Figure 5 | per lead time (`step_h, lead_days, valid_hour_utc`): `n_, bias_, mae_, rmse_, rmse_lo_, rmse_hi_, skill_` for each forecast |
| `fig06a_error_correlation_pairs.csv` | Figure 6a | `station_a, station_b, distance_km, error_correlation` |
| `fig06a_error_correlation_binned.csv` | Figure 6a | `distance_mid_km, mean_correlation, pairs, q25, q75` |
| `fig06b_aggregation_rmse_vs_n.csv` | Figure 6b | `n_stations, relative_rmse, relative_rmse_q10, relative_rmse_q90, theory` |
| `fig07a_power_curve.csv` | Figure 7a | `wind_speed_hub_ms, power_w, power_normalised` |
| `fig07b_partial_load_elasticity.csv` | Figure 7b | histogram of the power-to-wind error elasticity: `elasticity_bin_low, elasticity_bin_high, elasticity_bin_mid, share_of_pairs, pairs` |
| `fig07c_bid_cost_vs_quantile.csv` | Figure 7c | `tau, cost_asymmetric, cost_symmetric, share_below_bid`, and the costs of bidding the point forecast |
| `tab07_day_ahead_summary.csv` | Table 7 | `variable, unit, forecast, key, n, bias, mae, rmse, rmse_lo, rmse_hi` |
| `combination_check.csv` | Proposition 3 check | per variable, raw or bias-corrected, and lead time: RMSE of IFS and AIFS, ratio `k`, error correlation, `k^2+2*rho*k`, and whether their mean beats the better model |
| `power_error_by_lead.csv` | Section 10.4 | pseudo-power errors by model and lead time |
| `stations.csv` | Section 10.1 | candidate stations with `availability` and `used` |

## literature/

| File | Content |
|---|---|
| `market_facts.csv` | price and market observations quoted in Table 4 and Section 7, with source key, URL and access date |
| `forecast_accuracy_benchmarks.csv` | published accuracy figures quoted in Section 5 |
| `nwp_models.csv` | operational weather models in Table 5 |
| `data_sources.csv` | free data sources in Table 6, with URL and commercial-use status |
| `eu_market_timeline.csv` | gate closure times shown in Figure 4 |
| `horizons.csv` | lead-time ranges drawn in Figure 2 (expert assessment) |
