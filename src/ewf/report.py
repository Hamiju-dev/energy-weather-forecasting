"""Write forecast results: CSV (15-minute and daily), JSON and a self-contained HTML report."""

from __future__ import annotations

import base64
import io
import json
import re
from html import escape
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from ewf.forecast import ForecastResult  # noqa: E402

# House palette (research/STYLE_GUIDE.md): colour follows the model in every chart.
COLOURS = {"ifs": "#2A78D6", "aifs": "#EB6834", "gfs": "#1BAF7A", "blend": "#0B0B0B"}
INK2, MUTED, GRID = "#52514E", "#898781", "#E1E0D9"
LABELS = {"ifs": "ECMWF IFS", "aifs": "ECMWF AIFS", "gfs": "NOAA GFS", "blend": "Blend (mean)"}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "plant"


def write_outputs(result: ForecastResult, out_dir: str | Path, formats=("csv", "json", "html")) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = result.start.strftime("%Y%m%d-%H%M")
    written: list[Path] = []
    for plant in result.plants:
        base = out_dir / f"{slug(plant.name)}_{stamp}"
        df = result.frames[plant.name]
        daily = result.daily_energy(plant.name)
        if "csv" in formats:
            p = base.with_name(base.name + "_15min.csv")
            num = df.select_dtypes("number").columns
            df.assign(**{c: df[c].round(3) for c in num}).to_csv(
                p, index_label="period_start_utc", date_format="%Y-%m-%dT%H:%M:%SZ")
            written.append(p)
            p = base.with_name(base.name + "_daily.csv")
            daily.round(2).to_csv(p)
            written.append(p)
        if "json" in formats:
            p = base.with_name(base.name + "_summary.json")
            p.write_text(json.dumps(summary_dict(result, plant.name), indent=2, default=str))
            written.append(p)
        if "html" in formats:
            p = base.with_name(base.name + "_report.html")
            p.write_text(html_report(result, plant.name))
            written.append(p)
    return written


def summary_dict(result: ForecastResult, plant_name: str) -> dict:
    plant = next(p for p in result.plants if p.name == plant_name)
    daily = result.daily_energy(plant_name).reset_index()
    df = result.frames[plant_name]
    return {
        "plant": plant.to_dict(),
        "created_utc": result.created,
        "window_utc": [result.start, result.end],
        "resolution": "15 min; each row is the mean over the period that starts at period_start_utc",
        "runs": result.run_table().to_dict(orient="records"),
        "daily_energy_kwh": daily.round(1).to_dict(orient="records"),
        "peak_power_kw_blend": float(df["power_kw_blend"].max()),
        "problems": result.problems,
        "attribution": [r.spec.attribution for r in result.runs.values()],
        "note": "The blend is the equal-weight mean of the models; min and max show the spread between "
                "models, not a calibrated probability interval.",
    }


# ---------------------------------------------------------------- charts
def _style(ax):
    ax.grid(True, color=GRID, linewidth=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#C3C2B7")
    ax.tick_params(colors=INK2, labelsize=8)


def _png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def _time_axis(ax, tz):
    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12], tz=tz))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d.%m\n%H:%M", tz=tz))


def chart_power(result: ForecastResult, plant_name: str) -> str:
    plant = next(p for p in result.plants if p.name == plant_name)
    df = result.frames[plant_name]
    scale, unit = (1000.0, "MW") if plant.capacity_dc_kwp >= 2000 else (1.0, "kW")
    t = df.index.tz_convert(plant.timezone)
    fig, ax = plt.subplots(figsize=(9.5, 3.6))
    ax.fill_between(t, df.power_kw_min / scale, df.power_kw_max / scale, color=COLOURS["blend"], alpha=0.12,
                    linewidth=0, label="range between models")
    for m in result.models:
        ax.plot(t, df[f"power_kw_{m}"] / scale, color=COLOURS[m], linewidth=1.1, label=LABELS[m])
    ax.plot(t, df.power_kw_blend / scale, color=COLOURS["blend"], linewidth=2.0, label=LABELS["blend"])
    if plant.ac_limit_kw != float("inf"):
        ax.axhline(plant.ac_limit_kw / scale, color=MUTED, linestyle="--", linewidth=0.8)
        ax.text(t[-1], plant.ac_limit_kw / scale, " AC limit", color=INK2, fontsize=7, va="bottom", ha="right")
    ax.set_ylabel(f"AC power ({unit})", fontsize=9)
    ax.set_ylim(bottom=0)
    _style(ax)
    _time_axis(ax, t.tz)
    ax.legend(fontsize=7.5, frameon=False, ncol=5, loc="upper left", bbox_to_anchor=(0, 1.16))
    return _png(fig)


def chart_irradiance(result: ForecastResult, plant_name: str) -> str:
    plant = next(p for p in result.plants if p.name == plant_name)
    df = result.frames[plant_name]
    t = df.index.tz_convert(plant.timezone)
    fig, ax = plt.subplots(figsize=(9.5, 2.8))
    ax.plot(t, df.clearsky_ghi_wm2, color=MUTED, linestyle="--", linewidth=0.9, label="clear sky")
    for m in result.models:
        ax.plot(t, df[f"ghi_wm2_{m}"], color=COLOURS[m], linewidth=1.1, label=LABELS[m])
    ax.set_ylabel("GHI (W/m²)", fontsize=9)
    ax.set_ylim(bottom=0)
    _style(ax)
    _time_axis(ax, t.tz)
    ax.legend(fontsize=7.5, frameon=False, ncol=4, loc="upper left", bbox_to_anchor=(0, 1.2))
    return _png(fig)


def chart_daily(result: ForecastResult, plant_name: str) -> str:
    daily = result.daily_energy(plant_name)
    plant = next(p for p in result.plants if p.name == plant_name)
    scale, unit = (1000.0, "MWh") if plant.capacity_dc_kwp >= 2000 else (1.0, "kWh")
    keys = result.models + ["blend"]
    n = len(keys)
    width = 0.8 / n
    fig, ax = plt.subplots(figsize=(9.5, 2.8))
    x = range(len(daily))
    for i, k in enumerate(keys):
        ax.bar([xi - 0.4 + width * (i + 0.5) for xi in x], daily[f"energy_kwh_{k}"] / scale, width=width * 0.92,
               color=COLOURS[k], label=LABELS[k])
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{pd.Timestamp(d):%a %d.%m}" + ("" if c else "\n(partial)")
                        for d, c in zip(daily.index, daily.complete)], fontsize=8)
    ax.set_ylabel(f"Energy ({unit})", fontsize=9)
    _style(ax)
    ax.grid(axis="x", visible=False)
    ax.legend(fontsize=7.5, frameon=False, ncol=4, loc="upper left", bbox_to_anchor=(0, 1.2))
    return _png(fig)


# ---------------------------------------------------------------- HTML
def html_report(result: ForecastResult, plant_name: str) -> str:
    plant = next(p for p in result.plants if p.name == plant_name)
    df = result.frames[plant_name]
    daily = result.daily_energy(plant_name)
    unit_scale, unit = (1000.0, "MWh") if plant.capacity_dc_kwp >= 2000 else (1.0, "kWh")
    rows = "".join(
        f"<tr><td>{pd.Timestamp(d):%a %d %b %Y}{'' if r.complete else ' (partial)'}</td>"
        + "".join(f"<td>{r[f'energy_kwh_{k}'] / unit_scale:,.1f}</td>" for k in result.models)
        + f"<td><b>{r.energy_kwh_blend / unit_scale:,.1f}</b></td><td>{r.specific_yield_kwh_per_kwp:.2f}</td></tr>"
        for d, r in daily.iterrows())
    head = "".join(f"<th>{LABELS[k]}</th>" for k in result.models)
    runs = "".join(f"<li>{escape(r.spec.label)}: run {r.run:%Y-%m-%d %H:%M} UTC, steps to {r.steps[-1]} h</li>"
                   for r in result.runs.values())
    problems = "".join(f"<li>{escape(p)}</li>" for p in result.problems)
    attribution = "; ".join(escape(r.spec.attribution) for r in result.runs.values())
    params = (f"{plant.capacity_dc_kwp:,.0f} kWp DC, "
              + (f"{plant.capacity_ac_kw:,.0f} kW AC, " if plant.capacity_ac_kw else "no AC limit, ")
              + (f"fixed, tilt {plant.tilt_deg:g}°, azimuth {plant.azimuth_deg:g}°" if plant.tracking == "fixed"
                 else f"single-axis tracking, axis azimuth {plant.axis_azimuth_deg:g}°, ±{plant.max_angle_deg:g}°")
              + f", losses {plant.system_losses_pct:g} %")
    peak = df["power_kw_blend"].max()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PV forecast {escape(plant.name)}</title>
<style>
:root{{--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--bg:#fcfcfb}}
body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg);margin:0 auto;max-width:980px;padding:24px 16px}}
h1{{font-size:1.5rem;margin:0 0 4px}} h2{{font-size:1.05rem;margin:28px 0 8px}}
.sub{{color:var(--ink2);margin:0 0 18px}} img{{max-width:100%;height:auto}}
table{{border-collapse:collapse;font-size:.9rem;font-variant-numeric:tabular-nums}}
th,td{{padding:4px 10px;border-bottom:1px solid var(--grid);text-align:right}} th:first-child,td:first-child{{text-align:left}}
.tiles{{display:flex;gap:28px;flex-wrap:wrap;margin:8px 0 4px}} .tile .v{{font-size:1.6rem;font-weight:600}} .tile .l{{color:var(--ink2);font-size:.85rem}}
.note{{color:var(--ink2);font-size:.85rem}} ul{{margin:4px 0;padding-left:20px}}
</style></head><body>
<h1>PV power forecast: {escape(plant.name)}</h1>
<p class="sub">{plant.latitude:.4f}, {plant.longitude:.4f} · {escape(params)}<br>
Window {result.start.tz_convert(plant.timezone):%a %d %b %H:%M} to {result.end.tz_convert(plant.timezone):%a %d %b %H:%M} ({escape(plant.timezone)}) · created {result.created:%Y-%m-%d %H:%M} UTC</p>
<div class="tiles">
<div class="tile"><div class="v">{daily.energy_kwh_blend.sum() / unit_scale:,.1f} {unit}</div><div class="l">energy in window (blend)</div></div>
<div class="tile"><div class="v">{peak / (1000 if unit == 'MWh' else 1):,.2f} {'MW' if unit == 'MWh' else 'kW'}</div><div class="l">peak power (blend)</div></div>
</div>
<h2>AC power, 15-minute means</h2>
<img alt="AC power forecast per model" src="data:image/png;base64,{chart_power(result, plant_name)}">
<h2>Energy per day</h2>
<img alt="Daily energy per model" src="data:image/png;base64,{chart_daily(result, plant_name)}">
<table><thead><tr><th>Day ({escape(plant.timezone)})</th>{head}<th>Blend</th><th>kWh/kWp</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note">Values in {unit}.</p>
<h2>Global horizontal irradiance</h2>
<img alt="Irradiance forecast per model" src="data:image/png;base64,{chart_irradiance(result, plant_name)}">
<h2>Model runs used</h2><ul>{runs}</ul>{f'<p class="note">Problems:</p><ul>{problems}</ul>' if problems else ''}
<h2>How to read this</h2>
<p class="note">Each model's irradiance, temperature and wind are converted to AC power with a physical PV model (Erbs decomposition, Perez transposition, Faiman cell temperature, PVWatts DC and inverter models). The blend is the plain mean of the models; the shaded band is the range between models, not a calibrated probability interval. Snow, soiling events, outages and curtailment are not included. Times in the chart are local ({escape(plant.timezone)}); the CSV uses UTC period starts.</p>
<p class="note">Data: {attribution}.</p>
</body></html>"""
