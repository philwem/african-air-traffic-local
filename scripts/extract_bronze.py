import os
import sys
import time
import json
import requests

sys.path.append(os.path.join(os.path.dirname(__file__)))
from generate_mock_adsb import save_mock_payload

# 1. Get the absolute path to this script
script_path = os.path.abspath(__file__)

# 2. Go UP twice: scripts/ -> african-air-traffic-local/
BASE_DIR = os.path.dirname(os.path.dirname(script_path))

# 3. Target data/bronze from the project root
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")

# 4. Create the directory if it doesn't exist
os.makedirs(BRONZE_DIR, exist_ok=True)

OPENSKY_URL = "https://opensky-network.org/api/states/all"

WEST_AFRICA_BOUNDS = {
    "lamin": 4.0,   # Latitude Min
    "lomin": -18.0,  # Longitude Min
    "lamax": 16.0,  # Latitude Max
    "lomax": 10.0   # Longitude Max
}


def fetch_adbs_data():
    """Pings OpenSky API for West Africa state vectors with defensive fallback to mock generator."""
    print("[BRONZE INGESTION] Requesting state vectors from OpenSky API...")
    
    try:
        # Send GET request with a 10-second timeout
        response = requests.get(
            OPENSKY_URL,
            params=WEST_AFRICA_BOUNDS,timeout=10
        )
        
        # Check for rate limits (HTTP 429)\
        if response.status_code == 429 :
            print("[WARNING] API Rate Limit Hit (HTTP 429). Executing mock fallback...")
            return save_mock_payload()
        
        response.raise_for_status()
        data = response.json()
        
        
        if not data or "states" not in data or not data["states"]:
            print("[INFO] No active flight vectors returned.Excuting mock fallback...'")
            return save_mock_payload()
        
        # Save raw JSON payload to data/bronze/
        timestamp_str = time.strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(BRONZE_DIR, f"flight_states_{timestamp_str}.json")
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"[SUCCESS] Ingested {len(data['states'])} live records to {file_path}")
        return file_path
    
    except Exception as e:
        # Handle any network failures or timeouts cleanly
        print(f"[ERROR] API Connection Failed: {e}")
        return save_mock_payload()
    

# Execution Entry Point
if __name__ == "__main__":
    fetch_adbs_data()
