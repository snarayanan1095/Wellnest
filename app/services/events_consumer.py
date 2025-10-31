"""
Kafka consumer for real-time event streaming via WebSocket
Consumes events from wellnest-events topic and forwards to connected WebSocket clients
"""
import asyncio
import json
import os
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from app.services.ws_manager import manager
from datetime import datetime


class EventsConsumer:
    def __init__(self):
        self.consumer = None
        self.running = False
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = os.getenv("KAFKA_TOPIC_EVENTS", "wellnest-events")

    async def start(self):
        """Start consuming events from Kafka and forward to WebSocket clients"""
        self.running = True
        print(f"📡 Starting Events Consumer for topic: {self.topic}")

        while self.running:
            try:
                # Create Kafka consumer
                self.consumer = KafkaConsumer(
                    self.topic,
                    bootstrap_servers=self.bootstrap_servers,
                    auto_offset_reset='latest',  # Only get new messages
                    enable_auto_commit=True,
                    group_id='websocket-events-group',
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    consumer_timeout_ms=1000  # Timeout to allow checking self.running
                )

                print(f"✓ Events Consumer connected to Kafka at {self.bootstrap_servers}")

                # Consume messages
                while self.running:
                    messages = self.consumer.poll(timeout_ms=1000)

                    for topic_partition, records in messages.items():
                        for record in records:
                            try:
                                event = record.value

                                # Extract household_id from event
                                household_id = event.get("household_id")

                                if household_id:
                                    # Update cache with resident's latest location
                                    resident = event.get("resident")
                                    location = event.get("location")

                                    if resident and location:
                                        await manager.update_resident_location(household_id, resident, location)

                                    # Add timestamp to event before forwarding
                                    from datetime import datetime
                                    event["last_active"] = datetime.utcnow().isoformat()

                                    # Forward entire event to WebSocket clients for this household
                                    await manager.send_alert(household_id, event)

                                    # Log for debugging
                                    resident = event.get("resident", "unknown")
                                    location = event.get("location", "unknown")
                                    print(f"→ Event forwarded: {household_id} - {resident} at {location}")

                            except Exception as e:
                                print(f"❌ Error processing event: {e}")

                    # Small delay to prevent CPU spinning
                    await asyncio.sleep(0.1)

            except NoBrokersAvailable:
                print(f"⚠ Kafka not available, retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"❌ Events Consumer error: {e}")
                await asyncio.sleep(5)
            finally:
                if self.consumer:
                    self.consumer.close()
                    print("✓ Events Consumer closed")

    async def stop(self):
        """Stop the consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        print("✓ Events Consumer stopped")


# Global instance
events_consumer = EventsConsumer()


async def start_events_consumer():
    """Function to be called from main.py"""
    try:
        await events_consumer.start()
    except Exception as e:
        print(f"❌ Failed to start events consumer: {e}")