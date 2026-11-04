"""Compare a forecast with measured plant output (forecast vs actuals).

Pure computations: ``read_actuals`` turns a CSV text into a power series in kW,
``compare`` aligns it with the forecast frame and computes error measures.
"""

from __future__ import annotations

import io

import numpy as np
import pandas as pd

from ewf.resample import PERIOD


def read_actuals(text: str, timezone: str = "UTC") -> pd.Series:
    """Read measured AC power from CSV text.

    The first column that parses as dates is the time; it is taken as the
    START of each measuring period. Times without a zone are read in
    ``timezone``. The power column is the first numeric column whose name
    contains "power", "kw" or "mw", or else the first numeric column. Values
    are in kW, or in MW if the column name contains "mw".
    """
    df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    if df.empty:
        raise ValueError("the file has no rows")
    time_col = None
    for col in df.columns:
        if df[col].dtype.kind in "if":
            continue
        parsed = pd.to_datetime(df[col], errors="coerce", utc=False, format="mixed")
        if parsed.notna().mean() > 0.9:
            time_col, times = col, parsed
            break
    if time_col is None:
        raise ValueError("no column with dates and times found")
    numeric = [c for c in df.columns if c != time_col and pd.to_numeric(df[c], errors="coerce").notna().mean() > 0.9]
    if not numeric:
        raise ValueError("no numeric power column found")
    named = [c for c in numeric if any(k in str(c).lower() for k in ("power", "kw", "mw"))]
    col = (named or numeric)[0]
    values = pd.to_numeric(df[col], errors="coerce")
    if "mw" in str(col).lower() and "kw" not in str(col).lower():
        values = values * 1000.0
    idx = pd.DatetimeIndex(times)
    idx = idx.tz_localize(timezone, ambiguous="NaT", nonexistent="NaT") if idx.tz is None else idx
    s = pd.Series(values.to_numpy(), index=idx.tz_convert("UTC"), name=str(col)).dropna()
    s = s[s.index.notna()]
    s = s[~s.index.duplicated()].sort_index()
    if s.empty:
        raise ValueError("no valid rows after parsing")
    return s


def resolution(s: pd.Series) -> pd.Timedelta:
    """Median spacing of a series, at least 15 minutes."""
    if len(s) < 2:
        return PERIOD
    step = pd.Series(s.index).diff().median()
    return max(PERIOD, pd.Timedelta(step).round("min"))


def compare(df: pd.DataFrame, actual: pd.Series, models: list[str], capacity_dc_kwp: float) -> dict:
    """Error of each model and the blend against measured power.

    The forecast is averaged to the resolution of the measurements (15 minutes
    or coarser). Error measures use daylight periods only (clear-sky GHI above
    zero) where both forecast and measurement exist.
    """
    step = resolution(actual)
    keys = models + ["blend"]
    cols = [f"power_kw_{k}" for k in keys]
    fc = df[cols + ["clearsky_ghi_wm2"]].resample(step).mean()
    obs = actual.resample(step).mean()
    joined = fc.join(obs.rename("actual_kw"), how="inner")
    joined = joined[(joined["clearsky_ghi_wm2"] > 0) & joined["actual_kw"].notna()]
    hours = step / pd.Timedelta(hours=1)
    metrics = {}
    for k, c in zip(keys, cols):
        ok = joined[c].notna()
        err = (joined.loc[ok, c] - joined.loc[ok, "actual_kw"]).to_numpy()
        if not len(err):
            continue
        metrics[k] = {
            "n": int(len(err)),
            "mae_kw": float(np.mean(np.abs(err))),
            "rmse_kw": float(np.sqrt(np.mean(err ** 2))),
            "bias_kw": float(np.mean(err)),
            "nmae_pct_of_dc": float(100 * np.mean(np.abs(err)) / capacity_dc_kwp),
            "energy_forecast_kwh": float(joined.loc[ok, c].sum() * hours),
            "energy_actual_kwh": float(joined.loc[ok, "actual_kw"].sum() * hours),
        }
    return {
        "resolution_min": int(step / pd.Timedelta(minutes=1)),
        "periods": int(len(joined)),
        "first_utc": joined.index.min() if len(joined) else None,
        "last_utc": joined.index.max() if len(joined) else None,
        "metrics": metrics,
        "series": joined.drop(columns="clearsky_ghi_wm2"),
    }
