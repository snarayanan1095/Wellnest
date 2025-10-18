import requests
import random
import time
from datetime import datetime

SENSORS = [
    {"sensor_id": "motion_bedroom1", "location": "bedroom1", "sensor_type": "motion", "resident": "grandmom"},
    {"sensor_id": "motion_bedroom2", "location": "bedroom2", "sensor_type": "motion", "resident": "granddad"},
    {"sensor_id": "motion_kitchen",   "location": "kitchen",  "sensor_type": "motion"},
    {"sensor_id": "motion_livingroom","location": "livingroom","sensor_type": "motion"},
    {"sensor_id": "motion_bathroom1", "location": "bathroom1","sensor_type": "motion"},
    {"sensor_id": "motion_bathroom2", "location": "bathroom2","sensor_type": "motion"},
    {"sensor_id": "bed_bedroom1",     "location": "bedroom1", "sensor_type": "bed_presence", "resident": "grandmom"},
    {"sensor_id": "bed_bedroom2",     "location": "bedroom2", "sensor_type": "bed_presence", "resident": "granddad"},
    {"sensor_id": "door_main",        "location": "entrance", "sensor_type": "door"},
]

def simulate_day(api_endpoint, delay_seconds=5):
    """Simulate a day's worth of events with delays between them"""
    routine_schedule = [
        # Define event windows and target sensors
        ("07:00", "bed_bedroom1", False),   # Grandmom out of bed
        ("07:10", "motion_bedroom1", True),
        ("07:15", "motion_bathroom1", True),
        ("07:18", "motion_kitchen", True),
        ("08:00", "motion_livingroom", True),
        ("08:30", "motion_bedroom1", True),
        ("09:25", "motion_kitchen", True)
        # Add granularity and randomness as needed
    ]

    print(f"Starting simulation - sending events to {api_endpoint}")
    print(f"Delay between events: {delay_seconds} seconds\n")

    for event_time, sensor_id, value in routine_schedule:
        now = datetime.now().isoformat(timespec='seconds')
        payload = {
            "timestamp": now,
            "sensor_id": sensor_id,
            "sensor_type": sensor_id.split('_')[0],
            "location": sensor_id.split('_')[1],
            "value": str(value)  # Convert boolean to string for API
        }

        try:
            response = requests.post(api_endpoint, json=payload, timeout=5)
            if response.status_code == 201:
                print(f"✓ Sent {event_time}: {payload}")
            else:
                print(f"✗ Failed {event_time}: Status {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"✗ Error sending {event_time}: {e}")

        # Wait before next event (sped up for demo)
        time.sleep(delay_seconds)

    print("\nSimulation complete!")

def run_continuous_simulation(api_endpoint, delay_seconds=5):
    """Run simulation continuously in a loop"""
    iteration = 1
    while True:
        print(f"\n{'='*60}")
        print(f"Starting simulation iteration {iteration}")
        print(f"{'='*60}\n")
        simulate_day(api_endpoint, delay_seconds)
        iteration += 1
        print(f"\nWaiting 30 seconds before next iteration...\n")
        time.sleep(30)

if __name__ == "__main__":
    # Usage: Simulate events spaced out over a day
    # For a single run:
    # simulate_day("http://localhost:8000/api/events", delay_seconds=5)

    # For continuous simulation:
    run_continuous_simulation("http://localhost:8000/api/events", delay_seconds=5)