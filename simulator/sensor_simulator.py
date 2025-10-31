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

def generate_anomaly_value(sensor, current_hour, anomaly_type, event_count):
    """
    Generate sensor values that will trigger specific anomalies for household_003

    Args:
        sensor: Sensor configuration
        current_hour: Current hour of day
        anomaly_type: Type of anomaly to simulate
        event_count: Number of events generated so far

    Returns:
        Sensor value that helps create the anomaly pattern
    """
    sensor_type = sensor.get('sensor_type')
    location = sensor.get('location')

    if anomaly_type == 'missed_kitchen':
        # Wake up but skip kitchen
        if sensor_type == 'bed_presence' and location == 'bedroom1' and event_count < 5:
            return False  # Wake up
        elif sensor_type == 'motion' and location == 'kitchen':
            return False  # Never visit kitchen
        elif sensor_type == 'motion' and location in ['bedroom1', 'bathroom1']:
            return random.random() < 0.7  # Activity in other rooms

    elif anomaly_type == 'prolonged_inactivity':
        # Create long periods without motion after initial activity
        if event_count < 10:
            # Some initial activity
            return random.random() < 0.5
        else:
            # Then stop all motion for prolonged period
            if sensor_type == 'motion':
                return False
            elif sensor_type == 'bed_presence':
                return False  # Not in bed, just inactive

    elif anomaly_type == 'excessive_bathroom':
        # Generate excessive bathroom visits
        if sensor_type == 'bed_presence' and event_count < 5:
            return False  # Wake up first
        elif sensor_type == 'motion' and location == 'bathroom1':
            # High probability of bathroom motion
            return random.random() < 0.9
        elif sensor_type == 'motion' and location in ['bedroom1', 'bedroom2']:
            # Alternate between bathroom and bedrooms
            return random.random() < 0.6

    elif anomaly_type == 'late_wakeup':
        # Keep person in bed longer than usual
        if sensor_type == 'bed_presence' and location == 'bedroom1':
            if current_hour < 10:  # Stay in bed until late
                return True
            else:
                return random.random() < 0.3  # Eventually wake up
        elif sensor_type == 'motion':
            # Reduced activity in morning hours
            if current_hour < 10:
                return False
            else:
                return random.random() < 0.5

    # Default to normal behavior
    return generate_sensor_value(sensor, current_hour)

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

def simulate_day(api_endpoint, household_id, check_interval=10, duration_minutes=60, anomaly_type=None):
    """
    Simulate sensor events for a specific household based on realistic patterns.
    Uses realistic polling intervals and only sends events when sensor state changes.
    For household_003, can simulate anomalies.

    Args:
        api_endpoint: The API endpoint to send events to
        household_id: The ID of the household to simulate
        check_interval: How often to check if sensors should be polled (default: 10 seconds)
        duration_minutes: How long to run the simulation (default: 60 minutes)
        anomaly_type: For household_003, type of anomaly to simulate (None for normal)
    """
    household = HOUSEHOLDS.get(household_id)
    if not household:
        print(f"✗ Household {household_id} not found")
        return

    # Determine if we should simulate anomalies for household_003
    simulate_anomaly = False
    if household_id == "household_003" and anomaly_type:
        simulate_anomaly = True
        valid_anomalies = ['missed_kitchen', 'prolonged_inactivity', 'excessive_bathroom', 'late_wakeup']
        if anomaly_type not in valid_anomalies:
            print(f"⚠️ Invalid anomaly type: {anomaly_type}")
            print(f"Valid types: {', '.join(valid_anomalies)}")
            anomaly_type = random.choice(valid_anomalies)
            print(f"Using random anomaly: {anomaly_type}")

    print(f"Starting simulation for {household['name']} ({household_id})")
    if simulate_anomaly:
        print(f"🚨 ANOMALY MODE: Simulating '{anomaly_type}' anomaly pattern")
    print(f"Sending events to {api_endpoint}")
    print(f"Check interval: {check_interval} seconds")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Sensor polling intervals: Motion={SENSOR_INTERVALS['motion']}s, Bed={SENSOR_INTERVALS['bed_presence']}s, Door={SENSOR_INTERVALS.get('door', 120)}s\n")

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

            # Generate sensor value - use anomaly pattern for household_003 if specified
            if simulate_anomaly:
                value = generate_anomaly_value(sensor, current_hour, anomaly_type, events_sent)
            else:
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

def run_continuous_simulation(api_endpoint, check_interval=10, households=None, anomaly_for_003=False):
    """
    Run simulation continuously for multiple households.

    Args:
        api_endpoint: The API endpoint to send events to
        check_interval: How often to check sensors (default: 10 seconds)
        households: List of household IDs to simulate (default: all households)
        anomaly_for_003: If True, simulate anomalies for household_003
    """
    if households is None:
        households = list(HOUSEHOLDS.keys())

    print(f"\n{'='*70}")
    print(f"Starting CONTINUOUS simulation for {len(households)} households")
    if anomaly_for_003 and "household_003" in households:
        print(f"🚨 ANOMALY MODE ENABLED for household_003")
    print(f"This will run indefinitely. Press Ctrl+C to stop.")
    print(f"{'='*70}\n")

    # List of anomalies to cycle through for household_003
    anomaly_types = ['missed_kitchen', 'prolonged_inactivity', 'excessive_bathroom', 'late_wakeup']
    anomaly_index = 0

    iteration = 1
    while True:
        print(f"\n{'='*70}")
        print(f"Iteration {iteration}")
        print(f"{'='*70}\n")

        # Run a short simulation cycle for each household (10 minutes each)
        for household_id in households:
            household = HOUSEHOLDS[household_id]
            print(f"\n--- {household['name']} ({household_id}) ---")

            # For household_003, use anomaly simulation if enabled
            if household_id == "household_003" and anomaly_for_003:
                current_anomaly = anomaly_types[anomaly_index % len(anomaly_types)]
                simulate_day(api_endpoint, household_id, check_interval=check_interval,
                           duration_minutes=10, anomaly_type=current_anomaly)
                anomaly_index += 1
            else:
                simulate_day(api_endpoint, household_id, check_interval=check_interval, duration_minutes=10)

            print()  # Add spacing between households

        iteration += 1
        print(f"\n{'='*70}")
        print(f"Iteration {iteration-1} complete. Waiting 30 seconds before next iteration...")
        print(f"{'='*70}\n")
        time.sleep(30)

if __name__ == "__main__":
    import sys

    # Check for command line arguments
    anomaly_mode = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--anomaly":
            anomaly_mode = True
            print("🚨 ANOMALY MODE ACTIVATED for household_003")

    # Usage examples:

    # For a single household with specific anomaly (5 minute test):
    # simulate_day("http://localhost:8000/api/events", "household_003", check_interval=10, duration_minutes=5, anomaly_type="missed_kitchen")

    # For continuous simulation with anomalies for household_003:
    if anomaly_mode:
        # Run with anomalies for household_003
        run_continuous_simulation("http://localhost:8000/api/events", check_interval=10, anomaly_for_003=True)
    else:
        # Normal simulation for all households
        run_continuous_simulation("http://localhost:8000/api/events", check_interval=10)

    # For continuous simulation of specific households:
    # run_continuous_simulation("http://localhost:8000/api/events", check_interval=10, households=["household_001", "household_002"])