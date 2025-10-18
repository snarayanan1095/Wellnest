"""
API Router
Central router for all API endpoints
"""
from fastapi import APIRouter, status
from app.api import event_ingestion_service
from app.api.api_schema import EventIngestResponse

# Create main API router
api_router = APIRouter(prefix="/api")

# Register event ingestion endpoint directly using endpoint= parameter
api_router.add_api_route(
    path="/events",
    endpoint=event_ingestion_service.ingest_event,
    methods=["POST"],
    response_model=EventIngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["events"],
    summary="Ingest sensor event",
    description="Ingest a single event from sensor simulator (all string fields)"
)

# Future routers can be added here:
# api_router.add_api_route(path="/events/batch", endpoint=..., methods=["POST"])
# api_router.add_api_route(path="/events/{sensor_id}", endpoint=..., methods=["GET"])
