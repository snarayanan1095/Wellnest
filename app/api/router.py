"""
API Router
Central router for all API endpoints
"""
from fastapi import APIRouter, status
from app.api import event_ingestion_service
from app.api.api_schema import EventIngestResponse
from app.scheduler.routine_learner import batch_routine_learner_and_baseline as run_routine_learner
from app.api import websocket
from app.api import semantic_search
from app.api import households
from app.api import dashboard_endpoints

# Create main API router
api_router = APIRouter(prefix="/api")

# Include WebSocket router for real-time alerts
api_router.include_router(websocket.router, tags=["websockets"])

# Include Semantic Search router
api_router.include_router(semantic_search.router, tags=["semantic-search"])

# Include Households router
api_router.include_router(households.router)

# Include Dashboard endpoints router
api_router.include_router(dashboard_endpoints.router)

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

# Manual trigger endpoint for routine learner (for testing)
@api_router.post("/routines/trigger", tags=["routines"], summary="Manually trigger routine learning")
async def trigger_routine_learner():
    """
    Manually trigger the routine learning process.
    Useful for testing without waiting for the scheduled job.
    """
    result = await run_routine_learner()
    return result if result else {"message": "Routine learning completed", "status": "success"}

# Future routers can be added here:
# api_router.add_api_route(path="/events/batch", endpoint=..., methods=["POST"])
# api_router.add_api_route(path="/events/{sensor_id}", endpoint=..., methods=["GET"])
