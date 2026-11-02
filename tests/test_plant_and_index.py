"""Plant files and GRIB index parsing."""

import json

import pytest

from ewf.plant import Plant, load_plants
from ewf.weather.grib import parse_ecmwf_index, parse_gfs_index


def test_plant_validation():
    with pytest.raises(ValueError, match="capacity_dc_kwp"):
        Plant("x", 50, 10, capacity_dc_kwp=0)
    with pytest.raises(ValueError, match="tracking"):
        Plant("x", 50, 10, capacity_dc_kwp=100, tracking="dual")
    p = Plant("x", 50, 350, capacity_dc_kwp=100)       # 0-360 longitudes are converted
    assert p.longitude == -10
    assert Plant("y", 50, 10, 100, capacity_ac_kw=80, export_limit_kw=70).ac_limit_kw == 70


def test_load_plants_yaml_list(tmp_path):
    f = tmp_path / "plants.yaml"
    f.write_text("plants:\n  - {name: A, latitude: 51, longitude: 12, capacity_dc_kwp: 100}\n"
                 "  - {name: B, latitude: 52, longitude: 13, capacity_dc_kwp: 200, tracking: single_axis}\n")
    plants = load_plants(f)
    assert [p.name for p in plants] == ["A", "B"]
    assert plants[1].tracking == "single_axis"


def test_load_plants_rejects_unknown_fields(tmp_path):
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"name": "A", "latitude": 51, "longitude": 12, "capacity_dc_kwp": 1, "colour": "red"}))
    with pytest.raises(ValueError, match="colour"):
        load_plants(f)


def test_parse_ecmwf_index():
    lines = [
        {"param": "2t", "levtype": "sfc", "_offset": 0, "_length": 100},
        {"param": "t", "levtype": "pl", "_offset": 100, "_length": 50},
        {"param": "ssrd", "levtype": "sfc", "_offset": 150, "_length": 20},
    ]
    msgs = parse_ecmwf_index("\n".join(json.dumps(l) for l in lines), {"t2m": "2t", "ssrd": "ssrd", "x": "tp"})
    assert (msgs["t2m"].start, msgs["t2m"].end) == (0, 99)
    assert (msgs["ssrd"].start, msgs["ssrd"].end) == (150, 169)
    assert "x" not in msgs


def test_parse_gfs_index_averages_and_instants():
    idx = "\n".join([
        "1:0:d=2026110200:TMP:2 m above ground:7 hour fcst:",
        "2:500:d=2026110200:DSWRF:surface:6-7 hour ave fcst:",
        "3:900:d=2026110200:TCDC:entire atmosphere:7 hour fcst:",
        "4:1300:d=2026110200:TCDC:entire atmosphere:6-7 hour ave fcst:",
    ])
    want = {"t2m": ("TMP:2 m above ground", "inst"), "dswrf": ("DSWRF:surface", "avg"),
            "tcc": ("TCDC:entire atmosphere", "inst")}
    msgs = parse_gfs_index(idx, want, step=7)
    assert (msgs["t2m"].start, msgs["t2m"].end) == (0, 499)
    assert msgs["dswrf"].avg_window == (6, 7)
    assert (msgs["tcc"].start, msgs["tcc"].end) == (900, 1299)     # the instantaneous field, not the average
