#!/usr/bin/env python3
"""
Test script to simulate specific anomalies for household_003
Usage: python test_anomaly.py [anomaly_type]
"""

import sys
from sensor_simulator import simulate_day

def main():
    """Test anomaly simulation for household_003"""

    # Default values
    api_endpoint = "http://localhost:8000/api/events"
    household_id = "household_003"

    # Available anomaly types
    anomaly_types = {
        '1': 'missed_kitchen',
        '2': 'prolonged_inactivity',
        '3': 'excessive_bathroom',
        '4': 'late_wakeup'
    }

    print("\n" + "="*60)
    print("ANOMALY SIMULATOR TEST FOR household_003")
    print("="*60)

    # Get anomaly type from command line or prompt user
    if len(sys.argv) > 1:
        anomaly_type = sys.argv[1]
    else:
        print("\nSelect anomaly type to simulate:")
        for key, value in anomaly_types.items():
            print(f"  {key}. {value}")
        print("  5. Run normal simulation (no anomaly)")

        choice = input("\nEnter choice (1-5): ").strip()

        if choice == '5':
            anomaly_type = None
        elif choice in anomaly_types:
            anomaly_type = anomaly_types[choice]
        else:
            print("Invalid choice, running normal simulation")
            anomaly_type = None

    # Run the simulation
    print(f"\nRunning simulation for household_003")
    if anomaly_type:
        print(f"🚨 Anomaly type: {anomaly_type}")
        print("This should trigger alerts in the anomaly detection system")
    else:
        print("Normal mode (no anomaly)")

    print(f"Duration: 5 minutes (for testing)")
    print(f"API Endpoint: {api_endpoint}")
    print("-"*60)

    # Run the simulation
    simulate_day(
        api_endpoint=api_endpoint,
        household_id=household_id,
        check_interval=5,  # Check every 5 seconds for faster testing
        duration_minutes=5,  # Run for 5 minutes
        anomaly_type=anomaly_type
    )

    print("\n" + "="*60)
    print("TEST COMPLETE")
    if anomaly_type:
        print(f"✓ Simulated '{anomaly_type}' anomaly for household_003")
        print("Check the dashboard for alerts at http://localhost:5173")
        print("Check the API logs for anomaly detection triggers")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()