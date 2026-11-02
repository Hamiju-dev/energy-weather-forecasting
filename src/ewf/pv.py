"""Weather to PV power: the physical model chain (pvlib).

GHI -> Erbs decomposition -> Perez transposition (fixed or single-axis
tracking) -> ASHRAE incidence-angle loss on the beam -> Faiman cell
temperature -> PVWatts DC power -> system losses -> inverter (PVWatts
efficiency curve, clipping at the AC capacity) -> export limit.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pvlib

from ewf.plant import Plant
from ewf.resample import PERIOD


def simulate(plant: Plant, weather: pd.DataFrame) -> pd.DataFrame:
    """Power for each 15-minute period. ``weather`` is indexed by period start
    and has ``ghi_wm2``, ``temp_air_c`` and ``wind_speed_ms``."""
    mid = weather.index + PERIOD / 2
    loc = pvlib.location.Location(plant.latitude, plant.longitude, tz="UTC", altitude=plant.altitude_m)
    sp = loc.get_solarposition(mid)
    ghi = weather["ghi_wm2"].to_numpy()
    temp = weather["temp_air_c"].to_numpy()
    wind = weather["wind_speed_ms"].to_numpy()

    erbs = pvlib.irradiance.erbs(pd.Series(ghi, index=mid).fillna(0), sp["zenith"], mid)
    dni, dhi = erbs["dni"].fillna(0), erbs["dhi"].fillna(0)

    if plant.tracking == "single_axis":
        tr = pvlib.tracking.singleaxis(sp["apparent_zenith"], sp["azimuth"], axis_tilt=0,
                                       axis_azimuth=plant.axis_azimuth_deg, max_angle=plant.max_angle_deg,
                                       backtrack=plant.backtrack, gcr=plant.gcr)
        tilt = tr["surface_tilt"].fillna(0.0)
        azimuth = tr["surface_azimuth"].fillna(plant.axis_azimuth_deg + 90)
    else:
        tilt, azimuth = plant.tilt_deg, plant.azimuth_deg

    dni_extra = pvlib.irradiance.get_extra_radiation(mid)
    airmass = pvlib.atmosphere.get_relative_airmass(sp["apparent_zenith"], model="kastenyoung1989")
    poa = pvlib.irradiance.get_total_irradiance(
        tilt, azimuth, sp["apparent_zenith"], sp["azimuth"], dni, pd.Series(ghi, index=mid).fillna(0), dhi,
        dni_extra=dni_extra, airmass=airmass, albedo=plant.albedo, model="perez")
    aoi = pvlib.irradiance.aoi(tilt, azimuth, sp["apparent_zenith"], sp["azimuth"])
    iam = pvlib.iam.ashrae(aoi, b=0.05)
    poa_global = poa["poa_global"].fillna(0).clip(lower=0)
    poa_eff = (poa["poa_direct"].fillna(0) * iam + poa["poa_diffuse"].fillna(0)).clip(lower=0)

    t_cell = pvlib.temperature.faiman(poa_global, pd.Series(temp, index=mid), pd.Series(wind, index=mid),
                                      u0=plant.temp_u0, u1=plant.temp_u1)
    p_dc = pvlib.pvsystem.pvwatts_dc(poa_eff, t_cell, plant.capacity_dc_kwp, plant.gamma_pdc_per_k)
    p_dc = (p_dc * (1 - plant.system_losses_pct / 100)).clip(lower=0)

    if plant.capacity_ac_kw is not None:
        p_ac = pvlib.inverter.pvwatts(p_dc, pdc0=plant.capacity_ac_kw / plant.inverter_efficiency,
                                      eta_inv_nom=plant.inverter_efficiency)
    else:
        p_ac = p_dc * plant.inverter_efficiency
    p_ac = np.minimum(p_ac.clip(lower=0), plant.ac_limit_kw)

    out = pd.DataFrame({
        "poa_wm2": poa_global.to_numpy(),
        "cell_temp_c": t_cell.to_numpy(),
        "p_dc_kw": p_dc.to_numpy(),
        "p_ac_kw": np.asarray(p_ac, dtype=float),
    }, index=weather.index)
    missing = weather["ghi_wm2"].isna().to_numpy()
    out.loc[missing, :] = np.nan
    return out
