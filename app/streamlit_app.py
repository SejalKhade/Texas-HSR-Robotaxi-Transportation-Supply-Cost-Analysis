"""
Streamlit dashboard — Texas HSR + Robotaxi Analysis
Run: streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import streamlit.components.v1 as components
import duckdb
import pandas as pd
import folium
from folium.plugins import MarkerCluster, AntPath
from src.config import DB_PATH, CITY_COORDS
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


def build_corridor_map(filtered: pd.DataFrame, all_results: pd.DataFrame) -> str:
    """Build Folium corridor map showing HSR routes across Texas."""
    # Texas center
    m = folium.Map(
        location=[31.0, -98.5],
        zoom_start=6,
        tiles="CartoDB dark_matter",
    )

    # Route colors
    ROUTE_COLORS = {
        "Dallas-Houston":     "#00CC96",
        "Dallas-Austin":      "#636EFA",
        "Houston-San Antonio":"#EF553B",
    }

    # City coordinates
    CITIES = {
        "Dallas":      [32.7767, -96.7970],
        "Houston":     [29.7604, -95.3698],
        "Austin":      [30.2672, -97.7431],
        "San Antonio": [29.4241, -98.4936],
    }

    # Route city pairs
    ROUTE_PAIRS = {
        "Dallas-Houston":      ("Dallas",  "Houston"),
        "Dallas-Austin":       ("Dallas",  "Austin"),
        "Houston-San Antonio": ("Houston", "San Antonio"),
    }

    # Aggregate KPIs per route
    high = all_results[all_results["scenario"] == "High"]
    route_kpis = high.set_index("route")

    # Draw animated route lines
    for route, (city_a, city_b) in ROUTE_PAIRS.items():
        coords = [CITIES[city_a], CITIES[city_b]]
        color  = ROUTE_COLORS.get(route, "#FFFFFF")
        riders = route_kpis.loc[route, "hsr_annual_riders"] if route in route_kpis.index else 0
        co2    = route_kpis.loc[route, "avoided_metric_tons_co2"] if route in route_kpis.index else 0

        # Animated dashed line (AntPath shows movement direction)
        AntPath(
            locations=coords,
            color=color,
            weight=4,
            delay=800,
            tooltip=f"<b>{route}</b><br>Annual riders (High): {riders:,.0f}<br>CO₂ avoided: {co2:,.0f} tons/yr",
        ).add_to(m)

        # Static thicker line behind animation
        folium.PolyLine(
            locations=coords,
            color=color,
            weight=2,
            opacity=0.4,
        ).add_to(m)

    # City markers with KPI popups
    marker_cluster = MarkerCluster(name="Cities").add_to(m)

    city_routes = {
        "Dallas":      ["Dallas-Houston", "Dallas-Austin"],
        "Houston":     ["Dallas-Houston", "Houston-San Antonio"],
        "Austin":      ["Dallas-Austin"],
        "San Antonio": ["Houston-San Antonio"],
    }

    for city, coords in CITIES.items():
        routes_here = city_routes.get(city, [])
        total_riders = sum(
            route_kpis.loc[r, "hsr_annual_riders"]
            for r in routes_here if r in route_kpis.index
        )
        popup_html = f"""
        <div style='font-family:sans-serif;min-width:150px'>
            <b style='font-size:14px'>{city}</b><br>
            <hr style='margin:4px 0'>
            <b>Connecting routes:</b><br>
            {'<br>'.join(routes_here) if routes_here else 'Hub only'}<br>
            <hr style='margin:4px 0'>
            <b>High adoption riders:</b><br>
            {total_riders:,.0f}/year
        </div>
        """
        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=city,
            icon=folium.Icon(
                color="white",
                icon_color="#1a1a2e",
                icon="train",
                prefix="fa",
            ),
        ).add_to(marker_cluster)

        # Circle showing relative ridership size
        folium.CircleMarker(
            location=coords,
            radius=max(8, min(25, total_riders / 100_000)),
            color="#FFD700",
            fill=True,
            fill_color="#FFD700",
            fill_opacity=0.3,
            weight=2,
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                background:#1a1a2e;padding:12px 16px;border-radius:8px;
                border:1px solid #444;font-family:sans-serif;font-size:12px;color:white">
        <b style="font-size:13px">HSR Corridors</b><br><br>
        <span style="color:#00CC96">●</span> Dallas – Houston (239 mi)<br>
        <span style="color:#636EFA">●</span> Dallas – Austin (195 mi)<br>
        <span style="color:#EF553B">●</span> Houston – San Antonio (197 mi)<br>
        <br>
        <span style="color:#FFD700">◎</span> Circle size = ridership volume
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl().add_to(m)
    return m._repr_html_()


# ── Header ───────────────────────────────────────────────────────────────────
st.title("🚄 Texas HSR + Robotaxi: Transportation Supply Cost Analysis")
st.markdown(
    "Quantifying cost, emissions, and demand impact of High-Speed Rail "
    "with autonomous first/last-mile service across Texas major corridors. "
    "**239-mile Dallas–Houston corridor • 7 public government datasets • "
    "3 adoption scenarios • 1,000 Monte Carlo simulations**"
)

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

# ── Load data ─────────────────────────────────────────────────────────────────
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

    # ── KPI Row ───────────────────────────────────────────────────────────────
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
        help="Door-to-door time saved vs driving (includes robotaxi first/last mile)"
    )
    cost_vs_flight = filtered["cost_savings_vs_flight_usd"].mean()
    cost_vs_car    = filtered["cost_savings_vs_car_usd"].mean()
    c5.metric(
        "Cost Saved vs Flight",
        f"${cost_vs_flight:.0f}",
        delta=f"${abs(cost_vs_car):.0f} {'more' if cost_vs_car < 0 else 'less'} than driving",
        delta_color="off",
        help=f"HSR saves ${cost_vs_flight:.0f} vs flying. "
             f"HSR costs ${abs(cost_vs_car):.0f} {'more' if cost_vs_car < 0 else 'less'} than driving — "
             f"time savings ({filtered['time_savings_vs_drive_hr'].mean():.1f} hrs) is the car advantage."
    )

    st.divider()

    # ── Interactive Corridor Map ──────────────────────────────────────────────
    st.subheader("🗺️ Texas HSR Corridor Map")
    st.caption("Animated lines show HSR routes. Circle size = ridership volume. Click city markers for KPI details.")
    map_html = build_corridor_map(filtered, all_results)
    components.html(map_html, height=480, scrolling=False)

    st.divider()

    # ── Charts Row 1: Mode shift + Cost ──────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(mode_shift_bar(filtered),     use_container_width=True)
    with col2:
        st.plotly_chart(cost_comparison_bar(filtered), use_container_width=True)

    # ── Charts Row 2: Scenario comparison + Ridership ─────────────────────────
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(scenario_co2_bar(all_results),        use_container_width=True)
    with col4:
        st.plotly_chart(riders_by_scenario_line(all_results), use_container_width=True)

    st.divider()

    # ── Monte Carlo ───────────────────────────────────────────────────────────
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

    # ── Grid demand ───────────────────────────────────────────────────────────
    st.subheader("⚡ ERCOT Grid Demand Impact")
    st.plotly_chart(grid_demand_bar(filtered), use_container_width=True)

    # ── Raw data expander ─────────────────────────────────────────────────────
    with st.expander("📋 View raw scenario results"):
        st.dataframe(filtered, use_container_width=True)

except Exception as e:
    st.error(
        "**Database not found.** Run the pipeline first:\n\n"
        "```bash\npython run_pipeline.py\n```\n\n"
        "Then refresh this page."
    )
    st.caption(f"Error detail: {e}")