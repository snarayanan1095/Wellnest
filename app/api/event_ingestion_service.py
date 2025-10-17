"""
Event Ingestion Service
Handles incoming events from simulators, IoT devices, and user inputs
"""
from fastapi import HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.event import Event, EventCreate, EventResponse, EventType
from app.db.mongo import MongoDB
from app.api.api_schema import EventIngestResponse, BatchIngestResponse, EventListResponse

# Pure endpoint functions without decorators
async def ingest_event(event_data: EventCreate, user_id: str = Query(..., description="User identifier")):
    """
    Ingest a single event from simulator or device

    This is the main endpoint that sensor_simulator.py will POST to.
    Validates, enriches, and stores the event in MongoDB.
    """
    try:
        # Create event object with user_id and timestamp
        event = Event(
            user_id=user_id,
            event_type=event_data.event_type,
            value=event_data.value,
            metadata=event_data.metadata,
            notes=event_data.notes,
            timestamp=event_data.timestamp or datetime.utcnow()
        )

        # Get MongoDB collection
        collection = MongoDB.get_collection("events")

        # Prepare document for MongoDB
        event_dict = event.dict(by_alias=True, exclude={"id"})

        # Insert into MongoDB
        result = await collection.insert_one(event_dict)
        event_id = str(result.inserted_id)

        # TODO: Publish to Kafka/Redis for real-time processing
        # await publish_to_stream(event_dict)

        # TODO: Trigger anomaly detection for certain event types
        # if event.event_type in [EventType.MOOD, EventType.SLEEP]:
        #     await trigger_anomaly_detection(event_dict)

        return EventIngestResponse(
            status="success",
            message=f"Event {event.event_type} ingested successfully",
            event_id=event_id,
            timestamp=event.timestamp
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest event: {str(e)}"
        )

async def ingest_batch_events(events: List[EventCreate], user_id: str = Query(..., description="User identifier")):
    """
    Ingest multiple events in a batch

    Useful for bulk uploads or historical data imports.
    """
    try:
        collection = MongoDB.get_collection("events")
        event_ids = []
        failed_count = 0

        # Process each event
        event_docs = []
        for event_data in events:
            try:
                event = Event(
                    user_id=user_id,
                    event_type=event_data.event_type,
                    value=event_data.value,
                    metadata=event_data.metadata,
                    notes=event_data.notes,
                    timestamp=event_data.timestamp or datetime.utcnow()
                )
                event_dict = event.dict(by_alias=True, exclude={"id"})
                event_docs.append(event_dict)
            except Exception as e:
                failed_count += 1
                continue

        # Bulk insert
        if event_docs:
            result = await collection.insert_many(event_docs)
            event_ids = [str(id) for id in result.inserted_ids]

        return BatchIngestResponse(
            status="success",
            message=f"Batch ingestion complete",
            total_received=len(events),
            total_stored=len(event_ids),
            failed=failed_count,
            event_ids=event_ids
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest batch events: {str(e)}"
        )

async def get_user_events(
    user_id: str,
    event_type: Optional[EventType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """
    Retrieve events for a specific user with optional filters
    """
    try:
        collection = MongoDB.get_collection("events")

        # Build query
        query = {"user_id": user_id}

        if event_type:
            query["event_type"] = event_type.value

        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date

        # Get total count
        total = await collection.count_documents(query)

        # Get events with pagination
        cursor = collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        events_data = await cursor.to_list(length=limit)

        # Convert to EventResponse objects
        events = []
        for event_dict in events_data:
            event_dict["id"] = str(event_dict.pop("_id"))
            events.append(EventResponse(**event_dict))

        return EventListResponse(
            total=total,
            events=events,
            user_id=user_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve events: {str(e)}"
        )

async def get_recent_events(
    user_id: str,
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back")
):
    """
    Get recent events for a user (last N hours)
    """
    try:
        start_date = datetime.utcnow() - timedelta(hours=hours)

        collection = MongoDB.get_collection("events")
        query = {
            "user_id": user_id,
            "timestamp": {"$gte": start_date}
        }

        cursor = collection.find(query).sort("timestamp", -1).limit(100)
        events_data = await cursor.to_list(length=100)

        events = []
        for event_dict in events_data:
            event_dict["id"] = str(event_dict.pop("_id"))
            events.append(EventResponse(**event_dict))

        return EventListResponse(
            total=len(events),
            events=events,
            user_id=user_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recent events: {str(e)}"
        )

async def get_event_statistics(
    user_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days for statistics")
):
    """
    Get event statistics for a user over a time period
    """
    try:
        collection = MongoDB.get_collection("events")
        start_date = datetime.utcnow() - timedelta(days=days)

        # Aggregation pipeline for statistics
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": "$event_type",
                    "count": {"$sum": 1},
                    "avg_value": {"$avg": "$value"}
                }
            }
        ]

        cursor = collection.aggregate(pipeline)
        stats_data = await cursor.to_list(length=None)

        # Format statistics
        statistics = {
            "user_id": user_id,
            "period_days": days,
            "event_counts": {},
            "averages": {}
        }

        for stat in stats_data:
            event_type = stat["_id"]
            statistics["event_counts"][event_type] = stat["count"]
            if stat["avg_value"] is not None:
                statistics["averages"][event_type] = round(stat["avg_value"], 2)

        return statistics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

async def delete_event(user_id: str, event_id: str):
    """
    Delete a specific event
    """
    try:
        from bson import ObjectId

        collection = MongoDB.get_collection("events")

        result = await collection.delete_one({
            "_id": ObjectId(event_id),
            "user_id": user_id
        })

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        return {
            "status": "success",
            "message": "Event deleted successfully",
            "event_id": event_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}"
        )

# Helper functions for future implementation
async def publish_to_stream(event: Dict[str, Any]):
    """
    Publish event to Kafka or Redis stream for real-time processing
    TODO: Implement Kafka producer
    """
    pass

async def trigger_anomaly_detection(event: Dict[str, Any]):
    """
    Trigger anomaly detection for specific event types
    TODO: Implement anomaly detection trigger
    """
    pass
