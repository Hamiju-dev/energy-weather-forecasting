"""Run a forecast for one or more plants and collect the results."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from ewf.plant import Plant
from ewf.pv import simulate
from ewf.resample import PERIOD, to_15min
from ewf.weather.models import MODELS, ModelRun, PointForecast, fetch_points, find_run, required_until

DEFAULT_MODELS = ("ifs", "aifs", "gfs")


def cache_dir() -> Path:
    return Path(os.environ.get("EWF_CACHE_DIR", Path.home() / ".cache" / "ewf"))


@dataclass
class ForecastResult:
    plants: list[Plant]
    runs: dict[str, ModelRun]
    start: pd.Timestamp
    end: pd.Timestamp
    created: pd.Timestamp
    frames: dict[str, pd.DataFrame]
    problems: list[str] = field(default_factory=list)

    @property
    def models(self) -> list[str]:
        return list(self.runs)

    def power(self, plant_name: str) -> pd.DataFrame:
        cols = [f"power_kw_{m}" for m in self.models] + ["power_kw_blend", "power_kw_min", "power_kw_max"]
        return self.frames[plant_name][cols]

    def daily_energy(self, plant_name: str) -> pd.DataFrame:
        """Energy per local calendar day in kWh, per model and for the blend.

        ``complete`` is False for days that the forecast window covers only partly.
        """
        plant = next(p for p in self.plants if p.name == plant_name)
        df = self.frames[plant_name]
        local = df.index.tz_convert(plant.timezone)
        cols = [f"power_kw_{m}" for m in self.models] + ["power_kw_blend"]
        energy = (df[cols] * PERIOD / pd.Timedelta(hours=1)).groupby(local.date).sum(min_count=1)
        energy.columns = [c.replace("power_kw_", "energy_kwh_") for c in cols]
        # a day is complete when every daylight period of that local day is in the window
        daylight = (df["clearsky_ghi_wm2"] > 0).groupby(local.date).sum()
        covered = (df["power_kw_blend"].notna() & (df["clearsky_ghi_wm2"] > 0)).groupby(local.date).sum()
        first_day, last_day = local.min().date(), local.max().date()
        starts_mid_day = (local.min().hour, local.min().minute) != (0, 0)
        ends_mid_day = (local.max() + PERIOD).time() != pd.Timestamp("00:00").time()
        complete = []
        for d in energy.index:
            ok = covered.get(d, 0) >= daylight.get(d, 0)
            if d == first_day and starts_mid_day:
                ok = ok and _daylight_starts_after(df, local, d)
            if d == last_day and ends_mid_day:
                ok = ok and _daylight_ends_before(df, local, d)
            complete.append(bool(ok))
        energy["complete"] = complete
        energy["specific_yield_kwh_per_kwp"] = energy["energy_kwh_blend"] / plant.capacity_dc_kwp
        energy.index.name = "date_local"
        return energy

    def run_table(self) -> pd.DataFrame:
        return pd.DataFrame([{"model": k, "label": r.spec.label, "run_utc": r.run, "last_step_h": r.steps[-1],
                              "source": r.mirror, "licence": r.spec.licence} for k, r in self.runs.items()])


def _daylight_starts_after(df: pd.DataFrame, local: pd.DatetimeIndex, d) -> bool:
    """True if the window starts before sunrise on local day d."""
    day = df[local.date == d]
    return bool(len(day)) and day["clearsky_ghi_wm2"].iloc[0] == 0


def _daylight_ends_before(df: pd.DataFrame, local: pd.DatetimeIndex, d) -> bool:
    """True if the window ends after sunset on local day d."""
    day = df[local.date == d]
    return bool(len(day)) and day["clearsky_ghi_wm2"].iloc[-1] == 0


def _periods_in_local_day(d, tz: str) -> int:
    """Number of 15-minute periods in a local calendar day (92, 96 or 100 with DST)."""
    start = pd.Timestamp(d).tz_localize(tz)
    end = (pd.Timestamp(d) + pd.Timedelta(days=1)).tz_localize(tz)
    return int((end - start) / PERIOD)


# ---------------------------------------------------------------- weather with a disk cache
def _cache_key(mr: ModelRun, lat: float, lon: float) -> Path:
    tag = f"{mr.spec.key}_{mr.run:%Y%m%d%H}_{mr.steps[-1]:03d}_{lat:.4f}_{lon:.4f}"
    return cache_dir() / "points" / (hashlib.sha1(tag.encode()).hexdigest()[:16] + f"_{tag}.csv")


def get_point_forecasts(mr: ModelRun, plants: list[Plant], use_cache: bool = True) -> list[PointForecast]:
    paths = [_cache_key(mr, p.latitude, p.longitude) for p in plants]
    if use_cache and all(p.exists() for p in paths):
        return [PointForecast(mr.spec.key, mr.run, pd.read_csv(p, index_col=0, parse_dates=True),
                              {"label": mr.spec.label, "mirror": mr.mirror, "steps": mr.steps, "cached": True})
                for p in paths]
    pfs = fetch_points(mr, [p.latitude for p in plants], [p.longitude for p in plants])
    if use_cache:
        for pf, path in zip(pfs, paths):
            path.parent.mkdir(parents=True, exist_ok=True)
            pf.data.to_csv(path)
    return pfs


# ---------------------------------------------------------------- main entry point
def latest_runs(models=DEFAULT_MODELS, hours: int = 72, now: pd.Timestamp | None = None) -> dict[str, ModelRun]:
    """Latest available run of each model that reaches ``hours`` ahead (only index lookups, no downloads)."""
    now = (now or pd.Timestamp.now(tz="UTC"))
    until = required_until(now, hours)
    out = {}
    for key in models:
        try:
            out[key] = find_run(MODELS[key], until, now)
        except Exception:  # a missing model is reported by run_forecast
            continue
    return out


def run_forecast(plants: list[Plant], hours: int = 72, models=DEFAULT_MODELS, now: pd.Timestamp | None = None,
                 use_cache: bool = True, progress: Callable[[str], None] | None = None,
                 run_before: dict[str, pd.Timestamp] | None = None) -> ForecastResult:
    """Forecast 15-minute AC power for each plant from the latest model runs.

    The window starts at the most recent run time among the models used and
    ends ``hours`` after the current hour. ``run_before`` maps a model to a run
    time; that model then uses the latest run before it (for run-to-run
    comparisons).
    """
    say = progress or (lambda msg: None)
    now = (now or pd.Timestamp.now(tz="UTC"))
    until = required_until(now, hours)
    runs, problems = {}, []
    for key in models:
        spec = MODELS[key]
        say(f"Looking for the latest {spec.label} run...")
        try:
            before = (run_before or {}).get(key)
            runs[key] = find_run(spec, until, now if before is None else before - pd.Timedelta(hours=1))
            say(f"{spec.label}: run {runs[key].run:%Y-%m-%d %H} UTC, steps up to {runs[key].steps[-1]} h")
        except Exception as exc:  # keep the other models
            problems.append(f"{spec.label}: {exc}")
            say(f"{spec.label}: not available ({exc})")
    if not runs:
        raise RuntimeError("no model run could be found: " + "; ".join(problems))

    start = max(r.run for r in runs.values())
    point_data: dict[str, list[PointForecast]] = {}
    for key, mr in runs.items():
        say(f"Downloading {mr.spec.label} ({len(mr.steps)} time steps)...")
        try:
            point_data[key] = get_point_forecasts(mr, plants, use_cache)
        except Exception as exc:
            problems.append(f"{mr.spec.label}: download failed ({exc})")
            say(f"{mr.spec.label}: download failed ({exc})")
    runs = {k: v for k, v in runs.items() if k in point_data}
    if not runs:
        raise RuntimeError("all downloads failed: " + "; ".join(problems))

    frames = {}
    for i, plant in enumerate(plants):
        say(f"Computing power for {plant.name}...")
        frames[plant.name] = _combine(plant, {k: v[i] for k, v in point_data.items()}, start, until)
    return ForecastResult(plants, runs, start, until, pd.Timestamp.now(tz="UTC"), frames, problems)


def _combine(plant: Plant, pfs: dict[str, PointForecast], start, end) -> pd.DataFrame:
    parts, weather = {}, {}
    for key, pf in pfs.items():
        w = to_15min(pf.data, plant.latitude, plant.longitude, plant.altitude_m, start, end)
        weather[key] = w
        parts[key] = simulate(plant, w)
    idx = next(iter(weather.values())).index
    out = pd.DataFrame(index=idx)
    out["period_end_utc"] = idx + PERIOD
    out["period_start_local"] = idx.tz_convert(plant.timezone).strftime("%Y-%m-%d %H:%M")
    out["clearsky_ghi_wm2"] = next(iter(weather.values()))["clearsky_ghi_wm2"]
    for key in pfs:
        out[f"ghi_wm2_{key}"] = weather[key]["ghi_wm2"]
    for key in pfs:
        out[f"power_kw_{key}"] = parts[key]["p_ac_kw"]
    p = out[[f"power_kw_{k}" for k in pfs]]
    out["power_kw_blend"] = p.mean(axis=1)
    out["power_kw_min"] = p.min(axis=1)
    out["power_kw_max"] = p.max(axis=1)
    out["ghi_wm2_blend"] = out[[f"ghi_wm2_{k}" for k in pfs]].mean(axis=1)
    out["poa_wm2_blend"] = pd.concat([parts[k]["poa_wm2"] for k in pfs], axis=1).mean(axis=1)
    out["cell_temp_c_blend"] = pd.concat([parts[k]["cell_temp_c"] for k in pfs], axis=1).mean(axis=1)
    for col in ("temp_air_c", "wind_speed_ms", "cloud_cover_pct"):
        out[f"{col}_blend"] = pd.concat([weather[k][col] for k in pfs], axis=1).mean(axis=1)
    out["models_available"] = p.notna().sum(axis=1)
    out.loc[out.models_available == 0, ["power_kw_blend", "power_kw_min", "power_kw_max"]] = np.nan
    return out
