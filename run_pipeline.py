"""
Main pipeline entry point.
Usage: python run_pipeline.py

Full pipeline:
  check files → load → validate → transform → model → monte carlo → save to DuckDB
"""

import sys
import pandera.errors

from src.ingest    import (load_population, load_ercot, load_epa_factors,
                            load_aadt, load_bts, check_all_files, write_to_db)
from src.transform import build_route_baseline
from src.validate  import validate_population, validate_ercot, validate_baseline, validate_results
from src.model     import run_all_scenarios, monte_carlo


def main() -> int:
    print("=" * 60)
    print("Texas HSR + Robotaxi  |  Analytics Pipeline")
    print("=" * 60)

    # ── 1. File check ──────────────────────────────────────────────────────
    print("\n[1/6] Checking source files...")
    status  = check_all_files()
    missing = [k for k, ok in status.items() if not ok]
    if missing:
        print(f"  ❌ Missing: {missing}")
        print("  → Add them to data/raw/ and rerun.")
        return 1
    print(f"  ✅ All {len(status)} files present")

    # ── 2. Load ────────────────────────────────────────────────────────────
    print("\n[2/6] Loading data...")
    pop_df   = load_population()
    ercot_df = load_ercot()
    ef       = load_epa_factors()
    aadt_df  = load_aadt()
    bts_df   = load_bts()
    print(f"  Population  : {len(pop_df)} cities")
    print(f"  ERCOT       : {len(ercot_df):,} hourly records")
    print(f"  AADT        : {len(aadt_df):,} rows")
    print(f"  BTS (sample): {len(bts_df):,} rows")

    # ── 3. Validate ────────────────────────────────────────────────────────
    print("\n[3/6] Validating data...")
    try:
        validate_population(pop_df)
        validate_ercot(ercot_df)
        print("  ✅ All schema checks passed")
    except pandera.errors.SchemaError as exc:
        print(f"  ❌ Validation failed:\n  {exc}")
        return 1

    # ── 4. Transform ───────────────────────────────────────────────────────
    print("\n[4/6] Building route baseline...")
    baseline = build_route_baseline(pop_df, aadt_df, bts_df)
    try:
        validate_baseline(baseline)
    except pandera.errors.SchemaError as exc:
        print(f"  ❌ Baseline validation failed:\n  {exc}")
        return 1
    print(f"  ✅ Baseline ready — {len(baseline)} routes")
    for _, row in baseline.iterrows():
        print(f"     {row['route']:25s}  {row['distance_miles']:.0f} mi  "
              f"pop_gravity={row['population_gravity_score']:.2e}")

    # ── 5. Scenarios ───────────────────────────────────────────────────────
    print("\n[5/6] Running scenarios (Low / Medium / High)...")
    results = run_all_scenarios(baseline, ef)
    try:
        validate_results(results)
    except pandera.errors.SchemaError as exc:
        print(f"  ❌ Results validation failed:\n  {exc}")
        return 1
    print(f"  ✅ {len(results)} result rows")

    # ── 6. Monte Carlo ────────────────────────────────────────────────────
    print("\n[6/6] Running Monte Carlo (1,000 simulations)...")
    mc = monte_carlo(baseline, ef, n=1_000)
    p10 = mc["total_avoided_tons_co2"].quantile(0.10)
    p50 = mc["total_avoided_tons_co2"].quantile(0.50)
    p90 = mc["total_avoided_tons_co2"].quantile(0.90)
    print(f"  CO₂ avoided P10/P50/P90: {p10:,.0f} / {p50:,.0f} / {p90:,.0f} metric tons/yr")

    # ── Save ──────────────────────────────────────────────────────────────
    write_to_db(baseline, results, mc, ef)

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for scenario in ["Low", "Medium", "High"]:
        s = results[results["scenario"] == scenario]
        print(f"\n  {scenario} Adoption ({s['fare_usd'].iloc[0]:.0f}/ticket):")
        print(f"    Annual riders    : {s['hsr_annual_riders'].sum():>12,}")
        print(f"    CO₂ avoided      : {s['avoided_metric_tons_co2'].sum():>12,.0f} tons/yr")
        print(f"    Annual revenue   : ${s['annual_revenue_usd'].sum():>11,.0f}")
        print(f"    ERCOT peak add   : {s['estimated_peak_mw'].sum():>12.1f} MW")

    print("\n✅ Pipeline complete. Launch dashboard: make dashboard\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
