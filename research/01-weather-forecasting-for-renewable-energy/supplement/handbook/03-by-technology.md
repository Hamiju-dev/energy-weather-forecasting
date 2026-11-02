# 3. What each renewable technology needs from the weather

Different technologies care about completely different weather variables. A great wind forecast model can be useless for PV and the other way round.

## Overview matrix

●●● = critical, ●● = important, ● = minor, blank = irrelevant

| Variable | PV | CSP | Onshore wind | Offshore wind | Hydro | BESS | Load / grid |
|---|---|---|---|---|---|---|---|
| GHI / DNI / DHI (irradiance) | ●●● | ●●● (DNI) | | | | ● (via PV) | ●● (behind-the-meter PV) |
| Cloud cover by level, cloud type | ●●● | ●●● | | | | | ● |
| Aerosols / dust / smoke (AOD) | ●● | ●●● | | | | | |
| Air temperature | ●● | ● | ●● (density, icing) | ● | ●● (snowmelt) | ●● (derating, HVAC) | ●●● |
| Wind speed at hub height (100 to 160 m) | ● (cooling, stow) | ● (heliostat stow) | ●●● | ●●● | | | ●● (line rating) |
| Wind direction, shear, veer, turbulence, stability | | | ●● | ●●● (wakes) | | | |
| Gusts / extreme wind | ●● (tracker stow) | ●● | ●● (cut-out) | ●● | | | ●● (outages) |
| Air pressure + humidity (density) | | | ●● | ●● | | | |
| Precipitation | ● (cleaning) | | ● (icing) | | ●●● | | ● |
| Snow (depth, fall, melt) | ●● | ● | ● | | ●●● | | ● |
| Hail | ●● (damage, stow) | ●● | ● | | | | |
| Lightning | ● (damage) | | ●● (blade damage) | ●● | | | ●● |
| Waves (Hs, period, direction) | | | | ●●● (access, installation) | | | |
| Fog / visibility | ●● (low stratus) | | ● (icing) | ●● (helicopter/vessel ops) | | | |
| Soil moisture, evaporation, river flow | | | | | ●●● | | |

## Solar PV

**What drives output:** plane-of-array (POA) irradiance, then module temperature, then everything that blocks or wastes light.

Key weather variables:
- **GHI, DNI, DHI.** NWP usually provides GHI (and often direct/diffuse). You need DNI/DHI to transpose onto tilted or tracking modules. If you only have GHI, use a decomposition model (Erbs, DIRINT, Engerer2; see chapter 6).
- **Cloud cover at low/mid/high levels**, cloud optical depth, cloud type. Low clouds (stratus/fog) block far more than high cirrus.
- **Aerosol optical depth (AOD)**: dust, smoke, pollution. CAMS provides free aerosol forecasts.
- **Air temperature and wind speed** for cell temperature: roughly -0.3 to -0.4 % power per °C above 25 °C for modern crystalline modules.
- **Snow**: snowfall, snow depth, temperature for melt/slide timing.
- **Albedo** (ground reflectance) for bifacial modules; snow raises albedo from ~0.2 to ~0.8.
- **Rain**: cleans soiled modules; long dry dusty periods cause soiling losses.
- **Wind gusts and hail** for single-axis trackers: stow strategies (flat for wind, steep for hail).

Plant specifics that change the forecast:
- Fixed tilt vs single-axis trackers (trackers flatten the daily curve and backtrack in the morning/evening).
- Bifacial gain, row spacing, shading.
- **DC/AC ratio and clipping**: a 1.3 DC/AC plant clips on clear days; forecasting the inverter limit correctly matters more than irradiance error at noon.
- Export limits and grid-operator setpoints (Redispatch, 60 % feed-in caps on small new systems in Germany under the 2025 *Solarspitzengesetz*).
- **Behind-the-meter / rooftop PV** has no telemetry: TSOs estimate it by upscaling from reference systems, and it appears as *reduced load*. That's why load forecasting now needs irradiance.

Hard situations: low stratus/fog, scattered convection, Saharan dust, snow, eclipses (deterministic, but the grid must plan for them, e.g. 20 March 2015 in Europe and 12 August 2026 over Spain).

## Concentrated solar power (CSP)

- Needs **DNI**, which is far more sensitive to aerosols and thin cirrus than GHI.
- Thermal storage turns it into a dispatchable plant, so the forecast feeds a dispatch optimisation (when to store, when to sell).
- Heliostat fields have wind stow limits.

## Onshore wind

**What drives output:** wind speed at hub height through a cubic-then-flat power curve, corrected for air density, turbulence and wakes.

Key variables:
- **Wind speed and direction at hub height** (100 to 170 m for modern turbines). NWP gives 10 m and often 100 m wind; extrapolate with shear (chapter 6) or use model levels.
- **Air density** (from temperature, pressure, humidity). Cold winter air at -10 °C is about 15 % denser than at +30 °C, which means roughly 15 % more power below rated speed.
- **Shear, veer, turbulence intensity and atmospheric stability**: power curves are measured in "normal" conditions; stable nights with high shear and low turbulence, or very turbulent conditions, shift real output away from the curve.
- **Direction**: wakes from neighbouring turbines and terrain depend on it.
- **Gusts and storm cut-out** (often 25 m/s, some turbines ramp down softly up to ~30 m/s).
- **Icing**: temperature around -10 °C to +1 °C with fog, low cloud or freezing rain. Causes power loss, shutdowns and ice-throw risk.
- **Low-level jets** (nocturnal wind maxima at 100 to 500 m, common over the North German Plain) are important and hard for NWP.

Weather-dependent curtailments you must model (very important in Germany):
- **Bat protection** (*Fledermausabschaltung*): turbines stop at night in warm months when wind is low (often below ~6 m/s) and temperature above ~10 °C, with no rain. Rules are permit-specific.
- **Shadow flicker**: depends on sun position, clear sky and nearby houses.
- **Noise-reduced modes** at night.
- **Bird protection** around mowing and harvesting.
- **Grid curtailment** (Redispatch 2.0), negative-price shutdowns.

## Offshore wind

Everything from onshore, plus:
- **Marine boundary layer**: lower turbulence means wakes persist longer; whole *cluster wakes* can reduce output of downwind farms tens of km away.
- **Sea surface temperature vs air temperature** decides stability (warm air over cold sea in spring creates very stable layers, high shear, long wakes).
- **Waves**: significant wave height (Hs), peak period, swell direction. Crew transfer vessels typically work up to about 1.5 to 2 m Hs, walk-to-work vessels higher. This drives O&M scheduling and installation.
- **Sea fog and visibility** for helicopters and vessels.
- **Lightning** (blade damage).
- **Storm cut-out of whole clusters**: gigawatts can drop within an hour, a major TSO risk.

## Hydropower

Weather acts through the catchment, with long delays:
- **Run-of-river**: river flow forecast from precipitation, upstream gauges and snowmelt. Horizon hours to ~2 weeks.
- **Reservoir**: inflow over weeks to months; **snowpack (snow water equivalent)**, spring melt timing, glacier melt, evaporation. Seasonal forecasts matter here more than anywhere else.
- **Pumped storage**: mostly price-driven, so weather enters via prices.
- Tools: rainfall-runoff models (HBV, GR4J, LISFLOOD), ensemble streamflow prediction, Copernicus GloFAS/EFAS.
- Nordic electricity prices are driven by the "hydrological balance" (snow + reservoir + groundwater vs normal), which is basically a weather forecast.

## Battery storage (BESS)

Weather is indirect but real:
- **Prices** are weather-driven (chapter 5), and a BESS optimiser lives on price spreads.
- **Co-located PV or wind**: forecast clipping to store energy that would be lost; forecast export-limit hits.
- **Temperature**: auxiliary HVAC consumption and power derating in heat; cold reduces available capacity.
- Forecast output for BESS is usually **scenarios** (many plausible price/production paths) for stochastic optimisation.

## Hybrid plants (PV + wind + BESS behind one grid connection)

Need **joint** forecasts that respect correlation (wind and solar are often anti-correlated seasonally and diurnally) and the shared grid connection limit.

## Other technologies

- **Bioenergy / biogas**: little weather dependence on supply; heat demand for CHP is temperature-driven.
- **Geothermal**: nearly constant; air-cooled binary plants lose efficiency in hot weather.
- **Tidal**: astronomical, predictable years ahead; weather adds storm surge effects.
- **Wave energy**: wave models (ECMWF WAM, NOAA WAVEWATCH III).
- **Electrolysers / green hydrogen**: run when power is cheap or renewable supply is high, so they consume renewable and price forecasts.

## Demand and grid (the other side of the balance)

- **Load**: temperature (heating and cooling degree days), cloudiness (lighting), humidity, wind chill, holidays. Heat pumps and EVs are making load more temperature-sensitive. In France, RTE's commonly quoted rule is about +2.4 GW of demand per -1 °C in winter.
- **Behind-the-meter PV** reduces measured load on sunny days (the "duck curve").
- **Dynamic line rating (DLR)**: overhead line capacity depends on wind cooling (especially perpendicular to the conductor), ambient temperature and solar heating. Windy days raise line capacity exactly when wind power needs to be transported. Standards: IEEE 738, CIGRE TB 601.
- **Extreme weather**: ice storms, wildfires (California's public-safety power shutoffs), floods, heatwaves (river cooling water limits for thermal plants).
