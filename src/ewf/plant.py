"""PV plant description and loading from YAML or JSON."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import yaml


@dataclass
class Plant:
    """A PV plant. Only name, location and DC capacity are required.

    Angles in degrees; azimuth is measured clockwise from north (180 = south).
    """

    name: str
    latitude: float
    longitude: float
    capacity_dc_kwp: float
    capacity_ac_kw: float | None = None      # inverter limit; None = no clipping
    altitude_m: float = 0.0
    tracking: str = "fixed"                  # "fixed" or "single_axis"
    tilt_deg: float = 20.0                   # fixed plants
    azimuth_deg: float = 180.0               # fixed plants
    axis_azimuth_deg: float = 180.0          # single-axis trackers (180 = north-south axis)
    max_angle_deg: float = 60.0              # single-axis trackers
    gcr: float = 0.4                         # ground coverage ratio, for backtracking
    backtrack: bool = True
    gamma_pdc_per_k: float = -0.0035         # power temperature coefficient
    system_losses_pct: float = 10.0          # soiling, mismatch, wiring, availability
    inverter_efficiency: float = 0.98
    albedo: float = 0.20
    temp_u0: float = 25.0                    # Faiman model constants
    temp_u1: float = 6.84
    export_limit_kw: float | None = None     # grid connection limit, if lower than AC
    timezone: str = "Europe/Berlin"          # for daily totals and local-time columns

    def __post_init__(self) -> None:
        problems = []
        if not -90 <= self.latitude <= 90:
            problems.append("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 360:
            problems.append("longitude must be between -180 and 360")
        if self.capacity_dc_kwp <= 0:
            problems.append("capacity_dc_kwp must be positive")
        if self.capacity_ac_kw is not None and self.capacity_ac_kw <= 0:
            problems.append("capacity_ac_kw must be positive")
        if self.tracking not in ("fixed", "single_axis"):
            problems.append("tracking must be 'fixed' or 'single_axis'")
        if not 0 <= self.tilt_deg <= 90:
            problems.append("tilt_deg must be between 0 and 90")
        if not 0 <= self.system_losses_pct < 100:
            problems.append("system_losses_pct must be between 0 and 100")
        if not 0 < self.inverter_efficiency <= 1:
            problems.append("inverter_efficiency must be between 0 and 1")
        if problems:
            raise ValueError(f"plant '{self.name}': " + "; ".join(problems))
        if self.longitude > 180:
            self.longitude -= 360

    @property
    def ac_limit_kw(self) -> float:
        """Effective AC limit: inverter capacity and export limit, whichever is lower."""
        limits = [x for x in (self.capacity_ac_kw, self.export_limit_kw) if x is not None]
        return min(limits) if limits else float("inf")

    def to_dict(self) -> dict:
        return asdict(self)


def load_plants(path: str | Path) -> list[Plant]:
    """Load one plant or a list of plants from a YAML or JSON file.

    Accepted shapes: a single mapping, a list of mappings, or a mapping with a
    ``plants`` key holding a list.
    """
    path = Path(path)
    return parse_plants(path.read_text(), path.suffix, source=str(path))


def parse_plants(text: str, suffix: str = ".yaml", source: str = "input") -> list[Plant]:
    """Parse plants from YAML or JSON text (see ``load_plants`` for the accepted shapes)."""
    data = json.loads(text) if suffix.lower().endswith("json") else yaml.safe_load(text)
    return plants_from_data(data, source)


def plants_from_data(data, source: str = "input") -> list[Plant]:
    """Build plants from already parsed data (mapping, list, or mapping with ``plants``)."""
    if isinstance(data, dict) and "plants" in data:
        data = data["plants"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        raise ValueError(f"no plants found in {source}")
    known = {f.name for f in fields(Plant)}
    plants = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError(f"each plant in {source} must be a mapping")
        unknown = set(item) - known
        if unknown:
            raise ValueError(f"unknown plant fields in {source}: {sorted(unknown)}")
        plants.append(Plant(**item))
    names = [p.name for p in plants]
    if len(set(names)) != len(names):
        raise ValueError("plant names must be unique")
    return plants
