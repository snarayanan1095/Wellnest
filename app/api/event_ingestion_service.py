"""
Event Ingestion Service
Handles incoming events from sensor simulators
"""
import hashlib
from fastapi import HTTPException, status

from app.schema.event import Event, EventCreate
from app.api.api_schema import EventIngestResponse
from app.db.mongo import MongoDB
from app.db.kafka_client import KafkaClient

# Pure endpoint functions without decorators
async def ingest_event(event_data: EventCreate):
    """
    Ingest a single event from sensor client
    """
    try:
        # Generate a unique event ID (hash-based) - this will be used as document identifier
        event_id = hashlib.sha256(
            f"{event_data.household_id}_{event_data.sensor_id}_{event_data.timestamp}_{event_data.value}".encode()
        ).hexdigest()[:16]

        # Create event object with event_id
        event = Event(
            event_id=event_id,
            household_id=event_data.household_id,
            timestamp=event_data.timestamp,
            sensor_id=event_data.sensor_id,
            sensor_type=event_data.sensor_type,
            location=event_data.location,
            value=event_data.value,
            resident=event_data.resident
        )

        # Prepare document for MongoDB
        event_dict = event.model_dump(by_alias=False, exclude_none=True)

        # MongoDB document structure: _id = event_id (unique identifier)
        # Keep household_id as a separate field for querying
        event_dict['_id'] = event_id  # Use event_id as MongoDB _id for uniqueness
        #event_dict['household_id'] = event_data.household_id  # Explicitly preserve household_id

        # Insert into MongoDB events collection
        inserted_id = await MongoDB.write("events", event_dict)
        print(f"✓ Event inserted into MongoDB - ID: {inserted_id}, Sensor: {event.sensor_id}")

        """ Using kafka for real time processing to make sure:
        1. 
        """
        try:
            # Use household_id as key for Kafka partitioning to keep all household events together
            KafkaClient.publish_event(
                event=event_dict,
                key=event.household_id  # Partition by household for better isolation and parallelism
            )
            print(f"✓ Event published to Kafka - Household: {event.household_id}, Sensor: {event.sensor_id}")
        except Exception as kafka_error:
            # Log error but don't fail the request if Kafka is unavailable
            print(f"⚠ Failed to publish to Kafka: {kafka_error}")

        return EventIngestResponse(
            status="success",
            message=f"Event from household {event.household_id}, sensor {event.sensor_id} ingested successfully",
            event_id=event_id,
            timestamp=event.timestamp
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest event: {str(e)}"
        )

