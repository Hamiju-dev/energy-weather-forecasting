# 7. Models, methods and simulations

## 1. Numerical weather prediction (NWP): the physics engine

An NWP model solves the equations of the atmosphere (conservation of momentum, mass, energy and moisture, the "primitive equations") on a 3D grid, stepping forward in time from an initial state.

The pieces:
- **Data assimilation**: blends millions of observations (satellites, aircraft, radiosondes, surface stations, radar) with the previous forecast to build the starting state (the *analysis*). Methods: 4D-Var (ECMWF), hybrid ensemble-variational, ensemble Kalman filters (DWD's LETKF for ICON).
- **Dynamical core**: solves the fluid equations on the grid.
- **Parameterisations**: processes smaller than a grid box are approximated: radiation, clouds and microphysics, convection, turbulence in the boundary layer, land surface, snow. **For energy, the radiation, cloud and boundary-layer schemes are where most errors come from.**
- **Ensembles**: the model is run many times with slightly perturbed initial conditions and physics (ECMWF ENS: 51 members; GEFS: 31; ICON-D2-EPS: 20). The spread estimates uncertainty.
- **Resolution**: global models ~9 to 25 km; regional "convection-permitting" models 1 to 3 km resolve thunderstorms explicitly (ICON-D2, AROME, HRRR, UKV, MEPS).

### Main operational models (status late 2026)

| Model | Centre | Grid | Range | Runs/day | Open data? |
|---|---|---|---|---|---|
| IFS HRES / ENS | ECMWF | 9 km (ENS 51 members) | 10 / 15 days | 4 | 0.25° subset free (CC-BY-4.0); whole real-time catalogue open since 1 Oct 2025, service fees for high-volume delivery ([ECMWF](https://www.ecmwf.int/en/forecasts/datasets/open-data)) |
| AIFS Single / AIFS ENS | ECMWF | ~0.25° (ML) | 15 days | 4 | Yes, CC-BY-4.0; operational Feb 2025 / Jul 2025 ([ECMWF](https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwfs-ensemble-ai-forecasts-become-operational)) |
| ECMWF extended range | ECMWF | ensemble | 46 days | daily | Partly |
| GFS / GEFS | NOAA | 0.25° / 31 members | 16 days (GEFS 35 days at 00 UTC) | 4 | Yes, public domain |
| AIGFS / AIGEFS / HGEFS | NOAA | AI (GraphCast-based), 31-member AI ensemble, 62-member hybrid | 16 days | 4 | Yes; operational since 17 Dec 2025 ([WMO](https://wmo.int/media/news/noaa-deploys-new-generation-of-ai-driven-global-weather-models)) |
| ICON (global) | DWD | ~13 km | 7.5 days | 4 | Yes |
| ICON-EU | DWD | ~6.5 km | 5 days | 8 | Yes |
| ICON-D2 / ICON-D2-EPS | DWD | ~2 km, Germany + neighbours | 48 h | 8 (every 3 h) | Yes |
| ICON-D2-RUC (rapid update) | DWD | ~2 km | ~12 to 14 h | hourly | Operational from 2025 |
| MOSMIX | DWD | ~5,400 stations (statistical post-processing) | 10 days | several | Yes; includes station global radiation forecasts |
| ARPEGE / AROME | Météo-France | ~5 km Europe / 1.3 km France | 4 days / 2 days | 4 / several | Yes |
| MEPS (HARMONIE-AROME) | MET Norway + partners | 2.5 km Nordics | 2.5 days | 8 | Yes |
| HARMONIE (KNMI, DMI) | KNMI, DMI | ~2 km | 2 to 2.5 days | 8+ | Yes |
| UKV / MOGREPS | Met Office | 1.5 to 2 km UK | ~5 days | many | Limited free tier |
| HRRR | NOAA | 3 km US | 18 h (48 h at 00/06/12/18) | hourly | Yes |
| CAMS global | ECMWF/Copernicus | ~40 km | 5 days | 2 | Yes: aerosols, dust, AOD |

### Regional downscaling yourself
- **Dynamical downscaling** with WRF (WRF-Solar is tuned for irradiance) or ICON-LAM: run a high-resolution model over your area, driven by a global model. Expensive, mostly worth it for complex terrain or research.
- **Statistical downscaling**: MOS, ML super-resolution, analog methods. Far cheaper and usually what businesses do.
- **Microscale flow models** for wind in complex terrain: linear models (WAsP), CFD (OpenFOAM, WindSim, Meteodyn), large-eddy simulation (PALM; GPU-based LES used commercially by Whiffle).

## 2. AI weather models

Since 2023, machine-learning models trained on decades of reanalysis (ERA5) produce global forecasts that match or beat physics models on many headline scores, in minutes on a single GPU.

| Model | Who | Type | Notes |
|---|---|---|---|
| Pangu-Weather | Huawei | 3D transformer | Nature 2023 |
| GraphCast | Google DeepMind | Graph neural network, deterministic | Science 2023; base of NOAA's AIGFS |
| FourCastNet | NVIDIA | Neural operator / transformer | Available in NVIDIA Earth2Studio |
| FuXi | Fudan Univ. | Cascaded transformer | |
| GenCast | Google DeepMind | Diffusion model, ensemble | Nature 2024/25 |
| NeuralGCM | Google | Hybrid physics + ML | Nature 2024 |
| Aurora | Microsoft | Foundation model (weather, air quality, waves) | Nature 2025 |
| AIFS Single / AIFS ENS | ECMWF | Graph transformer; ENS trained on CRPS | Operational 2025; open weights on HuggingFace; framework: Anemoi |
| WeatherNext 2 | Google DeepMind | Functional Generative Network, fast ensembles, hourly | Nov 2025 ([Google](https://blog.google/technology/google-deepmind/weathernext-2/)); data in Earth Engine/BigQuery |
| AIGFS / AIGEFS / HGEFS | NOAA | GraphCast-based; hybrid physical-AI ensemble | Operational Dec 2025 |

**For energy users, watch out for:**
- **Variables**: early AI models output only a few fields (no solar radiation, no 100 m wind). Check that the model gives what you need (surface solar radiation, 100 m wind, cloud cover).
- **Resolution**: mostly 0.25° and 6-hourly steps, too coarse for 15-min site forecasts without post-processing.
- **Smoothing**: deterministic ML models blur extremes at longer lead times; ensembles (AIFS ENS, GenCast, WeatherNext 2) handle this better.
- **They still depend on physics-based data assimilation** for their starting state.
- **Useful as extra members** in a multi-model blend; they are cheap and often skilful for synoptic wind.

Tools to run them yourself: ECMWF `ai-models` / Anemoi, NVIDIA Earth2Studio. Evaluation benchmark: WeatherBench 2.

## 3. Nowcasting (0 to 6 hours)

NWP starts slowly (spin-up) and arrives late, so for the next hours other methods win:

- **Satellite-based solar nowcasting**: geostationary images (Meteosat SEVIRI, now MTG FCI on Meteosat-12, operational since Dec 2024 with 1 km visible channels and faster scans; GOES; Himawari) are turned into a *cloud index*, then into irradiance (Heliosat method). Cloud motion vectors from optical flow (or ML like U-Nets/ConvLSTMs) advect clouds forward. Good to ~4 to 6 h.
- **Sky imagers**: fisheye cameras at the plant, seconds to ~20 min. For ramp control and hybrid plants.
- **Sensor networks**: upstream plants/pyranometers detect approaching clouds.
- **Radar** (e.g. DWD RADOLAN/RADVOR, free): precipitation, hail, convective cells.
- **Lightning detection** for storm tracking.
- **Rapid-update NWP**: ICON-D2-RUC (hourly), HRRR.
- **Statistical models on live data**: persistence of the clear-sky index, AR/ARIMA, gradient boosting on recent measurements.
- **Blending**: weight shifts from measurements/satellite (first hour) to NWP (later), often learned with ML per lead time.

## 4. Turning weather into power

### Physical chain (PV)
```
NWP GHI (+ DNI/DHI or decomposition)
  -> solar position (SPA)
  -> transposition to POA (Perez)
  -> IAM, soiling, snow, shading
  -> cell temperature (Faiman / SAPM)
  -> DC power (PVWatts / single diode)
  -> inverter efficiency + clipping
  -> AC losses, export limit, availability
```
Implementation: `pvlib` (ModelChain).

### Physical chain (wind)
```
NWP wind at 10/100 m or model levels + T, p, q
  -> interpolate to site, extrapolate to hub height (shear, stability)
  -> air density correction
  -> per-turbine power curve (+ wake model by direction)
  -> availability, curtailment rules (bat, noise, flicker, grid)
```
Implementation: `windpowerlib`, `PyWake`, `FLORIS`.

### Statistical / ML layer
- **Linear MOS**: robust, interpretable, good baseline.
- **Gradient boosting** (LightGBM, XGBoost, CatBoost): the industry workhorse for tabular NWP features; supports quantile objectives.
- **Random forests / quantile regression forests**: robust probabilistic baseline.
- **Neural networks**: MLPs; sequence models (LSTM/GRU, TCN); Transformers (Temporal Fusion Transformer, PatchTST); N-BEATS/N-HiTS; CNNs on NWP grid patches around the site; graph neural networks across many sites.
- **Time-series foundation models** (Chronos, TimesFM, Moirai and similar): zero-shot forecasting of univariate series. For weather-driven power they are only useful with weather covariates; on their own they can't know tomorrow's clouds.

**Typical features:** multiple NWP sources (GHI, DNI, DHI, cloud cover per level, temperature, wind at several heights, gusts, pressure, humidity, precipitation, snow), clear-sky GHI and clear-sky power, solar zenith/azimuth/AOI, lead time, hour/day-of-year (as sine/cosine), ensemble mean/spread, lagged measurements (only for intraday), physical model output, capacity/availability.

**Targets:** normalise by capacity (or clear-sky power for PV) so the model generalises across sites and capacity changes.

### Portfolio and regional forecasts
- **Upscaling**: forecast a set of representative reference plants and scale to the whole fleet (how TSOs estimate unmonitored rooftop PV).
- **Hierarchical reconciliation**: forecasts for plants, portfolios and regions that add up consistently (e.g. MinT reconciliation).

## 5. Probabilistic forecasting

| Method | Idea | Pros / cons |
|---|---|---|
| Raw NWP ensemble → power | Run each member through the power model | Physically consistent; usually under-dispersive, needs calibration |
| EMOS / NGR, BMA | Fit a parametric distribution to ensemble mean/spread | Simple, well-tested; parametric assumptions |
| Quantile regression (linear, GBM, QRF) | Learn each quantile directly | Flexible, standard in industry; quantiles can cross (sort them) |
| Distributional models (NGBoost, DeepAR, mixture density nets) | Predict distribution parameters | Full density; more complex |
| Analog ensemble (AnEn) | Find similar past forecasts, use what happened | Intuitive; needs long forecast archive |
| Conformal prediction | Wrap any model with calibrated intervals | Guaranteed coverage under assumptions; intervals not conditional by default |
| Scenario generation (Gaussian copula) | Combine marginal quantiles with a temporal/spatial correlation structure | Needed for BESS and stochastic optimisation, where a time path matters |

## 6. Combining models (blending)

Different NWP models fail differently. Blending 3 to 5 sources (e.g. ECMWF + ICON + GFS + AIFS + a high-res regional model) via weighted averages, stacking regression or as joint ML features usually beats the best single model. Weights can be static, per lead time, per season or dynamic (based on recent performance).

## 7. Simulations used across the industry

| Simulation | Purpose | Tools |
|---|---|---|
| Energy yield simulation | P50 production, loss breakdown | PVsyst, SAM, pvlib; WAsP, WindPRO, openWind |
| Wake simulation | Farm and cluster losses, layout, wake steering | FLORIS, PyWake |
| CFD / LES | Complex terrain flow, offshore cluster wakes | OpenFOAM, WindSim, Meteodyn, PALM |
| Mesoscale (WRF/ICON-LAM) | Wind atlases, downscaled time series | WRF, WRF-Solar, ICON |
| Monte Carlo uncertainty | P90/P99, revenue at risk, DSCR risk | Python/NumPy, @Risk |
| Weather-year resampling | Many plausible years for budgets, PPAs, adequacy | ERA5 or PECD with 30+ years |
| Weather-window / workability | Construction and offshore O&M schedule risk | Hindcast + Markov chain or year-resampling Monte Carlo |
| Hydrological models | River inflow, reservoir planning | HBV, GR4J, LISFLOOD; GloFAS/EFAS |
| Ice / snow / soiling models | Seasonal loss estimates | Makkonen icing, Marion snow, HSU/Kimber soiling |
| Power system / market models | Price forecasts, capture rates, adequacy | PyPSA, Antares, PLEXOS, Aurora |
| Battery dispatch optimisation | Arbitrage, co-located PV clipping recapture | Linear/mixed-integer programming (Pyomo, linopy), stochastic programming with scenarios |
| Climate impact | Long-term resource change | CMIP6, EURO-CORDEX, bias-adjusted delta methods |
| Stress tests | Dunkelflaute, heatwave, cold snap, dust event | Historical analogues, synthetic scenarios |
