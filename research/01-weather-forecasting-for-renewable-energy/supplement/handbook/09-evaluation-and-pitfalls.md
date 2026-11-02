# 9. Evaluating forecasts properly, and the expensive mistakes

A forecast that looks great in a notebook and fails in operations almost always fails for one of the reasons in this chapter.

## Evaluation protocol

1. **Define the target exactly.** Fed-in power at the grid meter? Or *available* power (what the plant could have produced without curtailment)? Traders need fed-in power including expected curtailment; performance analysts need available power. Don't mix them.
2. **Use as-issued inputs only.** For a day-ahead model evaluated at 12:00 CET D-1, use only NWP runs that were *actually available* by, say, 11:00 CET, and only measurements up to then.
3. **Walk-forward (rolling-origin) backtests**, never random K-fold on time series. Train on months 1 to 12, test on 13; retrain, test on 14; and so on. Keep at least one full year of test data to cover all seasons.
4. **Evaluate by lead time** (hour 1, 2, ... 48) and **by time of day** (PV: daytime only, or clearly state if night zeros are included).
5. **Always compare against baselines**:
   - Persistence / smart persistence (intraday)
   - Climatology
   - A "naive physical" model (single NWP source through pvlib or a power curve)
   - For Germany/Europe: the **TSO forecasts published on ENTSO-E or netztransparenz.de** for regional aggregates. Beating the official TSO day-ahead forecast is a credible benchmark.
6. **Report proper scores**: MAE and RMSE for deterministic; pinball loss / CRPS plus reliability for probabilistic. State normalisation (by capacity, by mean, daytime only).
7. **Check significance** (Diebold-Mariano test) before claiming improvement; one sunny week proves nothing.
8. **Break down errors by regime**: clear vs overcast vs broken clouds, fog days, snow days, frontal passages, storms, high/low wind. Averages hide the days that cost money.
9. **Evaluate value**, not only accuracy: simulate imbalance costs with real imbalance prices, or lost-energy accuracy against a reference.
10. **Monitor continuously in production**: rolling 30-day error per site, with alerts when it drifts (sensor fault, new curtailment rule, NWP model upgrade).

## The expensive mistakes (pitfalls)

### Time
- **Time zones and DST.** Store everything in **UTC**. Local time has a 23-hour and a 25-hour day each year; joins across DST break silently.
- **Interval conventions.** Is "10:00" the average of 09:45-10:00 (interval ending), 10:00-10:15 (interval beginning), or an instantaneous value? SCADA systems, NWP, markets and APIs differ. A 15-min shift creates a large, systematic error in morning/evening ramps.
- **Accumulated and averaged NWP fields.** Radiation in NWP is rarely instantaneous:
  - ECMWF `ssrd` is **accumulated** in J/m² since the start of the run: difference consecutive steps and divide by the step length in seconds.
  - DWD ICON `ASWDIR_S`, `ASWDIFD_S` are **averaged since the start of the run**: de-average as $\bar{G}_{[t-1,t]} = t\,\bar{A}_t - (t-1)\,\bar{A}_{t-1}$ (in step units).
  - GFS `DSWRF` alternates between 3-hour and 6-hour averaging windows.
  - Open-Meteo returns averages over the preceding hour.
  Get this wrong and your forecast is shifted or scaled.
- **Solar position for interval averages**: compute it at the interval midpoint, not the label.

### Leakage
- **Training on observations or reanalysis instead of forecasts.** A model trained on ERA5 or measured irradiance as input learns a relationship that doesn't exist in operations (forecast inputs are worse). Training must use archived **forecasts**, with the same lead time as in operation.
- **Using data that wasn't available yet** (late NWP runs, measurements published hours later, revised data).
- **Random cross-validation** on autocorrelated data.

### Plant state
- **Curtailment and outages in training data.** If 10 % of training hours are curtailed, the model learns to under-forecast. Filter them using availability/curtailment flags, or model them explicitly.
- **Capacity changes.** Extensions, repowering, failed strings, degradation. Keep a capacity history and normalise targets.
- **Clipping and export limits.** Model them explicitly; don't let ML guess.
- **Snow-covered modules**, frozen turbines: weather looks fine, output is zero.
- **Weather-dependent curtailment rules** (bat, flicker, noise, negative prices): part of the forecast for traders.

### Sensors
- **Pyranometers**: soiling, misalignment, dew/frost, calibration drift; reference cells vs pyranometers differ (spectral and angular response). Cross-check with satellite irradiance and clear-sky curves.
- **Nacelle anemometers** sit behind the rotor and are corrected with a transfer function; not a free-stream measurement.
- **Meter vs SCADA vs inverter data** don't sum the same way (losses, timestamps).
- Quality control (QC) rules: physical limits (e.g. BSRN limits for irradiance), stuck values, spikes, night-time offsets, comparison between redundant sensors.

### Spatial
- **Nearest grid point vs interpolation**: use bilinear or a small neighbourhood (and neighbourhood statistics as features).
- **Elevation and coastline effects**: grid cells mixing sea and land, mountain vs valley sites.
- **Aggregation hides site problems**: a good portfolio score can contain badly broken individual sites.

### Metrics
- **MAPE** with zeros (night, calm) is meaningless.
- **Including night hours** in PV metrics makes errors look half as large.
- **Optimising the wrong loss.** MAE is minimised by the median, RMSE by the mean. With asymmetric imbalance prices the optimal bid is another quantile (chapter 6).
- **Normalisation games.** "5 % error" can mean anything. Always say "% of installed capacity, daytime, 15-min resolution, lead time 24-48 h".

### Operations
- **NWP model upgrades** (new IFS cycles, ICON updates) shift biases overnight. Retrain on a rolling window and watch errors after announced upgrades.
- **Late or missing NWP runs.** Always have a fallback (previous run, second model, climatology).
- **Units**: kW vs kWh per 15 min vs MW; W/m² vs Wh/m² vs J/m².
- **Silent failures**: a pipeline that keeps publishing yesterday's forecast. Monitor input freshness.

## Production-readiness checklist

- [ ] All timestamps UTC, interval convention documented per source
- [ ] NWP accumulation/averaging handled and unit-tested
- [ ] Training only on archived as-issued forecasts with realistic availability times
- [ ] Curtailment/outage filtering, capacity history
- [ ] Baselines and walk-forward backtest over at least one full year
- [ ] Probabilistic output with reliability checks
- [ ] Per-regime and per-lead-time error reports
- [ ] Fallbacks for missing inputs, monitoring of input freshness and forecast error
- [ ] Clear data licences for every source in use
