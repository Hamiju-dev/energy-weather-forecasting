# 5. Energy trading: why weather forecasts move power prices

Yes: in power markets with a lot of wind and solar, the weather forecast is the single most important input for short-term prices. Traders watch every new model run.

## Why weather moves prices: the merit order

Power plants are dispatched in order of marginal cost (the **merit order**). Wind and solar have near-zero marginal cost, so they enter first and push expensive plants (gas, coal, oil) out of the market. The price is set by the most expensive plant still needed.

```
 price
 EUR/MWh                                              ___ oil / peakers
   |                                            _____|
   |                                  ____gas__|
   |                       ___coal___|
   |          ___lignite__|
   |  wind/PV|  nuclear                demand (low wind)  -> high price
   |_________|_________________________|____________|______________ GW
                       demand (high wind) -> low price
```

The key concept is **residual load**:

$$\text{Residual load} = \text{Load} - \text{Wind} - \text{Solar} \;(-\text{other must-run})$$

Prices correlate strongly with residual load. Weather affects both sides of that equation.

| Weather driver | Effect on price |
|---|---|
| Strong wind | Low prices across all hours, especially at night; negative prices in windy low-demand periods |
| Sunny day | Price "duck curve": midday collapse, evening peak when the sun sets |
| Sunny + windy + holiday/weekend + spring | Very negative prices (low demand, high supply) |
| Dunkelflaute (dark, calm winter period) | Price spikes, gas/coal set the price; on 12 December 2024 the German day-ahead price reached 936 EUR/MWh for 17-18 h ([SMARD](https://www.smard.de/en/study-of-electricity-price-peaks-completed-218346)) |
| Cold snap | Higher heating demand (electric heating, heat pumps), higher gas prices |
| Heatwave | Air conditioning demand; reduced thermal plant output due to cooling water limits (French nuclear on warm rivers); low PV efficiency |
| Drought / low rivers | Less hydro; coal barge transport limits (Rhine) |
| Wet and snowy winters (Nordics, Alps) | More hydro, lower prices for months |
| Forecast error across the market | Imbalance prices move against everyone who made the same error |

## Evidence of how strong the effect is (Germany)

- **Negative prices**: 573 hours with negative day-ahead prices in 2025, a record and about 25 % more than 2024 ([Bloomberg](https://www.bloomberg.com/news/articles/2026-01-05/europe-saw-record-surge-in-negative-power-prices-in-2025), [SMARD](https://www.smard.de/page/de/topic-article/5892/219038/rekord-bei-der-solarerzeugung-in-jedem-quartal)).
- **Solar cannibalisation**: the solar capture rate (solar-weighted price / average price) fell to 29.7 % in May 2025 ([S&P Global](https://www.spglobal.com/commodity-insights/en/news-research/latest-news/electric-power/061025-german-solar-capture-price-sinks-below-eur20mwh-in-may-as-cannibalization-deflates-value)). About 28 % of potential solar output in early 2025 occurred during negative prices (Enervis, via [pv magazine](https://www.pv-magazine.com/2025/08/26/germany-records-453-hours-of-year-to-date-negative-electricity-prices/)).
- **Dunkelflaute spikes**: 6 November and 11/12 December 2024, with the 936 EUR/MWh hourly peak; BNetzA later found no evidence of abuse ([SMARD](https://www.smard.de/en/study-of-electricity-price-peaks-completed-218346)).

## The European market timeline (Germany as example)

| Market | When | Products | Weather forecast used |
|---|---|---|---|
| Futures / forwards (EEX) | Years to days ahead | Year, quarter, month, week, weekend, day | Climatology, seasonal/sub-seasonal, 1-15 day ensembles for front week/month |
| Day-ahead auction (SDAC, EPEX/Nord Pool/etc.) | Gate closure **12:00 CET on D-1** | **15-min** products since 1 Oct 2025 | 00/06 UTC NWP runs, D+1 production and load forecasts |
| Intraday auctions (SIDC IDA) | IDA1 15:00 D-1, IDA2 22:00 D-1, IDA3 10:00 D (covers 12:00-24:00) | 15-min | 06/12 UTC runs, intraday updates |
| Continuous intraday (SIDC/XBID + local) | From afternoon D-1 until shortly before delivery (cross-border about 1 h before; within a German control area down to minutes before) | 15-min, 30-min, hourly, blocks | Nowcasts, rapid-update NWP, live plant data |
| Balancing / imbalance | After delivery | 15-min imbalance settlement (Germany: reBAP price) | You pay for whatever forecast error is left |

Since 2024/2025 the market has many more decision points per day, so a forecast pipeline that updates **every hour** (or faster) is normal for active traders.

## Who in trading uses weather, and how

| User | What they forecast | Typical horizon |
|---|---|---|
| **Direct marketers** (*Direktvermarkter*) | Production of each plant and the whole portfolio, in 15-min steps; curtail-or-not decisions at negative prices | 15 min to D+2 |
| **Utilities / balance groups** | Load + own generation + customers' PV | 15 min to D+7 |
| **Weather-driven traders** | Changes in country-level wind/solar/temperature between model runs ("the 12z ECMWF added 4 GW of wind for Thursday") and their price impact | D+1 to D+15 |
| **Gas and power fundamentals desks** | Heating/cooling degree days, residual load, hydro balance | D+1 to seasonal |
| **BESS optimisers** | Price spreads (DA, ID, balancing), co-located PV | D-1 to intraday |
| **Hydro producers** (Nordics, Alps) | Inflow, snow, reservoir levels | Weeks to months |
| **TSOs** | Infeed, load, reserves, cross-border flows | Minutes to D+7 |

Trading desks typically consume ECMWF (IFS HRES and ENS, now also AIFS), GFS/GEFS, ICON and vendor forecasts, and react to each new run. The **run-to-run change** ("delta") is often traded, not the absolute forecast.

## Price forecasting in brief

**Approaches:**
1. **Fundamental models**: build the supply stack (plants, fuel prices, CO2 price, availability from REMIT outage messages, interconnectors) and intersect with demand minus renewables. Tools: PyPSA, Antares (open source by RTE), PLEXOS, Aurora.
2. **Statistical / ML models**: regress price on residual load forecasts, gas/CO2 prices, calendar, lagged prices, cross-border data. Strong open benchmarks: LEAR (lasso-estimated autoregressive) and DNN in the [epftoolbox](https://github.com/jeslago/epftoolbox) (Lago et al. 2021).
3. **Hybrid**: fundamental model output as a feature for ML.

**Key features for a DA price model:** forecast load, wind and solar for the zone and neighbours, residual load, gas (TTF) and CO2 (EUA) prices, nuclear/thermal availability, hydro levels, calendar (holidays, weekends), and the last days' prices.

**Horizons:** intraday and D+1 (most accurate, weather forecast is good); balance-of-week (D+2 to D+7, weather still useful); next weeks/months (ensembles and climatology combined with forwards); long-term (fundamental scenarios run across 30+ historical weather years).

## Imbalance: where forecast error turns into money

If you sell a forecast volume day-ahead and the plant produces less, you're **short** and must buy the difference at the imbalance price; if it produces more, you're **long** and sell at the imbalance price.

Two important facts:
1. **Errors are correlated across the market.** When wind across Germany comes in lower than forecast, almost every wind marketer is short at the same time, the system is short, and the imbalance price goes up. Your own error tends to coincide with the market's error, so imbalance costs are higher than a naive "average spread × volume" estimate.
2. **The optimal bid is a quantile, not the mean** when penalties are asymmetric (chapter 6, newsvendor formula). That's why probabilistic forecasts have direct financial value.

## Germany-specific mechanics worth knowing

- **Direktvermarktung and market premium (*Marktprämie*)**: plants sell via a direct marketer and receive a sliding premium = guaranteed value (*anzulegender Wert*) minus the technology-specific market value (*Marktwert Solar / Wind an Land / Wind auf See*), published by the TSOs on netztransparenz.de.
- **Negative prices, §51 EEG**: for new plants (the 2025 *Solarspitzengesetz*, in force since 25 February 2025), no premium is paid for any negative-price quarter-hour; lost periods can be appended at the end of the support period. Older plants have different thresholds depending on their commissioning year. So your production forecast needs a **price forecast** to know when output is worthless or should be curtailed.
- **Redispatch 2.0**: grid-related curtailment with compensation of the lost energy; the curtailed energy also changes your balance group, so marketers need curtailment forecasts.
- **Imbalance price (reBAP)**: single 15-min price for Germany, published by the TSOs.

## A few other markets

- **Nordics (Nord Pool)**: hydro balance drives prices for months; weather forecasts of precipitation, snow and temperature matter more than wind for the long run.
- **UK**: half-hourly settlement; NESO and Elexon publish forecasts and actuals; wind drives prices.
- **US ISOs/RTOs** (ERCOT, CAISO, PJM, MISO, SPP): day-ahead markets clear hourly on the day before, real-time markets in 5-minute intervals. ERCOT is energy-only with scarcity pricing (Winter Storm Uri in February 2021 held prices at the 9,000 USD/MWh cap for days). CAISO is the textbook "duck curve" market.
- **Weather derivatives**: HDD/CDD futures (e.g. on CME) let utilities hedge temperature-driven demand.

## Formulas (summary; derivations in chapter 6)

$$\text{Revenue} = \sum_t q_t \, p_t$$

$$\text{Capture price} = \frac{\sum_t q_t \, p_t}{\sum_t q_t}, \qquad \text{Capture rate} = \frac{\text{Capture price}}{\overline{p}_{\text{baseload}}}$$

$$\text{Imbalance cost} \approx \sum_t (q^{\text{sold}}_t - q^{\text{actual}}_t)\,(p^{\text{imb}}_t - p^{\text{DA}}_t)$$

**Value of a better forecast (illustration):** a 100 MW wind portfolio whose day-ahead MAE drops from 10 % to 9 % of capacity has about 1 MW less average absolute error, i.e. about 8,760 MWh less imbalance volume per year. At an assumed 15 EUR per MWh of absolute imbalance, that's around 130,000 EUR/year. This is why marketers pay for multiple forecast vendors.
