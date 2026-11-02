"""ewf: PV power forecasts from open weather-model data.

Typical use::

    from ewf import Plant, run_forecast
    plant = Plant(name="Leipzig", latitude=51.42, longitude=12.24, capacity_dc_kwp=10_000,
                  capacity_ac_kw=7_700, tilt_deg=20, azimuth_deg=180)
    result = run_forecast([plant], hours=72)
    result.power("Leipzig")      # 15-minute power per model, blend and model range

See README.md for the command-line interface and the web app.
"""

from ewf.plant import Plant, load_plants
from ewf.forecast import ForecastResult, run_forecast

__all__ = ["Plant", "load_plants", "run_forecast", "ForecastResult"]
__version__ = "0.1.0"
