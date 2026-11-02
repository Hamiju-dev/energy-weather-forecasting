"""Weather models, their archives, run selection and point extraction.

Supported models (all open data, commercial use allowed):

  ifs    ECMWF IFS, 0.25 deg, 3-hourly to 144 h (6-hourly beyond), CC-BY-4.0
  aifs   ECMWF AIFS Single (machine learning), 0.25 deg, 6-hourly, CC-BY-4.0
  gfs    NOAA GFS, 0.25 deg, hourly to 120 h (3-hourly beyond), public domain

For each model the latest run that covers the requested horizon is used, and
only the GRIB messages that are needed are downloaded (HTTP byte ranges).
"""

from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ewf.weather.grib import (Message, NotFound, PointDecoder, exists, http_get,
                              parse_ecmwf_index, parse_gfs_index)

ECMWF_MIRRORS = [
    "https://storage.googleapis.com/ecmwf-open-data",
    "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com",
    "https://data.ecmwf.int/forecasts",
]
GFS_MIRRORS = [
    "https://storage.googleapis.com/global-forecast-system",
    "https://noaa-gfs-bdp-pds.s3.amazonaws.com",
    "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod",
]


@dataclass(frozen=True)
class ModelSpec:
    key: str
    label: str
    kind: str                      # "ecmwf" or "gfs"
    path: str = ""                 # ECMWF: path inside a run folder
    runs_utc: tuple[int, ...] = (0, 6, 12, 18)
    attribution: str = ""
    licence: str = ""

    def steps(self, run_hour: int) -> list[int]:
        if self.key == "ifs":
            s = list(range(0, 145, 3))
            return s + list(range(150, 361, 6)) if run_hour in (0, 12) else s
        if self.key == "aifs":
            return list(range(0, 361, 6))
        if self.key == "gfs":
            return list(range(0, 121)) + list(range(123, 385, 3))
        raise ValueError(self.key)

    def urls(self, mirror: str, run: pd.Timestamp, step: int) -> tuple[str, str]:
        d, h = run.strftime("%Y%m%d"), run.strftime("%H")
        if self.kind == "ecmwf":
            base = f"{mirror}/{d}/{h}z/{self.path}/{d}{h}0000-{step}h-oper-fc"
            return base + ".index", base + ".grib2"
        base = f"{mirror}/gfs.{d}/{h}/atmos/gfs.t{h}z.pgrb2.0p25.f{step:03d}"
        return base + ".idx", base

    @property
    def mirrors(self) -> list[str]:
        return ECMWF_MIRRORS if self.kind == "ecmwf" else GFS_MIRRORS


MODELS: dict[str, ModelSpec] = {
    "ifs": ModelSpec("ifs", "ECMWF IFS", "ecmwf", "ifs/0p25/oper",
                     attribution="Contains modified ECMWF open data (IFS), (c) ECMWF", licence="CC-BY-4.0"),
    "aifs": ModelSpec("aifs", "ECMWF AIFS", "ecmwf", "aifs-single/0p25/oper",
                      attribution="Contains modified ECMWF open data (AIFS Single), (c) ECMWF", licence="CC-BY-4.0"),
    "gfs": ModelSpec("gfs", "NOAA GFS", "gfs",
                     attribution="NOAA NCEP Global Forecast System", licence="public domain"),
}

ECMWF_VARS = {"ssrd": "ssrd", "t2m": "2t", "u10": "10u", "v10": "10v", "tcc": "tcc"}
GFS_VARS = {"dswrf": ("DSWRF:surface", "avg"), "t2m": ("TMP:2 m above ground", "inst"),
            "u10": ("UGRD:10 m above ground", "inst"), "v10": ("VGRD:10 m above ground", "inst"),
            "tcc": ("TCDC:entire atmosphere", "inst")}


@dataclass
class ModelRun:
    spec: ModelSpec
    run: pd.Timestamp
    mirror: str
    steps: list[int]

    @property
    def label(self) -> str:
        return f"{self.spec.label} {self.run:%Y-%m-%d %H} UTC"


@dataclass
class PointForecast:
    """Raw model output at one point, at the model's own time steps.

    ``data`` is indexed by valid time (UTC) and has columns
    ``ghi_wm2`` (mean over the interval ending at that time; NaN at step 0),
    ``interval_h`` (length of that interval), ``temp_air_c``, ``wind_speed_ms``
    and ``cloud_cover_pct`` (instantaneous values at that time).
    """
    model: str
    run: pd.Timestamp
    data: pd.DataFrame
    meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------- run selection
def find_run(spec: ModelSpec, until: pd.Timestamp, now: pd.Timestamp | None = None,
             search_hours: int = 48) -> ModelRun:
    """Latest run of ``spec`` whose published steps reach ``until``."""
    now = (now or pd.Timestamp.now(tz="UTC")).floor("h")
    candidate = now.floor("6h")
    for _ in range(search_hours // 6 + 1):
        if candidate.hour in spec.runs_utc:
            steps = spec.steps(candidate.hour)
            need = (until - candidate) / pd.Timedelta(hours=1)
            covering = [s for s in steps if s >= need]
            if covering:
                last = covering[0]
                for mirror in spec.mirrors:
                    idx_url, _ = spec.urls(mirror, candidate, last)
                    if exists(idx_url):
                        return ModelRun(spec, candidate, mirror, [s for s in steps if s <= last])
        candidate -= pd.Timedelta(hours=6)
    raise RuntimeError(f"no {spec.label} run found that reaches {until:%Y-%m-%d %H:%M} UTC "
                       f"(searched {search_hours} h back from {now:%Y-%m-%d %H} UTC)")


# ---------------------------------------------------------------- extraction
def _fetch_step(mr: ModelRun, step: int, decode: PointDecoder) -> dict:
    idx_url, data_url = mr.spec.urls(mr.mirror, mr.run, step)
    text = http_get(idx_url).decode()
    if mr.spec.kind == "ecmwf":
        msgs = parse_ecmwf_index(text, ECMWF_VARS)
    else:
        msgs = parse_gfs_index(text, GFS_VARS, step)
    out: dict = {"step": step}
    for var, msg in msgs.items():
        values, units = decode(http_get(data_url, (msg.start, msg.end)))
        out[var] = (values, units, msg)
    return out


def fetch_points(mr: ModelRun, lats, lons, workers: int = 8) -> list[PointForecast]:
    """Download the needed messages of one run and return one PointForecast per point."""
    decode = PointDecoder(lats, lons)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda s: _fetch_step(mr, s, decode), mr.steps))
    results.sort(key=lambda r: r["step"])
    n = len(np.atleast_1d(lats))
    steps = [r["step"] for r in results]
    valid = pd.DatetimeIndex([mr.run + pd.Timedelta(hours=s) for s in steps], name="valid_time_utc")

    def series(var, convert=None):
        arr = np.full((len(results), n), np.nan)
        for i, r in enumerate(results):
            if var in r:
                vals, units, _ = r[var]
                arr[i] = convert(vals, units) if convert else vals
        return arr

    kelvin = lambda v, u: v - 273.15 if u == "K" else v
    percent = lambda v, u: v * 100.0 if u in ("(0 - 1)", "0-1", "Fraction") else v   # IFS: fraction; AIFS, GFS: %
    t2m = series("t2m", kelvin)
    wind = np.hypot(series("u10"), series("v10"))
    tcc = series("tcc", percent)

    if mr.spec.kind == "ecmwf":
        ghi, interval = deaccumulate(steps, series("ssrd"))
    else:
        windows = [r["dswrf"][2].avg_window if "dswrf" in r else None for r in results]
        ghi, interval = deaverage(steps, windows, series("dswrf"))

    out = []
    for p in range(n):
        df = pd.DataFrame({"ghi_wm2": ghi[:, p], "interval_h": interval,
                           "temp_air_c": t2m[:, p], "wind_speed_ms": wind[:, p],
                           "cloud_cover_pct": tcc[:, p]}, index=valid)
        out.append(PointForecast(mr.spec.key, mr.run, df,
                                 {"label": mr.spec.label, "mirror": mr.mirror, "steps": steps,
                                  "attribution": mr.spec.attribution, "licence": mr.spec.licence}))
    return out


# ---------------------------------------------------------------- radiation conventions
def deaccumulate(steps: list[int], accum_jm2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """ECMWF accumulations since the start of the run (J/m2) -> mean flux (W/m2)
    over each interval between consecutive steps. Row 0 is NaN."""
    steps = np.asarray(steps, dtype=float)
    acc = np.asarray(accum_jm2, dtype=float)
    out = np.full_like(acc, np.nan)
    interval = np.full(len(steps), np.nan)
    for i in range(1, len(steps)):
        dt = (steps[i] - steps[i - 1]) * 3600.0
        out[i] = (acc[i] - acc[i - 1]) / dt
        interval[i] = steps[i] - steps[i - 1]
    return np.clip(out, 0, None), interval


def deaverage(steps: list[int], windows: list[tuple[int, int] | None], avg_wm2: np.ndarray
              ) -> tuple[np.ndarray, np.ndarray]:
    """GFS averages over windows that restart every few hours -> mean flux over
    each interval between consecutive steps. Row 0 is NaN.

    If step i reports the mean over [a, b_i] and step i-1 the mean over [a, b_{i-1}]
    (same window start a), the mean over [b_{i-1}, b_i] is
    (A_i (b_i - a) - A_{i-1} (b_{i-1} - a)) / (b_i - b_{i-1}).
    """
    avg = np.asarray(avg_wm2, dtype=float)
    out = np.full_like(avg, np.nan)
    interval = np.full(len(steps), np.nan)
    for i in range(1, len(steps)):
        w, wp = windows[i], windows[i - 1]
        if w is None:
            continue
        a, b = w
        bp = steps[i - 1]
        if wp is not None and wp[0] == a and bp > a:
            out[i] = (avg[i] * (b - a) - avg[i - 1] * (bp - a)) / (b - bp)
        elif a == bp:
            out[i] = avg[i]
        else:
            continue
        interval[i] = b - bp
    return np.clip(out, 0, None), interval


def required_until(now: pd.Timestamp, hours: int) -> pd.Timestamp:
    return now.floor("h") + pd.Timedelta(hours=int(math.ceil(hours)))


__all__ = ["MODELS", "ModelSpec", "ModelRun", "PointForecast", "find_run", "fetch_points",
           "deaccumulate", "deaverage", "required_until", "NotFound", "Message"]
