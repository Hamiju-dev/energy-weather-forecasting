"""Shared configuration for the analysis pipeline of paper 01.

Every script in this folder imports its paths and study settings from here, so
the study design is defined in exactly one place.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths (all relative to this paper's folder, so the compendium is portable)
# --------------------------------------------------------------------------
PAPER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PAPER_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
LITERATURE_DIR = DATA_DIR / "literature"
GENERATED_TEX_DIR = PAPER_DIR / "paper" / "generated"

ISD_CACHE_DIR = DATA_DIR / "cache" / "noaa-isd"      # raw station files, as downloaded
POWER_CURVE_RAW_DIR = RAW_DIR / "turbine-power-curves"
CACHE_DIR = DATA_DIR / "cache"                      # re-creatable downloads, not versioned
FORECAST_PARTS_DIR = CACHE_DIR / "forecast-point-values"

# --------------------------------------------------------------------------
# Study period and forecast steps
# --------------------------------------------------------------------------
# One 00 UTC run per day; lead times every 12 h out to 10 days, so every
# forecast is verified at 00 UTC or 12 UTC.
INIT_FIRST = "2025-05-01"
INIT_LAST = "2025-07-31"
INIT_HOUR_UTC = 0
STEPS_H = list(range(0, 241, 12))

# --------------------------------------------------------------------------
# Forecast models (all public archives, no login needed)
# --------------------------------------------------------------------------
ECMWF_OPEN_DATA = "https://storage.googleapis.com/ecmwf-open-data"
GFS_ARCHIVE = "https://storage.googleapis.com/global-forecast-system"

MODELS = {
    "ifs": {
        "label": "ECMWF IFS",
        "kind": "ecmwf",
        "path": "ifs/0p25/oper",
        "params": {"u10": "10u", "v10": "10v", "t2m": "2t"},
    },
    "aifs": {
        "label": "ECMWF AIFS Single",
        "kind": "ecmwf",
        "path": "aifs-single/0p25/oper",
        "params": {"u10": "10u", "v10": "10v", "t2m": "2t"},
    },
    "gfs": {
        "label": "NOAA GFS",
        "kind": "gfs",
        "params": {
            "u10": "UGRD:10 m above ground",
            "v10": "VGRD:10 m above ground",
            "t2m": "TMP:2 m above ground",
        },
    },
}

# --------------------------------------------------------------------------
# Station observations (NOAA Integrated Surface Database, hourly)
# --------------------------------------------------------------------------
ISD_BUCKET = "https://noaa-isd-pds.s3.amazonaws.com"
ISD_YEAR = 2025
STATION_COUNTRY = "GM"            # ISD/FIPS code for Germany
STATION_MAX_ELEVATION_M = 600.0   # lowland sites only
STATION_ACTIVE_UNTIL = "20250820"
STATION_MIN_AVAILABILITY = 0.90   # share of verification times with a valid obs
OBS_MATCH_WINDOW_MIN = 30         # nearest report within +/- 30 min of valid time
CLIMATOLOGY_YEARS = [2020, 2021, 2022, 2023, 2024]   # out-of-sample reference climate
CLIMATOLOGY_MONTHS = [5, 6, 7, 8]

# --------------------------------------------------------------------------
# Wind power and bidding illustration
# --------------------------------------------------------------------------
TURBINE_TYPE = "V126/3450"        # from the OEDB turbine library bundled with windpowerlib
HUB_HEIGHT_M = 120.0
SHEAR_EXPONENT = 1.0 / 7.0        # neutral power-law profile, 10 m -> hub height
DAY_AHEAD_STEPS_H = (24, 36, 48)  # lead times treated as "day-ahead" from a 00 UTC run
BID_TRAIN_LAST_INIT = "2025-06-30"   # June: estimate error quantiles; July: test
BID_FORECAST_BINS = [-0.01, 0.0001, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 1.01]  # forecast power classes
BID_COST_LONG = 1.0               # cost per unit of surplus (under-forecast)
BID_COST_SHORT = 3.0              # cost per unit of shortfall (over-forecast)

# --------------------------------------------------------------------------
# PV clear-sky chain illustration
# --------------------------------------------------------------------------
PV_SITE = {"name": "Leipzig", "station_id": "104690-99999",
           "latitude": 51.424, "longitude": 12.236, "altitude": 142.0}
PV_DAY = "2025-06-21"
PV_PLANT = {
    "p_dc_kw": 10_000.0,          # 10 MWp DC
    "p_ac_kw": 7_700.0,           # DC/AC ratio 1.3
    "tilt_deg": 20.0,
    "azimuth_deg": 180.0,
    "gamma_pdc": -0.0035,         # 1/K
    "albedo": 0.20,
    "inverter_eta": 0.98,
}

# Verification design
EVAL_FIRST_INIT = "2025-06-01"   # May is used only to spin up the bias correction
BIAS_WINDOW_DAYS = 30            # running bias correction window (past errors only)
BIAS_MIN_SAMPLES = 10

# Bootstrap settings for confidence intervals (resampling initialisation days)
BOOTSTRAP_SAMPLES = 1000
RANDOM_SEED = 20251102
