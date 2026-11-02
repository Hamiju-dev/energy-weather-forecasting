"""Step 3: match every forecast with the observation at its valid time.

Rules
  * Valid times are 00 UTC and 12 UTC (00 UTC runs, 12-hourly lead times).
  * The observation is the report closest to the valid time within
    +/- config.OBS_MATCH_WINDOW_MIN minutes, chosen separately for wind and
    temperature (German airports report at :20 and :50, so this is usually
    the report 10 minutes before the valid time).
  * A station is kept if it has both a wind and a temperature observation at
    no less than config.STATION_MIN_AVAILABILITY of all valid times.
  * Forecast wind speed is computed from the interpolated u and v components.

Inputs  : data/interim/station_candidates.csv
          data/interim/station_observations_2025.csv.gz
          data/interim/forecast_point_values_<model>.csv.gz
Outputs : data/interim/verification_pairs.csv.gz
          data/processed/stations.csv   final station list with availability
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import config as C


def observations_at_valid_times(obs: pd.DataFrame, valid: pd.DatetimeIndex) -> pd.DataFrame:
    tol = pd.Timedelta(minutes=C.OBS_MATCH_WINDOW_MIN)
    out = []
    grid = pd.DataFrame({"valid_time_utc": valid})
    for sid, g in obs.groupby("station_id"):
        g = g.sort_values("time_utc")
        res = grid.copy()
        for col, name in (("wind_speed_10m_ms", "wind_obs"), ("temperature_2m_c", "t2m_obs")):
            s = g.dropna(subset=[col])[["time_utc", col]].rename(columns={"time_utc": "valid_time_utc", col: name})
            res = pd.merge_asof(res, s, on="valid_time_utc", direction="nearest", tolerance=tol)
        res["station_id"] = sid
        out.append(res)
    return pd.concat(out, ignore_index=True)


def main() -> None:
    cand = pd.read_csv(C.INTERIM_DIR / "station_candidates.csv")
    obs = pd.read_csv(C.INTERIM_DIR / "station_observations_2025.csv.gz", parse_dates=["time_utc"])

    first = pd.Timestamp(C.INIT_FIRST, tz="UTC") + pd.Timedelta(hours=C.INIT_HOUR_UTC)
    last = pd.Timestamp(C.INIT_LAST, tz="UTC") + pd.Timedelta(hours=C.INIT_HOUR_UTC + max(C.STEPS_H))
    valid = pd.date_range(first, last, freq="12h")
    # observations are also needed 12 h before the first run (persistence baseline)
    valid_ext = pd.date_range(first - pd.Timedelta(hours=12), last, freq="12h")
    ov = observations_at_valid_times(obs, valid_ext)

    in_period = ov[ov.valid_time_utc.isin(valid)]
    avail = (in_period.dropna(subset=["wind_obs", "t2m_obs"]).groupby("station_id").size()
             / len(valid)).rename("availability")
    stations = cand.merge(avail, left_on="station_id", right_index=True, how="left").fillna({"availability": 0})
    stations["used"] = stations.availability >= C.STATION_MIN_AVAILABILITY
    stations.round({"availability": 3}).to_csv(C.PROCESSED_DIR / "stations.csv", index=False)
    keep = set(stations.loc[stations.used, "station_id"])
    print(f"{len(keep)} of {len(stations)} stations pass the availability filter")

    fc = pd.concat([pd.read_csv(C.INTERIM_DIR / f"forecast_point_values_{m}.csv.gz") for m in C.MODELS],
                   ignore_index=True)
    fc = fc[fc.station_id.isin(keep)]
    fc["init_time_utc"] = pd.to_datetime(fc.init_time_utc, utc=True)
    fc["valid_time_utc"] = fc.init_time_utc + pd.to_timedelta(fc.step_h, unit="h")
    fc["wind_fc"] = np.hypot(fc.u10, fc.v10)
    fc = fc.rename(columns={"t2m": "t2m_fc"})

    pairs = fc.merge(ov, on=["station_id", "valid_time_utc"], how="left")
    pairs = pairs[["model", "init_time_utc", "step_h", "valid_time_utc", "station_id",
                   "wind_fc", "wind_obs", "t2m_fc", "t2m_obs"]]
    pairs[["wind_fc", "wind_obs", "t2m_fc", "t2m_obs"]] = pairs[["wind_fc", "wind_obs", "t2m_fc", "t2m_obs"]].round(3)
    pairs.to_csv(C.INTERIM_DIR / "verification_pairs.csv.gz", index=False,
                          date_format="%Y-%m-%dT%H:%M:%SZ")
    ov[ov.station_id.isin(keep)].to_csv(C.INTERIM_DIR / "observations_at_valid_times.csv.gz",
                                         index=False, date_format="%Y-%m-%dT%H:%M:%SZ")
    print(pairs.groupby("model").size())


if __name__ == "__main__":
    main()
