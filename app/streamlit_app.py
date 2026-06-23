"""
Streamlit dashboard — Texas HSR + Robotaxi Analysis
Run: streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import duckdb
import pandas as pd
from src.config import DB_PATH
from src.viz import (
    mode_shift_bar,
    cost_comparison_bar,
    scenario_co2_bar,
    monte_carlo_histogram,
    riders_by_scenario_line,
    grid_demand_bar,
)

st.set_page_config(
    page_title="Texas HSR + Robotaxi Analysis",
    page_icon="🚄",
    layout="wide",
)


@st.cache_resource
def _conn():
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data
def load_results():
    return _conn().execute("SELECT * FROM scenario_results").df()


@st.cache_data
def load_mc():
    return _conn().execute("SELECT * FROM monte_carlo_results").df()


# ── Header ──────────────────────────────────────────────────────────────────
st.title("🚄 Texas HSR + Robotaxi: Transportation Supply Cost Analysis")
st.markdown(
    "Quantifying cost, emissions, and demand impact of High-Speed Rail "
    "with autonomous first/last-mile service across Texas major corridors. "
    "**239-mile Dallas–Houston corridor • 7 public government datasets • "
    "3 adoption scenarios • 1,000 Monte Carlo simulations**"
)

# Data source indicator
import os
from src.config import FILES
files_present = sum(1 for p in FILES.values() if p.exists())
if files_present < len(FILES):
    st.info(
        f"ℹ️ **Running on model baseline data** ({files_present}/{len(FILES)} source files loaded). "
        "Add TxDOT, BTS, ERCOT, EPA, and Census files to `data/raw/` and rerun the pipeline "
        "to see results from real government data.",
        icon="📂"
    )
else:
    st.success(f"✅ All {files_present} government data sources loaded.", icon="📊")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Controls")
    scenario = st.selectbox(
        "Adoption Scenario",
        ["Low", "Medium", "High"],
        index=1,
        help="Low = 15K riders/week | Medium = 35K | High = 60K"
    )
    all_routes = ["Dallas-Houston", "Dallas-Austin", "Houston-San Antonio"]
    route_filter = st.multiselect(
        "Routes", options=all_routes, default=all_routes
    )
    st.divider()
    st.caption("Data sources: TxDOT, BTS, ERCOT, EPA, Census ACS 2024")

# ── Load data ────────────────────────────────────────────────────────────────
try:
    all_results = load_results()
    mc          = load_mc()

    filtered = all_results[
        (all_results["scenario"] == scenario) &
        (all_results["route"].isin(route_filter))
    ]

    if filtered.empty:
        st.warning("No data for selected filters. Adjust the sidebar controls.")
        st.stop()

    # ── KPI Row ──────────────────────────────────────────────────────────────
    st.subheader(f"📊 Key Performance Indicators — {scenario} Adoption")
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Annual Riders",
        f"{filtered['hsr_annual_riders'].sum():,.0f}",
        help="Total projected HSR passengers per year across selected routes"
    )
    c2.metric(
        "CO₂ Avoided (tons/yr)",
        f"{filtered['avoided_metric_tons_co2'].sum():,.0f}",
        help="Net CO₂ avoided vs car + flight baseline (accounting for ERCOT grid emissions)"
    )
    c3.metric(
        "Annual Revenue",
        f"${filtered['annual_revenue_usd'].sum()/1e6:.1f}M",
        help="Estimated ticket revenue at scenario fare price"
    )
    c4.metric(
        "Time Saved vs Driving",
        f"{filtered['time_savings_vs_drive_hr'].mean():.1f} hrs",
        help="Door-to-door time saved compared to driving (including robotaxi first/last mile)"
    )

    # Cost vs flight is the meaningful comparison — HSR competes with flying, not driving
    cost_vs_flight = filtered["cost_savings_vs_flight_usd"].mean()
    cost_vs_car    = filtered["cost_savings_vs_car_usd"].mean()
    c5.metric(
        "Cost Saved vs Flight",
        f"${cost_vs_flight:.0f}",
        delta=f"${abs(cost_vs_car):.0f} {'more' if cost_vs_car < 0 else 'less'} than driving",
        delta_color="off",
        help=f"HSR saves ${cost_vs_flight:.0f} vs flying. "
             f"HSR costs ${abs(cost_vs_car):.0f} {'more' if cost_vs_car < 0 else 'less'} than driving — "
             f"competitive advantage vs car is TIME ({filtered['time_savings_vs_drive_hr'].mean():.1f} hrs saved), not cost."
    )

    st.divider()

    # ── Row 1: Mode shift + Cost ──────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(mode_shift_bar(filtered),    use_container_width=True)
    with col2:
        st.plotly_chart(cost_comparison_bar(filtered), use_container_width=True)

    # ── Row 2: Scenario comparison + Ridership ────────────────────────────────
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(scenario_co2_bar(all_results),         use_container_width=True)
    with col4:
        st.plotly_chart(riders_by_scenario_line(all_results),  use_container_width=True)

    st.divider()

    # ── Row 3: Monte Carlo ────────────────────────────────────────────────────
    st.subheader("🎲 Monte Carlo Sensitivity Analysis (1,000 simulations)")
    st.caption(
        "Key assumptions randomized per simulation: "
        "weekly ridership ±35K • fare $40–$110 • emission factors ±10%"
    )
    mc_c1, mc_c2, mc_c3 = st.columns(3)
    mc_c1.metric("P10 CO₂ Avoided", f"{mc['total_avoided_tons_co2'].quantile(0.10):,.0f} tons")
    mc_c2.metric("P50 CO₂ Avoided", f"{mc['total_avoided_tons_co2'].quantile(0.50):,.0f} tons")
    mc_c3.metric("P90 CO₂ Avoided", f"{mc['total_avoided_tons_co2'].quantile(0.90):,.0f} tons")
    st.plotly_chart(monte_carlo_histogram(mc), use_container_width=True)

    st.divider()

    # ── Row 4: Grid demand ────────────────────────────────────────────────────
    st.subheader("⚡ ERCOT Grid Demand Impact")
    st.plotly_chart(grid_demand_bar(filtered), use_container_width=True)

    # ── Raw data expander ────────────────────────────────────────────────────
    with st.expander("📋 View raw scenario results"):
        st.dataframe(filtered, use_container_width=True)

except Exception as e:
    st.error(
        "**Database not found.** Run the pipeline first:\n\n"
        "```bash\npython run_pipeline.py\n```\n\n"
        "Then refresh this page."
    )
    st.caption(f"Error detail: {e}")
