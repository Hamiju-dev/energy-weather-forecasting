"""Step 1: station observations for Germany (NOAA Integrated Surface Database).

Downloads the ISD station catalogue and the hourly station files of all
lowland German stations for the study year (2025) and for the reference
climate years (2020-2024), parses 10 m wind speed and 2 m temperature, and
builds an out-of-sample station climatology for the verification hours.

Inputs  : NOAA ISD on AWS Open Data (public domain)
Outputs : data/cache/noaa-isd/...                         raw files as downloaded (not versioned)
          data/raw/noaa-isd-download-manifest.csv          URL, size and SHA-256 of every file
          data/interim/station_candidates.csv               lowland German stations considered
          data/interim/station_observations_2025.csv.gz     parsed reports around the study period
          data/interim/station_climatology_2020_2024.csv    mean per station, month and hour (00/12 UTC)

ISD fixed-width format (1-based positions): 16-23 date, 24-27 time (UTC),
42-46 report type, 65 wind type code, 66-69 wind speed (m/s x 10), 70 speed QC,
88-92 air temperature (deg C x 10), 93 temperature QC.
"""

from __future__ import annotations

import gzip
import io
import shutil

import pandas as pd

import config as C
from common import Manifest, http_get

GOOD_QC = set("0145")  # passed checks; 2/3/6/7 are suspect or erroneous, 9 missing
MANIFEST = Manifest(C.CACHE_DIR / "noaa-isd-download-manifest.csv")


def select_candidate_stations(history_csv: bytes) -> pd.DataFrame:
    h = pd.read_csv(io.BytesIO(history_csv), dtype=str)
    h["elevation_m"] = pd.to_numeric(h["ELEV(M)"], errors="coerce")
    sel = h[(h.CTRY == C.STATION_COUNTRY)
            & (h.END >= C.STATION_ACTIVE_UNTIL)
            & (h.BEGIN <= f"{min(C.CLIMATOLOGY_YEARS)}0101")
            & (h.elevation_m <= C.STATION_MAX_ELEVATION_M)].copy()
    sel["station_id"] = sel.USAF + "-" + sel.WBAN
    sel["latitude"] = sel.LAT.astype(float)
    sel["longitude"] = sel.LON.astype(float)
    sel = sel.rename(columns={"STATION NAME": "name", "ICAO": "icao"})
    return sel[["station_id", "name", "icao", "latitude", "longitude", "elevation_m"]] \
        .sort_values("station_id").reset_index(drop=True)


def parse_isd(raw_gz: bytes, station_id: str) -> pd.DataFrame:
    rows = []
    for line in gzip.decompress(raw_gz).decode("ascii", "replace").splitlines():
        if len(line) < 105:
            continue
        ts = pd.Timestamp(f"{line[15:23]}T{line[23:27]}", tz="UTC")
        speed_raw, speed_qc, wind_type = line[65:69], line[69], line[64]
        temp_raw, temp_qc = line[87:92], line[92]
        speed = float(speed_raw) / 10.0 if speed_raw != "9999" and speed_qc in GOOD_QC else None
        if wind_type == "C":  # calm reported explicitly
            speed = 0.0
        temp = float(temp_raw) / 10.0 if temp_raw != "+9999" and temp_qc in GOOD_QC else None
        rows.append((station_id, ts, line[41:46].strip(), speed, temp))
    return pd.DataFrame(rows, columns=["station_id", "time_utc", "report_type",
                                       "wind_speed_10m_ms", "temperature_2m_c"])


def fetch_station_year(sid: str, year: int) -> bytes | None:
    fname = f"{sid}-{year}.gz"
    path = C.ISD_CACHE_DIR / str(year) / fname
    if path.exists():
        return path.read_bytes()
    url = f"{C.ISD_BUCKET}/data/{year}/{fname}"
    try:
        raw = http_get(url)
    except RuntimeError as exc:
        print("missing", sid, year, exc)
        return None
    MANIFEST.add(url, raw, note=f"station file {year}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def nearest_to_synoptic_hours(obs: pd.DataFrame) -> pd.DataFrame:
    """Report closest to 00 and 12 UTC (within the match window), per variable."""
    tol = pd.Timedelta(minutes=C.OBS_MATCH_WINDOW_MIN)
    start, end = obs.time_utc.min().floor("D"), obs.time_utc.max().ceil("D")
    grid = pd.DataFrame({"valid_time_utc": pd.date_range(start, end, freq="12h")})
    out = []
    for sid, g in obs.groupby("station_id"):
        res = grid.copy()
        for col, name in (("wind_speed_10m_ms", "wind_obs"), ("temperature_2m_c", "t2m_obs")):
            s = g.dropna(subset=[col]).sort_values("time_utc")[["time_utc", col]] \
                .rename(columns={"time_utc": "valid_time_utc", col: name})
            res = pd.merge_asof(res, s, on="valid_time_utc", direction="nearest", tolerance=tol)
        res["station_id"] = sid
        out.append(res)
    return pd.concat(out, ignore_index=True)


def main() -> None:
    hist_path = C.ISD_CACHE_DIR / "isd-history.csv"
    if hist_path.exists():
        hist = hist_path.read_bytes()
    else:
        url = f"{C.ISD_BUCKET}/isd-history.csv"
        hist = http_get(url)
        MANIFEST.add(url, hist, note="station catalogue")
        hist_path.parent.mkdir(parents=True, exist_ok=True)
        hist_path.write_bytes(hist)

    stations = select_candidate_stations(hist)
    C.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    stations.to_csv(C.INTERIM_DIR / "station_candidates.csv", index=False)
    print(f"{len(stations)} candidate stations")

    # study year
    frames = [parse_isd(raw, sid) for sid in stations.station_id
              if (raw := fetch_station_year(sid, C.ISD_YEAR)) is not None]
    obs = pd.concat(frames, ignore_index=True)
    window = (obs.time_utc >= pd.Timestamp(C.INIT_FIRST, tz="UTC") - pd.Timedelta("2D")) & \
             (obs.time_utc <= pd.Timestamp(C.INIT_LAST, tz="UTC") + pd.Timedelta("12D"))
    obs = obs[window].sort_values(["station_id", "time_utc"])
    obs.to_csv(C.INTERIM_DIR / "station_observations_2025.csv.gz", index=False,
               date_format="%Y-%m-%dT%H:%M:%SZ")
    print(f"{len(obs):,} observation reports in the study window")

    # reference climate
    clim_frames = []
    for year in C.CLIMATOLOGY_YEARS:
        for sid in stations.station_id:
            raw = fetch_station_year(sid, year)
            if raw is None:
                continue
            o = parse_isd(raw, sid)
            o = o[o.time_utc.dt.month.isin(C.CLIMATOLOGY_MONTHS)]
            if len(o):
                clim_frames.append(nearest_to_synoptic_hours(o))
    syn = pd.concat(clim_frames, ignore_index=True)
    syn = syn[syn.valid_time_utc.dt.month.isin(C.CLIMATOLOGY_MONTHS)]
    syn["month"] = syn.valid_time_utc.dt.month
    syn["hour"] = syn.valid_time_utc.dt.hour
    clim = syn.groupby(["station_id", "month", "hour"]).agg(
        wind_mean=("wind_obs", "mean"), wind_n=("wind_obs", "count"),
        t2m_mean=("t2m_obs", "mean"), t2m_n=("t2m_obs", "count")).reset_index()
    clim.round(3).to_csv(C.INTERIM_DIR / "station_climatology_2020_2024.csv", index=False)
    print(f"climatology: {len(clim)} station-month-hour cells")

    # versioned copy of the download log
    C.RAW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MANIFEST.path, C.RAW_DIR / "noaa-isd-download-manifest.csv")


if __name__ == "__main__":
    main()
