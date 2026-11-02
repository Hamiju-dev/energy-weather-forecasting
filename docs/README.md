# Weather forecasting for renewable energy: research notes

Reference notes on everything that goes into a good weather-based forecasting system for renewables: what each technology and department needs, horizons, maths, methods, free data, evaluation, visualisation, and how weather drives power prices. Researched November 2026; time-sensitive facts are linked to sources in [chapter 12](12-glossary-and-reading.md#sources-used-for-the-time-sensitive-facts-in-these-notes).

## Chapters

| # | Chapter | Answers |
|---|---|---|
| 1 | [What makes a good forecast](01-what-makes-a-good-forecast.md) | The forecast chain, what "good" means, the full ingredient list, where forecasts fail |
| 2 | [Forecast horizons](02-forecast-horizons.md) | How far ahead (seconds to decades), predictability limits, typical accuracy, timing vs market deadlines |
| 3 | [By technology](03-by-technology.md) | PV, CSP, onshore/offshore wind, hydro, BESS, hybrids, load and grid: which weather variables matter |
| 4 | [By department](04-by-department.md) | Development, financing, engineering, construction, commissioning, O&M, performance, lost energy, asset management, trading, grid, PPA |
| 5 | [Energy trading and prices](05-energy-trading-and-prices.md) | Merit order, residual load, market timeline, negative prices, Dunkelflaute, imbalance, price forecasting |
| 6 | [Maths and formulas](06-math-and-formulas.md) | Solar geometry, irradiance, PV and wind power, wakes, hydro, statistics, metrics, optimal bids, P90, PR, lost energy |
| 7 | [Models, methods, simulations](07-models-methods-simulations.md) | NWP, AI weather models, nowcasting, ML, probabilistic methods, blending, all simulation types |
| 8 | [Free data sources](08-free-data-sources.md) | Forecasts, archives, reanalysis, satellite, observations, market data, open plant data, licences |
| 9 | [Evaluation and pitfalls](09-evaluation-and-pitfalls.md) | Backtesting properly, baselines, the expensive mistakes |
| 10 | [Visualisation](10-visualization.md) | Chart types per audience, dashboards, tools |
| 11 | [Building it: roadmap](11-building-it-roadmap.md) | Architecture and a phased plan for this repo |
| 12 | [Glossary and reading](12-glossary-and-reading.md) | Terms (incl. German), books, papers, standards, sources |

## The short version

**1. A forecast is a chain.** Observations → data assimilation → weather model (physics NWP or AI) → post-processing → weather-to-power model → uncertainty → decision. Most day-ahead error comes from the weather model (clouds, front timing); most *avoidable* error comes from plant state (outages, curtailment, wrong capacity) and data handling (timestamps, units).

**2. Each technology needs different weather.** PV: irradiance (GHI/DNI/DHI), clouds by level, aerosols/dust, temperature, snow. Wind: hub-height wind, direction, air density, shear/stability, icing, gusts. Offshore adds waves. Hydro: precipitation, snowpack, river flow, over weeks to months. BESS: prices (which are weather-driven).

**3. Each department needs a different horizon.**

| Who | Horizon |
|---|---|
| Plant control, hybrid PV+BESS | seconds to minutes |
| Intraday trading, TSO control rooms | minutes to hours |
| Day-ahead trading, scheduling | D+1 (gate closure 12:00 CET), 15-min resolution |
| O&M, construction, commissioning planning | 1 to 10 days (+ climatology for months ahead) |
| Hedging, hydro, budgets | weeks to months (sub-seasonal, seasonal) |
| Development, financing, PPAs | 20 to 40 years from historical data (P50/P90) |
| Performance analysis, lost energy, insurance | the past (hindcast with measured/satellite data) |

**4. Yes, traders use weather to forecast prices.** Wind and solar push expensive plants out of the merit order; residual load (load minus wind and solar) drives the price. Germany had 573 negative-price hours in 2025 and a 936 EUR/MWh hour during the December 2024 Dunkelflaute. Traders react to each new ECMWF/GFS/ICON run; useful weather-driven price signals reach out roughly 1 to 2 weeks, beyond that it's ensembles, climatology and fundamentals.

**5. The maths** ranges from solar geometry and transposition (pvlib), the cubic wind power law and air density, to quantile regression, EMOS, CRPS/pinball scoring, the newsvendor-optimal bid quantile, P90 statistics and lost-energy formulas. All in chapter 6.

**6. Free data is plentiful.** ECMWF open data (CC-BY-4.0, incl. AIFS), NOAA GFS/GEFS/AIGFS, DWD ICON-D2/MOSMIX (archive it yourself, files vanish after ~24 h), Open-Meteo (easiest, but free tier is non-commercial), ERA5, SARAH-3, PVGIS, ENTSO-E, SMARD, Energy-Charts, netztransparenz.de. Train on *as-issued* archived forecasts, not reanalysis.

**7. Visualise uncertainty.** Fan charts, ensemble plumes, run-to-run deltas for traders; meteograms with thresholds for operations; expected-vs-actual, carpet plots and loss waterfalls for asset management; reliability diagrams and error-by-lead-time for model work.

**8. For this repo**: start with German PV (SMARD/ENTSO-E) as the target, Open-Meteo + DWD as inputs, a pvlib physical baseline, a LightGBM quantile correction, and benchmark against the TSO day-ahead forecast. See chapter 11.
