# Texas HSR + Robotaxi: Transportation Supply Cost Analysis

[![CI](https://github.com/SejalKhade/texas-hsr-robotaxi-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/SejalKhade/texas-hsr-robotaxi-analysis/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/database-DuckDB-yellow)](https://duckdb.org/)
[![Streamlit](https://img.shields.io/badge/dashboard-Streamlit-red)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Problem

Texas moves 40M+ annual passengers between Dallas, Houston, Austin, and San Antonio — primarily by car (3.75 hr) and plane (1.1 hr). Both modes are high-cost and carbon-intensive.

**Business question:** At what adoption level does High-Speed Rail + robotaxi first/last-mile service become cost-competitive with driving and flying — and what is the CO₂ and grid demand impact at each level?

---

## Live Dashboard

[🚄 View Interactive Dashboard →](https://your-streamlit-url.streamlit.app)

---

## Key Findings

| Scenario | Weekly Riders | Annual Riders | CO₂ Avoided | Est. Revenue |
|---|---|---|---|---|
| Low Adoption | 15,000 | 780,000 | 284,000 tons/yr | $66M |
| Medium Adoption | 35,000 | 1,820,000 | 661,000 tons/yr | $117M |
| High Adoption | 60,000 | 3,120,000 | 1,100,000 tons/yr | $155M |

**Monte Carlo (1,000 simulations):** CO₂ P10 / P50 / P90 = 190K / 660K / 1.4M metric tons/year

**Cost comparison — 239-mile Dallas–Houston corridor:**

| Mode | Door-to-door cost | Door-to-door time |
|---|---|---|
| Car | $65 | 4.25 hr |
| Flight | $180 | 3.60 hr |
| HSR + Robotaxi | $78 | 2.20 hr |

---

## Data Sources

| Dataset | Source | Rows | Purpose |
|---|---|---|---|
| TxDOT AADT 2024 | Texas DOT Open Data | 50K+ | Highway traffic volume |
| BTS DB1B Q1 2025 | Bureau of Transportation Statistics | 2M+ | Air passenger O-D flow |
| ERCOT Native Load 2025 | ERCOT Open Data | 8,760 | Grid demand modeling |
| EPA GHG Factors 2025 | U.S. EPA | — | CO₂ emission rates |
| Census ACS 2024 — Dallas | U.S. Census Bureau | — | Population gravity |
| Census ACS 2024 — Houston | U.S. Census Bureau | — | Population gravity |
| TxDOT AADT Data Dictionary | Texas DOT | — | Schema mapping |

---

## Methodology

### 1. Gravity Model (Rider Allocation)
```
Route Weight = 0.45 × normalized(flight demand)
             + 0.35 × normalized(road person-trips)
             + 0.20 × normalized(population gravity)

Population Gravity Score = (Pop_A × Pop_B) / Distance²
```

Weights normalized to sum = 1.0 across all routes.

### 2. Mode Shift
- 40% of HSR riders shift from flights (capped by available flight volume)
- Remaining riders shift from cars

### 3. Energy and CO₂ Model
```
HSR energy        = passenger-miles × 0.083 kWh/pax-mile
Robotaxi VMT      = (8 mi × 2 × 1.30 deadhead) per rider
New CO₂ emitted   = total kWh × 0.386 kg/kWh (ERCOT grid avg)

Baseline CO₂      = (car trips / 1.6 occupancy) × miles × 0.404 kg/vehicle-mile
                  + flight pax × miles × 0.255 kg/pax-mile

Net CO₂ avoided   = Baseline CO₂ − New electric CO₂
```

### 4. Monte Carlo Sensitivity
1,000 simulations randomizing:
- Weekly ridership: 10K–70K (uniform)
- Fare: $40–$110 (uniform)
- Emission factors: ±10% (uniform)

Produces P10/P50/P90 confidence intervals for all KPIs.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Language | Python 3.11 | |
| Data ingestion | Pandas | Per-source loading functions |
| Database | DuckDB | SQL analytics layer, zero server needed |
| Data validation | Pandera | Schema checks before model runs |
| Modeling | NumPy | Gravity model, emissions, Monte Carlo |
| Testing | pytest + pytest-cov | 22 unit tests, model + schema |
| CI/CD | GitHub Actions | Runs lint + tests on every push and PR |
| Dashboard | Streamlit + Plotly | Interactive scenario explorer |
| Linting | ruff | |

---

## Setup

### Prerequisites
- Python 3.11+
- Raw data files in `data/raw/` (see `data/raw/README.md` for sources)

### Quick start

```bash
# 1. Clone
git clone https://github.com/SejalKhade/texas-hsr-robotaxi-analysis.git
cd texas-hsr-robotaxi-analysis

# 2. Copy your .env
cp .env.example .env

# 3. Install
make install

# 4. Run pipeline (loads data → builds DuckDB)
make run

# 5. Run tests
make test

# 6. Launch dashboard
make dashboard
```

### Manual steps (without Make)

```bash
pip install -r requirements.txt
python run_pipeline.py
pytest tests/ -v
streamlit run app/streamlit_app.py
```

---

## Project Structure

```
texas-hsr-robotaxi/
├── src/
│   ├── config.py       # paths, route definitions, model constants, scenarios
│   ├── ingest.py       # one function per data source + DuckDB writer
│   ├── transform.py    # baseline builder, feature engineering
│   ├── model.py        # gravity model, emissions, Monte Carlo
│   ├── validate.py     # Pandera schemas for data quality gates
│   └── viz.py          # Plotly chart builders
├── tests/
│   ├── test_model.py   # 16 unit tests (gravity, emissions, scenarios, MC)
│   └── test_validate.py # 6 schema validation tests
├── app/
│   └── streamlit_app.py # Streamlit dashboard
├── data/
│   ├── raw/            # source files — gitignored, see raw/README.md
│   └── processed/      # pipeline outputs
├── .github/workflows/
│   └── ci.yml          # GitHub Actions: lint → test on every push
├── run_pipeline.py     # main entry point
├── Makefile            # install / run / test / dashboard / clean
├── requirements.txt
└── .env.example
```

---

## Assumptions and Limitations

- Gravity model weights (45/35/20) are calibrated to known Texas ridership patterns but not validated against historical HSR data
- BTS DB1B is sampled at 500K rows for memory efficiency; full dataset would improve air demand accuracy
- ERCOT grid emission factor (0.386 kg/kWh) is the 2025 annual average; actual factor varies by hour and fuel mix
- Robotaxi deadhead multiplier (1.30) is an industry estimate, not observed
- CAPEX (construction cost $20–30B) is excluded; focus is operating cost and emissions

---

## Contact

**Sejal Khade**
[linkedin.com/in/sejallk](https://linkedin.com/in/sejallk) · [sejalkhade0023@gmail.com](mailto:sejalkhade0023@gmail.com) · [github.com/SejalKhade](https://github.com/SejalKhade)
