"""15-minute resampling and the PV chain."""

import numpy as np
import pandas as pd
import pytest

from ewf.plant import Plant
from ewf.pv import simulate
from ewf.resample import PERIOD, clearsky_1min, to_15min

LAT, LON, ALT = 51.42, 12.24, 140.0
DAY = pd.Timestamp("2025-06-21", tz="UTC")


def model_like(step_h: int, kc: float, hours: int = 24) -> pd.DataFrame:
    """A model-style series with interval-mean GHI equal to kc x clear sky."""
    cs = clearsky_1min(LAT, LON, ALT, DAY, DAY + pd.Timedelta(hours=hours))
    valid = pd.date_range(DAY, DAY + pd.Timedelta(hours=hours), freq=f"{step_h}h")
    ghi = [np.nan] + [kc * cs[(cs.index >= a) & (cs.index < b)].mean() for a, b in zip(valid[:-1], valid[1:])]
    return pd.DataFrame({"ghi_wm2": ghi, "interval_h": [np.nan] + [step_h] * (len(valid) - 1),
                         "temp_air_c": np.linspace(15, 25, len(valid)), "wind_speed_ms": 3.0,
                         "cloud_cover_pct": 20.0}, index=valid)


@pytest.mark.parametrize("step_h", [1, 3, 6])
def test_resampling_keeps_interval_energy(step_h):
    data = model_like(step_h, kc=0.7)
    out = to_15min(data, LAT, LON, ALT, DAY, DAY + pd.Timedelta(hours=24))
    # energy per model interval is preserved
    for end, row in data.dropna().iterrows():
        start = end - pd.Timedelta(hours=row.interval_h)
        sel = out[(out.index >= start) & (out.index < end)]
        np.testing.assert_allclose(sel.ghi_wm2.sum() * 0.25, row.ghi_wm2 * row.interval_h, rtol=1e-6, atol=1e-6)
    assert (out.ghi_wm2[out.clearsky_ghi_wm2 == 0] == 0).all()        # dark at night
    # constant clear-sky index stays constant in daylight
    day = out[out.clearsky_ghi_wm2 > 100]
    np.testing.assert_allclose(day.clearsky_index, 0.7, rtol=0.03)


def test_instantaneous_variables_are_interpolated_not_extrapolated():
    data = model_like(3, kc=0.5, hours=12)
    out = to_15min(data, LAT, LON, ALT, DAY, DAY + pd.Timedelta(hours=12))
    assert out.temp_air_c.iloc[0] == pytest.approx(15 + (25 - 15) * (7.5 / 60) / 12, rel=1e-6)
    assert out.temp_air_c.notna().all()


def test_pv_clear_day_is_plausible_and_respects_ac_limit():
    plant = Plant("t", LAT, LON, capacity_dc_kwp=1000, capacity_ac_kw=770, altitude_m=ALT)
    data = model_like(1, kc=1.0)
    w = to_15min(data, LAT, LON, ALT, DAY, DAY + pd.Timedelta(hours=24))
    p = simulate(plant, w)
    assert p.p_ac_kw.max() <= 770 + 1e-6
    assert (p.p_ac_kw[w.clearsky_ghi_wm2 == 0] == 0).all()
    specific_yield = p.p_ac_kw.sum() * 0.25 / 1000            # kWh/kWp
    assert 5.0 < specific_yield < 8.5                          # clear June day in central Germany


def test_tracker_yields_more_than_fixed_on_a_clear_summer_day():
    data = model_like(1, kc=1.0)
    w = to_15min(data, LAT, LON, ALT, DAY, DAY + pd.Timedelta(hours=24))
    fixed = Plant("f", LAT, LON, capacity_dc_kwp=1000, tilt_deg=20)
    tracker = Plant("t", LAT, LON, capacity_dc_kwp=1000, tracking="single_axis")
    assert simulate(tracker, w).p_ac_kw.sum() > 1.1 * simulate(fixed, w).p_ac_kw.sum()


def test_period_constant():
    assert PERIOD == pd.Timedelta(minutes=15)
