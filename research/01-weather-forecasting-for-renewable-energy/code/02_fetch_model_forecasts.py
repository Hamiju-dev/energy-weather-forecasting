"""Step 2: extract model forecasts at the station locations.

For every 00 UTC run in the study period and every lead time in config.STEPS_H,
the script reads the GRIB2 index of ECMWF IFS, ECMWF AIFS Single and NOAA GFS,
downloads only the needed messages (10 m wind components and 2 m temperature)
with HTTP byte-range requests, interpolates them bilinearly to each candidate
station and discards the global field. Only the point values are kept.

Inputs  : ECMWF open data (CC-BY-4.0), Google Cloud mirror
          NOAA GFS archive (public domain), Google Cloud mirror
          data/interim/station_candidates.csv
Outputs : data/cache/forecast-point-values/<model>/<YYYYMMDD>.csv   one file per run (not versioned)
          data/interim/forecast_point_values_<model>.csv.gz        all runs of a model (versioned)
          data/raw/forecast-download-manifest.csv.gz              URL, byte range, size, SHA-256

The script is resumable: runs whose cache file exists are skipped.
"""

from __future__ import annotations

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import eccodes
import numpy as np
import pandas as pd

import config as C
from common import Manifest, http_get

MANIFEST = Manifest(C.CACHE_DIR / "forecast-download-manifest.csv")


# ---------------------------------------------------------------- indexes
def ecmwf_urls(model_path: str, run: pd.Timestamp, step: int) -> tuple[str, str]:
    d, h = run.strftime("%Y%m%d"), run.strftime("%H")
    base = f"{C.ECMWF_OPEN_DATA}/{d}/{h}z/{model_path}/{d}{h}0000-{step}h-oper-fc"
    return base + ".index", base + ".grib2"


def ecmwf_ranges(index_text: str, wanted: dict[str, str]) -> dict[str, tuple[int, int]]:
    out = {}
    for line in index_text.splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("levtype") != "sfc":
            continue
        for var, param in wanted.items():
            if rec["param"] == param:
                out[var] = (rec["_offset"], rec["_offset"] + rec["_length"] - 1)
    return out


def gfs_urls(run: pd.Timestamp, step: int) -> tuple[str, str]:
    d, h = run.strftime("%Y%m%d"), run.strftime("%H")
    base = f"{C.GFS_ARCHIVE}/gfs.{d}/{h}/atmos/gfs.t{h}z.pgrb2.0p25.f{step:03d}"
    return base + ".idx", base


def gfs_ranges(index_text: str, wanted: dict[str, str], step: int) -> dict[str, tuple[int, int]]:
    lines = [l for l in index_text.splitlines() if l.strip()]
    lead = "anl" if step == 0 else f"{step} hour fcst"
    out = {}
    for i, line in enumerate(lines):
        parts = line.split(":")
        key = f"{parts[3]}:{parts[4]}"
        for var, want in wanted.items():
            if key == want and parts[5] == lead and var not in out:
                start = int(parts[1])
                end = int(lines[i + 1].split(":")[1]) - 1 if i + 1 < len(lines) else None
                out[var] = (start, end)
    return out


# ---------------------------------------------------------------- grids
class PointInterpolator:
    """Bilinear interpolation weights from a regular lat-lon GRIB grid to points."""

    def __init__(self, gid, lats: np.ndarray, lons: np.ndarray):
        g = lambda k: eccodes.codes_get(gid, k)
        self.ni, self.nj = g("Ni"), g("Nj")
        la1, lo1 = g("latitudeOfFirstGridPointInDegrees"), g("longitudeOfFirstGridPointInDegrees")
        di, dj = g("iDirectionIncrementInDegrees"), g("jDirectionIncrementInDegrees")
        dlat = -dj if g("jScansPositively") == 0 else dj
        dlon = -di if g("iScansNegatively") == 1 else di
        fi = ((lons - lo1) % 360.0) / dlon
        fj = (lats - la1) / dlat
        i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
        wi, wj = fi - i0, fj - j0
        i1 = (i0 + 1) % self.ni
        self.idx = np.stack([j0 * self.ni + i0, j0 * self.ni + i1,
                             (j0 + 1) * self.ni + i0, (j0 + 1) * self.ni + i1])
        self.w = np.stack([(1 - wi) * (1 - wj), wi * (1 - wj), (1 - wi) * wj, wi * wj])
        self.signature = (self.ni, self.nj, la1, lo1, di, dj)

    def __call__(self, values: np.ndarray) -> np.ndarray:
        return (values[self.idx] * self.w).sum(axis=0)


_interp_cache: dict = {}
_decode_lock = threading.Lock()  # ecCodes handles are decoded one at a time


def decode_points(msg: bytes, lats: np.ndarray, lons: np.ndarray) -> tuple[np.ndarray, str]:
    with _decode_lock:
        return _decode_points(msg, lats, lons)


def _decode_points(msg: bytes, lats: np.ndarray, lons: np.ndarray) -> tuple[np.ndarray, str]:
    gid = eccodes.codes_new_from_message(msg)
    try:
        sig = tuple(eccodes.codes_get(gid, k) for k in (
            "Ni", "Nj", "latitudeOfFirstGridPointInDegrees", "longitudeOfFirstGridPointInDegrees"))
        if sig not in _interp_cache:
            _interp_cache[sig] = PointInterpolator(gid, lats, lons)
        values = eccodes.codes_get_values(gid)
        units = eccodes.codes_get(gid, "units")
        return _interp_cache[sig](values), units
    finally:
        eccodes.codes_release(gid)


# ---------------------------------------------------------------- one run
def process_run(model: str, run: pd.Timestamp, stations: pd.DataFrame) -> pd.DataFrame:
    spec = C.MODELS[model]
    lats, lons = stations.latitude.to_numpy(), stations.longitude.to_numpy()
    records = []
    for step in C.STEPS_H:
        if spec["kind"] == "ecmwf":
            idx_url, data_url = ecmwf_urls(spec["path"], run, step)
            idx_text = http_get(idx_url).decode()
            ranges = ecmwf_ranges(idx_text, spec["params"])
        else:
            idx_url, data_url = gfs_urls(run, step)
            idx_text = http_get(idx_url).decode()
            ranges = gfs_ranges(idx_text, spec["params"], step)
        missing = set(spec["params"]) - set(ranges)
        if missing:
            raise RuntimeError(f"{model} {run} +{step}h: missing {missing}")
        row = {"station_id": stations.station_id.to_numpy()}
        for var, rng in ranges.items():
            msg = http_get(data_url, rng)
            MANIFEST.add(data_url, msg, rng, note=f"{model} {var} +{step}h")
            vals, units = decode_points(msg, lats, lons)
            if var == "t2m":
                vals = vals - 273.15 if units == "K" else vals
            row[var] = vals
        df = pd.DataFrame(row)
        df.insert(0, "step_h", step)
        records.append(df)
    out = pd.concat(records, ignore_index=True)
    out.insert(0, "init_time_utc", run.strftime("%Y-%m-%dT%H:%M:%SZ"))
    out.insert(0, "model", model)
    return out


def main(models: list[str]) -> None:
    stations = pd.read_csv(C.INTERIM_DIR / "station_candidates.csv")
    runs = pd.date_range(C.INIT_FIRST, C.INIT_LAST, freq="D", tz="UTC") + pd.Timedelta(hours=C.INIT_HOUR_UTC)
    jobs = []
    for model in models:
        out_dir = C.FORECAST_PARTS_DIR / model
        out_dir.mkdir(parents=True, exist_ok=True)
        for run in runs:
            path = out_dir / f"{run:%Y%m%d}.csv"
            if not path.exists():
                jobs.append((model, run, path))
    print(f"{len(jobs)} runs to fetch", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(process_run, m, r, stations): (m, r, p) for m, r, p in jobs}
        for fut in as_completed(futs):
            m, r, p = futs[fut]
            try:
                df = fut.result()
                df.round(3).to_csv(p, index=False)
                done += 1
                print(f"[{done}/{len(jobs)}] {m} {r:%Y-%m-%d}", flush=True)
            except Exception as exc:  # keep going; rerun the script to retry
                print(f"FAILED {m} {r:%Y-%m-%d}: {exc}", flush=True)
    consolidate(models, len(runs))


def consolidate(models: list[str], expected_runs: int) -> None:
    """Write one versioned file per model and a compressed copy of the download log."""
    for model in models:
        parts = sorted((C.FORECAST_PARTS_DIR / model).glob("*.csv"))
        if len(parts) != expected_runs:
            print(f"{model}: {len(parts)} of {expected_runs} runs present, not consolidating")
            continue
        df = pd.concat([pd.read_csv(f) for f in parts], ignore_index=True)
        df = df[["model", "init_time_utc", "step_h", "station_id", "u10", "v10", "t2m"]]
        df.to_csv(C.INTERIM_DIR / f"forecast_point_values_{model}.csv.gz", index=False)
        print(f"{model}: {len(df):,} rows consolidated")
    log = pd.read_csv(MANIFEST.path).sort_values(["url", "byte_start"])
    log.to_csv(C.RAW_DIR / "forecast-download-manifest.csv.gz", index=False)


if __name__ == "__main__":
    main(sys.argv[1:] or list(C.MODELS))
