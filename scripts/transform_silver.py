import os 
import glob 
import json
import pandas as pd

# 1. Get the absolute path to this script
script_path = os.path.abspath(__file__)

# 2. Go UP twice: scripts/ -> african-air-traffic-local/
BASE_DIR = os.path.dirname(os.path.dirname(script_path))

# 3. Target data/bronze from the project root
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")


SILVER_DIR = os.path.join(BASE_DIR, "data", "silver")

# 4. Create the directory if it doesn't exist
os.makedirs(SILVER_DIR, exist_ok=True)

COLUMN_NAMES = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source"
]


def process_bronze_to_silver():
    
    # Step A: Find all JSON files in bronze directory
    json_files = glob.glob(os.path.join(BRONZE_DIR, "*.json"))
    if not json_files:
        print("[ERROR] No JSON files found in the bronze directory.")
        return None
    
    # Step B: Get the latest file based on modification time
    latest_file = max(json_files, key=os.path.getmtime)
    print(f"[SILVER TRANSFORM] Processing payload: {os.path.basename(latest_file)}")
    
    # Step C: Read JSON payload
    with open(latest_file, "r") as f:
        payload = json.load(f)
    
    raw_states = payload.get("states", [])
    if not raw_states:
        print("[WARNING] Selected Bronze file contains no state records.")
        return None
    

    # Load raw arrays into a structured Pandas DataFrame
    df = pd.DataFrame(raw_states, columns=COLUMN_NAMES)

    # ADD THIS MISSING LINE HERE:
    initial_count = len(df)
    
    # DATA QUALITY RULE 2: Filter out missing GPS
    df_clean = df.dropna(subset=["latitude", "longitude"]).copy()
    dropped_gps_count = initial_count - len(df_clean)

    # Make sure this line exists!
    df_clean["time_position_utc"] = pd.to_datetime(
        df_clean["time_position"], unit="s", utc=True
    )

    # Now select columns safely
    silver_df = df_clean[
        [
            "icao24",
            "callsign",
            "origin_country",
            "time_position_utc",  # <--- Pandas can now find this column
            "longitude",
            "latitude",
            "baro_altitude",
            "velocity",
            "on_ground",
        ]
    ]
    # Step E: Save clean data as columnar Parquet file in data/silver/
    timestamp_str = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        SILVER_DIR, f"flights_silver_{timestamp_str}.parquet")
    silver_df.to_parquet(output_path, index=False)

    print("\n--- DATA QUALITY METRICS ---")
    print(f"Total Raw Bronze Records : {initial_count}")
    print(f"Dropped Records (Null GPS): {dropped_gps_count}")
    print(f"Valid Silver Records      : {len(silver_df)}")
    print(f"[SUCCESS] Exported Parquet to: {output_path}\n")

    return output_path


if __name__ == "__main__":
    process_bronze_to_silver()


