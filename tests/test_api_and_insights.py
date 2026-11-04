"""Maintenance windows, clipping, forecast vs actuals, run history and the HTTP API (no network)."""

import time

import numpy as np
import pandas as pd
import pytest

from ewf.forecast import ForecastResult
from ewf.insights import clipping, maintenance_windows
from ewf.plant import Plant
from ewf.verify import compare, read_actuals
from ewf.weather.models import MODELS, ModelRun

MODEL_KEYS = ["ifs", "gfs"]


def synthetic_result(days: int = 3, ac_kw: float = 80.0) -> ForecastResult:
    """A forecast frame with a sine-shaped day (06-18 UTC) and two models; not real data, for tests only."""
    plant = Plant("Test", 51.0, 12.0, capacity_dc_kwp=100, capacity_ac_kw=ac_kw, timezone="UTC")
    start = pd.Timestamp.now(tz="UTC").floor("D") + pd.Timedelta(days=1)     # in the future, like a forecast
    idx = pd.date_range(start, periods=days * 96, freq="15min", tz="UTC")
    hour = (idx.hour + idx.minute / 60).to_numpy()
    shape = np.clip(np.sin((hour - 6) / 12 * np.pi), 0, None)
    shape[(hour < 6) | (hour >= 18)] = 0
    df = pd.DataFrame(index=idx)
    df["clearsky_ghi_wm2"] = 900 * shape
    df["power_kw_ifs"] = np.minimum(100 * shape, ac_kw)
    df["power_kw_gfs"] = np.minimum(70 * shape, ac_kw)
    for k in MODEL_KEYS:
        df[f"ghi_wm2_{k}"] = 800 * shape
    p = df[[f"power_kw_{k}" for k in MODEL_KEYS]]
    df["power_kw_blend"], df["power_kw_min"], df["power_kw_max"] = p.mean(axis=1), p.min(axis=1), p.max(axis=1)
    for c in ("ghi_wm2_blend", "poa_wm2_blend"):
        df[c] = 800 * shape
    df["cell_temp_c_blend"], df["temp_air_c_blend"] = 30.0, 20.0
    df["wind_speed_ms_blend"], df["cloud_cover_pct_blend"] = 3.0, 40.0
    runs = {k: ModelRun(MODELS[k], idx[0], "test", [0, 6]) for k in MODEL_KEYS}
    return ForecastResult([plant], runs, idx[0], idx[-1], idx[0], {"Test": df})


def test_maintenance_windows_daylight_only_and_lowest_first():
    df = synthetic_result().frames["Test"]
    wins = maintenance_windows(df, duration_h=2, top=3)
    assert len(wins) == 3
    for w in wins:
        assert w["start_utc"].hour >= 6 and w["end_utc"].hour <= 18       # inside daylight
        assert w["end_utc"] - w["start_utc"] == pd.Timedelta(hours=2)
    assert wins[0]["energy_kwh"] <= wins[1]["energy_kwh"] <= wins[2]["energy_kwh"]
    assert wins[0]["energy_kwh_worst"] >= wins[0]["energy_kwh"]
    starts = [w["start_utc"] for w in wins]                               # no overlaps
    assert all(abs(a - b) >= pd.Timedelta(hours=2) for i, a in enumerate(starts) for b in starts[i + 1:])


def test_clipping_counts_hours_at_limit():
    df = synthetic_result(days=1).frames["Test"]
    c = clipping(df, 80.0, MODEL_KEYS)
    assert c["hours"]["ifs"] > 0 and c["hours"]["gfs"] == 0
    assert clipping(df, float("inf"), MODEL_KEYS)["limit_kw"] is None


def test_read_actuals_and_compare():
    res = synthetic_result(days=1)
    df = res.frames["Test"]
    hourly = df["power_kw_ifs"].resample("1h").mean()
    text = "timestamp;Power MW\n" + "\n".join(f"{t:%Y-%m-%d %H:%M};{v / 1000:.6f}" for t, v in hourly.items())
    s = read_actuals(text, timezone="UTC")
    assert s.name == "Power MW" and s.max() == pytest.approx(hourly.max(), rel=1e-4)    # MW converted to kW
    out = compare(df, s, MODEL_KEYS, 100)
    assert out["resolution_min"] == 60
    assert out["metrics"]["ifs"]["mae_kw"] == pytest.approx(0, abs=1e-3)
    assert out["metrics"]["gfs"]["bias_kw"] < 0


def test_read_actuals_rejects_files_without_times():
    with pytest.raises(ValueError, match="dates"):
        read_actuals("a,b\n1,2\n3,4\n")


def test_history_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("EWF_CACHE_DIR", str(tmp_path))
    from ewf import history
    res = synthetic_result()
    history.record(res)
    history.record(res)                                                   # same runs: no duplicates
    entries = history.read(res.plants[0])
    assert sorted(e["model"] for e in entries) == sorted(MODEL_KEYS)
    assert all(len(e["energy_kwh"]) == 3 for e in entries)


def test_api_forecast_job(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from ewf import api

    monkeypatch.setenv("EWF_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(api, "run_forecast", lambda plants, **kw: synthetic_result())
    client = TestClient(api.app)
    assert client.post("/api/forecast", json={"plants": [{"name": "x"}]}).status_code == 422
    plant = {"name": "Test", "latitude": 51, "longitude": 12, "capacity_dc_kwp": 100, "capacity_ac_kw": 80,
             "timezone": "UTC"}
    job = client.post("/api/forecast", json={"plants": [plant], "models": MODEL_KEYS}).json()["job"]
    for _ in range(50):
        body = client.get(f"/api/jobs/{job}").json()
        if body["status"] != "running":
            break
        time.sleep(0.05)
    assert body["status"] == "done", body
    p = body["result"]["plants"][0]
    assert len(p["series"]["t"]) == len(p["series"]["power"]["blend"]) == 288
    assert p["clipping"]["hours"]["ifs"] > 0 and len(p["windows"]["4"]) > 0
    assert client.get(f"/api/jobs/{job}/download", params={"plant": "Test", "kind": "daily"}).status_code == 200
    z = client.get(f"/api/jobs/{job}/download", params={"plant": "Test", "kind": "zip"})
    assert z.status_code == 200 and z.content[:2] == b"PK"
    day = pd.Timestamp(p["series"]["t"][0], unit="ms").strftime("%Y-%m-%d")
    csv = f"time,power_kw\n{day} 10:00,50\n{day} 11:00,60\n{day} 12:00,70\n"
    r = client.post(f"/api/jobs/{job}/actuals", data={"plant": "Test"}, files={"file": ("m.csv", csv)})
    assert r.status_code == 200 and r.json()["periods"] == 3, (csv, r.json())
    parsed = client.post("/api/plants/parse", files={"file": ("p.yaml", "name: A\nlatitude: 50\nlongitude: 10\n"
                                                                       "capacity_dc_kwp: 5\n")})
    assert parsed.json()[0]["name"] == "A"
    assert client.post("/api/history", json={"plant": plant}).json()
