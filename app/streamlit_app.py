"""Web app: describe a PV plant, get a 15-minute power forecast.

Run with:  streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import io
import json
import zipfile

import altair as alt
import pandas as pd
import streamlit as st
import yaml

from ewf import Plant, run_forecast
from ewf.report import COLOURS, LABELS, html_report, slug, summary_dict

st.set_page_config(page_title="PV power forecast", page_icon="☀️", layout="wide")

MODEL_KEYS = ["ifs", "aifs", "gfs"]
COLOUR_SCALE = alt.Scale(domain=[LABELS[k] for k in MODEL_KEYS + ["blend"]],
                         range=[COLOURS[k] for k in MODEL_KEYS + ["blend"]])


# ---------------------------------------------------------------- inputs
st.sidebar.header("Plant")
uploaded = st.sidebar.file_uploader("Load a plant file (optional)", type=["yaml", "yml", "json"],
                                    help="Same format as `ewf example-plant`. The first plant in the file is used.")
defaults = dict(name="My PV plant", latitude=51.424, longitude=12.236, altitude_m=140.0, capacity_dc_kwp=10000.0,
                capacity_ac_kw=7700.0, tracking="fixed", tilt_deg=20.0, azimuth_deg=180.0, axis_azimuth_deg=180.0,
                max_angle_deg=60.0, system_losses_pct=10.0, gamma_pdc_per_k=-0.0035, timezone="Europe/Berlin")
if uploaded is not None:
    data = yaml.safe_load(uploaded.getvalue())
    if isinstance(data, dict) and "plants" in data:
        data = data["plants"]
    if isinstance(data, list):
        data = data[0]
    defaults.update({k: v for k, v in data.items() if k in defaults})

name = st.sidebar.text_input("Name", defaults["name"])
c1, c2 = st.sidebar.columns(2)
lat = c1.number_input("Latitude", -90.0, 90.0, float(defaults["latitude"]), 0.001, format="%.4f")
lon = c2.number_input("Longitude", -180.0, 180.0, float(defaults["longitude"]), 0.001, format="%.4f")
c1, c2 = st.sidebar.columns(2)
dc = c1.number_input("DC capacity (kWp)", 1.0, 5_000_000.0, float(defaults["capacity_dc_kwp"]), 100.0)
has_ac = c2.checkbox("Inverter limit", value=defaults["capacity_ac_kw"] is not None)
ac = c2.number_input("AC capacity (kW)", 1.0, 5_000_000.0, float(defaults["capacity_ac_kw"] or dc), 100.0,
                     disabled=not has_ac, label_visibility="collapsed")
tracking = st.sidebar.radio("Mounting", ["fixed", "single_axis"], horizontal=True,
                            index=0 if defaults["tracking"] == "fixed" else 1,
                            format_func=lambda x: "Fixed tilt" if x == "fixed" else "Single-axis tracker")
c1, c2 = st.sidebar.columns(2)
if tracking == "fixed":
    tilt = c1.number_input("Tilt (°)", 0.0, 90.0, float(defaults["tilt_deg"]), 1.0)
    azimuth = c2.number_input("Azimuth (°, 180 = south)", 0.0, 360.0, float(defaults["azimuth_deg"]), 5.0)
    axis_az, max_angle = 180.0, 60.0
else:
    axis_az = c1.number_input("Axis azimuth (°)", 0.0, 360.0, float(defaults["axis_azimuth_deg"]), 5.0)
    max_angle = c2.number_input("Max rotation (°)", 0.0, 90.0, float(defaults["max_angle_deg"]), 5.0)
    tilt, azimuth = 0.0, 180.0
with st.sidebar.expander("More settings"):
    losses = st.number_input("System losses (%)", 0.0, 50.0, float(defaults["system_losses_pct"]), 0.5)
    gamma = st.number_input("Temperature coefficient (1/K)", -0.01, 0.0, float(defaults["gamma_pdc_per_k"]),
                            0.0001, format="%.4f")
    altitude = st.number_input("Altitude (m)", -100.0, 5000.0, float(defaults["altitude_m"]), 10.0)
    tz = st.text_input("Time zone", defaults["timezone"])

st.sidebar.header("Forecast")
hours = st.sidebar.slider("Horizon from now (hours)", 24, 240, 72, 12)
models = st.sidebar.multiselect("Weather models", MODEL_KEYS, MODEL_KEYS, format_func=lambda k: LABELS[k])
go = st.sidebar.button("Run forecast", type="primary", width="stretch")


# ---------------------------------------------------------------- forecast (cached per hour)
@st.cache_data(ttl=1800, show_spinner=False)
def cached_forecast(plant_dict: dict, hours: int, models: tuple, hour_key: str):
    return run_forecast([Plant(**plant_dict)], hours=hours, models=models)


st.title("☀️ PV power forecast")
st.caption("15-minute AC power from the latest ECMWF IFS, ECMWF AIFS and NOAA GFS runs, converted with a "
           "physical PV model. Open data: ECMWF (CC-BY-4.0), NOAA (public domain).")

if go:
    try:
        plant = Plant(name=name, latitude=lat, longitude=lon, altitude_m=altitude, capacity_dc_kwp=dc,
                      capacity_ac_kw=ac if has_ac else None, tracking=tracking, tilt_deg=tilt, azimuth_deg=azimuth,
                      axis_azimuth_deg=axis_az, max_angle_deg=max_angle, system_losses_pct=losses,
                      gamma_pdc_per_k=gamma, timezone=tz)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    if not models:
        st.error("Choose at least one weather model.")
        st.stop()
    with st.spinner("Finding the latest model runs and downloading the data (about 20-60 s the first time)..."):
        try:
            st.session_state["result"] = cached_forecast(plant.to_dict(), hours, tuple(models),
                                                         pd.Timestamp.now(tz="UTC").strftime("%Y%m%d%H"))
            st.session_state["plant_name"] = plant.name
        except Exception as exc:
            st.error(f"Forecast failed: {exc}")
            st.stop()

if "result" not in st.session_state:
    st.info("Describe the plant on the left and press **Run forecast**.")
    st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=6, height=320)
    st.stop()

result = st.session_state["result"]
pname = st.session_state["plant_name"]
plant = result.plants[0]
df = result.frames[pname]
daily = result.daily_energy(pname)
big = plant.capacity_dc_kwp >= 2000
scale, p_unit, e_unit = (1000.0, "MW", "MWh") if big else (1.0, "kW", "kWh")

for p in result.problems:
    st.warning(p)

# ---------------------------------------------------------------- headline numbers
today = pd.Timestamp.now(tz=plant.timezone).date()
start_local = result.start.tz_convert(plant.timezone)
cols = st.columns(4)
for col, (label, d) in zip(cols[:2], [("Today", today), ("Tomorrow", today + pd.Timedelta(days=1))]):
    if d in daily.index:
        r = daily.loc[d]
        if not r.complete and d == start_local.date():
            label = f"{label} from {start_local:%H:%M}"
        col.metric(f"{label} ({e_unit})", f"{r.energy_kwh_blend / scale:,.1f}",
                   help=f"Blend of the models. Range {min(r[f'energy_kwh_{m}'] for m in result.models) / scale:,.1f}"
                        f" to {max(r[f'energy_kwh_{m}'] for m in result.models) / scale:,.1f}."
                        + ("" if r.complete else " Partial day: the window does not cover all daylight hours."))
cols[2].metric(f"Peak power ({p_unit})", f"{df.power_kw_blend.max() / scale:,.2f}")
cols[3].metric(f"Energy in window ({e_unit})", f"{daily.energy_kwh_blend.sum() / scale:,.1f}")
st.caption("Model runs: " + " · ".join(f"{r.spec.label} {r.run:%d.%m. %H:%M} UTC" for r in result.runs.values())
           + f" · window {start_local:%a %d.%m. %H:%M} to "
             f"{result.end.tz_convert(plant.timezone):%a %d.%m. %H:%M} ({plant.timezone})")

# ---------------------------------------------------------------- charts
local = df.index.tz_convert(plant.timezone).tz_localize(None)
long = pd.concat([pd.DataFrame({"time": local, "power": df[f"power_kw_{k}"] / scale, "model": LABELS[k]})
                  for k in result.models + ["blend"]])
band = pd.DataFrame({"time": local, "low": df.power_kw_min / scale, "high": df.power_kw_max / scale})
base = alt.Chart(band).mark_area(opacity=0.12, color=COLOURS["blend"]).encode(
    x=alt.X("time:T", title=f"Local time ({plant.timezone})", axis=alt.Axis(format="%a %H:%M")),
    y=alt.Y("low:Q", title=f"AC power ({p_unit})"),
    y2="high:Q")
lines = alt.Chart(long).mark_line().encode(
    x="time:T", y="power:Q",
    color=alt.Color("model:N", scale=COLOUR_SCALE, title=None, legend=alt.Legend(orient="top")),
    strokeWidth=alt.condition(alt.datum.model == LABELS["blend"], alt.value(2.6), alt.value(1.3)),
    tooltip=[alt.Tooltip("time:T", format="%a %d.%m %H:%M"), "model:N", alt.Tooltip("power:Q", format=",.2f")])
st.subheader("AC power, 15-minute means")
st.altair_chart((base + lines).properties(height=340), width="stretch")
st.caption("Grey band: range between the models (not a calibrated probability interval).")

left, right = st.columns([3, 2])
with left:
    st.subheader("Energy per day")
    dl = daily.reset_index()
    dl["day"] = [f"{pd.Timestamp(d):%a %d.%m}" + ("" if c else " (partial)") for d, c in zip(dl.date_local, dl.complete)]
    bars = pd.concat([pd.DataFrame({"day": dl.day, "energy": dl[f"energy_kwh_{k}"] / scale, "model": LABELS[k]})
                      for k in result.models + ["blend"]])
    st.altair_chart(alt.Chart(bars).mark_bar().encode(
        x=alt.X("day:N", title=None, sort=None), xOffset="model:N",
        y=alt.Y("energy:Q", title=f"Energy ({e_unit})"),
        color=alt.Color("model:N", scale=COLOUR_SCALE, title=None, legend=alt.Legend(orient="top")),
        tooltip=["day:N", "model:N", alt.Tooltip("energy:Q", format=",.1f")]).properties(height=280),
        width="stretch")
with right:
    st.subheader("Table")
    table = daily.copy()
    table.index = [f"{pd.Timestamp(d):%a %d.%m}" for d in table.index]
    show = (table[[c for c in table.columns if c.startswith("energy_kwh_")]] / scale).round(1)
    show.columns = [c.replace("energy_kwh_", "").upper() if "blend" not in c else "Blend" for c in show.columns]
    show["kWh/kWp"] = table["specific_yield_kwh_per_kwp"].round(2)
    show["complete"] = table["complete"]
    st.dataframe(show, width="stretch")

st.subheader("Irradiance")
ghi = pd.concat([pd.DataFrame({"time": local, "ghi": df[f"ghi_wm2_{k}"], "model": LABELS[k]}) for k in result.models])
cs = pd.DataFrame({"time": local, "ghi": df.clearsky_ghi_wm2})
st.altair_chart((alt.Chart(cs).mark_line(strokeDash=[4, 3], color="#898781").encode(x="time:T", y="ghi:Q")
                 + alt.Chart(ghi).mark_line().encode(
                     x=alt.X("time:T", title=f"Local time ({plant.timezone})", axis=alt.Axis(format="%a %H:%M")),
                     y=alt.Y("ghi:Q", title="GHI (W/m²)"),
                     color=alt.Color("model:N", scale=COLOUR_SCALE, title=None, legend=alt.Legend(orient="top"))))
                .properties(height=260), width="stretch")
st.caption("Dashed: clear-sky irradiance.")

# ---------------------------------------------------------------- downloads
st.subheader("Download")
stamp = result.start.strftime("%Y%m%d-%H%M")
base_name = f"{slug(pname)}_{stamp}"
csv15 = df.to_csv(index_label="period_start_utc", date_format="%Y-%m-%dT%H:%M:%SZ").encode()
csvd = daily.to_csv().encode()
html = html_report(result, pname).encode()
c1, c2, c3, c4 = st.columns(4)
c1.download_button("15-minute CSV", csv15, f"{base_name}_15min.csv", "text/csv")
c2.download_button("Daily CSV", csvd, f"{base_name}_daily.csv", "text/csv")
c3.download_button("HTML report", html, f"{base_name}_report.html", "text/html")
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(f"{base_name}_15min.csv", csv15)
    z.writestr(f"{base_name}_daily.csv", csvd)
    z.writestr(f"{base_name}_report.html", html)
    z.writestr(f"{base_name}_plant.yaml", yaml.safe_dump(plant.to_dict(), sort_keys=False))
    z.writestr(f"{base_name}_summary.json", json.dumps(summary_dict(result, pname), indent=2, default=str))
c4.download_button("Everything (zip)", buf.getvalue(), f"{base_name}.zip", "application/zip")

with st.expander("Model runs and method"):
    st.dataframe(result.run_table(), width="stretch")
    st.markdown("Each model's irradiance (interval means, interpolated to 15 minutes through the clear-sky index), "
                "temperature and wind are converted to AC power with pvlib: Erbs decomposition, Perez transposition, "
                "ASHRAE incidence-angle losses, Faiman cell temperature, PVWatts DC and inverter models, system losses. "
                "Snow, soiling events, outages and curtailment are not modelled.")
