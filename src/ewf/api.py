"""HTTP API for the web front end (FastAPI).

Start with ``ewf serve`` (or ``uvicorn ewf.api:app``). Endpoints:

  GET  /api/models                      models, labels, colours, licences
  GET  /api/example-plant               an example plant
  POST /api/plants/parse                plant file (YAML or JSON) -> plants
  POST /api/forecast                    start a forecast job -> job id
  GET  /api/jobs/{id}                   progress messages, then the result
  GET  /api/jobs/{id}/download          CSV, JSON, HTML or zip of a finished job
  POST /api/jobs/{id}/actuals           measured CSV -> forecast vs actuals
  GET  /api/history                     earlier runs for a plant (run-to-run changes)

If the front end has been built (``web/dist``), it is served at ``/``.
"""

from __future__ import annotations

import io
import math
import os
import tempfile
import threading
import time
import uuid
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ewf import history
from ewf.forecast import DEFAULT_MODELS, ForecastResult, latest_runs, run_forecast
from ewf.insights import clipping, maintenance_windows
from ewf.plant import Plant, parse_plants, plants_from_data
from ewf.report import COLOURS, LABELS, html_report, slug, summary_dict, write_outputs
from ewf.verify import compare, read_actuals
from ewf.weather.models import MODELS

app = FastAPI(title="ewf", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])

EXAMPLE_PLANT = Plant(name="Leipzig solar park", latitude=51.42, longitude=12.24, capacity_dc_kwp=10_000,
                      capacity_ac_kw=7_700, tilt_deg=20, azimuth_deg=180)


# ---------------------------------------------------------------- jobs
class Job:
    def __init__(self) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.status = "running"
        self.messages: list[dict] = []
        self.error: str | None = None
        self.result: ForecastResult | None = None
        self.payload: dict | None = None
        self.started = time.time()

    def say(self, msg: str) -> None:
        self.messages.append({"t": round(time.time() - self.started, 1), "text": msg})


JOBS: dict[str, Job] = {}
MAX_JOBS = 20


class ForecastRequest(BaseModel):
    plants: list[dict] = Field(..., min_length=1)
    hours: int = Field(72, ge=6, le=240)
    models: list[str] = Field(default_factory=lambda: list(DEFAULT_MODELS))
    use_cache: bool = True
    previous_run: bool = False          # use the runs before the latest ones (for run-to-run changes)
    window_hours: float = Field(4.0, ge=0.25, le=12)


def _run_job(job: Job, req: ForecastRequest, plants: list[Plant]) -> None:
    try:
        before = None
        if req.previous_run:
            job.say("Finding the latest runs, to step back one run...")
            before = {k: r.run for k, r in latest_runs(tuple(req.models), req.hours).items()}
        result = run_forecast(plants, hours=req.hours, models=tuple(req.models), run_before=before,
                              use_cache=req.use_cache, progress=job.say)
        job.say("Preparing charts...")
        job.payload = serialise(result, req.window_hours)
        job.result = result
        try:
            history.record(result)
        except OSError as exc:            # history is a convenience; never fail the forecast for it
            job.say(f"Could not write history ({exc})")
        job.status = "done"
        job.say("Done.")
    except Exception as exc:  # report every failure to the client
        job.error = str(exc)
        job.status = "error"
        job.say(f"Failed: {exc}")


@app.post("/api/forecast")
def start_forecast(req: ForecastRequest) -> dict:
    unknown = [m for m in req.models if m not in MODELS]
    if unknown or not req.models:
        raise HTTPException(422, f"unknown models: {unknown}" if unknown else "choose at least one model")
    try:
        plants = plants_from_data(req.plants, "request")
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    job = Job()
    JOBS[job.id] = job
    for old in sorted(JOBS.values(), key=lambda j: j.started)[:-MAX_JOBS]:
        JOBS.pop(old.id, None)
    threading.Thread(target=_run_job, args=(job, req, plants), daemon=True).start()
    return {"job": job.id}


def _job(job_id: str) -> Job:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job (the server may have restarted)")
    return job


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, since: int = 0) -> dict:
    job = _job(job_id)
    out = {"job": job.id, "status": job.status, "messages": job.messages[since:], "error": job.error}
    if job.status == "done":
        out["result"] = job.payload
    return out


@app.get("/api/jobs/{job_id}/download")
def download(job_id: str, plant: str, kind: str = "zip") -> Response:
    job = _job(job_id)
    if job.status != "done" or job.result is None:
        raise HTTPException(409, "the forecast is not finished")
    res = job.result
    if plant not in res.frames:
        raise HTTPException(404, f"unknown plant {plant}")
    stamp = f"{slug(plant)}_{res.start:%Y%m%d-%H%M}"
    if kind == "html":
        return Response(html_report(res, plant), media_type="text/html",
                        headers={"Content-Disposition": f'attachment; filename="{stamp}_report.html"'})
    if kind == "json":
        import json
        return Response(json.dumps(summary_dict(res, plant), indent=2, default=str), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{stamp}_summary.json"'})
    if kind in ("csv", "daily"):
        df = res.frames[plant] if kind == "csv" else res.daily_energy(plant)
        buf = io.StringIO()
        if kind == "csv":
            num = df.select_dtypes("number").columns
            df.assign(**{c: df[c].round(3) for c in num}).to_csv(buf, index_label="period_start_utc",
                                                                date_format="%Y-%m-%dT%H:%M:%SZ")
        else:
            df.round(2).to_csv(buf)
        name = f"{stamp}_{'15min' if kind == 'csv' else 'daily'}.csv"
        return Response(buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{name}"'})
    if kind == "zip":
        sub = ForecastResult([p for p in res.plants if p.name == plant], res.runs, res.start, res.end, res.created,
                             {plant: res.frames[plant]}, res.problems)
        with tempfile.TemporaryDirectory() as tmp:
            files = write_outputs(sub, tmp)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for f in files:
                    z.write(f, f.name)
        return Response(buf.getvalue(), media_type="application/zip",
                        headers={"Content-Disposition": f'attachment; filename="{stamp}.zip"'})
    raise HTTPException(422, "kind must be csv, daily, json, html or zip")


@app.post("/api/jobs/{job_id}/actuals")
async def actuals(job_id: str, plant: str = Form(...), file: UploadFile = File(...),
                  timezone: str = Form("UTC")) -> dict:
    job = _job(job_id)
    if job.status != "done" or job.result is None:
        raise HTTPException(409, "the forecast is not finished")
    res = job.result
    p = next((x for x in res.plants if x.name == plant), None)
    if p is None:
        raise HTTPException(404, f"unknown plant {plant}")
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(413, "file larger than 20 MB")
    try:
        series = read_actuals(raw.decode("utf-8-sig", errors="replace"), timezone=timezone)
        out = compare(res.frames[plant], series, res.models, p.capacity_dc_kwp)
    except (ValueError, KeyError) as exc:
        raise HTTPException(422, str(exc)) from exc
    s = out.pop("series")
    out["series"] = {"t": _ms(s.index), **{c.replace("power_kw_", ""): _arr(s[c], 1) for c in s.columns}}
    out["column"] = series.name
    out["measured_from_utc"] = series.index.min()
    out["measured_to_utc"] = series.index.max()
    return _clean(out)


# ---------------------------------------------------------------- plants, models, history
@app.get("/api/models")
def models() -> list[dict]:
    return [{"key": k, "label": s.label, "colour": COLOURS[k], "licence": s.licence, "attribution": s.attribution}
            for k, s in MODELS.items()]


@app.get("/api/example-plant")
def example_plant() -> dict:
    return EXAMPLE_PLANT.to_dict()


@app.post("/api/plants/parse")
async def parse_plant_file(file: UploadFile = File(...)) -> list[dict]:
    raw = await file.read()
    if len(raw) > 1024 * 1024:
        raise HTTPException(413, "plant file larger than 1 MB")
    try:
        plants = parse_plants(raw.decode("utf-8-sig"), Path(file.filename or "x.yaml").suffix, file.filename or "file")
    except Exception as exc:  # YAML, JSON and validation errors all go back to the user
        raise HTTPException(422, str(exc)) from exc
    return [p.to_dict() for p in plants]


class PlantBody(BaseModel):
    plant: dict


@app.post("/api/history")
def get_history(body: PlantBody) -> list[dict]:
    try:
        plant = plants_from_data(body.plant)[0]
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return history.read(plant)


# ---------------------------------------------------------------- serialisation
def _ms(idx: pd.DatetimeIndex) -> list[int]:
    if not len(idx):
        return []
    epoch = pd.Timestamp("1970-01-01", tz="UTC")
    return ((idx.tz_convert("UTC") - epoch) // pd.Timedelta(milliseconds=1)).astype("int64").tolist()


def _arr(s: pd.Series, digits: int = 1) -> list:
    v = s.to_numpy(dtype=float)
    return [None if not math.isfinite(x) else round(x, digits) for x in v]


def _clean(o):
    """Make a structure JSON-safe: timestamps to ISO strings, NaN to None, numpy to Python."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, pd.Timestamp):
        return o.isoformat()
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def serialise(result: ForecastResult, window_hours: float = 4.0) -> dict:
    models = result.models
    plants = []
    now = pd.Timestamp.now(tz="UTC")
    for plant in result.plants:
        df = result.frames[plant.name]
        daily = result.daily_energy(plant.name)
        series = {
            "t": _ms(df.index),
            "power": {k: _arr(df[f"power_kw_{k}"]) for k in models + ["blend", "min", "max"]},
            "ghi": {**{k: _arr(df[f"ghi_wm2_{k}"], 0) for k in models}, "blend": _arr(df["ghi_wm2_blend"], 0),
                    "clearsky": _arr(df["clearsky_ghi_wm2"], 0)},
            "poa": _arr(df["poa_wm2_blend"], 0),
            "cell_temp_c": _arr(df["cell_temp_c_blend"]),
            "temp_air_c": _arr(df["temp_air_c_blend"]),
            "wind_speed_ms": _arr(df["wind_speed_ms_blend"]),
            "cloud_cover_pct": _arr(df["cloud_cover_pct_blend"], 0),
        }
        complete = {str(d) for d, r in daily.iterrows() if r["complete"]}
        local_day = lambda ts: str(ts.tz_convert(plant.timezone).date())  # noqa: E731
        days = [{"date": str(d), "complete": bool(r["complete"]),
                 "energy_kwh": {k: r[f"energy_kwh_{k}"] for k in models + ["blend"]},
                 "specific_yield_kwh_per_kwp": r["specific_yield_kwh_per_kwp"]}
                for d, r in daily.iterrows()]
        plants.append({
            "plant": plant.to_dict(),
            "key": history.plant_key(plant),
            "ac_limit_kw": None if not math.isfinite(plant.ac_limit_kw) else plant.ac_limit_kw,
            "series": series,
            "daily": days,
            "peak_kw": df["power_kw_blend"].max(),
            "peak_utc": df["power_kw_blend"].idxmax() if df["power_kw_blend"].notna().any() else None,
            # only windows on fully covered local days, so "share of that day" means the whole day
            "windows": {f"{h:g}": [w for w in maintenance_windows(df, h, top=12, not_before=now,
                                                                    timezone=plant.timezone)
                                   if local_day(w["start_utc"]) in complete][:6]
                        for h in sorted({1.0, 2.0, 4.0, 8.0, float(window_hours)})},
            "clipping": clipping(df, plant.ac_limit_kw, models),
        })
    return _clean({
        "created_utc": result.created,
        "window_utc": [result.start, result.end],
        "models": models,
        "runs": [{"model": k, "label": r.spec.label, "run_utc": r.run, "last_step_h": r.steps[-1],
                  "steps": len(r.steps), "source": r.mirror, "licence": r.spec.licence,
                  "attribution": r.spec.attribution} for k, r in result.runs.items()],
        "problems": result.problems,
        "plants": plants,
        "labels": LABELS,
        "colours": COLOURS,
        "note": "The blend is the equal-weight mean of the models; the band is the range between models, "
                "not a calibrated probability interval.",
    })


# ---------------------------------------------------------------- static front end
_DIST = Path(os.environ.get("EWF_WEB_DIST", Path(__file__).resolve().parents[2] / "web" / "dist"))
if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        target = (_DIST / path).resolve()
        if path and target.is_file() and _DIST.resolve() in target.parents:
            return FileResponse(target)
        return FileResponse(_DIST / "index.html")
