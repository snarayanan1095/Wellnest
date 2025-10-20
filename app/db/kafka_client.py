# -*- coding: utf-8 -*-
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from typing import Optional, Dict, Any
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class KafkaClient:
    producer: Optional[KafkaProducer] = None
    _bootstrap_servers: str = None
    _topic_events: str = None

    @classmethod
    async def connect(cls, max_retries: int = 3, retry_delay: int = 2):
        """
        Connect to Kafka with retry logic

        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay in seconds between retries
        """
        cls._bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        cls._topic_events = os.getenv("KAFKA_TOPIC_EVENTS", "wellnest-events")

        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to Kafka at {cls._bootstrap_servers} (attempt {attempt + 1}/{max_retries})...")

                # Create Kafka producer with JSON serialization
                cls.producer = KafkaProducer(
                    bootstrap_servers=cls._bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',  # Wait for all replicas to acknowledge
                    retries=3,
                    max_in_flight_requests_per_connection=1,
                    # Connection timeout settings for local debugging
                    api_version_auto_timeout_ms=5000,  # 5 seconds to detect broker version
                    request_timeout_ms=30000,  # 30 seconds for requests
                    metadata_max_age_ms=300000,  # 5 minutes for metadata refresh
                )

                print(f"✓ Kafka connected to {cls._bootstrap_servers}")
                print(f"✓ Events topic: {cls._topic_events}")
                return

            except NoBrokersAvailable as e:
                if attempt < max_retries - 1:
                    print(f"⚠ Kafka not available yet, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"✗ Kafka connection failed after {max_retries} attempts: {e}")
                    raise
            except Exception as e:
                print(f"✗ Kafka connection failed: {e}")
                raise

    @classmethod
    def publish_event(cls, event: Dict[str, Any], key: Optional[str] = None) -> None:
        """
        Publish an event to Kafka

        Args:
            event: Event data to publish
            key: Optional message key for partitioning
        """
        if cls.producer is None:
            raise RuntimeError("Kafka producer is not connected. Call connect() first.")

        try:
            # Send message to Kafka
            future = cls.producer.send(
                cls._topic_events,
                key=key,
                value=event
            )

            # Wait for message to be sent (with timeout)
            future.get(timeout=10)

        except Exception as e:
            print(f"✗ Failed to publish event to Kafka: {e}")
            raise

    @classmethod
    def close(cls):
        """Close Kafka producer"""
        if cls.producer:
            cls.producer.flush()  # Ensure all messages are sent
            cls.producer.close()
            print("✓ Kafka producer closed")
