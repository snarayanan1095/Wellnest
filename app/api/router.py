"""
API Router
Central router for all API endpoints
"""
from fastapi import APIRouter, status
from app.api import event_ingestion_service
from app.api.api_schema import EventIngestResponse, BatchIngestResponse, EventListResponse

# Create main API router
api_router = APIRouter(prefix="/api")

# Register event ingestion endpoints directly using endpoint= parameter
api_router.add_api_route(
    path="/events/",
    endpoint=event_ingestion_service.ingest_event,
    methods=["POST"],
    response_model=EventIngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["events"],
    summary="Ingest a single event",
    description="Ingest a single event from simulator or device"
)

api_router.add_api_route(
    path="/events/batch",
    endpoint=event_ingestion_service.ingest_batch_events,
    methods=["POST"],
    response_model=BatchIngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["events"],
    summary="Ingest batch events",
    description="Ingest multiple events in a batch"
)

api_router.add_api_route(
    path="/events/{user_id}",
    endpoint=event_ingestion_service.get_user_events,
    methods=["GET"],
    response_model=EventListResponse,
    tags=["events"],
    summary="Get user events",
    description="Retrieve events for a specific user with optional filters"
)

api_router.add_api_route(
    path="/events/{user_id}/recent",
    endpoint=event_ingestion_service.get_recent_events,
    methods=["GET"],
    response_model=EventListResponse,
    tags=["events"],
    summary="Get recent events",
    description="Get recent events for a user (last N hours)"
)

api_router.add_api_route(
    path="/events/{user_id}/stats",
    endpoint=event_ingestion_service.get_event_statistics,
    methods=["GET"],
    tags=["events"],
    summary="Get event statistics",
    description="Get event statistics for a user over a time period"
)

api_router.add_api_route(
    path="/events/{user_id}/events/{event_id}",
    endpoint=event_ingestion_service.delete_event,
    methods=["DELETE"],
    tags=["events"],
    summary="Delete event",
    description="Delete a specific event"
)

# Future routers can be added here:
# api_router.add_api_route(path="/users/", endpoint=users.create_user, methods=["POST"])
# api_router.add_api_route(path="/alerts/", endpoint=alerts.create_alert, methods=["POST"])
