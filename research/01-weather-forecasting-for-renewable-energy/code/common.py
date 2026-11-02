"""Small helpers shared by the pipeline scripts: HTTP with retries, provenance
logging and great-circle distances."""

from __future__ import annotations

import csv
import hashlib
import math
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

_session_local = threading.local()


def session() -> requests.Session:
    """One requests.Session per thread (sessions are not thread-safe)."""
    if not hasattr(_session_local, "s"):
        _session_local.s = requests.Session()
        _session_local.s.headers["User-Agent"] = "energy-weather-forecasting research pipeline"
    return _session_local.s


def http_get(url: str, byte_range: tuple[int, int] | None = None, tries: int = 7,
             timeout: int = 120) -> bytes:
    """GET a URL (optionally a byte range) with exponential backoff."""
    headers = {}
    if byte_range is not None:
        headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"
    last = None
    for attempt in range(tries):
        try:
            r = session().get(url, headers=headers, timeout=timeout)
            if r.status_code in (200, 206):
                return r.content
            last = f"HTTP {r.status_code}"
            if r.status_code == 404:
                break
        except requests.RequestException as exc:  # network hiccup
            last = repr(exc)
        time.sleep(min(60, 2 * 2 ** attempt))
    raise RuntimeError(f"GET failed for {url} {byte_range}: {last}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Manifest:
    """Append-only CSV log of every downloaded object (URL, range, size, hash)."""

    FIELDS = ["retrieved_utc", "url", "byte_start", "byte_end", "bytes", "sha256", "note"]

    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with path.open("w", newline="") as f:
                csv.writer(f).writerow(self.FIELDS)

    def add(self, url: str, data: bytes, byte_range=None, note: str = "") -> None:
        start, end = (byte_range or ("", ""))
        row = [utc_now_iso(), url, start, end, len(data), sha256(data), note]
        with self.lock, self.path.open("a", newline="") as f:
            csv.writer(f).writerow(row)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def write_tex(path: Path, lines: list[str]) -> None:
    """Write generated LaTeX macro definitions.

    Values that start with a minus or a less-than sign are wrapped in
    \\ensuremath so that they print with a true minus sign in running text.
    """
    import re

    out = []
    for line in lines:
        m = re.match(r"^(\\newcommand\{\\[A-Za-z]+\})\{(.*)\}$", line)
        if m and m.group(2)[:1] in ("-", "<"):
            line = f"{m.group(1)}{{\\ensuremath{{{m.group(2)}}}}}"
        out.append(line)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n")
