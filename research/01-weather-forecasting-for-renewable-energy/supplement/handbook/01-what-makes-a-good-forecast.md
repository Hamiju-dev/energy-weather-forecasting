# 1. What makes a good weather-to-energy forecast

## The forecast is a chain, and every link adds error

Nobody forecasts "power" directly from the sky. Every renewable forecast, whether it comes from a TSO, a direct marketer, a vendor or a hobby script, is built from the same chain:

```
 Observations           satellites, radiosondes, aircraft, stations, radar
      |
 Data assimilation      best estimate of the atmosphere "right now" (the analysis)
      |
 Weather model          physics NWP (IFS, ICON, GFS ...) or AI model (AIFS, GraphCast ...)
      |                 deterministic run + ensemble of perturbed runs
 Post-processing        bias correction, downscaling to the site, blending of models
      |
 Weather-to-power       physical model (pvlib, power curve) and/or ML model
      |                 + plant state: capacity, outages, curtailment rules
 Uncertainty            quantiles, scenarios, ensembles, calibrated
      |
 Decision               bid, schedule, alert, report, invoice, claim
```

Where the error comes from changes with the horizon:

| Horizon | Dominant error source |
|---|---|
| Minutes to 1-2 h | Local cloud/wind fluctuations; plant state (outages, curtailment) |
| 2-6 h | Cloud and front timing; how fast you ingest new satellite/measurement data |
| Day-ahead | NWP error (cloud cover, cloud type, wind speed, front timing) |
| 3-15 days | NWP predictability limit; only ensembles carry useful information |
| Weeks-seasons | Large-scale regimes (NAO, blocking); only shifts in odds |
| Years | Interannual variability, long-term trends, measurement/model bias |

In practice, at day-ahead the biggest *avoidable* errors are often not meteorological: wrong capacity, an inverter that has been down for a week, a curtailment rule (bat protection, export limit, negative-price shutdown) that the forecast didn't know about, or a timestamp shifted by one hour.

## What "good" means

Allan Murphy's classic paper *What is a good forecast?* (1993) splits goodness into three parts, and it still holds:

1. **Consistency.** The forecast says what the forecaster actually believes. For a model: it is optimised for the same loss the user cares about. If you trade and pay asymmetric imbalance prices, the best bid is a quantile, not the mean.
2. **Quality.** How well forecasts match observations: bias, MAE, RMSE, CRPS, reliability, sharpness.
3. **Value.** Whether decisions improve. A forecast with slightly worse RMSE but much better ramp timing can be worth more to a trader.

Concrete properties of a good operational energy forecast:

- **Accurate for the target variable.** Being good at 2 m temperature is irrelevant if POA irradiance under low stratus is bad.
- **Unbiased** across seasons, times of day and weather regimes (a model that is fine on average but always overshoots on foggy winter mornings is a bad model).
- **Probabilistic and calibrated.** When it says 90 % interval, reality falls inside about 90 % of the time. Then as *sharp* (narrow) as possible.
- **Timely.** Delivered before the decision deadline. A brilliant forecast that arrives at 12:05 CET misses the day-ahead auction.
- **Right resolution.** European markets now settle in 15-minute units (day-ahead since 1 October 2025), so hourly forecasts are no longer enough.
- **Frequently updated.** New NWP runs, satellite images and live plant data should flow in; intraday value comes from updates.
- **Stable.** Doesn't jump around between runs without reason (traders hate "flip-flopping" forecasts).
- **Robust.** Falls back to a second weather source if one feed is late; flags stale inputs.
- **Aware of the plant.** Knows capacity, availability, curtailment rules, clipping, snow, soiling.
- **Traceable.** You can explain a bad day afterwards (which input caused it?).
- **Cheap enough.** Data licences, compute and maintenance scale with the number of sites.

## The full ingredient list

This is the "everything you need" checklist. Later chapters go into each part.

| # | Ingredient | Examples | Chapter |
|---|---|---|---|
| 1 | Weather forecasts, several sources | ECMWF IFS/AIFS, ICON-D2, GFS, MOSMIX, ensembles | 7, 8 |
| 2 | Archived *as-issued* forecasts for training | Open-Meteo Previous Runs, own archive | 8, 9 |
| 3 | Observations / ground truth | Plant SCADA, POA pyranometers, met masts, DWD stations, satellite irradiance | 8 |
| 4 | Plant metadata and its history | Coordinates, kWp/kWac, tilt/azimuth, trackers, module and inverter type, turbine type, hub height, power curve, layout, commissioning dates, repowering | 3 |
| 5 | Plant state | Availability, outages, curtailment (Redispatch, export limits, negative prices, bat/noise modes) | 4, 5 |
| 6 | Physical conversion model | Solar geometry, transposition, temperature, power curve, wakes | 6 |
| 7 | Statistical/ML layer | MOS, gradient boosting, neural nets, model blending | 7 |
| 8 | Uncertainty model | Quantile regression, ensemble calibration, conformal prediction, scenarios | 6, 7 |
| 9 | Evaluation framework | Baselines, walk-forward backtests, proper scores, per-regime checks | 9 |
| 10 | Operations | Scheduler aligned to NWP run times, monitoring, alerting, fallbacks | 11 |
| 11 | Delivery and visualisation | APIs/files for trading systems, dashboards per department | 10 |
| 12 | Domain knowledge | Market rules, grid codes, standards (IEC 61724, IEC 61400-12-1), local weather quirks | 4, 5 |

## Three ways to turn weather into power

| Approach | How | Strengths | Weaknesses |
|---|---|---|---|
| **Physical** | NWP irradiance/wind into a physics model (pvlib chain, power curve with density correction, wake model) | Works from day one with no history; explainable; handles new plants | Inherits NWP bias; needs exact metadata; ignores unknown losses |
| **Statistical / ML** | Learn power directly from NWP features and historical output | Corrects systematic NWP and plant errors automatically; usually more accurate with 1+ year of good data | Needs clean history (curtailment-filtered); breaks when plant changes; can extrapolate badly |
| **Hybrid** (industry standard) | Physical model output used as a feature (or baseline) for an ML correction; or ML for irradiance then physics for power | Best of both; robust for new and changing plants | More moving parts |

Separately, there's **deterministic** (one number per time step) versus **probabilistic** (a distribution: quantiles, ensembles or scenarios). Probabilistic is now standard in serious operations because trading, BESS optimisation and reserve sizing all need the risk, not only the expected value.

## Where forecasts typically fail

### Solar PV
- **Low stratus and fog** (German *Hochnebel* in autumn/winter under high pressure). NWP often dissolves it too early or too late; errors of most of the plant's output.
- **Convective clouds** in summer: the model gets "scattered cumulus" right but not *where*, so single sites see big errors while a portfolio averages out.
- **Thin cirrus and contrails**: small irradiance dimming that models miss.
- **Aerosols, especially Saharan dust.** On 4 April 2014 the German day-ahead PV forecast overestimated output by up to 5.3 GW because the dust was not in the model ([KIT/DWD study, ACP 2017](https://acp.copernicus.org/articles/17/13391/2017/)). Dust outbreaks reach Germany 5 to 15 times a year. Wildfire smoke has the same effect.
- **Snow** on modules: the weather is sunny, but output is zero. Melting/sliding timing is hard.
- **Frost, dew and soiling** changing over days.
- **Clipping and export limits**: the weather can be "perfect" but output is capped.

### Wind
- **Timing (phase) errors** of fronts and lows: a ramp forecast 3 hours late creates a "double penalty" (wrong both before and after).
- **Stable nights**: low-level jets, strong shear and decoupling; models under-mix or over-mix.
- **Convective gusts and thunderstorm outflows.**
- **Storm cut-out** (often around 25 m/s): huge simultaneous ramps across a region.
- **Icing**: reduced output or shutdowns when temperature is near or below 0 °C with fog or supercooled droplets.
- **Rule-based curtailments** that are weather-dependent but not "weather": bat protection (low wind, warm nights), shadow flicker (sun position plus clear sky), noise-reduced night modes, bird protection during harvesting/mowing.

### Everyone
- Wrong timestamp conventions, DST, average vs instantaneous values (see chapter 9).
- Model upgrades at the weather centre that shift biases overnight.
- Unknown outages and curtailment in training data teaching the model to under-forecast.
