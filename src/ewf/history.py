"""A small log of past forecasts, to show how the forecast for a day changed from run to run.

Each forecast appends one line per plant and model to
``<cache>/history/<plant key>.jsonl`` with the model run and the energy per
local day. Repeated forecasts from the same run replace the earlier entry.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from ewf.forecast import ForecastResult, cache_dir
from ewf.plant import Plant


def plant_key(plant: Plant) -> str:
    """Stable key for a plant: everything that changes the power, not the name."""
    d = {k: float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v
         for k, v in plant.to_dict().items() if k != "name"}          # 51 and 51.0 are the same plant
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]


def _path(key: str) -> Path:
    return cache_dir() / "history" / f"{key}.jsonl"


def record(result: ForecastResult) -> None:
    for plant in result.plants:
        daily = result.daily_energy(plant.name)
        path = _path(plant_key(plant))
        path.parent.mkdir(parents=True, exist_ok=True)
        entries = {(e["model"], e["run_utc"]): e for e in read(plant)}
        for key, run in result.runs.items():
            entries[(key, run.run.isoformat())] = {
                "model": key,
                "run_utc": run.run.isoformat(),
                "created_utc": result.created.isoformat(),
                "energy_kwh": {str(d): round(float(r[f"energy_kwh_{key}"]), 2)
                               for d, r in daily.iterrows() if r["complete"] and pd.notna(r[f"energy_kwh_{key}"])},
            }
        with path.open("w") as f:
            for e in sorted(entries.values(), key=lambda e: (e["run_utc"], e["model"])):
                f.write(json.dumps(e) + "\n")


def read(plant: Plant) -> list[dict]:
    path = _path(plant_key(plant))
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
