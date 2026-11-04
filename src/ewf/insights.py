"""Derived results from a forecast frame: maintenance windows and clipping.

Pure computations on the 15-minute frame that ``forecast.run_forecast`` builds
(columns ``power_kw_<model>``, ``power_kw_blend``, ``power_kw_max`` and
``clearsky_ghi_wm2``, indexed by UTC period start).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ewf.resample import PERIOD

HOURS_PER_PERIOD = PERIOD / pd.Timedelta(hours=1)


def maintenance_windows(df: pd.DataFrame, duration_h: float = 4.0, top: int = 5,
                        not_before: pd.Timestamp | None = None, timezone: str = "UTC") -> list[dict]:
    """Daylight windows of ``duration_h`` with the least forecast energy.

    A window only counts if every period in it is in daylight (clear-sky GHI
    above zero), because field work needs daylight; night windows would always
    win with zero loss. Windows do not overlap: the best is taken first, then
    the best of the rest, and so on.

    Returns, per window, the UTC start and end, the blend energy that a stop
    would lose, the worst case (highest model, ``power_kw_max``) and the share
    of that local day's blend energy (``timezone`` is the plant's time zone).
    """
    n = int(round(duration_h / HOURS_PER_PERIOD))
    if n < 1 or len(df) < n:
        return []
    day = (df["clearsky_ghi_wm2"] > 0).to_numpy()
    blend = df["power_kw_blend"].to_numpy(dtype=float)
    upper = df["power_kw_max"].to_numpy(dtype=float)
    ok = day & np.isfinite(blend)
    if not_before is not None:
        ok &= (df.index >= not_before)
    energy = np.convolve(np.where(ok, blend, 0.0), np.ones(n), "valid") * HOURS_PER_PERIOD
    worst = np.convolve(np.where(ok, upper, 0.0), np.ones(n), "valid") * HOURS_PER_PERIOD
    valid = np.convolve(ok.astype(int), np.ones(n, dtype=int), "valid") == n
    # one window must also stay inside one daylight stretch (no jump over a night)
    idx = df.index
    contiguous = np.array([idx[i + n - 1] - idx[i] == PERIOD * (n - 1) for i in range(len(valid))])
    valid &= contiguous
    order = np.argsort(np.where(valid, energy, np.inf), kind="stable")
    taken = np.zeros(len(df), dtype=bool)
    local_dates = idx.tz_convert(timezone).date
    day_energy = (pd.Series(np.where(np.isfinite(blend), blend, 0.0) * HOURS_PER_PERIOD, index=idx)
                  .groupby(local_dates).sum())
    out = []
    for i in order:
        if not valid[i] or len(out) >= top:
            break
        if taken[i:i + n].any():
            continue
        taken[i:i + n] = True
        day_total = float(day_energy[local_dates[i]])
        out.append({
            "start_utc": idx[i],
            "end_utc": idx[i + n - 1] + PERIOD,
            "energy_kwh": float(energy[i]),
            "energy_kwh_worst": float(worst[i]),
            "share_of_day": float(energy[i] / day_total) if day_total > 0 else 0.0,
        })
    return out


def clipping(df: pd.DataFrame, ac_limit_kw: float, models: list[str], tolerance: float = 0.995) -> dict:
    """Periods at the AC or export limit, per model and for the blend.

    A period counts as clipped when power reaches ``tolerance`` times the limit.
    Returns hours at the limit and the first and last clipped period of the blend.
    """
    if not np.isfinite(ac_limit_kw):
        return {"limit_kw": None, "hours": {}, "first_utc": None, "last_utc": None}
    hours = {}
    for key in models + ["blend"]:
        col = df[f"power_kw_{key}"]
        hours[key] = float((col >= tolerance * ac_limit_kw).sum() * HOURS_PER_PERIOD)
    at = df.index[df["power_kw_blend"] >= tolerance * ac_limit_kw]
    return {"limit_kw": float(ac_limit_kw), "hours": hours,
            "first_utc": at.min() if len(at) else None, "last_utc": at.max() if len(at) else None}
