"""Command-line interface.

    ewf forecast --plant plants/example-leipzig.yaml
    ewf forecast --lat 51.42 --lon 12.24 --dc-kwp 10000 --ac-kw 7700 --tilt 20 --azimuth 180
    ewf runs
    ewf example-plant > my-plant.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from ewf.forecast import DEFAULT_MODELS, run_forecast
from ewf.plant import Plant, load_plants
from ewf.weather.models import MODELS, find_run, required_until

EXAMPLE = """\
# PV plant description for `ewf forecast --plant <file>`.
# A file can also hold several plants under a `plants:` list.
name: Example Leipzig
latitude: 51.424
longitude: 12.236
altitude_m: 140
capacity_dc_kwp: 10000      # module power at STC
capacity_ac_kw: 7700        # inverter limit (leave out for no clipping)
tracking: fixed             # fixed or single_axis
tilt_deg: 20
azimuth_deg: 180            # 180 = south, 90 = east, 270 = west
gamma_pdc_per_k: -0.0035    # module temperature coefficient
system_losses_pct: 10       # soiling, mismatch, wiring, availability
timezone: Europe/Berlin
"""


def _plants_from_args(a) -> list[Plant]:
    if a.plant:
        return load_plants(a.plant)
    if a.lat is None or a.lon is None or a.dc_kwp is None:
        raise SystemExit("give --plant FILE, or at least --lat, --lon and --dc-kwp")
    return [Plant(name=a.name, latitude=a.lat, longitude=a.lon, capacity_dc_kwp=a.dc_kwp,
                  capacity_ac_kw=a.ac_kw, tilt_deg=a.tilt, azimuth_deg=a.azimuth, tracking=a.tracking,
                  timezone=a.timezone)]


def cmd_forecast(a) -> int:
    from ewf.report import write_outputs  # matplotlib only when needed

    plants = _plants_from_args(a)
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    unknown = set(models) - set(MODELS)
    if unknown:
        raise SystemExit(f"unknown models: {sorted(unknown)} (choose from {sorted(MODELS)})")
    say = (lambda m: None) if a.quiet else (lambda m: print(f"  {m}", file=sys.stderr))
    result = run_forecast(plants, hours=a.hours, models=models, use_cache=not a.no_cache, progress=say)
    files = write_outputs(result, a.out, formats=[f.strip() for f in a.format.split(",")])

    for plant in plants:
        daily = result.daily_energy(plant.name)
        print(f"\n{plant.name}  ({plant.capacity_dc_kwp:,.0f} kWp)")
        print(f"window {result.start:%Y-%m-%d %H:%M} to {result.end:%Y-%m-%d %H:%M} UTC")
        cols = [c for c in daily.columns if c.startswith("energy_kwh_")]
        show = daily[cols].rename(columns=lambda c: c.replace("energy_kwh_", "")).round(0)
        show["kWh/kWp"] = daily["specific_yield_kwh_per_kwp"].round(2)
        show["day"] = ["complete" if c else "partial" for c in daily["complete"]]
        print("energy per local day (kWh):")
        print(show.to_string())
    print("\nruns: " + ", ".join(f"{r.spec.label} {r.run:%d.%m %H} UTC" for r in result.runs.values()))
    for p in result.problems:
        print(f"warning: {p}", file=sys.stderr)
    print("written:\n" + "\n".join(f"  {f}" for f in files))
    return 0


def cmd_runs(a) -> int:
    now = pd.Timestamp.now(tz="UTC")
    until = required_until(now, a.hours)
    print(f"latest runs that reach {until:%Y-%m-%d %H:%M} UTC:")
    for key in a.models.split(","):
        try:
            r = find_run(MODELS[key], until, now)
            print(f"  {MODELS[key].label:12s} {r.run:%Y-%m-%d %H} UTC  steps to {r.steps[-1]} h  ({r.mirror})")
        except Exception as exc:
            print(f"  {MODELS[key].label:12s} not available: {exc}")
    return 0


def cmd_serve(a) -> int:
    try:
        import uvicorn
    except ImportError:
        print("The web app needs extra packages: pip install -e '.[web]'", file=sys.stderr)
        return 1
    print(f"Dashboard on http://{a.host}:{a.port}  (build the front end once with: cd web && npm install && npm run build)")
    uvicorn.run("ewf.api:app", host=a.host, port=a.port)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ewf", description="PV power forecasts from open weather-model data.")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("forecast", help="forecast AC power for one or more plants")
    f.add_argument("--plant", type=Path, help="YAML or JSON file with one plant or a list of plants")
    f.add_argument("--name", default="PV plant")
    f.add_argument("--lat", type=float)
    f.add_argument("--lon", type=float)
    f.add_argument("--dc-kwp", type=float, help="DC capacity in kWp")
    f.add_argument("--ac-kw", type=float, default=None, help="inverter (AC) capacity in kW")
    f.add_argument("--tilt", type=float, default=20.0)
    f.add_argument("--azimuth", type=float, default=180.0, help="180 = south")
    f.add_argument("--tracking", choices=["fixed", "single_axis"], default="fixed")
    f.add_argument("--timezone", default="Europe/Berlin")
    f.add_argument("--hours", type=int, default=72, help="forecast horizon from now (default 72, max about 240)")
    f.add_argument("--models", default=",".join(DEFAULT_MODELS), help="comma list of ifs, aifs, gfs")
    f.add_argument("--out", type=Path, default=Path("outputs"), help="output folder (default ./outputs)")
    f.add_argument("--format", default="csv,json,html", help="comma list of csv, json, html")
    f.add_argument("--no-cache", action="store_true", help="always download again")
    f.add_argument("--quiet", action="store_true")
    f.set_defaults(func=cmd_forecast)

    r = sub.add_parser("runs", help="show the latest available model runs")
    r.add_argument("--hours", type=int, default=72)
    r.add_argument("--models", default=",".join(DEFAULT_MODELS))
    r.set_defaults(func=cmd_runs)

    e = sub.add_parser("example-plant", help="print an example plant file")
    e.set_defaults(func=lambda a: print(EXAMPLE, end="") or 0)

    s = sub.add_parser("serve", help="start the web app (API and dashboard)")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    s.set_defaults(func=cmd_serve)

    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
