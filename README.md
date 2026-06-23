# Texas HSR + Robotaxi: Transportation Supply Cost Analysis

[![CI](https://github.com/SejalKhade/texas-hsr-robotaxi-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/SejalKhade/texas-hsr-robotaxi-analysis/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/database-DuckDB-f5c842.svg)](https://duckdb.org/)
[![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen.svg)](https://github.com/SejalKhade/texas-hsr-robotaxi-analysis/actions)
[![Dashboard](https://img.shields.io/badge/dashboard-live-red.svg)](https://texas-hsr-robotaxi-analysis-krq2zexxxymto8skk8p4bx.streamlit.app/)

End-to-end analytics pipeline quantifying the cost, emissions, and demand impact of High-Speed Rail with autonomous robotaxi first/last-mile service across three Texas corridors.

**[🚄 Live Dashboard →](https://texas-hsr-robotaxi-analysis-krq2zexxxymto8skk8p4bx.streamlit.app/)**

---

## Results

| Scenario | Weekly Riders | Annual Riders | CO₂ Avoided | Revenue |
|---|---|---|---|---|
| Low | 15,000 | 780,000 | 38,000 tons/yr | $66M |
| Medium | 35,000 | 1,820,000 | 87,000 tons/yr | $118M |
| High | 60,000 | 3,120,000 | 149,000 tons/yr | $156M |

**Monte Carlo — CO₂ avoidance (1,000 simulations):** P10 = 38K · P50 = 97K · P90 = 161K metric tons/year

**239-mile Dallas–Houston corridor — door-to-door comparison:**

| Mode | Cost | Time |
|---|---|---|
| Car | $65 | 4.25 hr |
| Flight | $180 | 3.60 hr |
| **HSR + Robotaxi** | **$78** | **2.20 hr** |

HSR saves **$102 vs flying** and **2.05 hr vs driving**.

---

## Architecture

```
data/raw/          ← 7 government datasets (TxDOT, BTS, ERCOT, EPA, Census)
    │
    ▼
src/ingest.py      ← per-source loaders with fallback handling
    │
    ▼
src/validate.py    ← Pandera schema checks (types, ranges, nulls)
    │
    ▼
src/transform.py   ← gravity score features, route baseline
    │
    ▼
src/model.py       ← gravity allocation · emissions · Monte Carlo (1,000 runs)
    │
    ▼
data/hsr_analysis.duckdb   ← SQL analytics layer
    │
    ▼
app/streamlit_app.py       ← interactive dashboard (Plotly + Folium)
```

---

## Data Sources

| Dataset | Source | Rows |
|---|---|---|
| TxDOT AADT 2024 | Texas DOT Open Data | 50K+ |
| BTS DB1B Q1 2025 | Bureau of Transportation Statistics | 2M+ |
| ERCOT Native Load 2025 | ERCOT Open Data | 8,760 |
| EPA GHG Factors 2025 | U.S. EPA | — |
| Census ACS 2024 — Dallas | U.S. Census Bureau | — |
| Census ACS 2024 — Houston | U.S. Census Bureau | — |
| TxDOT AADT Data Dictionary | Texas DOT | — |

---

## Methodology

**Rider allocation — gravity model:**
```
Route Weight = 0.45 × norm(flight demand)
             + 0.35 × norm(road person-trips)
             + 0.20 × norm(population gravity)

Population Gravity = (Pop_A × Pop_B) / Distance²
```

**Mode shift:** 40% of HSR riders shift from flights (capped by available flight volume), remainder from cars.

**Emissions:**
```
HSR energy       = passenger-miles × 0.083 kWh/pax-mile
Robotaxi VMT     = 8 mi × 2 ends × 1.30 deadhead per rider
New CO₂          = total kWh × 0.386 kg/kWh (ERCOT 2025)
Baseline CO₂     = car trips × mi × 0.404 + flight pax × mi × 0.255
Net CO₂ avoided  = Baseline − New
```

**Sensitivity:** Monte Carlo randomizes weekly ridership (10K–70K), fare ($40–$110), and emission factors (±10%) across 1,000 runs to produce confidence intervals.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Pipeline | Python · Pandas · NumPy |
| Database | DuckDB |
| Validation | Pandera |
| Testing | pytest (29 tests) · pytest-cov |
| CI/CD | GitHub Actions |
| Dashboard | Streamlit · Plotly · Folium |
| Linting | ruff |

---

## Setup

```bash
git clone https://github.com/SejalKhade/texas-hsr-robotaxi-analysis.git
cd texas-hsr-robotaxi-analysis
cp .env.example .env

make install     # pip install -r requirements.txt
make run         # load → validate → model → write DuckDB
make test        # 29 unit tests
make dashboard   # localhost:8501
```

Add source files to `data/raw/` before running — see [`data/raw/README.md`](data/raw/README.md) for download links.

---

## Project Structure

```
├── src/
│   ├── config.py       routes, constants, scenario definitions
│   ├── ingest.py       one loader per data source + DuckDB writer
│   ├── transform.py    gravity features, route baseline builder
│   ├── model.py        rider allocation, emissions, Monte Carlo
│   ├── validate.py     Pandera schemas — 4 validation gates
│   └── viz.py          Plotly chart builders
├── tests/
│   ├── test_model.py   22 model unit tests
│   └── test_validate.py 7 schema tests
├── app/
│   └── streamlit_app.py
├── .github/workflows/
│   └── ci.yml          lint + test on every push
├── run_pipeline.py
├── Makefile
└── requirements.txt
```

---

## Limitations

- Gravity weights (45/35/20) calibrated to Texas demand patterns — not validated against historical HSR data
- ERCOT emission factor (0.386 kg/kWh) is the 2025 annual average — varies by hour
- Robotaxi deadhead multiplier (1.30) is an industry estimate
- BTS DB1B sampled at 500K rows — full dataset improves air demand accuracy
- CAPEX excluded — model covers operating cost and emissions only

---

## Contact

**Sejal Khade** · [linkedin.com/in/sejallk](https://linkedin.com/in/sejallk) · [sejalkhade0023@gmail.com](mailto:sejalkhade0023@gmail.com)