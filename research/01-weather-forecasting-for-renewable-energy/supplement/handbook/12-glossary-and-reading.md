# 12. Glossary and reading list

## Glossary

| Term | Meaning |
|---|---|
| **AIFS** | ECMWF's Artificial Intelligence Forecasting System (deterministic "Single" and ensemble "ENS") |
| **Analysis** | Best estimate of the current atmosphere from data assimilation; starting point of a forecast |
| **AOD** | Aerosol optical depth: how much aerosol (dust, smoke) dims sunlight |
| **AOI** | Angle of incidence of sunlight on the module |
| **Ausfallarbeit** | Lost energy due to curtailment, compensated under Redispatch 2.0 (DE) |
| **Availability** | Share of time or energy a plant was able to produce |
| **Backtest** | Testing a model on historical periods as if in operation |
| **Balance group** (*Bilanzkreis*) | Accounting unit that must balance its schedule; deviations settled at imbalance price |
| **Capture price / rate** | Production-weighted average price; ratio to baseload price |
| **Clear-sky index (kc)** | GHI divided by clear-sky GHI |
| **Clipping** | Output limited by inverter/export capacity |
| **CRPS** | Continuous Ranked Probability Score: proper score for probabilistic forecasts |
| **Cut-out** | Wind speed above which turbines shut down (often ~25 m/s) |
| **DA / ID** | Day-ahead / intraday market |
| **Data assimilation** | Combining observations with a model to estimate the atmospheric state |
| **DHI / DNI / GHI** | Diffuse horizontal / direct normal / global horizontal irradiance |
| **Direktvermarktung** | Direct marketing: selling renewable output through a marketer who also forecasts and balances it (DE) |
| **Dunkelflaute** | Period of low wind and little sun, usually in winter |
| **EMOS** | Ensemble model output statistics: calibrating ensembles with a fitted distribution |
| **Ensemble** | Set of forecasts from perturbed starting conditions/physics to quantify uncertainty |
| **Ertragsausfall** | Yield loss: energy (and revenue) lost due to outages or curtailment |
| **EYA** | Energy yield assessment (pre-construction P50/P90 study) |
| **Gate closure** | Deadline for submitting bids for a market or time unit |
| **Hindcast / reforecast** | Running a forecast model on past dates, for training and verification |
| **Hochnebel** | Low stratus under an inversion (DE autumn/winter); a classic PV forecast failure |
| **Hochrechnung** | Real-time extrapolation of total wind/PV infeed from reference plants (TSOs) |
| **Hs** | Significant wave height |
| **IAV** | Interannual variability |
| **IDA** | Intraday auctions in SIDC (15:00 and 22:00 D-1, 10:00 D) |
| **Lead time** | Time between forecast issue and the valid time |
| **Marktprämie / Marktwert** | Market premium / monthly technology market value under the German EEG |
| **MCP** | Measure-correlate-predict: long-term correction of short on-site measurement campaigns |
| **Merit order** | Ranking of power plants by marginal cost, which sets the price |
| **MOS** | Model output statistics: statistical correction of NWP output |
| **MOSMIX** | DWD's MOS-based point forecasts for ~5,400 stations |
| **MTU** | Market time unit (15 min in the EU day-ahead market since 1 Oct 2025) |
| **Nowcasting** | Forecasting the next minutes to ~6 hours, mostly from observations |
| **NWP** | Numerical weather prediction |
| **P50 / P90** | Production level exceeded with 50 % / 90 % probability |
| **Persistence / smart persistence** | "Same as now" baseline / persisting the clear-sky index |
| **Pinball loss** | Proper score for a single quantile |
| **POA** | Plane-of-array irradiance (on the module surface) |
| **PR** | Performance ratio |
| **reBAP** | German single imbalance price (15 min) |
| **Redispatch 2.0** | German grid congestion management including renewables, with compensation |
| **Reanalysis** | Consistent reconstruction of past weather by a fixed model + assimilation (e.g. ERA5) |
| **Residual load** | Load minus wind and solar |
| **SDAC / SIDC** | Single day-ahead coupling / single intraday coupling (EU markets) |
| **Shear / veer** | Change of wind speed / direction with height |
| **Skill score** | Relative improvement over a reference forecast |
| **Solarspitzengesetz** | German 2025 law: no premium at negative prices for new PV, 60 % feed-in cap for small systems without smart meter |
| **TMY** | Typical meteorological year |
| **TSO / DSO** | Transmission / distribution system operator |
| **UTC / CET / CEST** | Universal time / Central European (summer) time |
| **Weather window** | Period long enough with conditions below operational limits |

## Reading list

### Foundations
- Murphy, A. H. (1993). *What is a good forecast? An essay on the nature of goodness in weather forecasting.* Weather and Forecasting 8(2).
- Gneiting, T. & Raftery, A. E. (2007). *Strictly proper scoring rules, prediction, and estimation.* JASA 102.
- Gneiting, T. & Katzfuss, M. (2014). *Probabilistic forecasting.* Annual Review of Statistics and Its Application.
- Hyndman, R. J. & Athanasopoulos, G. *Forecasting: Principles and Practice* (3rd ed.), free online at otexts.com/fpp3.
- Vannitsem, S. et al. (2021). *Statistical postprocessing for weather forecasts: review, challenges, and avenues in a big data world.* BAMS.

### Solar
- Yang, D. & Kleissl, J. (2024). *Solar Irradiance and Photovoltaic Power Forecasting.* CRC Press. (The most complete modern textbook.)
- Kleissl, J. (ed.) (2013). *Solar Energy Forecasting and Resource Assessment.* Academic Press.
- Antonanzas, J. et al. (2016). *Review of photovoltaic power forecasting.* Solar Energy 136.
- Yang, D. et al. (2022). *A review of solar forecasting, its dependence on atmospheric sciences and implications for grid integration.* Renewable and Sustainable Energy Reviews.
- Duffie, J. A. & Beckman, W. A. *Solar Engineering of Thermal Processes* (solar geometry).
- Holmgren, W. F., Hansen, C. W. & Mikofski, M. A. (2018). *pvlib python: a python package for modeling solar energy systems.* JOSS. Plus the pvlib documentation.
- NREL (now National Laboratory of the Rockies) *Best Practices Handbook for the Collection and Use of Solar Resource Data* (latest edition).
- IEA PVPS Task 16 reports on solar resource and forecasting.

### Wind
- Möhrlen, C., Zack, J. W. & Giebel, G. (eds.) *IEA Wind Recommended Practice for the Implementation of Renewable Energy Forecasting Solutions.* Academic Press. (From IEA Wind Task 36, now Task 51.)
- Giebel, G. et al. (2011). *The State-of-the-Art in Short-Term Prediction of Wind Power.* ANEMOS.plus.
- Pinson, P. (2013). *Wind energy: Forecasting challenges for its operational management.* Statistical Science 28(4).
- Burton, T. et al. *Wind Energy Handbook.* Wiley.

### Energy forecasting in general
- Hong, T. et al. (2016). *Probabilistic energy forecasting: Global Energy Forecasting Competition 2014 and beyond.* International Journal of Forecasting.
- Hong, T., Pinson, P. et al. (2020). *Energy forecasting: A review and outlook.* IEEE Open Access Journal of Power and Energy.

### Prices
- Weron, R. (2014). *Electricity price forecasting: A review of the state-of-the-art with a look into the future.* International Journal of Forecasting.
- Lago, J. et al. (2021). *Forecasting day-ahead electricity prices: A review of state-of-the-art algorithms, best practices and an open-access benchmark.* Applied Energy. (epftoolbox)

### Weather models and data
- Hersbach, H. et al. (2020). *The ERA5 global reanalysis.* QJRMS.
- Lam, R. et al. (2023). *Learning skillful medium-range global weather forecasting* (GraphCast). Science.
- Price, I. et al. *Probabilistic weather forecasting with machine learning* (GenCast). Nature.
- Lang, S. et al. (2024). *AIFS: ECMWF's data-driven forecasting system.* arXiv.
- Bodnar, C. et al. (2025). *A foundation model for the Earth system* (Aurora). Nature.
- Rasp, S. et al. (2024). *WeatherBench 2.* JAMES.

### Standards
- IEC 61724-1 (PV monitoring), IEC TS 61724-2:2025 (capacity test), IEC TS 61724-3 (energy test)
- ASTM E2848 (PV capacity test)
- IEC 61400-12-1:2022 (wind power performance), IEC 61400-15-1:2025 (site suitability), IEC 61400-26 (availability)
- ISO 9060:2018 (pyranometer classes)
- EN 1991-1-3 / 1-4 (snow / wind loads)
- IEEE 738, CIGRE TB 601 (line rating)

## Sources used for the time-sensitive facts in these notes

- ECMWF open data and full open catalogue: [ECMWF open data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [Science Business](https://sciencebusiness.net/network-updates/ecmwf-makes-its-entire-real-time-catalogue-open-all)
- AIFS ENS operational: [ECMWF news](https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwfs-ensemble-ai-forecasts-become-operational)
- NOAA AI models: [WMO](https://wmo.int/media/news/noaa-deploys-new-generation-of-ai-driven-global-weather-models)
- WeatherNext 2: [Google blog](https://blog.google/technology/google-deepmind/weathernext-2/)
- 15-min MTU in SDAC: [APG](https://markt.apg.at/en/news-press/sdac-go-live-of-15-minute-market-time-unit-in-day-ahead-market-coupling-successful-as-of-september-30-2025/), [EPEX SPOT](https://www.epexspot.com/en/news/market-coupling-steering-committee-confirms-go-live-15-minute-mtu-sdac-trading-day-30)
- Intraday auctions: [Nord Pool](https://support.nordpoolgroup.com/support/solutions/articles/8000111575-about-the-sidc-intraday-auctions-idas-), [NEMO Committee](https://www.nemo-committee.eu/ida)
- Negative prices 2025: [Bloomberg](https://www.bloomberg.com/news/articles/2026-01-05/europe-saw-record-surge-in-negative-power-prices-in-2025), [SMARD](https://www.smard.de/page/de/topic-article/5892/219038/rekord-bei-der-solarerzeugung-in-jedem-quartal), [pv magazine](https://www.pv-magazine.com/2025/08/26/germany-records-453-hours-of-year-to-date-negative-electricity-prices/)
- Solar capture rate May 2025: [S&P Global](https://www.spglobal.com/commodity-insights/en/news-research/latest-news/electric-power/061025-german-solar-capture-price-sinks-below-eur20mwh-in-may-as-cannibalization-deflates-value)
- Dunkelflaute price peaks: [SMARD](https://www.smard.de/en/study-of-electricity-price-peaks-completed-218346)
- Saharan dust and PV forecasts: [ACP 2017](https://acp.copernicus.org/articles/17/13391/2017/), [Clean Energy Wire](https://www.cleanenergywire.org/news/saharan-dust-cuts-solar-power-output-germany)
- Solarspitzengesetz: [Rödl & Partner](https://www.roedl.com/insights/das-solarspitzengesetz-zweitausendfuenfundzwanzig-wichtige-aenderungen-fuer-erneuerbare-energie-anlagen/), [pv magazine](https://www.pv-magazine.com/?p=40018)
- Redispatch 2.0 lost energy: [BDEW guide](https://www.bdew.de/service/anwendungshilfen/bdew-leitfaden-zur-berechnung-der-ausfallarbeit-redispatch-20/)
- Open-Meteo APIs and terms: [terms](https://open-meteo.com/en/terms), [Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api), [Historical Forecast API](https://openmeteo.substack.com/p/introducing-the-historical-forecast), [Satellite Radiation API](https://open-meteo.com/en/docs/satellite-radiation-api)
- ICON-D2-RUC: [wetterdienst.de](https://www.wetterdienst.de/Deutschlandwetter/Thema_des_Tages/6210/abbr-titleicosahedral-non-hydrostatic-general-circulation-modeliconabbr-ruc-wetterupdate-im-stundentakt)
- PVGIS 5.3: [EU JRC](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/pvgis-releases/pvgis-53_en)
- ERA6 timeline: [ECMWF Newsletter](https://www.ecmwf.int/node/38351)
- MTG / Meteosat-12: [Solcast](https://solcast.com/blog/eyes-in-the-sky-meteosat-third-generation-is-now-live-improving-solar-forecasting)
- NREL rename: [DOE](https://www.energy.gov/eere/articles/energy-department-renames-nrel-national-lab-rockies)
- IEC 61400-15-1:2025: [IEC webstore](https://webstore.iec.ch/en/publication/29169); IEC TS 61724-2:2025: [IEC webstore](https://webstore.iec.ch/en/publication/66710)
- German TSO wind/solar projections: [netztransparenz.de](https://netztransparenz.de/en/Renewable-energies-and-levies/Voluntary-publications/Wind-and-solar-energy-projection)
- Wind farm SCADA open data: [Kelmarsh](https://zenodo.org/records/16807551), [Penmanshiel](https://zenodo.org/records/16807304)
- Forecast accuracy benchmarks: [Visser et al.](https://research-portal.uu.nl/en/publications/benchmark-analysis-of-day-ahead-solar-power-forecasting-technique/), [WINDSAGE/UBIMET](https://www.ubimet.com/en/?p=13825)
- Crane wind limits: [Malin Group](https://malingroup.com/2026/01/16/specific-challenges-of-lifting-wind-turbine-generators/)
