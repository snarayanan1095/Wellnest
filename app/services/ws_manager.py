# app/services/ws_manager.py
from typing import Dict, List, Optional
import json
from datetime import datetime
import asyncio
import os
from kafka import KafkaConsumer
from kafka.errors import KafkaError

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List] = {}
        # Kafka is used as the source of truth for all events

    async def connect(self, websocket, household_id: str):
        await websocket.accept()
        if household_id not in self.active_connections:
            self.active_connections[household_id] = []
        self.active_connections[household_id].append(websocket)

    async def add_connection_with_state(self, websocket, household_id: str):
        """Add an already-accepted WebSocket connection and send initial state"""
        print(f"📤 Starting add_connection_with_state for {household_id}")

        if household_id not in self.active_connections:
            self.active_connections[household_id] = []
        self.active_connections[household_id].append(websocket)
        print(f"📝 Added connection to list for {household_id}, total: {len(self.active_connections[household_id])}")

        # Fetch recent events directly from Kafka
        residents_data = {}
        timestamps = {}

        try:
            # Read recent events from Kafka topic
            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            topic = os.getenv("KAFKA_TOPIC_EVENTS", "wellnest-events")

            print(f"🔌 Connecting to Kafka at {bootstrap_servers} to fetch recent events...")

            # Create a consumer to read recent messages
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                auto_offset_reset='earliest',  # Start from beginning to get recent history
                enable_auto_commit=False,
                group_id=f'initial-state-{household_id}',  # Unique group per household
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=2000  # 2 second timeout
            )

            # Poll to trigger partition assignment
            consumer.poll(timeout_ms=100)

            # Check if partitions are assigned
            if consumer.assignment():
                # Seek to end first to get partition info
                consumer.seek_to_end()

                # Now seek backwards to get last N messages (e.g., last 100)
                for partition in consumer.assignment():
                    current_position = consumer.position(partition)
                    # Go back 100 messages or to beginning
                    new_position = max(0, current_position - 100)
                    consumer.seek(partition, new_position)

                # Consume and process messages
                messages = consumer.poll(timeout_ms=2000)
            else:
                print(f"⚠️ No partitions assigned yet for topic {topic}")
                messages = {}

            for topic_partition, records in messages.items():
                for record in records:
                    event = record.value

                    # Only process events for this household
                    if event.get("household_id") == household_id:
                        resident = event.get("resident")
                        location = event.get("location")
                        timestamp = event.get("timestamp") or event.get("last_active")

                        if resident and location:
                            # Always update with latest (newer messages come later)
                            residents_data[resident] = location
                            if timestamp:
                                timestamps[resident] = timestamp

            consumer.close()
            print(f"🔍 Kafka fetch for {household_id}: {len(residents_data)} residents")

        except Exception as e:
            print(f"⚠️ Error fetching events from Kafka: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to empty state if Kafka query fails
            pass

        initial_state = {
            "type": "initial_state",
            "residents": residents_data,
            "timestamps": timestamps
        }

        try:
            print(f"📨 Attempting to send initial state to {household_id}...")
            await websocket.send_json(initial_state)
            if residents_data:
                print(f"✓ Sent initial state to household {household_id}: {len(residents_data)} residents with timestamps")
                # Debug: Show what we're actually sending
                for resident, location in residents_data.items():
                    ts = timestamps.get(resident, "no timestamp")
                    print(f"  - {resident}: {location} (ts: {ts})")
            else:
                print(f"✓ Sent empty initial state to household {household_id} (no cached data yet)")
        except Exception as e:
            print(f"❌ Failed to send initial state for {household_id}: {e}")
            import traceback
            traceback.print_exc()

    def add_connection(self, websocket, household_id: str):
        """Add an already-accepted WebSocket connection"""
        if household_id not in self.active_connections:
            self.active_connections[household_id] = []
        self.active_connections[household_id].append(websocket)

    async def update_resident_location(self, household_id: str, resident: str, location: str):
        """
        No-op: Location updates are now handled directly via Kafka.
        This method is kept for backward compatibility with events_consumer.py
        """
        # Events are already in Kafka - no need to cache separately
        pass

    def disconnect(self, websocket, household_id: str):
        if household_id in self.active_connections:
            try:
                self.active_connections[household_id].remove(websocket)
                # Clean up empty connection lists immediately
                if not self.active_connections[household_id]:
                    del self.active_connections[household_id]
                    print(f"🧹 Cleaned up connection list for household {household_id}")
            except ValueError:
                # Connection wasn't in the list
                pass

    async def send_alert(self, household_id: str, message: dict):
        # Check if there are any active connections for this household
        if household_id not in self.active_connections or not self.active_connections[household_id]:
            # Only print warning occasionally to avoid log spam
            if not hasattr(self, '_warning_count'):
                self._warning_count = {}
            if household_id not in self._warning_count:
                self._warning_count[household_id] = 0
            self._warning_count[household_id] += 1

            # Only warn every 10th attempt to reduce log noise
            if self._warning_count[household_id] % 10 == 1:
                print(f"⚠️ No active WebSocket connections for household {household_id} (suppressing further warnings)")
            return

        dead_connections = []
        for connection in self.active_connections[household_id]:
            try:
                await connection.send_json(message)
                print(f"✓ Alert sent via WebSocket to household {household_id}")
            except Exception as e:
                print(f"❌ Failed to send alert via WebSocket to household {household_id}: {e}")
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            try:
                self.active_connections[household_id].remove(conn)
                print(f"🧹 Removed dead WebSocket connection for household {household_id}")
            except ValueError:
                # Connection already removed
                pass

        # Clean up empty connection lists
        if household_id in self.active_connections and not self.active_connections[household_id]:
            del self.active_connections[household_id]
            print(f"🧹 Cleaned up empty connection list for household {household_id}")

    async def send_alert_resolved(self, household_id: str, resolution_info: dict):
        """
        Send a notification that an alert has been auto-resolved

        Args:
            household_id: The household ID
            resolution_info: Details about the resolved alert
        """
        message = {
            "type": "alert_resolved",
            "household_id": household_id,
            "alert_type": resolution_info.get("type"),
            "message": resolution_info.get("message"),
            "resolved_count": resolution_info.get("resolved_count", 1),
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_alert(household_id, message)

manager = ConnectionManager()
