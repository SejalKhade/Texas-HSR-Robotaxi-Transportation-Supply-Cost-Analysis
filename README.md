# Texas HSR + Robotaxi: Transportation Supply Cost Analysis

[![CI](https://github.com/SejalKhade/texas-hsr-robotaxi-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/SejalKhade/texas-hsr-robotaxi-analysis/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/database-DuckDB-yellow)](https://duckdb.org/)
[![Streamlit](https://img.shields.io/badge/dashboard-live-red)](https://texas-hsr-robotaxi-analysis-krq2zexxxymto8skk8p4bx.streamlit.app/)
[![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen)](https://github.com/SejalKhade/texas-hsr-robotaxi-analysis/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Problem

Texas moves 40M+ annual passengers between Dallas, Houston, Austin, and San Antonio — primarily by car (3.75 hr) and plane (1.1 hr). Both modes are high-cost and carbon-intensive.

**Business question:** At what adoption level does High-Speed Rail + autonomous robotaxi first/last-mile service become cost-competitive with flying — and what is the CO₂ and grid demand impact at each level?

---

## Live Dashboard

### [🚄 View Interactive Dashboard →](https://texas-hsr-robotaxi-analysis-krq2zexxxymto8skk8p4bx.streamlit.app/)

Features:
- Interactive Texas corridor map with animated HSR routes
- Scenario selector (Low / Medium / High adoption)
- 5 live KPI cards updating in real time
- Mode shift, cost comparison, and ridership charts
- Monte Carlo distribution with P10/P50/P90 confidence lines
- ERCOT grid demand impact by corridor
- Raw data table (expandable)

---

## Key Findings

| Scenario | Weekly Riders | Annual Riders | CO₂ Avoided | Revenue |
|---|---|---|---|---|
| Low Adoption | 15,000 | 780,000 | 38,000 tons/yr | $66M |
| Medium Adoption | 35,000 | 1,820,000 | 87,000 tons/yr | $118M |
| High Adoption | 60,000 | 3,120,000 | 149,000 tons/yr | $156M |

**Monte Carlo (1,000 simulations):** CO₂ P10 / P50 / P90 = 38K / 97K / 161K metric tons/year

**Cost comparison — 239-mile Dallas–Houston corridor:**

| Mode | Door-to-door cost | Door-to-door time |
|---|---|---|
| Car | $65 | 4.25 hr |
| Flight | $180 | 3.60 hr |
| HSR + Robotaxi | $78 | 2.20 hr |

HSR saves **$102 vs flying** and **2.05 hours vs driving** door-to-door.

---

## Data Sources

| Dataset | Source | Purpose |
|---|---|---|
| TxDOT AADT 2024 | Texas DOT Open Data | Highway traffic volume baseline |
| BTS DB1B Q1 2025 | Bureau of Transportation Statistics | Air passenger O-D flow |
| ERCOT Native Load 2025 | ERCOT Open Data | Grid demand impact calculation |
| EPA GHG Factors 2025 | U.S. EPA | CO₂ emission rates per mode per mile |
| Census ACS 2024 — Dallas | U.S. Census Bureau | Population gravity model |
| Census ACS 2024 — Houston | U.S. Census Bureau | Population gravity model |
| TxDOT AADT Data Dictionary | Texas DOT | Schema mapping and column definitions |

---

## Methodology

### 1. Gravity Model (Rider Allocation)
```
Route Weight = 0.45 × normalized(flight demand)
             + 0.35 × normalized(road person-trips)
             + 0.20 × normalized(population gravity)

Population Gravity = (Pop_A × Pop_B) / Distance²
```
Weights normalized to sum = 1.0. Routes with higher flight demand and population receive proportionally more HSR riders.

### 2. Mode Shift
- 40% of HSR riders shift from flights (capped by available flight volume)
- Remaining riders shift from car trips

### 3. Energy and CO₂ Model
```
HSR energy      = passenger-miles × 0.083 kWh/pax-mile
Robotaxi VMT    = 8 mi × 2 × 1.30 deadhead per rider
New CO₂         = total kWh × 0.386 kg/kWh (ERCOT 2025 grid average)

Baseline CO₂    = (car trips / 1.6 occupancy) × miles × 0.404 kg/vehicle-mile
                + flight pax × miles × 0.255 kg/pax-mile

Net CO₂ avoided = Baseline − New electric CO₂
```

### 4. Monte Carlo Sensitivity (1,000 runs)
Randomizes 4 inputs per simulation:
- Weekly ridership: 10K–70K (uniform)
- Fare: $40–$110 (uniform)
- Emission factors: ±10% (uniform)

Produces P10/P50/P90 confidence intervals for CO₂ avoidance and revenue.

---

## Tech Stack

| Layer | Tool | Why chosen |
|---|---|---|
| Language | Python 3.11 | Industry standard for data analytics |
| Data ingestion | Pandas | Per-source loading with fallback handling |
| Database | DuckDB | SQL analytics layer, zero infrastructure needed |
| Data validation | Pandera | Schema checks with clear error messages |
| Modeling | NumPy | Gravity model, emissions, Monte Carlo |
| Testing | pytest + pytest-cov | 29 unit tests, 100% model coverage |
| CI/CD | GitHub Actions | Lint + test on every push and PR |
| Dashboard | Streamlit + Plotly + Folium | Interactive scenario explorer with map |
| Linting | ruff | Fast Python linter |

---

## Setup

### Prerequisites
- Python 3.11+
- Raw data files in `data/raw/` (see `data/raw/README.md`)

### Quick start
```bash
git clone https://github.com/SejalKhade/texas-hsr-robotaxi-analysis.git
cd texas-hsr-robotaxi-analysis

cp .env.example .env
make install    # pip install -r requirements.txt
make run        # loads data → builds DuckDB → runs model
make test       # 29 unit tests
make dashboard  # launches Streamlit at localhost:8501
```

### Without Make
```bash
pip install -r requirements.txt
python run_pipeline.py
pytest tests/ -v
streamlit run app/streamlit_app.py
```

---

## Project Structure

```
texas-hsr-robotaxi-analysis/
├── src/
│   ├── config.py       # paths, route definitions, model constants, scenarios
│   ├── ingest.py       # one function per data source + DuckDB writer
│   ├── transform.py    # baseline builder, gravity score features
│   ├── model.py        # gravity model, emissions, scenarios, Monte Carlo
│   ├── validate.py     # Pandera schemas — 4 data quality gates
│   └── viz.py          # 6 Plotly chart builders
├── tests/
│   ├── test_model.py   # 22 unit tests (gravity, emissions, scenarios, MC)
│   └── test_validate.py # 7 schema validation tests
├── app/
│   └── streamlit_app.py # Streamlit dashboard with corridor map
├── data/
│   ├── raw/            # source files (gitignored — see raw/README.md)
│   └── processed/      # pipeline outputs
├── .github/workflows/
│   └── ci.yml          # GitHub Actions: lint + test on every push
├── run_pipeline.py     # main entry point — check → load → validate → model → save
├── Makefile
├── requirements.txt
└── .env.example
```

---

## Assumptions and Limitations

- Gravity model weights (45/35/20) calibrated to known Texas demand patterns but not validated against historical HSR ridership data
- ERCOT emission factor (0.386 kg/kWh) is the 2025 annual average — actual factor varies by hour and fuel mix
- Robotaxi deadhead multiplier (1.30) is an industry estimate, not observed operational data
- BTS DB1B sampled at 500K rows for memory efficiency — full dataset improves accuracy
- CAPEX ($20–30B construction cost) is excluded — model focuses on operating cost and emissions

---

## Recruiter FAQ — Common Interview Questions

### "Walk me through your methodology."
The model has three layers. First, a gravity model allocates weekly HSR riders across routes weighted by flight demand (45%), road traffic (35%), and population gravity (20%). Second, mode shift distributes those riders between people shifting from flights vs. cars. Third, the emissions model calculates new ERCOT grid demand and net CO₂ avoidance against the baseline. I ran 1,000 Monte Carlo simulations randomizing the key assumptions to produce confidence intervals rather than single-point estimates.

### "Why DuckDB instead of Pandas for the data layer?"
DuckDB gives a SQL analytics layer on top of the processed data without needing a database server. The dashboard queries results directly via SQL, which mirrors how an analyst would interact with a data warehouse like BigQuery or Snowflake. Pandas alone would mean reloading CSVs on every dashboard interaction.

### "How do you ensure data quality?"
Pandera schemas validate every DataFrame before it enters the model — checking column types, value ranges, and null constraints. If ERCOT data arrives with a zero load value or a population figure outside plausible bounds, the pipeline exits with a clear error message rather than silently propagating bad data downstream. That approach caught a 15% metric inflation issue in my professional experience.

### "What would you do differently with more time?"
Three things. First, pull live ERCOT API data on a weekly schedule using GitHub Actions to keep the emission factor current. Second, add a proper dbt modeling layer so data transformations are tested, documented, and versioned with lineage. Third, validate the gravity model weights against actual Texas ridership surveys to replace the calibrated estimates with empirically grounded parameters.

### "Why HSR + robotaxi specifically?"
The core insight is that HSR fails on first/last-mile access — most Texas stations would be 8+ miles from where people actually are. Pairing HSR with autonomous robotaxi solves the access problem at lower cost than car ownership. The project models that combined system against the realistic door-to-door alternative, not just the train segment in isolation.

### "Can this model be extended?"
Yes. The route definitions, city coordinates, and scenario parameters are all in `config.py` — adding a new corridor is 8 lines of configuration. The model and dashboard adapt automatically because they read from the config rather than hardcoding route logic.

---

## Contact

**Sejal Khade**
[linkedin.com/in/sejallk](https://linkedin.com/in/sejallk) · [sejalkhade0023@gmail.com](mailto:sejalkhade0023@gmail.com) · [github.com/SejalKhade](https://github.com/SejalKhade)