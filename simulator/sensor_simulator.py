import requests
import random
import time
from datetime import datetime

# Define multiple households with their sensors
HOUSEHOLDS = {
    "household_001": {
        "name": "Smith Family",
        "sensors": [
            {"sensor_id": "motion_bedroom1", "location": "bedroom1", "sensor_type": "motion", "resident": "grandmom"},
            {"sensor_id": "motion_bedroom2", "location": "bedroom2", "sensor_type": "motion", "resident": "granddad"},
            {"sensor_id": "motion_kitchen",   "location": "kitchen",  "sensor_type": "motion"},
            {"sensor_id": "motion_livingroom","location": "livingroom","sensor_type": "motion"},
            {"sensor_id": "motion_bathroom1", "location": "bathroom1","sensor_type": "motion"},
            {"sensor_id": "bed_bedroom1",     "location": "bedroom1", "sensor_type": "bed_presence", "resident": "grandmom"},
            {"sensor_id": "door_main",        "location": "entrance", "sensor_type": "door"},
        ]
    },
    "household_002": {
        "name": "Johnson Family",
        "sensors": [
            {"sensor_id": "motion_bedroom1", "location": "bedroom1", "sensor_type": "motion", "resident": "grandpa"},
            {"sensor_id": "motion_kitchen",   "location": "kitchen",  "sensor_type": "motion"},
            {"sensor_id": "motion_livingroom","location": "livingroom","sensor_type": "motion"},
            {"sensor_id": "bed_bedroom1",     "location": "bedroom1", "sensor_type": "bed_presence", "resident": "grandpa"},
            {"sensor_id": "door_main",        "location": "entrance", "sensor_type": "door"},
        ]
    },
    "household_003": {
        "name": "Davis Family",
        "sensors": [
            {"sensor_id": "motion_bedroom1", "location": "bedroom1", "sensor_type": "motion"},
            {"sensor_id": "motion_bedroom2", "location": "bedroom2", "sensor_type": "motion"},
            {"sensor_id": "motion_kitchen",   "location": "kitchen",  "sensor_type": "motion"},
            {"sensor_id": "motion_bathroom1", "location": "bathroom1","sensor_type": "motion"},
            {"sensor_id": "bed_bedroom1",     "location": "bedroom1", "sensor_type": "bed_presence"},
            {"sensor_id": "bed_bedroom2",     "location": "bedroom2", "sensor_type": "bed_presence"},
        ]
    }
}

def simulate_day(api_endpoint, household_id, delay_seconds=5):
    """Simulate a day's worth of events for a specific household"""
    routine_schedule = [
        # Define event windows and target sensors
        ("07:00", "bed_bedroom1", False),   # Out of bed
        ("07:10", "motion_bedroom1", True),
        ("07:15", "motion_bathroom1", True),
        ("07:18", "motion_kitchen", True),
        ("08:00", "motion_livingroom", True),
        ("08:30", "motion_bedroom1", True),
        ("09:25", "motion_kitchen", True)
        # Add granularity and randomness as needed
    ]

    household = HOUSEHOLDS.get(household_id)
    if not household:
        print(f"✗ Household {household_id} not found")
        return

    print(f"Starting simulation for {household['name']} ({household_id})")
    print(f"Sending events to {api_endpoint}")
    print(f"Delay between events: {delay_seconds} seconds\n")

    for event_time, sensor_id, value in routine_schedule:
        now = datetime.now().isoformat(timespec='seconds')
        payload = {
            "household_id": household_id,
            "timestamp": now,
            "sensor_id": sensor_id,
            "sensor_type": sensor_id.split('_')[0],
            "location": sensor_id.split('_')[1],
            "value": str(value)  # Convert boolean to string for API
        }

        try:
            response = requests.post(api_endpoint, json=payload, timeout=5)
            if response.status_code == 201:
                print(f"✓ [{household['name']}] Sent {event_time}: {sensor_id} = {value}")
            else:
                print(f"✗ [{household['name']}] Failed {event_time}: Status {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"✗ [{household['name']}] Error sending {event_time}: {e}")

        # Wait before next event (sped up for demo)
        time.sleep(delay_seconds)

    print(f"\n[{household['name']}] Simulation complete!")

def run_continuous_simulation(api_endpoint, delay_seconds=5, households=None):
    """Run simulation continuously for multiple households in parallel"""
    if households is None:
        households = list(HOUSEHOLDS.keys())

    iteration = 1
    while True:
        print(f"\n{'='*70}")
        print(f"Starting simulation iteration {iteration} for {len(households)} households")
        print(f"{'='*70}\n")

        # Simulate all households in this iteration
        for household_id in households:
            household = HOUSEHOLDS[household_id]
            print(f"\n--- {household['name']} ({household_id}) ---")
            simulate_day(api_endpoint, household_id, delay_seconds)
            print()  # Add spacing between households

        iteration += 1
        print(f"\n{'='*70}")
        print(f"Iteration {iteration-1} complete. Waiting 30 seconds before next iteration...")
        print(f"{'='*70}\n")
        time.sleep(30)

if __name__ == "__main__":
    # Usage examples:

    # For a single household:
    # simulate_day("http://localhost:8000/api/events", "household_001", delay_seconds=5)

    # For continuous simulation of all households:
    run_continuous_simulation("http://localhost:8000/api/events", delay_seconds=5)

    # For continuous simulation of specific households:
    # run_continuous_simulation("http://localhost:8000/api/events", delay_seconds=5, households=["household_001", "household_002"])