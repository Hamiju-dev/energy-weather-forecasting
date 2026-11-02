"""End-to-end test against the live archives. Run with: pytest -m network"""

import pytest

from ewf import Plant, run_forecast

pytestmark = pytest.mark.network


def test_live_forecast_one_model(tmp_path, monkeypatch):
    monkeypatch.setenv("EWF_CACHE_DIR", str(tmp_path))
    plant = Plant("live test", 51.42, 12.24, capacity_dc_kwp=1000, capacity_ac_kw=800)
    result = run_forecast([plant], hours=24, models=("aifs",))
    df = result.frames["live test"]
    assert len(df) >= 24 * 4
    assert df.power_kw_aifs.max() <= 800 + 1e-6
    assert (df.power_kw_aifs >= 0).all()
    assert result.daily_energy("live test").energy_kwh_blend.sum() >= 0
