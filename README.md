# ✈️ African Air Traffic Platform (Local Medallion Lakehouse & Warehouse)

An end-to-end, production-style **Medallion Data Lakehouse & Warehouse Pipeline** built locally on macOS with Python, Pandas, Columnar Parquet storage, and Microsoft SQL Server 2022 running in Docker.

This platform ingests live telemetry state vectors across the West African airspace (covering Ghana, Nigeria, Ivory Coast, Senegal, and the Atlantic Flight Information Region) via the OpenSky Network REST API, performs defensive validation and data cleansing, and models an analytics-ready Star Schema warehouse.


## 🏗️ Architecture & Data Flow

```text
 ┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
 │     Bronze Layer (Raw)    │ ───► │   Silver Layer (Clean)    │ ───► │    Gold Layer (Warehouse)  │
 │                           │      │                           │      │                           │
 │  • OpenSky REST API       │      │  • Data Quality Checks    │      │  • Microsoft SQL Server   │
 │  • Mock Fallback Engine   │      │  • Null Coordinate Drop   │      │    (Docker Container)     │
 │  • Raw JSON Landings      │      │  • Unix to UTC Datetime   │      │  • DimAircraft (Dim)      │
 │  • data/bronze/*.json     │      │  • Standardized Columnar  │      │  • FactFlightPositions    │
 │                           │      │  • data/silver/*.parquet  │      │    (Incremental Fact)     │
 └───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘




##🛠️ Tech Stack & Engineering Decisions

* **Language & Core:** Python 3.9+, Pandas
* **Ingestion:** HTTP `requests` consuming the OpenSky Network REST API with an automated defensive synthetic fallback generator.
* **Storage Layer:** Columnar Apache Parquet (`pyarrow`) for Silver data quality preservation and storage compression.
* **Database & Warehouse:** Microsoft SQL Server 2022 (`mcr.microsoft.com/mssql/server`) running in **Docker**.
* **ORM & Database Drivers:** `SQLAlchemy`, `pymssql`.
* **Project Management & CI:** GitHub Projects Kanban Board, Semantic Git Branching & Commits.

---

## 🌟 Key Engineering Highlights & Solutions

* **Defensive API Ingestion:**
  * Handled real-world rate limits and transient network timeouts by pairing live REST API calls with an automated synthetic fallback generator that maintains strict schema compliance.
* **Data Quality & Cleansing Rules (Silver Layer):**
  * Filtered out corrupt telemetry records missing valid Latitude/Longitude coordinate pairs.
  * Converted raw Unix epoch integer timestamps to standardized ISO UTC datetimes (`YYYY-MM-DD HH:MM:SS+00:00`).
  * Stripped trailing whitespace and normalized callsigns and ICAO24 hex codes.
* **Relational Star Schema Modeling & Type Safety (Gold Layer):**
  * **Dimension Table (`DimAircraft`):** Deduplicated aircraft metadata (`icao24`, `callsign`, `origin_country`).
  * **Fact Table (`FactFlightPositions`):** High-volume time-series positioning vectors (`latitude`, `longitude`, `baro_altitude`, `velocity`, `time_position_utc`).
  * **SQL Server Type Collisions Resolved:** Explicitly mapped timestamp fields to SQLAlchemy `DATETIME2` types to prevent collisions with legacy T-SQL `TIMESTAMP` (`rowversion`) binary types.
  * **Incremental Appending:** Configured fact table persistence to `append` mode, enabling continuous real-time historical data accumulation.

---

## 📂 Repository Structure

```text
african-air-traffic-local/
├── data/
│   ├── bronze/               # Raw JSON API snapshots (ignored in .gitignore)
│   ├── silver/               # Cleansed Parquet columnar payloads
│   └── gold/                 # Local warehouse outputs
├── scripts/
│   ├── extract_bronze.py     # Bronze ingestion & mock fallback
│   ├── transform_silver.py   # Silver data quality & transformations
│   └── load_gold.py          # Gold SQL Server Star Schema loader
├── .gitignore                # Protects secrets, cache, and large binaries
├── README.md                 # System architecture & documentation
└── requirements.txt          # Python dependencies