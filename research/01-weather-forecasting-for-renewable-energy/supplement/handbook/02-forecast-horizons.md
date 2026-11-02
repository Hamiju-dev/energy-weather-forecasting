# 2. Forecast horizons: how far ahead, and for what

Short answer: anything from **seconds** to **30+ years**, but each horizon uses different data, methods and users. The workhorse of the industry is **day-ahead (D+1)** and **intraday** in 15-minute resolution, followed by **up to ~14 days** for planning.

## The horizon table

| Name | Lead time | Typical resolution | Main inputs | Typical methods | Main users |
|---|---|---|---|---|---|
| Very short-term | seconds to 30 min | 1 s to 1 min | Sky cameras, live plant data, nacelle/lidar wind | Persistence, cloud tracking in images, AR models | Plant controllers (ramp-rate limits), hybrid PV+BESS, island grids |
| Nowcasting | 30 min to ~6 h | 5 to 15 min | Satellite images (every 5 to 15 min, 2.5 min rapid scan with MTG), live SCADA, rapid-update NWP (ICON-D2-RUC, HRRR), radar | Cloud motion vectors / optical flow, ML on satellite, blending with NWP | Intraday traders, TSO control rooms, BESS, curtailment management |
| Intraday | ~1 to 24 h | 15 min | Latest NWP runs + nowcast + live data | Blended statistical models, frequent re-runs | Intraday trading (continuous + auctions), balance groups, direct marketers |
| Day-ahead | 12 to 48 h (D+1) | 15 min (EU), 1 h (US DA) | 00 UTC and 06 UTC NWP runs, multiple models | Physical + ML post-processing, probabilistic | Day-ahead auction (12:00 CET gate closure), TSO scheduling, O&M planning |
| Short / medium range | 2 to 15 days | 1 h to 1 day | Global NWP + ensembles (ECMWF ENS, AIFS ENS, GEFS) | Ensemble statistics, calibrated quantiles | Maintenance windows, construction/crane planning, weekly hedging, BESS strategy, price outlook |
| Extended range / sub-seasonal | 2 to 6 weeks | weekly means | ECMWF extended-range ensemble (46 days, daily), weather regimes | Weekly anomalies vs climate, regime probabilities | Monthly forward trading, hydro scheduling, gas storage, staffing |
| Seasonal | 1 to 7 months | monthly means | C3S multi-system seasonal forecasts, ENSO/NAO indices | Anomaly probabilities ("above normal" terciles) | Budget re-forecasts, hydro reservoirs, winter adequacy, gas procurement |
| Long-term / resource | 1 to 30+ years | hourly to annual | Reanalysis (ERA5), satellite irradiance (SARAH-3), on-site measurements, climate projections | Long-term correction (MCP), P50/P90 statistics, Monte Carlo | Development, financing, PPAs, valuation |
| Hindcast / "backcast" | the past | 1 to 15 min | Measured data, satellite irradiance, reanalysis | Expected-power models | Performance analysis, lost energy (Ertragsausfall), Redispatch settlement, insurance claims |

## How predictability decays

Weather is chaotic: small errors in the initial state double every couple of days. Rough rules for European mid-latitudes:

- **Day 1 to 2**: deterministic forecasts are good for wind and synoptic cloud; local convection and fog still hard.
- **Day 3 to 5**: still useful; front timing errors of several hours become common; use ensembles.
- **Day 6 to 10**: only the ensemble mean and spread are meaningful for wind and cloud; single runs flip.
- **Day 10 to 15**: mostly regime-level information (e.g. "windy westerly pattern likely").
- **Week 3 to 6**: weekly-mean anomalies only, skill varies strongly with the situation (some weeks predictable, many not).
- **Seasonal**: in Europe, weak skill except some winter signals (NAO, sudden stratospheric warmings). In the tropics and for ENSO-linked regions, much better.

Surface variables that matter for energy (cloud cover, irradiance, 100 m wind) lose skill **faster** than the upper-air fields used in headline skill scores (like 500 hPa geopotential).

## How accurate is "good"?

Numbers depend heavily on normalisation (by installed capacity, by mean production, daytime only or not) so always check definitions. Indicative values from the literature:

| Case | Typical error | Source/notes |
|---|---|---|
| Single PV site, day-ahead | nRMSE roughly 6 to 8 % of capacity in several studies, much higher in cloudy climates or per hour of daylight | Various studies; see [Antonanzas et al. 2016](https://doi.org/10.1016/j.solener.2016.06.069) review |
| PV region vs single site | Regional upscaling reduced day-ahead RMSE by about 12 % vs single clusters (Italy); aggregating 152 Utrecht systems improved MAE by ≥18 % and RMSE by ≥20 % | Cornaro et al. 2017; [Visser et al.](https://research-portal.uu.nl/en/publications/benchmark-analysis-of-day-ahead-solar-power-forecasting-technique/) |
| Single wind farm, day-ahead | RMSE about 10 to 15 % of installed capacity | Ernst et al. 2007 (older benchmark) |
| German control area / all Germany wind, day-ahead | about 6 to 7 % and 5 to 6 % (2007); about 3 to 4 % of capacity by the mid-2010s | Ernst et al. 2007; [WINDSAGE project](https://www.ubimet.com/en/?p=13825) |
| Clear-sky days, PV | around 1 % nRMSE | Clear days are easy; the score is decided on cloudy days |

Rules of thumb:
- **Aggregation reduces relative error** (geographic smoothing). A 1,000-site portfolio is far easier than one site.
- **Intraday updates** with live data cut errors substantially in the first hours.
- **Combining several NWP sources** usually beats the best single source.
- Wind power errors are amplified by the cubic power curve: a 10 % wind speed error in the steep part of the curve becomes roughly a 33 % power error.

## Timing matters as much as horizon

A forecast is only useful if it exists before the decision. For the European day-ahead auction (gate closure 12:00 CET on D-1):

| NWP run | Roughly available | Usable for DA? |
|---|---|---|
| ICON-D2 / ICON-EU 00 UTC | early morning UTC | Yes |
| GFS 00 UTC | about 3.5 to 5 h after run start | Yes |
| ECMWF IFS/AIFS 00 UTC | from about 6 h after run start (open data adds about 1 h to the dissemination schedule) | Yes |
| ICON-D2 06 UTC, ICON-D2-RUC hourly runs, GFS 06 UTC | late morning UTC | Yes, if your pipeline is fast |
| ECMWF 06 UTC | around midday | Usually too late for DA, good for intraday |
| 12 UTC runs | afternoon/evening | Intraday auctions (IDA2 22:00) and next-day continuous trading |

Check each provider's current dissemination schedule (e.g. [ECMWF](https://confluence.ecmwf.int/display/DAC/Dissemination+schedule)); they change with model upgrades.

## Time resolution in markets (Europe)

- Day-ahead (SDAC): **15-minute market time unit since delivery day 1 October 2025** ([APG](https://markt.apg.at/en/news-press/sdac-go-live-of-15-minute-market-time-unit-in-day-ahead-market-coupling-successful-as-of-september-30-2025/)).
- Intraday auctions (IDA1 15:00 D-1, IDA2 22:00 D-1, IDA3 10:00 D) since 13 June 2024.
- Continuous intraday: 15-minute products, trading close to delivery.
- Imbalance settlement: 15 minutes.

So your forecast should be in **15-minute steps, in UTC internally**, with clear interval convention (see chapter 9).
