# 8. Where to get the data for free

Organised by what you need it for. Licences change; always re-check terms before commercial use. Short version of the licence situation is at the end.

## A. Real-time weather forecasts (raw model output)

| Source | What | Access | Licence / notes |
|---|---|---|---|
| **ECMWF Open Data** | IFS + AIFS (deterministic and ensemble), 0.25°, 4 runs/day | [data.ecmwf.int](https://www.ecmwf.int/en/forecasts/datasets/open-data), mirrors on AWS/Azure/Google; Python `ecmwf-opendata`, `earthkit` | CC-BY-4.0, commercial use allowed. Since 1 Oct 2025 the whole real-time catalogue is open; high-volume delivery has service charges |
| **NOAA GFS / GEFS / HRRR** | Global 0.25°, ensemble, US 3 km hourly | [NOMADS](https://nomads.ncep.noaa.gov), AWS Open Data (`noaa-gfs-bdp-pds`, `noaa-hrrr-bdp-pds`, ...); Python `herbie` | Public domain |
| **NOAA AIGFS / AIGEFS / HGEFS** | AI global models | NOAA NOMADS/NODD | Public domain |
| **DWD ICON, ICON-EU, ICON-D2 (+EPS, RUC)** | GRIB2 fields incl. direct/diffuse radiation, cloud levels, wind at many heights | [opendata.dwd.de](https://opendata.dwd.de/weather/nwp/) | Free incl. commercial use with source attribution. **Files are kept only about 24 hours, so archive them yourself** |
| **DWD MOSMIX** | Statistically optimised point forecasts for ~5,400 stations, 10 days, incl. global radiation, cloud, wind | opendata.dwd.de; Python `wetterdienst`; JSON wrapper [Bright Sky](https://brightsky.dev) | As above. Excellent free benchmark for Germany |
| **Météo-France** ARPEGE/AROME | Europe/France | [meteo.data.gouv.fr](https://meteo.data.gouv.fr) / portail-api | Open licence (Etalab) |
| **MET Norway** | MEPS, Locationforecast API | [api.met.no](https://api.met.no), THREDDS | CC-BY-4.0; send a proper User-Agent |
| **KNMI, DMI** | HARMONIE (NL, DK/DINI) | KNMI Data Platform, DMI Open Data | Open, registration for API keys |
| **CAMS** (Copernicus Atmosphere) | Aerosol/dust/AOD forecasts, 5 days | [Atmosphere Data Store](https://ads.atmosphere.copernicus.eu) | Free with registration |
| **DWD warnings, radar (RADOLAN/RADVOR), lightning** | Severe weather alerts, precipitation nowcasts | opendata.dwd.de | Free |

## B. Convenience APIs (easiest start)

| Source | What | Notes |
|---|---|---|
| **[Open-Meteo](https://open-meteo.com)** | Forecast API (ICON, ECMWF, GFS, AROME, ...), ensemble API, **Historical Forecast API** (stitched past forecasts since 2021), **Previous Runs API** (fixed lead times 1 to 7 days, since Jan 2024), **Single Runs API** (full single runs, since Sept 2025), Historical (ERA5) API, **Satellite Radiation API** (SARAH-3/Himawari-based, near real time) | **Free API is for non-commercial use only** (<10,000 calls/day). Commercial use needs a subscription ([terms](https://open-meteo.com/en/terms)) or self-hosting the open-source server. Radiation values are averages over the preceding hour |
| MET Norway Locationforecast | Point forecasts | Free, CC-BY |
| Bright Sky | DWD MOSMIX and observations as JSON | Free |

## C. Archived *as-issued* forecasts (essential for training)

You must train on forecasts as they were issued, not on what actually happened (chapter 9). Sources:

| Source | Coverage |
|---|---|
| Open-Meteo Historical Forecast / Previous Runs / Single Runs | Several models, since 2021 (stitched) / 2024 (fixed lead times) / 2025 (single runs) |
| NOAA GFS archive on AWS / NCEI | GFS since ~2015 (0.25°), longer at coarser resolution |
| HRRR archive on AWS | Since 2014 |
| GEFS v12 reforecast on AWS | 2000-2019 daily reforecasts, great for training ensemble post-processing |
| ECMWF Open Data cloud mirrors | Recent years of open data |
| TIGGE (ECMWF) | Multi-centre ensembles since 2006; **research/non-commercial only** |
| ECMWF MARS archive | Full archive; licence/fees for non-research use |
| **Your own archive** | Start a daily cron job now (DWD ICON-D2 and MOSMIX, ECMWF open data). Every month you wait is a month of training data you lose |

## D. Reanalysis (best estimate of past weather, gap-free)

| Dataset | Resolution | Period | Notes |
|---|---|---|---|
| **ERA5** (ECMWF/C3S) | 0.25°, hourly | 1940 to ~5 days ago | The global standard. [CDS](https://cds.climate.copernicus.eu), `cdsapi`; also ARCO Zarr copies on Google Cloud |
| ERA5-Land | 0.1°, hourly, land only | 1950 onward | Better for temperature/snow; not for offshore |
| CERRA | 5.5 km, Europe | 1984-2021 | European regional reanalysis, good for wind |
| COSMO-REA6 (DWD) | ~6 km, Europe | 1995-2019 | On DWD open data |
| MERRA-2 (NASA) | ~0.5° | 1980 onward | Used by Renewables.ninja; includes aerosols |
| NEWA | 3 km mesoscale, 50 m microscale | ~30 years | New European Wind Atlas time series |
| ERA6 | coming | first streams expected late 2027 ([ECMWF](https://www.ecmwf.int/node/38351)) | |

Reanalysis irradiance is weaker than satellite irradiance (clouds are modelled, not observed), so for solar use satellite data.

## E. Satellite irradiance and imagery

| Source | Coverage / resolution | Period | Access |
|---|---|---|---|
| **CM SAF SARAH-3** (EUMETSAT) | Europe, Africa, parts of S. America and Asia; 0.05°, 30 min | 1983 onward | [CM SAF](https://wui.cmsaf.eu); free registration |
| **CAMS Solar Radiation Time-series** (Heliosat-4) | MSG + Himawari disks, 1 min to monthly | 2004 onward | ADS / SoDa, free registration; also clear-sky (McClear) |
| **PVGIS** (EU JRC) | Hourly irradiance and PV simulation; SARAH-3 2005-2023 and ERA5 since v5.3 (Sept 2024), PVGIS 6 in preparation | | [PVGIS](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en), API, `pvlib.iotools` |
| **NSRDB** (US lab formerly called NREL, renamed National Laboratory of the Rockies in Dec 2025) | Americas and more, 4 km/30 min, 2 km/5 min recent | 1998 onward | Free API key |
| **NASA POWER** | Global ~0.5°, hourly from 2001, daily from 1981 | | Free API |
| Open-Meteo Satellite Radiation API | SARAH-3 based (Europe/Africa), Himawari (Asia/Australia); 10-15 min; low latency | | Free non-commercial |
| Raw imagery: EUMETSAT Data Store | MSG SEVIRI, **MTG FCI** (Meteosat-12, operational Dec 2024) | | Free registration |
| Raw imagery: GOES-East/West, Himawari | Americas, Asia-Pacific | | AWS Open Data, free |

## F. Ground observations

| Source | What |
|---|---|
| **DWD Climate Data Center** | Station data incl. 10-min global and diffuse radiation (subset of stations), wind, temperature, sunshine; free. Python `wetterdienst` |
| Meteostat | Global station data (hourly/daily), free API |
| NOAA ISD / GHCN | Global stations |
| **BSRN** | Highest-quality radiation stations worldwide (via PANGAEA, free registration). Use them to validate irradiance products |
| SURFRAD / SOLRAD (US) | High-quality radiation |
| **FINO1/2/3** | Offshore research masts in the North and Baltic Seas (free registration via BSH) |
| Tall towers (Cabauw, Hamburg weather mast, ...) | Wind profiles up to 200 m |
| Pegelonline | German river gauges (hydro), free API |

## G. Resource atlases and long-term simulations

| Source | What |
|---|---|
| [Global Solar Atlas](https://globalsolaratlas.info) | Long-term solar resource and PV yield maps, CC BY 4.0 |
| [Global Wind Atlas](https://globalwindatlas.info) | 250 m long-term mean wind, CC BY 4.0 |
| NEWA | European wind atlas + time series |
| [Renewables.ninja](https://www.renewables.ninja) | Simulated hourly PV and wind output for any location from MERRA-2/SARAH; free for non-commercial use (CC BY-NC) |
| PECD (ENTSO-E / C3S) | Pan-European Climate Database: decades of weather-year capacity factors per country |
| C3S Energy | Climate-energy indicators |

## H. Energy system and market data (targets, benchmarks, prices)

| Source | What | Notes |
|---|---|---|
| **[ENTSO-E Transparency Platform](https://transparency.entsoe.eu)** | Actual generation per type and zone, **TSO day-ahead wind/solar forecasts**, load and load forecasts, day-ahead prices, cross-border flows, imbalance, outages | Free, API token by email; Python `entsoe-py` |
| **[SMARD](https://www.smard.de)** (Bundesnetzagentur) | German generation, consumption, forecasts, prices, quarter-hourly | CC BY 4.0, download + JSON endpoints |
| **[Energy-Charts](https://www.energy-charts.info)** (Fraunhofer ISE) | Generation, prices, installed capacity, solar/wind maps; API | CC BY 4.0 |
| **[netztransparenz.de](https://www.netztransparenz.de)** | German TSOs: wind/solar extrapolations (Hochrechnung) and forecasts, market values (*Marktwerte*), reBAP imbalance price, Redispatch | Free downloads |
| regelleistung.net | German balancing reserve tenders | Free |
| **Elia Open Data** (Belgium) | Solar/wind forecasts at several horizons + measured, per region | Free; a great benchmark dataset |
| Energinet Energi Data Service (DK) | Production, prices, forecasts | Free API |
| RTE éCO2mix / ODRÉ (FR), Fingrid (FI), Elexon Insights + NESO (GB), Sheffield Solar PV_Live (GB PV) | National data | Free |
| EIA, CAISO OASIS, ERCOT, PJM Data Miner (US) | Generation, load, prices | Free |
| Ember | Global monthly/annual electricity data | Free |
| Open Power System Data | Cleaned European time series (archived, still useful) | Free |

Detailed intraday trade data and EEX forward curves are mostly paid; day-ahead prices are free via ENTSO-E, SMARD and Energy-Charts.

## I. Plant-level open datasets (to train and test models)

| Dataset | What |
|---|---|
| **Open Climate Fix** (HuggingFace) | UK PV system data; open-source solar forecasting models (Quartz Solar) |
| PVDAQ (US) | PV performance data on AWS |
| PVOutput.org | Community PV data (limited free access) |
| DKASC Alice Springs | Many PV technologies, free |
| Folsom dataset (Pedro et al. 2019) | Irradiance, sky images, satellite, NWP for benchmarking solar forecasts |
| SKIPP'D (Stanford) | Sky images + PV for nowcasting |
| **Kelmarsh and Penmanshiel wind farms** (Cubico, Zenodo) | 10-min SCADA of real UK wind farms 2016-2024, CC-BY-4.0 ([Kelmarsh v4](https://zenodo.org/records/16807551), [Penmanshiel](https://zenodo.org/records/16807304)) |
| GEFCom2014 | Competition data for wind, solar, load, price forecasting |
| WeatherBench 2 | Benchmark for global weather models |
| epftoolbox | Price forecasting benchmark datasets |

## J. Hydro, seasonal and climate

| Source | What |
|---|---|
| GloFAS / EFAS (Copernicus) | River discharge forecasts and reanalysis (EFAS real-time is partner-only; historical on CDS) |
| C3S seasonal (CDS) | Multi-system seasonal forecasts (ECMWF, Met Office, Météo-France, DWD, CMCC, NCEP, JMA, ECCC) |
| ECMWF extended range | Sub-seasonal (46 days); partly in open data |
| S2S database | Sub-seasonal reforecasts for research |
| CMIP6, EURO-CORDEX (CDS/ESGF), C3S Climate Atlas | Climate projections |

## K. Python tools to fetch it all

| Package | For |
|---|---|
| `openmeteo-requests` | Open-Meteo APIs |
| `wetterdienst` | DWD observations, MOSMIX, ICON point data, and more |
| `ecmwf-opendata`, `earthkit-data`, `earthkit-plots` | ECMWF open data |
| `herbie` | GFS, HRRR, GEFS, ECMWF open data and other GRIB archives |
| `cdsapi` | ERA5, CERRA, seasonal, CMIP6 (Copernicus CDS/ADS) |
| `xarray`, `cfgrib`/`eccodes`, `zarr`, `dask` | Reading and storing gridded data |
| `pvlib` (`pvlib.iotools`) | PVGIS, NSRDB, BSRN, CAMS, SURFRAD readers + all PV modelling |
| `entsoe-py` | ENTSO-E Transparency |
| `windpowerlib`, `PyWake`, `FLORIS` | Wind power, wakes |

## L. Paid providers (when free isn't enough)

Examples, not endorsements: Solcast, Solargis, Meteomatics, meteocontrol, enercast, energy & meteo systems, Meteotest (Meteonorm), Vortex, Whiffle, Dexter Energy, Spire, Tomorrow.io, DTN, Vaisala Xweather; for trading-focused weather: Atmospheric G2, Speedwell, Montel, LSEG, Volue Insight. They add value through higher-res satellite nowcasts, multi-model blends, SLAs and plant-specific tuning.

## Licence cheat sheet

| Data | Commercial use? |
|---|---|
| NOAA (GFS, HRRR, GOES, ...) | Yes, public domain |
| ECMWF Open Data | Yes, CC-BY-4.0 with attribution |
| DWD Open Data | Yes, with source attribution |
| Copernicus (ERA5, CAMS, CERRA, SARAH via CM SAF, ...) | Yes, Copernicus licence / EUMETSAT terms with attribution |
| PVGIS, NASA POWER | Yes |
| Open-Meteo **free API** | **No**, non-commercial only; subscription or self-hosting for business |
| Renewables.ninja | No (CC BY-NC) |
| TIGGE | No (research only) |
| ENTSO-E, SMARD, Energy-Charts | Generally yes with attribution; check each |

If this project is for work, budget for an Open-Meteo commercial plan or build the pipeline directly on DWD + ECMWF + NOAA open data (all commercially usable).
