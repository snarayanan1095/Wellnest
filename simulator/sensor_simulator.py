import requests
import random
import time
import json
import os
from datetime import datetime

# Load households configuration from JSON file
def load_households():
    """Load households data from JSON file"""
    config_path = os.path.join(os.path.dirname(__file__), 'households.json')
    with open(config_path, 'r') as f:
        return json.load(f)

HOUSEHOLDS = load_households()

# Realistic polling intervals (in seconds) for different sensor types
SENSOR_INTERVALS = {
    'motion': 60,        # Motion sensors: check every 60 seconds
    'bed_presence': 300, # Bed sensors: check every 5 minutes
    'door': 120          # Door sensors: check every 2 minutes
}

# Track previous sensor states to only send events on state changes
sensor_states = {}

def get_time_of_day_factor(hour):
    """
    Return activity factor based on time of day
    - Morning (6-9): High activity
    - Midday (9-17): Moderate activity
    - Evening (17-22): High activity
    - Night (22-6): Low activity
    """
    if 6 <= hour < 9:
        return 'morning'
    elif 9 <= hour < 17:
        return 'midday'
    elif 17 <= hour < 22:
        return 'evening'
    else:
        return 'night'

def calculate_sensor_probability(sensor, current_hour):
    """
    Calculate probability of sensor being triggered based on sensor type,
    location, and current time of day
    Returns probability between 0.0 and 1.0
    """
    time_period = get_time_of_day_factor(current_hour)
    sensor_type = sensor.get('sensor_type')
    location = sensor.get('location')

    # Base probabilities for different sensor types and times
    probabilities = {
        'motion': {
            'bedroom1': {'morning': 0.7, 'midday': 0.2, 'evening': 0.5, 'night': 0.1},
            'bedroom2': {'morning': 0.7, 'midday': 0.2, 'evening': 0.5, 'night': 0.1},
            'kitchen': {'morning': 0.8, 'midday': 0.5, 'evening': 0.8, 'night': 0.05},
            'livingroom': {'morning': 0.3, 'midday': 0.6, 'evening': 0.7, 'night': 0.05},
            'bathroom1': {'morning': 0.6, 'midday': 0.3, 'evening': 0.4, 'night': 0.15},
            'entrance': {'morning': 0.3, 'midday': 0.2, 'evening': 0.3, 'night': 0.02}
        },
        'bed_presence': {
            'bedroom1': {'morning': 0.2, 'midday': 0.1, 'evening': 0.3, 'night': 0.9},
            'bedroom2': {'morning': 0.2, 'midday': 0.1, 'evening': 0.3, 'night': 0.9}
        },
        'door': {
            'entrance': {'morning': 0.2, 'midday': 0.15, 'evening': 0.2, 'night': 0.02}
        }
    }

    # Get probability for this sensor type and location
    if sensor_type in probabilities and location in probabilities[sensor_type]:
        return probabilities[sensor_type][location][time_period]

    # Default probability if not defined
    return 0.3

def generate_sensor_value(sensor, current_hour):
    """
    Generate a realistic sensor value based on probability
    Returns True (detected) or False (not detected)
    """
    probability = calculate_sensor_probability(sensor, current_hour)
    return random.random() < probability

def should_poll_sensor(household_id, sensor_id, sensor_type, current_time):
    """
    Determine if a sensor should be polled based on its last poll time and sensor type interval
    Returns True if enough time has passed since last poll
    """
    state_key = f"{household_id}:{sensor_id}"

    # Get the polling interval for this sensor type
    interval = SENSOR_INTERVALS.get(sensor_type, 60)

    # Check if we have a record of the last poll time
    if state_key not in sensor_states:
        sensor_states[state_key] = {'last_poll': None, 'last_value': None}

    last_poll = sensor_states[state_key]['last_poll']

    # If never polled or interval has passed, poll it
    if last_poll is None or (current_time - last_poll) >= interval:
        sensor_states[state_key]['last_poll'] = current_time
        return True

    return False

def has_state_changed(household_id, sensor_id, new_value):
    """
    Check if sensor value has changed since last reading
    Returns True if value changed or this is the first reading
    """
    state_key = f"{household_id}:{sensor_id}"

    if state_key not in sensor_states:
        sensor_states[state_key] = {'last_poll': None, 'last_value': None}

    last_value = sensor_states[state_key]['last_value']

    # If this is the first reading or value changed, update and return True
    if last_value is None or last_value != new_value:
        sensor_states[state_key]['last_value'] = new_value
        return True

    return False

def simulate_day(api_endpoint, household_id, check_interval=10, duration_minutes=60):
    """
    Simulate sensor events for a specific household based on realistic patterns.
    Uses realistic polling intervals and only sends events when sensor state changes.

    Args:
        api_endpoint: The API endpoint to send events to
        household_id: The ID of the household to simulate
        check_interval: How often to check if sensors should be polled (default: 10 seconds)
        duration_minutes: How long to run the simulation (default: 60 minutes)
    """
    household = HOUSEHOLDS.get(household_id)
    if not household:
        print(f"✗ Household {household_id} not found")
        return

    print(f"Starting simulation for {household['name']} ({household_id})")
    print(f"Sending events to {api_endpoint}")
    print(f"Check interval: {check_interval} seconds")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Sensor polling intervals: Motion={SENSOR_INTERVALS['motion']}s, Bed={SENSOR_INTERVALS['bed_presence']}s, Door={SENSOR_INTERVALS['door']}s\n")

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    cycle = 0
    events_sent = 0

    # Run simulation for specified duration
    while time.time() < end_time:
        cycle += 1
        current_timestamp = time.time()
        current_datetime = datetime.now()
        current_hour = current_datetime.hour

        print(f"\n--- Check Cycle {cycle} at {current_datetime.strftime('%H:%M:%S')} ({get_time_of_day_factor(current_hour)}) ---")

        # Iterate through all sensors in the household
        for sensor in household['events']:
            sensor_id = sensor['sensor_id']
            sensor_type = sensor['sensor_type']
            location = sensor['location']
            resident = sensor.get('resident', 'unknown')  # Default to 'unknown' if not specified

            # Check if enough time has passed to poll this sensor
            if not should_poll_sensor(household_id, sensor_id, sensor_type, current_timestamp):
                continue  # Skip this sensor, not time to poll yet

            # Generate realistic sensor value based on time and sensor type
            value = generate_sensor_value(sensor, current_hour)

            # Only send event if state has changed
            if not has_state_changed(household_id, sensor_id, value):
                print(f"  [{household['name']}] {sensor_id} ({location}): {value} (no change, skipped)")
                continue

            # Create payload with resident always included
            payload = {
                "household_id": household_id,
                "timestamp": current_datetime.isoformat(timespec='seconds'),
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "location": location,
                "value": str(value),
                "resident": resident
            }

            # Send event to API
            try:
                response = requests.post(api_endpoint, json=payload, timeout=5)
                if response.status_code == 201:
                    print(f"✓ [{household['name']}] {sensor_id} ({location}, {resident}): {value} [STATE CHANGED]")
                    events_sent += 1
                else:
                    print(f"✗ [{household['name']}] Failed {sensor_id}: Status {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"✗ [{household['name']}] Error sending {sensor_id}: {e}")

        # Wait before next check cycle
        time.sleep(check_interval)

    elapsed = time.time() - start_time
    print(f"\n[{household['name']}] Simulation complete!")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Events sent: {events_sent}")
    print(f"Events per minute: {events_sent/(elapsed/60):.1f}")

def run_continuous_simulation(api_endpoint, check_interval=10, households=None):
    """
    Run simulation continuously for multiple households.

    Args:
        api_endpoint: The API endpoint to send events to
        check_interval: How often to check sensors (default: 10 seconds)
        households: List of household IDs to simulate (default: all households)
    """
    if households is None:
        households = list(HOUSEHOLDS.keys())

    print(f"\n{'='*70}")
    print(f"Starting CONTINUOUS simulation for {len(households)} households")
    print(f"This will run indefinitely. Press Ctrl+C to stop.")
    print(f"{'='*70}\n")

    iteration = 1
    while True:
        print(f"\n{'='*70}")
        print(f"Iteration {iteration}")
        print(f"{'='*70}\n")

        # Run a short simulation cycle for each household (10 minutes each)
        for household_id in households:
            household = HOUSEHOLDS[household_id]
            print(f"\n--- {household['name']} ({household_id}) ---")
            simulate_day(api_endpoint, household_id, check_interval=check_interval, duration_minutes=10)
            print()  # Add spacing between households

        iteration += 1
        print(f"\n{'='*70}")
        print(f"Iteration {iteration-1} complete. Waiting 30 seconds before next iteration...")
        print(f"{'='*70}\n")
        time.sleep(30)

if __name__ == "__main__":
    # Usage examples:

    # For a single household (60 minute simulation):
    # simulate_day("http://localhost:8000/api/events", "household_001", check_interval=10, duration_minutes=60)

    # For a quick test (5 minute simulation):
    # simulate_day("http://localhost:8000/api/events", "household_001", check_interval=10, duration_minutes=5)

    # For continuous simulation of all households (runs forever):
    run_continuous_simulation("http://localhost:8000/api/events", check_interval=10)

    # For continuous simulation of specific households:
    # run_continuous_simulation("http://localhost:8000/api/events", check_interval=10, households=["household_001", "household_002"])