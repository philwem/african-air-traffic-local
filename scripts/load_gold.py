import glob
import os
import pandas as pd
from sqlalchemy import create_engine, text, DateTime
from sqlalchemy.types import DateTime as SQLDateTime

# 1. Setup Base Paths
script_path = os.path.abspath(__file__)
BASE_DIR = os.path.dirname(os.path.dirname(script_path))
SILVER_DIR = os.path.join(BASE_DIR, "data", "silver")

# 2. SQL Server Docker Connection Parameters
DB_USER = "sa"
DB_PASS = "YourStrong!Passw0rd"  # Your verified container password
DB_HOST = "127.0.0.1"
DB_PORT = "1433"
DB_NAME = "AirTrafficDB"

SERVER_URL = f"mssql+pymssql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/master"
DATABASE_URL = f"mssql+pymssql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def ensure_database_exists():
    """Connects to master DB and creates AirTrafficDB if it does not exist."""
    print("[GOLD LOAD] Ensuring AirTrafficDB exists in SQL Server...")
    engine_master = create_engine(SERVER_URL, isolation_level="AUTOCOMMIT")
    with engine_master.connect() as conn:
        conn.execute(
            text(
                f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{DB_NAME}') "
                f"CREATE DATABASE [{DB_NAME}];"
            )
        )
    engine_master.dispose()


def load_silver_to_sql_server():
    """Reads latest Silver Parquet file and loads data directly into SQL Server in Docker."""
    ensure_database_exists()

    print("[GOLD LOAD] Searching for latest Silver Parquet file...")
    silver_files = glob.glob(os.path.join(SILVER_DIR, "*.parquet"))
    if not silver_files:
        print(
            "[ERROR] No Parquet files found in data/silver/. Run transform_silver.py first!")
        return

    latest_file = max(silver_files, key=os.path.getmtime)
    print(
        f"[GOLD LOAD] Reading Silver payload: {os.path.basename(latest_file)}")

    df = pd.read_parquet(latest_file)

    print(
        f"[GOLD LOAD] Connecting to Microsoft SQL Server database ({DB_NAME})...")
    engine = create_engine(DATABASE_URL)

    # 1. Model DimAircraft (Dimension Table)
    dim_aircraft = df[["icao24", "callsign", "origin_country"]
                      ].drop_duplicates(subset=["icao24"]).copy()
    dim_aircraft.to_sql("DimAircraft", engine,
                        if_exists="replace", index=False)
    print(
        f"[SUCCESS] Loaded {len(dim_aircraft)} records into SQL Server table: DimAircraft")

    # 2. Model FactFlightPositions (Fact Table)
    fact_positions = df[
        [
            "icao24",
            "time_position_utc",
            "latitude",
            "longitude",
            "baro_altitude",
            "velocity",
            "on_ground",
        ]
    ].copy()

    # Explicitly map time_position_utc to DateTime and APPEND new records!
    fact_positions.to_sql(
        "FactFlightPositions",
        engine,
        if_exists="append",  # <-- CHANGE THIS FROM "replace" TO "append"
        index=False,
        dtype={"time_position_utc": SQLDateTime()}
    )
    print(
        f"[SUCCESS] Loaded {len(fact_positions)} records into SQL Server table: FactFlightPositions")

    # 3. Verification T-SQL Query
    print("\n--- VERIFYING SQL SERVER TABLES WITH T-SQL JOIN ---")
    query = """
        SELECT TOP 5
            f.time_position_utc,
            d.callsign,
            d.origin_country,
            f.latitude,
            f.longitude,
            f.baro_altitude
        FROM FactFlightPositions f
        JOIN DimAircraft d ON f.icao24 = d.icao24;
    """
    sample = pd.read_sql_query(query, engine)
    print(sample.to_string(index=False))

   # Print cumulative total count
    total_count = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM FactFlightPositions", engine).iloc[0]['total']
    print(
        f"\n[SUCCESS] Total cumulative records in FactFlightPositions: {total_count}")

if __name__ == "__main__":
    load_silver_to_sql_server()
