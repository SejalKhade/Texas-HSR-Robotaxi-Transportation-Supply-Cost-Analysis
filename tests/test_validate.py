"""
Unit tests for src/validate.py — Pandera schema checks.
"""

import pytest
import pandas as pd
import pandera as pa
from src.validate import validate_population, validate_ercot, validate_baseline


def test_valid_population_passes():
    df = pd.DataFrame({
        "city":       ["Dallas", "Houston"],
        "population": [1_326_093, 2_387_910],
    })
    result = validate_population(df)
    assert len(result) == 2


def test_zero_population_fails():
    df = pd.DataFrame({"city": ["Dallas"], "population": [0]})
    with pytest.raises(pa.errors.SchemaError):
        validate_population(df)


def test_negative_population_fails():
    df = pd.DataFrame({"city": ["Dallas"], "population": [-500]})
    with pytest.raises(pa.errors.SchemaError):
        validate_population(df)


def test_valid_ercot_passes():
    df = pd.DataFrame({
        "HourEnding": ["01/01/2025 01:00"],
        "ERCOT_MWh":  [42_500.0],
    })
    result = validate_ercot(df)
    assert len(result) == 1


def test_zero_ercot_fails():
    df = pd.DataFrame({
        "HourEnding": ["01/01/2025 01:00"],
        "ERCOT_MWh":  [0.0],
    })
    with pytest.raises(pa.errors.SchemaError):
        validate_ercot(df)


def test_unrealistic_ercot_fails():
    df = pd.DataFrame({
        "HourEnding": ["01/01/2025 01:00"],
        "ERCOT_MWh":  [999_999.0],
    })
    with pytest.raises(pa.errors.SchemaError):
        validate_ercot(df)


def test_valid_baseline_passes():
    df = pd.DataFrame({
        "route":                          ["Dallas-Houston"],
        "distance_miles":                 [239.0],
        "annual_flight_passengers_est":   [3_200_000],
        "annual_road_person_trips_proxy": [28_000_000],
        "population_gravity_score":       [44_000_000_000.0],
        "car_cost_usd":                   [65.19],
        "hsr_robotaxi_cost_usd":          [77.58],
    })
    result = validate_baseline(df)
    assert len(result) == 1
