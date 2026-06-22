"""
Core analytical models:
  - Gravity-based rider allocation
  - Energy and CO2 emissions calculation
  - Scenario runner (Low / Medium / High)
  - Monte Carlo sensitivity analysis
"""

import numpy as np
import pandas as pd

from src.config import (
    GRAVITY_WEIGHTS,
    HSR_KWH_PER_PASSENGER_MILE,
    ROBOTAXI_MILES_PER_KWH,
    AVG_CAR_OCCUPANCY,
    FIRST_LAST_MILE_DIST,
    DEADHEAD_MULTIPLIER,
    STATION_BASE_LOAD_MW,
    TRAIN_TRACTION_PEAK_MW,
    SCENARIOS,
)
from src.transform import normalize_series


def allocate_riders(baseline: pd.DataFrame, weekly_total: int) -> pd.DataFrame:
    """
    Distribute weekly HSR riders across routes using a gravity model.

    Gravity weights (from config):
      45% flight demand + 35% road demand + 20% population gravity score

    Mode shift:
      40% of HSR riders shift from flights (capped by available flight volume)
      Remainder shift from cars
    """
    df = baseline.copy()

    df["w_flight"]  = normalize_series(df["annual_flight_passengers_est"])
    df["w_road"]    = normalize_series(df["annual_road_person_trips_proxy"])
    df["w_gravity"] = normalize_series(df["population_gravity_score"])

    df["route_weight"] = (
        GRAVITY_WEIGHTS["flight"]  * df["w_flight"]
        + GRAVITY_WEIGHTS["road"]  * df["w_road"]
        + GRAVITY_WEIGHTS["gravity"] * df["w_gravity"]
    )

    # Normalize so weights sum to exactly 1
    weight_sum = df["route_weight"].sum()
    if weight_sum > 0:
        df["route_weight"] = df["route_weight"] / weight_sum

    df["hsr_weekly_riders"] = (weekly_total * df["route_weight"]).round().astype(int)
    df["hsr_annual_riders"] = df["hsr_weekly_riders"] * 52

    df["shift_from_flights"] = np.minimum(
        df["hsr_annual_riders"] * 0.40,
        df["annual_flight_passengers_est"]
    )
    df["shift_from_cars"] = np.maximum(
        df["hsr_annual_riders"] - df["shift_from_flights"], 0
    )

    return df


def add_energy_emissions(df: pd.DataFrame, ef: dict) -> pd.DataFrame:
    """
    Calculate energy demand and CO2 avoidance for each route.

    Parameters
    ----------
    df : output of allocate_riders()
    ef : emission factors dict {car_kg_per_vehicle_mile,
                                 flight_kg_per_passenger_mile,
                                 ercot_kg_per_kwh}
    """
    out = df.copy()

    # ── Energy ────────────────────────────────────────────────────────────
    flm_vmt_per_rider = FIRST_LAST_MILE_DIST * 2 * DEADHEAD_MULTIPLIER
    out["annual_robotaxi_vmt"] = out["hsr_annual_riders"] * flm_vmt_per_rider
    out["annual_robotaxi_kwh"] = out["annual_robotaxi_vmt"] / ROBOTAXI_MILES_PER_KWH

    out["annual_hsr_passenger_miles"] = out["hsr_annual_riders"] * out["distance_miles"]
    out["annual_hsr_kwh"]             = out["annual_hsr_passenger_miles"] * HSR_KWH_PER_PASSENGER_MILE

    out["annual_total_electric_kwh"] = out["annual_robotaxi_kwh"] + out["annual_hsr_kwh"]
    out["annual_total_electric_mwh"] = out["annual_total_electric_kwh"] / 1_000

    # ── Baseline CO2 (what cars + flights WOULD have emitted) ─────────────
    out["baseline_car_kg_co2"] = (
        (out["shift_from_cars"] / AVG_CAR_OCCUPANCY)
        * out["distance_miles"]
        * ef["car_kg_per_vehicle_mile"]
    )
    out["baseline_flight_kg_co2"] = (
        out["shift_from_flights"]
        * out["distance_miles"]
        * ef["flight_kg_per_passenger_mile"]
    )

    # ── New electric CO2 ──────────────────────────────────────────────────
    out["new_electric_kg_co2"] = (
        out["annual_total_electric_kwh"] * ef["ercot_kg_per_kwh"]
    )

    # ── Net CO2 avoided ───────────────────────────────────────────────────
    out["avoided_kg_co2"] = (
        out["baseline_car_kg_co2"]
        + out["baseline_flight_kg_co2"]
        - out["new_electric_kg_co2"]
    )
    out["avoided_metric_tons_co2"] = out["avoided_kg_co2"] / 1_000

    # ── Grid demand ───────────────────────────────────────────────────────
    out["avg_depot_mw"] = (out["annual_robotaxi_kwh"] * 0.90 / 365 / 24) / 1_000
    out["estimated_peak_mw"] = (
        STATION_BASE_LOAD_MW + TRAIN_TRACTION_PEAK_MW + out["avg_depot_mw"]
    )

    # ── Travel + cost savings ─────────────────────────────────────────────
    out["time_savings_vs_drive_hr"]  = out["drive_door_to_door_hr"]   - out["hsr_robotaxi_door_to_door_hr"]
    out["time_savings_vs_flight_hr"] = out["flight_door_to_door_hr"]  - out["hsr_robotaxi_door_to_door_hr"]
    out["cost_savings_vs_car_usd"]   = out["car_cost_usd"]            - out["hsr_robotaxi_cost_usd"]
    out["cost_savings_vs_flight_usd"]= out["flight_cost_usd"]         - out["hsr_robotaxi_cost_usd"]

    return out


def run_scenario(baseline: pd.DataFrame, ef: dict, scenario_name: str) -> pd.DataFrame:
    """
    Run full model pipeline for one scenario (Low / Medium / High).

    Returns enriched DataFrame with all KPI columns + scenario label.
    """
    if scenario_name not in SCENARIOS:
        raise ValueError(
            f"Unknown scenario '{scenario_name}'. Valid options: {list(SCENARIOS.keys())}"
        )
    cfg = SCENARIOS[scenario_name]
    df = allocate_riders(baseline, weekly_total=cfg["weekly_riders"])
    df = add_energy_emissions(df, ef)
    df["scenario"]          = scenario_name
    df["fare_usd"]          = cfg["fare_usd"]
    df["annual_revenue_usd"]= df["hsr_annual_riders"] * cfg["fare_usd"]
    return df


def run_all_scenarios(baseline: pd.DataFrame, ef: dict) -> pd.DataFrame:
    """Run all three scenarios and return stacked DataFrame."""
    return pd.concat(
        [run_scenario(baseline, ef, name) for name in SCENARIOS],
        ignore_index=True
    )


def monte_carlo(
    baseline: pd.DataFrame,
    ef: dict,
    n: int = 1_000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Monte Carlo sensitivity analysis — randomizes 4 key assumptions per run.

    Randomized inputs (uniform distributions):
      - weekly_riders : 10,000 – 70,000
      - fare_usd      : $40 – $110
      - emission factors: ±10% on each factor
      - model constants : ±5% via capacity factor

    Returns DataFrame of n rows, one per simulation, with aggregate KPIs.
    """
    import warnings
    warnings.filterwarnings("ignore")

    rng = np.random.default_rng(seed)
    records = []

    for _ in range(n):
        weekly_riders = int(rng.uniform(10_000, 70_000))
        fare          = float(rng.uniform(40, 110))
        ef_variant    = {k: v * rng.uniform(0.90, 1.10) for k, v in ef.items()}

        df  = allocate_riders(baseline, weekly_total=weekly_riders)
        df  = add_energy_emissions(df, ef_variant)

        records.append({
            "weekly_riders":           weekly_riders,
            "fare_usd":                round(fare, 2),
            "total_annual_riders":     int(df["hsr_annual_riders"].sum()),
            "total_avoided_tons_co2":  float(df["avoided_metric_tons_co2"].sum()),
            "total_revenue_usd":       float(df["hsr_annual_riders"].sum() * fare),
            "total_electric_mwh":      float(df["annual_total_electric_mwh"].sum()),
            "avg_cost_savings_vs_car": float(df["cost_savings_vs_car_usd"].mean()),
        })

    return pd.DataFrame(records)
