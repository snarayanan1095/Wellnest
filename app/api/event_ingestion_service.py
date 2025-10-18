"""
Event Ingestion Service
Handles incoming events from sensor simulators
"""
import hashlib
from fastapi import HTTPException, status

from app.models.event import Event, EventCreate
from app.api.api_schema import EventIngestResponse
from app.db.mongo import MongoDB

# Pure endpoint functions without decorators
async def ingest_event(event_data: EventCreate):
    """
    Ingest a single event from sensor client

    Expected payload (all strings):
    {
        "timestamp": "string",
        "sensor_id": "string",
        "sensor_type": "string",
        "location": "string",
        "value": "string"
    }
    """
    try:
        # Generate a unique event ID (hash-based) - this will be the primary key
        event_id = hashlib.sha256(
            f"{event_data.sensor_id}_{event_data.timestamp}_{event_data.value}".encode()
        ).hexdigest()[:16]

        # Create event object with event_id
        event = Event(
            id=event_id,
            timestamp=event_data.timestamp,
            sensor_id=event_data.sensor_id,
            sensor_type=event_data.sensor_type,
            location=event_data.location,
            value=event_data.value
        )

        # Prepare document for MongoDB
        event_dict = event.model_dump(by_alias=True, exclude_none=True)

        # Use event_id as MongoDB's _id (primary key)
        if 'id' in event_dict:
            event_dict['_id'] = event_dict.pop('id')
        elif '_id' in event_dict:
            # If alias is already _id, use it as is
            pass
        else:
            # Fallback: set _id explicitly
            event_dict['_id'] = event_id

        # Insert into MongoDB events collection
        inserted_id = await MongoDB.write("events", event_dict)
        print(f"✓ Event inserted into MongoDB - ID: {inserted_id}, Sensor: {event.sensor_id}")

        # TODO: Publish to Kafka/Redis for real-time processing
        # await publish_to_stream(event_dict)

        return EventIngestResponse(
            status="success",
            message=f"Event from sensor {event.sensor_id} ingested successfully",
            event_id=event_id,
            timestamp=event.timestamp
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest event: {str(e)}"
        )

