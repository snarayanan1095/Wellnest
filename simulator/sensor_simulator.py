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

def simulate_day(api_endpoint):
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
    for event_time, sensor_id, value in routine_schedule:
        now = datetime.now().isoformat(timespec='seconds')
        payload = {
            "timestamp": now,
            "sensor_id": sensor_id,
            "sensor_type": sensor_id.split('_')[0],
            "location": sensor_id.split('_')[1],
            "value": value
        }
        requests.post(api_endpoint, json=payload)
        print(f"Sent {event_time}: {payload}")
        # Wait a realistic 10-30 minutes between events, or use time.sleep(5) if sped up for demo

# Usage: Simulate events spaced out over a day
simulate_day("http://localhost:8000/api/events")