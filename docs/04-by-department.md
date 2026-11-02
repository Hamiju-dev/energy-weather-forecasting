# 4. Who uses weather forecasts, for what, and how far ahead

Across the life of a wind or solar project, almost every department needs weather data, but each asks a different question on a different time scale. That changes the data source, the method and what "accurate" means.

## Summary matrix

| Department | Core question | Horizon | Main output | What "good" means |
|---|---|---|---|---|
| Development / origination | Is this site worth building? | 20 to 40 years (from the past) | Long-term mean resource, monthly/diurnal profile | Unbiased long-term mean |
| Yield assessment / financing | How much will it produce, with what certainty? | 1, 10, 20 years | P50, P75, P90, P99 | Honest uncertainty |
| Engineering / design | What must it survive, and how should it be sized? | Return periods 50+ years | Extreme wind/snow/hail/temperature, clipping, stow settings | Correct extremes |
| Construction / project team | Can we work tomorrow? How many weather days to plan for? | 0 to 10 days + climatology | Go/no-go per activity, weather-downtime statistics | Reliable thresholds, no surprises |
| Commissioning | When can we run the acceptance tests? Was the test valid? | 0 to 7 days + measured data | Test windows, weather-corrected test results | Stable conditions identified correctly |
| Operations / control room / O&M | What do we do today and this week? | 0 to 10 days | Alerts, maintenance windows, crew safety | Good warnings, few false alarms |
| Performance analysis / technical asset management | Is the plant performing? | The past | Expected vs actual, PR, availability, loss breakdown | Correct expected-power model |
| Lost energy, Redispatch, insurance | How much energy (and money) was or will be lost? | Past and next days/weeks | kWh and EUR lost, claims | Defensible method |
| Asset management / finance | Will we hit budget? | Month to year | Budget, year-end re-forecast, revenue | Unbiased P50 |
| Trading / direct marketing | What do we sell and at what risk? | 15 min to weeks | Production and price forecasts, quantiles | Low imbalance cost |
| Grid operators (TSO/DSO) | Is the grid balanced and secure? | Minutes to a week | Infeed, load, congestion, reserve needs | Few big misses |
| PPA / risk / insurance | What volume and shape risk do we carry? | Years | Profile, capture rate, tail risk | Correct correlations and tails |

Below, each in detail.

---

## 1. Development and site selection

**Questions:** Where is the resource best? How does production vary by month and hour (for grid and market value)? How variable is it year to year?

**Data:** satellite irradiance (CM SAF SARAH-3, CAMS, NSRDB), reanalysis (ERA5, ERA5-Land, CERRA, MERRA-2), atlases (Global Solar Atlas, Global Wind Atlas, NEWA), PVGIS, nearby station data, later on-site measurements (met mast, lidar, pyranometers).

**Methods:**
- **Typical Meteorological Year (TMY)** for PV yield simulation (PVsyst, SAM, pvlib).
- **Long-term correction / Measure-Correlate-Predict (MCP)** for wind: correlate 1 to 2 years of on-site mast/lidar data with a 20+ year reference (ERA5, MERRA-2) to estimate the long-term mean.
- **Interannual variability** (IAV): PV annual irradiation varies roughly ±3 to 5 % (1σ) in Central Europe; annual wind energy often ±8 to 12 % (wind speed varies less, but the power curve amplifies it).
- Climate trends: brightening/dimming of irradiance, possible changes in wind climate (use CMIP6/CORDEX carefully, the signal for wind is uncertain).
- Market value: combine the hourly production profile with price scenarios to estimate capture rates (chapter 5).

## 2. Energy yield assessment (EYA) and financing

**Questions:** P50 (expected), P90 (exceeded with 90 % probability) for 1 year and 10 years; this drives debt sizing.

**Uncertainty components** (combined as root-sum-square if independent):
- Resource: long-term mean of the irradiance/wind dataset, measurement uncertainty, MCP uncertainty
- Interannual variability (shrinks with the number of years: σ/√N)
- Vertical extrapolation (wind shear), horizontal extrapolation (flow model)
- Energy model: transposition, temperature, mismatch, wake model, power curve
- Losses: availability, soiling, snow, degradation, curtailment, electrical

**Standards and guides:** IEC 61400-15 series for wind (15-1 on site suitability published 2025; 15-2 on energy yield reporting still in preparation at time of writing), IEC 61724-3 for PV energy evaluation, PVsyst/SAM loss models.

Formulas in chapter 6.

## 3. Engineering and design

- **Extreme values:** 50-year wind speeds and gusts (turbine class, tracker and mounting structure design), snow loads (EN 1991-1-3), wind loads (EN 1991-1-4), hail size return periods (module glass thickness, insurance), extreme temperatures (cable and inverter derating).
- **Sizing:** DC/AC ratio vs clipping losses (needs high-resolution irradiance, 1 to 15 min, not hourly averages), BESS sizing against PV/wind profiles.
- **Control strategies:** tracker stow thresholds (wind speed and gust, hail warning, snow), turbine cold-climate packages, de-icing.

## 4. Construction / project team

Forecasts here protect **schedule, cost and people**.

**Daily and weekly decisions (0 to 10 days):**

| Activity | Typical weather limits (always check manufacturer/crane manuals and permits) |
|---|---|
| Turbine component lifts (blades, nacelle, hub) | Hub-height wind and gusts. Many conventional crawler-crane blade lifts are limited to roughly 8 to 10 m/s; special single-blade tools allow 12 to 15+ m/s. Large light loads (blades) are limited far below crane chart values |
| Offshore installation / transfers | Hs (significant wave height), wave period, wind, visibility; crew transfer vessels often ~1.5 to 2 m Hs |
| Pile driving, ramming (PV) | Ground conditions after rain, frozen ground |
| Earthworks, cabling, access roads | Rain (trafficability), frost |
| Concrete foundations | Air temperature (frost protection, curing), heavy rain |
| Module installation | Wind (modules act like sails), rain/slippery, heat stress |
| Electrical work, HV energisation | Lightning (stop-work radius, commonly ~10 to 15 km), rain/humidity |
| All outdoor work | Heat stress (WBGT), cold, storms, thunderstorms |

**Planning decisions (months ahead):** Use 20+ years of hindcast (ERA5, wave reanalysis) to estimate **weather downtime** per month: the probability of having enough consecutive hours below the limits (a "weather window"). Run Monte Carlo schedule simulations with historical weather years to get P50/P90 completion dates and set schedule contingency.

**Contracts:** construction contracts often define "exceptionally adverse weather" against historical statistics. For example, NEC contracts treat weather that occurs on average less than once in ten years as a compensation event, which requires a defensible weather record (station or reanalysis) and a statistical comparison.

## 5. Commissioning

**What happens:** mechanical/electrical completion, energisation, grid compliance tests, reliability runs, **performance / capacity tests**, provisional and final acceptance.

**Why weather forecasts matter:**
- **PV capacity tests** (ASTM E2848, IEC TS 61724-2, edition 2 published September 2025) need **stable, high irradiance** (practitioners often filter for POA above roughly 200 to 400 W/m² or higher, low variability), so you use forecasts to find clear-sky windows and avoid wasting crew days.
- **PV energy performance tests** (IEC TS 61724-3) run over weeks; expected energy is computed from measured weather.
- **Wind power curve verification** (IEC 61400-12-1:2022) needs enough valid data across all wind-speed bins and in valid wind-direction sectors. Wind forecasts and climatology tell you how long the campaign will take.
- **Grid compliance tests** (reactive power capability, frequency response, fault-ride-through checks) often require the plant to produce above a certain share of rated power, so you need forecasts of sunny or windy periods.
- **Reliability runs** (e.g. 72 h, 120 h, 240 h) need the plant to actually run, preferably in representative conditions.

**After the test:** results are **weather-corrected** to reference conditions (irradiance, cell temperature, air density). This is where measured on-site data quality (pyranometer class, calibration, cleaning, alignment) matters most.

## 6. Operations, control room and O&M

**Daily/weekly use (0 to 10 days):**
- **Severe weather alerts**: storms (tracker stow, turbine checks), hail (tracker hail stow), heavy snow (structural loads, snow clearing, tracker positioning), icing (turbine shutdown/ice detection, ice throw zones), lightning (post-strike inspections), floods, heat (inverter derating, transformer temperatures). In Germany, DWD warnings are available as open data.
- **Maintenance scheduling in low-yield windows**: do inverter/turbine work during cloudy or calm periods to minimise lost energy. A forecast that says "Thursday is overcast and windless" is worth real money.
- **Crew safety and access**: storms, heat, lightning, offshore sea state.
- **Cleaning decisions**: compare soiling loss vs cleaning cost, and check if rain is coming anyway.
- **Snow management**: whether to clear modules, how trackers should be positioned.
- **Spare parts and logistics** during winter or storm seasons.

## 7. Performance analysis and technical asset management

This looks **backwards**: what *should* the plant have produced given the actual weather?

- **Expected power model**: measured POA irradiance + module temperature (PV) or nacelle wind + density (wind) into the plant model. Satellite irradiance (e.g. SARAH-3, CAMS, Open-Meteo satellite API) is the independent check when on-site sensors are dirty, drifting or broken.
- **KPIs**: Performance Ratio (PR), temperature-corrected PR, availability (time-based and energy-based, IEC 61400-26 for wind), specific yield (kWh/kWp), loss breakdown (waterfall from theoretical to metered energy).
- **Underperformance detection**: string-level comparison, degradation trends, soiling rate, tracker faults, power curve deviations (pitch/yaw misalignment, blade erosion).
- **Sensor QC**: detect drifting pyranometers by comparing with satellite and clear-sky models.
- **Weather-normalised reporting**: "the plant produced 7 % below budget, of which 5 % is weather (low irradiance) and 2 % is technical."

Wind industry uses **wind indices** (e.g. the German BDB or anemos indices) to normalise monthly yields against the long-term "normal" wind year.

## 8. Lost energy (Ertragsausfall), Redispatch and insurance

### Looking backward (what was lost)
- **Outage losses**: expected minus actual output during downtime. References: neighbouring inverters/turbines, irradiance-based expected power, power curve with nacelle anemometer, or satellite/reanalysis when on-site data is missing.
- **Redispatch 2.0 (Germany)**: when the grid operator curtails a plant, the operator is compensated for the *Ausfallarbeit* (lost energy). Methods include a flat-rate approach (*Pauschal*, roughly carrying forward the last measured quarter-hour) and peak settlement (*Spitzabrechnung*, calculating theoretical output from measured wind or irradiance and the power curve/PV model). The [BDEW guide](https://www.bdew.de/service/anwendungshilfen/bdew-leitfaden-zur-berechnung-der-ausfallarbeit-redispatch-20/) describes the calculation; rules are being revised (BNetzA procedure BK6-23-241).
- **Insurance claims**: business interruption after hail, storm, fire, lightning. Needs defensible lost-energy and lost-revenue calculations (production times market price or tariff), often with independent weather data.
- **Negative price hours**: under §51 EEG, plants commissioned since 25 February 2025 get no market premium during negative prices, so "lost" revenue during those periods must be tracked separately from technical losses.

### Looking forward ("future losses")
This is where forecasts add value:
- **Expected loss of an open fault until repair**: e.g. an inverter is down and the technician comes in 5 days. Forecast production of that inverter × forecast price = expected loss in EUR. Rank all open faults by EUR to prioritise the field team.
- **Planned outage cost**: choose the maintenance day with the lowest forecast loss (low irradiance, low wind, or low/negative prices).
- **Curtailment forecasts**: anticipated Redispatch, export limits and negative-price hours.
- **Seasonal loss outlook**: expected snow losses, soiling build-up during dry periods, icing season.
- **Long-term losses**: degradation, increasing negative-price exposure (cannibalisation), clipping growth after repowering.

## 9. Asset management and finance

- **Budget**: monthly P50 production from the long-term EYA, distributed by month.
- **Year-end re-forecast**: year-to-date actuals + rest-of-year expectation (climatology, optionally adjusted with sub-seasonal and seasonal forecasts).
- **Revenue forecast**: production × capture price (not baseload price), market premium, PPA terms, negative-price rules.
- **Covenant monitoring**: DSCR risk if a poor wind year is developing.
- **Investor reporting**: weather-adjusted performance (resource index), so management doesn't get blamed for a dull year.

## 10. Trading and direct marketing

The heaviest real-time users; full detail in [chapter 5](05-energy-trading-and-prices.md). In Germany, the **Direktvermarkter** (direct marketer) is responsible for forecasting each plant and the portfolio, selling in day-ahead and intraday, and paying imbalance costs. They also decide whether to curtail plants at negative prices.

## 11. Grid operators (TSO / DSO)

- **Infeed forecasts and extrapolations** (*Hochrechnung*) of wind and solar for each control area; the German TSOs publish these on [netztransparenz.de](https://netztransparenz.de/en/Renewable-energies-and-levies/Voluntary-publications/Wind-and-solar-energy-projection).
- **Load forecasts** (including behind-the-meter PV).
- **Reserve sizing** using forecast uncertainty.
- **Congestion management and redispatch planning** (day-ahead and intraday congestion forecasts).
- **Dynamic line rating.**
- **Extreme events**: storms, cut-out ramps, Saharan dust, solar eclipses, heatwaves, cold spells (adequacy).

## 12. PPA structuring, origination and risk

- **Volume risk**: how much the plant produces (weather).
- **Shape / profile risk**: *when* it produces vs when prices are high; solar produces when everyone else does.
- **Capture rate forecasting**: long-term price scenarios combined with many weather years. The Pan-European Climate Database (PECD), which ENTSO-E uses for its adequacy studies (ERAA) and which is produced with Copernicus C3S, is a good reference for multi-decade weather-year modelling.
- **Hedging products**: baseload PPAs (buyer gets a flat profile, seller carries shape risk), pay-as-produced PPAs, proxy revenue swaps, weather derivatives (e.g. HDD/CDD futures, wind index products).
- **Tail risk**: Dunkelflaute (low wind + low sun in winter), long calm periods, drought years for hydro.

## 13. HSE and insurance / risk engineering

- Heat, cold, lightning, storms, ice and floods for crew safety.
- Natural-catastrophe models (hail, windstorm, flood) for insurance pricing; parametric insurance triggered by measured weather indices.
