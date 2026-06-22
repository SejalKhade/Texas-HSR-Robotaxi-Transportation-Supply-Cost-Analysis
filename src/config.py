"""
Central configuration — all paths and constants live here.
No hardcoded paths. Everything driven by .env file.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_RAW       = Path(os.getenv("DATA_RAW_DIR",       "./data/raw"))
DATA_PROCESSED = Path(os.getenv("DATA_PROCESSED_DIR", "./data/processed"))
DATA_OUTPUT    = Path(os.getenv("DATA_OUTPUT_DIR",    "./data/outputs"))
DB_PATH        = Path(os.getenv("DB_PATH",            "./data/hsr_analysis.duckdb"))

# ── Source file names ──────────────────────────────────────────────────────
FILES = {
    "aadt":           DATA_RAW / "TxDOT_AADT.csv",
    "aadt_dict":      DATA_RAW / "TxDOT_AADT_Data_Dictionary.csv",
    "ercot":          DATA_RAW / "Native_Load_2025.xlsx",
    "epa":            DATA_RAW / "ghg-emission-factors-hub-2025.csv",
    "census_dallas":  DATA_RAW / "census_dallas.csv",
    "census_houston": DATA_RAW / "census_houston.csv",
    "bts":            DATA_RAW / "db1b.public.202503.asc",
}

# ── Route definitions ──────────────────────────────────────────────────────
ROUTES = {
    "Dallas-Houston": {
        "cities":          ("Dallas", "Houston"),
        "distance_miles":  239,
        "drive_time_hr":   3.75,
        "flight_time_hr":  1.10,
        "corridor_roads":  ["IH0045", "I0045", "IH45", "I45"],
    },
    "Dallas-Austin": {
        "cities":          ("Dallas", "Austin"),
        "distance_miles":  195,
        "drive_time_hr":   3.25,
        "flight_time_hr":  0.90,
        "corridor_roads":  ["IH0035", "I35"],
    },
    "Houston-San Antonio": {
        "cities":          ("Houston", "San Antonio"),
        "distance_miles":  197,
        "drive_time_hr":   3.00,
        "flight_time_hr":  0.85,
        "corridor_roads":  ["IH0010", "I10"],
    },
}

# ── City coordinates for maps ──────────────────────────────────────────────
CITY_COORDS = {
    "Dallas":      [32.7767, -96.7970],
    "Houston":     [29.7604, -95.3698],
    "Austin":      [30.2672, -97.7431],
    "San Antonio": [29.4241, -98.4936],
    "Fort Worth":  [32.7555, -97.3308],
}

# ── Population fallbacks if Census fails ───────────────────────────────────
CITY_POP_FALLBACK = {
    "Dallas":      1_326_093,
    "Houston":     2_387_910,
    "Austin":      1_000_000,
    "San Antonio": 1_500_000,
    "Fort Worth":    989_878,
}

# ── Gravity model weights (must sum to 1.0) ────────────────────────────────
GRAVITY_WEIGHTS = {
    "flight":  0.45,
    "road":    0.35,
    "gravity": 0.20,
}

# ── Physics/engineering constants ──────────────────────────────────────────
HSR_KWH_PER_PASSENGER_MILE = 0.083      # kWh per passenger-mile (Amtrak Acela reference)
ROBOTAXI_MILES_PER_KWH     = 3.5        # miles per kWh (Waymo/Tesla robotaxi estimate)
AVG_CAR_OCCUPANCY           = 1.6       # persons per vehicle (US average)
FIRST_LAST_MILE_DIST        = 8.0       # miles each end by robotaxi
DEADHEAD_MULTIPLIER         = 1.30      # 30% extra miles for empty repositioning
STATION_BASE_LOAD_MW        = 2.5       # MW station HVAC/lighting baseline
TRAIN_TRACTION_PEAK_MW      = 12.0      # MW peak traction draw per trainset

# ── Scenarios ──────────────────────────────────────────────────────────────
SCENARIOS = {
    "Low":    {"weekly_riders": 15_000, "fare_usd": 85},
    "Medium": {"weekly_riders": 35_000, "fare_usd": 65},
    "High":   {"weekly_riders": 60_000, "fare_usd": 50},
}
