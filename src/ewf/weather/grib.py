"""Low-level access to GRIB2 archives: HTTP with retries, index parsing,
byte-range downloads and bilinear interpolation to points."""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass

import eccodes
import numpy as np
import requests

_local = threading.local()
_decode_lock = threading.Lock()
USER_AGENT = "ewf/0.1 (github.com/Hamiju-dev/energy-weather-forecasting)"


def _session() -> requests.Session:
    if not hasattr(_local, "session"):
        _local.session = requests.Session()
        _local.session.headers["User-Agent"] = USER_AGENT
    return _local.session


class NotFound(Exception):
    """The requested object does not exist (yet) on this server."""


def http_get(url: str, byte_range: tuple[int, int | None] | None = None,
             tries: int = 5, timeout: int = 60) -> bytes:
    headers = {}
    if byte_range is not None:
        start, end = byte_range
        headers["Range"] = f"bytes={start}-{'' if end is None else end}"
    last = ""
    for attempt in range(tries):
        try:
            r = _session().get(url, headers=headers, timeout=timeout)
            if r.status_code in (200, 206):
                return r.content
            if r.status_code in (403, 404):
                raise NotFound(url)
            last = f"HTTP {r.status_code}"
        except requests.RequestException as exc:
            last = repr(exc)
        time.sleep(min(30, 1.5 * 2 ** attempt))
    raise RuntimeError(f"download failed after {tries} attempts: {url} ({last})")


def exists(url: str, timeout: int = 30) -> bool:
    try:
        r = _session().head(url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
    except requests.RequestException:
        return False


# ---------------------------------------------------------------- indexes
@dataclass
class Message:
    """Location of one GRIB message inside a file, plus what it contains."""
    start: int
    end: int | None          # inclusive; None = to end of file
    avg_window: tuple[int, int] | None = None   # GFS averages: (from_h, to_h)


def parse_ecmwf_index(text: str, wanted: dict[str, str]) -> dict[str, Message]:
    """ECMWF open-data index (one JSON object per line). wanted: {var: param}."""
    out: dict[str, Message] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("levtype") != "sfc":
            continue
        for var, param in wanted.items():
            if rec.get("param") == param and var not in out:
                out[var] = Message(rec["_offset"], rec["_offset"] + rec["_length"] - 1)
    return out


_AVG = re.compile(r"^(\d+)-(\d+) hour ave fcst$")


def parse_gfs_index(text: str, wanted: dict[str, tuple[str, str]], step: int) -> dict[str, Message]:
    """NOAA .idx file. wanted: {var: (name:level, kind)} with kind 'inst' or 'avg'."""
    lines = [l for l in text.splitlines() if l.strip()]
    out: dict[str, Message] = {}
    for i, line in enumerate(lines):
        parts = line.split(":")
        key, when = f"{parts[3]}:{parts[4]}", parts[5]
        end = int(lines[i + 1].split(":")[1]) - 1 if i + 1 < len(lines) else None
        for var, (want, kind) in wanted.items():
            if key != want or var in out:
                continue
            if kind == "inst" and when == ("anl" if step == 0 else f"{step} hour fcst"):
                out[var] = Message(int(parts[1]), end)
            elif kind == "avg":
                m = _AVG.match(when)
                if m and int(m.group(2)) == step:
                    out[var] = Message(int(parts[1]), end, (int(m.group(1)), int(m.group(2))))
    return out


# ---------------------------------------------------------------- interpolation
class PointInterpolator:
    """Bilinear weights from a regular latitude-longitude grid to points."""

    def __init__(self, gid, lats: np.ndarray, lons: np.ndarray):
        g = lambda k: eccodes.codes_get(gid, k)
        self.ni, self.nj = g("Ni"), g("Nj")
        la1, lo1 = g("latitudeOfFirstGridPointInDegrees"), g("longitudeOfFirstGridPointInDegrees")
        di, dj = g("iDirectionIncrementInDegrees"), g("jDirectionIncrementInDegrees")
        dlat = -dj if g("jScansPositively") == 0 else dj
        dlon = -di if g("iScansNegatively") == 1 else di
        fi = ((np.asarray(lons) - lo1) % 360.0) / dlon
        fj = (np.asarray(lats) - la1) / dlat
        i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
        wi, wj = fi - i0, fj - j0
        i1 = (i0 + 1) % self.ni
        j1 = np.minimum(j0 + 1, self.nj - 1)
        self.idx = np.stack([j0 * self.ni + i0, j0 * self.ni + i1, j1 * self.ni + i0, j1 * self.ni + i1])
        self.w = np.stack([(1 - wi) * (1 - wj), wi * (1 - wj), (1 - wi) * wj, wi * wj])

    def __call__(self, values: np.ndarray) -> np.ndarray:
        return (values[self.idx] * self.w).sum(axis=0)


class PointDecoder:
    """Decode GRIB messages and return values at fixed points (thread-safe)."""

    def __init__(self, lats, lons):
        self.lats = np.asarray(lats, dtype=float)
        self.lons = np.asarray(lons, dtype=float)
        self._cache: dict = {}

    def __call__(self, message: bytes) -> tuple[np.ndarray, str]:
        with _decode_lock:
            gid = eccodes.codes_new_from_message(message)
            try:
                sig = tuple(eccodes.codes_get(gid, k) for k in (
                    "Ni", "Nj", "latitudeOfFirstGridPointInDegrees", "longitudeOfFirstGridPointInDegrees"))
                if sig not in self._cache:
                    self._cache[sig] = PointInterpolator(gid, self.lats, self.lons)
                values = eccodes.codes_get_values(gid)
                units = eccodes.codes_get(gid, "units")
                return self._cache[sig](values), units
            finally:
                eccodes.codes_release(gid)
