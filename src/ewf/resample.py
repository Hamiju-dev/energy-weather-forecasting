"""From model time steps (1 to 6 hours) to 15-minute periods.

Irradiance is interpolated through the clear-sky index, so that the daily
cycle comes from solar geometry and only the weather is interpolated, and
the energy of every model interval is preserved exactly. Temperature, wind
and cloud cover are interpolated linearly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pvlib

PERIOD = pd.Timedelta(minutes=15)
_EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def _secs(times) -> np.ndarray:
    """Seconds since 1970 as floats (independent of the pandas time unit)."""
    return np.asarray((pd.DatetimeIndex(times) - _EPOCH) / pd.Timedelta(seconds=1), dtype=float)


def clearsky_1min(latitude: float, longitude: float, altitude: float,
                  start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Ineichen-Perez clear-sky GHI (W/m2) at 1-minute resolution, labelled by minute start."""
    loc = pvlib.location.Location(latitude, longitude, tz="UTC", altitude=altitude)
    t = pd.date_range(start, end, freq="1min", inclusive="left")
    cs = loc.get_clearsky(t + pd.Timedelta(seconds=30), model="ineichen")
    return pd.Series(cs["ghi"].to_numpy(), index=t)


def to_15min(data: pd.DataFrame, latitude: float, longitude: float, altitude: float,
             start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Resample one model's point forecast to 15-minute periods in [start, end).

    ``data`` comes from :class:`ewf.weather.models.PointForecast`. The result is
    indexed by period start (UTC) and holds the mean over each period.
    """
    periods = pd.date_range(start, end, freq=PERIOD, inclusive="left", name="period_start_utc")
    mid = periods + PERIOD / 2
    first_interval_start = (pd.DatetimeIndex(data.index)
                            - pd.to_timedelta(data["interval_h"].fillna(0).to_numpy(), unit="h")).min()
    cs1 = clearsky_1min(latitude, longitude, altitude, min(first_interval_start, start), end)
    cs15 = cs1.resample(PERIOD, label="left", closed="left").mean().reindex(periods).fillna(0.0)

    # model intervals with radiation
    iv = data.dropna(subset=["ghi_wm2", "interval_h"])
    iv_end = pd.DatetimeIndex(iv.index)
    iv_start = pd.DatetimeIndex(iv_end - pd.to_timedelta(iv["interval_h"].to_numpy(), unit="h"))
    cs_iv = np.array([cs1[(cs1.index >= a) & (cs1.index < b)].mean() for a, b in zip(iv_start, iv_end)])
    with np.errstate(invalid="ignore", divide="ignore"):
        kc_iv = np.where(cs_iv > 10.0, iv["ghi_wm2"].to_numpy() / cs_iv, np.nan)
    iv_mid = iv_start + (iv_end - iv_start) / 2

    ok = ~np.isnan(kc_iv)
    x_mid = _secs(mid)
    if ok.any():
        kc15 = np.interp(x_mid, _secs(iv_mid)[ok], np.clip(kc_iv[ok], 0, 1.5))
    else:
        kc15 = np.zeros(len(periods))
    ghi15 = kc15 * cs15.to_numpy()

    # restore the energy of each model interval
    for a, b, g in zip(iv_start, iv_end, iv["ghi_wm2"].to_numpy()):
        inside = (mid > a) & (mid < b)
        if not inside.any():
            continue
        target = g * (b - a) / PERIOD                     # in units of (W/m2 x periods)
        frac = inside.sum() * PERIOD / (b - a)          # share of the interval inside the window
        target *= frac
        have = ghi15[inside].sum()
        if have > 1e-6:
            ghi15[inside] *= np.clip(target / have, 0.0, 5.0)
        elif target > 0:
            shape = cs15.to_numpy()[inside]
            if shape.sum() > 0:
                ghi15[inside] = target * shape / shape.sum()

    # instantaneous variables: linear in time; no extrapolation beyond the model steps
    out = pd.DataFrame(index=periods)
    out["ghi_wm2"] = ghi15
    out["clearsky_ghi_wm2"] = cs15.to_numpy()
    for col in ("temp_air_c", "wind_speed_ms", "cloud_cover_pct"):
        s = data[col].dropna()
        out[col] = np.interp(x_mid, _secs(s.index), s.to_numpy(),
                             left=np.nan, right=np.nan) if len(s) else np.nan
    covered = (mid > iv_start.min()) & (mid < iv_end.max()) if len(iv) else np.zeros(len(mid), bool)
    out.loc[~covered, "ghi_wm2"] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        out["clearsky_index"] = np.where(out.clearsky_ghi_wm2 > 10, out.ghi_wm2 / out.clearsky_ghi_wm2, np.nan)
    return out
