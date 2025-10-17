"""
Event Simulator
Generates and sends simulated sensor/user events to the Wellnest API
"""
import asyncio
import httpx
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
from fake_data_utils import (
    generate_mood_event,
    generate_sleep_event,
    generate_exercise_event,
    generate_medication_event,
    generate_social_event
)

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"

class EventSimulator:
    def __init__(self, config_path: Path = CONFIG_PATH):
        """Initialize the event simulator"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.api_url = self.config['api']['base_url']
        self.endpoint = self.config['api']['events_endpoint']
        self.users = self.config['simulation']['users']
        self.event_types = self.config['simulation']['event_types']
        self.interval = self.config['simulation']['interval_seconds']
        self.batch_size = self.config['simulation'].get('batch_size', 1)

    def generate_event(self, user_id: str, event_type: str) -> Dict[str, Any]:
        """Generate a single event based on type"""
        event_generators = {
            'mood': generate_mood_event,
            'sleep': generate_sleep_event,
            'exercise': generate_exercise_event,
            'medication': generate_medication_event,
            'social': generate_social_event
        }

        if event_type not in event_generators:
            raise ValueError(f"Unknown event type: {event_type}")

        event_data = event_generators[event_type]()
        event_data['user_id'] = user_id

        return event_data

    async def send_event(self, client: httpx.AsyncClient, event: Dict[str, Any]) -> bool:
        """Send a single event to the API"""
        url = f"{self.api_url}{self.endpoint}"
        try:
            response = await client.post(url, json=event)
            response.raise_for_status()
            print(f"✓ Sent {event['event_type']} event for user {event['user_id']}")
            return True
        except httpx.HTTPError as e:
            print(f"✗ Failed to send event: {e}")
            return False

    async def send_batch(self, client: httpx.AsyncClient, events: List[Dict[str, Any]]) -> int:
        """Send a batch of events"""
        tasks = [self.send_event(client, event) for event in events]
        results = await asyncio.gather(*tasks)
        return sum(results)

    def generate_event_batch(self) -> List[Dict[str, Any]]:
        """Generate a batch of random events for random users"""
        events = []
        for _ in range(self.batch_size):
            user_id = random.choice(self.users)
            event_type = random.choice(self.event_types)
            event = self.generate_event(user_id, event_type)
            events.append(event)
        return events

    async def run_continuous(self, duration_minutes: int = None):
        """Run continuous event generation"""
        print(f"Starting event simulator...")
        print(f"API URL: {self.api_url}")
        print(f"Users: {self.users}")
        print(f"Event types: {self.event_types}")
        print(f"Interval: {self.interval}s")
        print(f"Batch size: {self.batch_size}")
        print("-" * 50)

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes else None
        total_sent = 0

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                while True:
                    # Check if we should stop
                    if end_time and datetime.now() >= end_time:
                        break

                    # Generate and send batch
                    events = self.generate_event_batch()
                    sent_count = await self.send_batch(client, events)
                    total_sent += sent_count

                    print(f"Batch complete: {sent_count}/{len(events)} sent successfully (Total: {total_sent})")

                    # Wait before next batch
                    await asyncio.sleep(self.interval)

            except KeyboardInterrupt:
                print("\n\nSimulation stopped by user")
            finally:
                elapsed = (datetime.now() - start_time).total_seconds()
                print("-" * 50)
                print(f"Simulation summary:")
                print(f"  Duration: {elapsed:.1f}s")
                print(f"  Total events sent: {total_sent}")
                print(f"  Average rate: {total_sent / (elapsed / 60):.1f} events/minute")

    async def run_historical(self, days: int = 7):
        """Generate historical events for the past N days"""
        print(f"Generating historical data for the past {days} days...")
        print(f"Users: {self.users}")
        print(f"Event types: {self.event_types}")
        print("-" * 50)

        now = datetime.now()
        total_sent = 0

        async with httpx.AsyncClient(timeout=10.0) as client:
            for day_offset in range(days):
                current_date = now - timedelta(days=day_offset)

                # Generate multiple events per day for each user
                for user_id in self.users:
                    # Generate 3-8 events per day per user
                    num_events = random.randint(3, 8)

                    for _ in range(num_events):
                        event_type = random.choice(self.event_types)
                        event = self.generate_event(user_id, event_type)

                        # Set timestamp to random time on that day
                        hour = random.randint(6, 23)
                        minute = random.randint(0, 59)
                        event['timestamp'] = current_date.replace(
                            hour=hour, minute=minute, second=0
                        ).isoformat()

                        success = await self.send_event(client, event)
                        if success:
                            total_sent += 1

                print(f"Day {day_offset + 1}/{days} complete")

        print("-" * 50)
        print(f"Historical data generation complete: {total_sent} events sent")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Wellnest Event Simulator')
    parser.add_argument(
        '--mode',
        choices=['continuous', 'historical'],
        default='continuous',
        help='Simulation mode'
    )
    parser.add_argument(
        '--duration',
        type=int,
        help='Duration in minutes (for continuous mode)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days of historical data (for historical mode)'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=CONFIG_PATH,
        help='Path to config file'
    )

    args = parser.parse_args()

    simulator = EventSimulator(config_path=args.config)

    if args.mode == 'continuous':
        await simulator.run_continuous(duration_minutes=args.duration)
    elif args.mode == 'historical':
        await simulator.run_historical(days=args.days)


if __name__ == "__main__":
    asyncio.run(main())
