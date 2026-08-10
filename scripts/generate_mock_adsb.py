import os
import json
import random
import time

# 1. Get the absolute path to this script
script_path = os.path.abspath(__file__)

# 2. Go UP twice: scripts/ -> african-air-traffic-local/
BASE_DIR = os.path.dirname(os.path.dirname(script_path))

# 3. Target data/bronze from the project root
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")

# 4. Create the directory if it doesn't exist
os.makedirs(BRONZE_DIR, exist_ok=True)

MOCK_CALLSIGNS = ["GHA102", "KQA504","ETH901"]


def generate_mock_state_vectors(count=20):
    """Generates synthetic ADS-B state vectors matching OpenSky API JSON structure."""
    states = []
    now = int(time.time())

    for i in range(count):
        # Generate random flight values
        icao24 = f"4b{random.randint(1000, 9999):x}"
        callsign = random.choice(MOCK_CALLSIGNS)
        country = "Ghana" if callsign.startswith("GHA") else "Kenya"
        time_position = now - random.randint(1, 30)

        # West Africa / Ghana GPS coordinates
        longitude = round(random.uniform(-3.5, 1.2), 4)
        latitude = round(random.uniform(4.8, 11.1), 4)
        baro_altitude = round(random.uniform(3000.0, 12000.0), 2)
        on_ground = random.choice([True, False, False])
        velocity = round(random.uniform(150.0, 250.0), 2)

        # Inject occasional null coordinates (i % 7 == 0) to test Silver cleaning later
        if i % 7 == 0:
            longitude = None
            latitude = None

        # Assemble the array matching OpenSky index order
        state_vector = [
            icao24,          # Index 0
            callsign,        # Index 1
            country,         # Index 2
            time_position,   # Index 3
            now,             # Index 4 (last_contact)
            longitude,       # Index 5
            latitude,        # Index 6
            baro_altitude,   # Index 7
            on_ground,       # Index 8
            velocity,        # Index 9
            0.0, None, None, baro_altitude, "7000", False, 0
        ]
        states.append(state_vector)

    return {"time": now, "states": states}


def save_mock_payload():
    """Calls the generator and writes the resulting JSON dictionary to the bronze folder."""
    payload = generate_mock_state_vectors()

    # Create a timestamped filename so files don't overwrite each other
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(
        BRONZE_DIR, f"flight_states_mock_{timestamp_str}.json")

    # Open the file and dump the JSON payload
    with open(filepath, "w") as f:
        json.dump(payload, f, indent=2)

    print(
        f"[MOCK GENERATOR] Saved {len(payload['states'])} mock records to {filepath}")
    return filepath


# This block executes ONLY when you run this script directly from the terminal
if __name__ == "__main__":
    save_mock_payload()
