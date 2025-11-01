"""
API Router
Central router for all API endpoints
"""
from fastapi import APIRouter, status, HTTPException
from app.api import event_ingestion_service
from app.api.api_schema import EventIngestResponse
from app.scheduler.routine_learner import batch_routine_learner_and_baseline as run_routine_learner
from app.api import websocket
from app.api import households
from app.api import dashboard_endpoints
from app.api import alerts
from app.api import routine_comparison
from app.services.nim_embedding_service import NIMEmbeddingService
from app.schema.search import SearchRequest, SearchResponse, SearchResult
import logging

logger = logging.getLogger(__name__)

# Create main API router
api_router = APIRouter(prefix="/api")

# Include WebSocket router for real-time alerts
api_router.include_router(websocket.router, tags=["websockets"])

# Include Households router
api_router.include_router(households.router)

# Include Dashboard endpoints router
api_router.include_router(dashboard_endpoints.router)

# Include Alerts router
api_router.include_router(alerts.router, tags=["alerts"])

# Include Routine Comparison router
api_router.include_router(routine_comparison.router, tags=["routines"])

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

# Search endpoint using NIM embedding service directly
@api_router.post("/search", response_model=SearchResponse, tags=["search"], summary="Semantic search")
async def search(request: SearchRequest):
    """
    Perform semantic search using NIM embedding service's semantic_search method directly.
    This searches through daily routines using natural language queries.
    """
    try:
        logger.info(f"Searching for query: '{request.query}' in household: {request.household_id}")

        # Initialize NIM embedding service if not already done
        if NIMEmbeddingService.client is None:
            NIMEmbeddingService.initialize()

        # Call the semantic_search method directly from NIM embedding service
        search_results = await NIMEmbeddingService.semantic_search(
            query=request.query,
            household_id=request.household_id,
            top_k=request.limit
        )

        # Format results for frontend
        formatted_results = []
        for result in search_results:
            # Extract metadata from the result
            metadata = {}

            # Handle various field names for compatibility
            if 'wake_up_time' in result:
                metadata['wake_up_time'] = result.get('wake_up_time')
            if 'bed_time' in result:
                metadata['bed_time'] = result.get('bed_time')

            # Handle bathroom visits (might be under different names)
            bathroom_visits = result.get('bathroom_visits') or result.get('total_bathroom_events')
            if bathroom_visits is not None:
                metadata['bathroom_visits'] = bathroom_visits

            # Handle kitchen visits (might be under different names)
            kitchen_visits = result.get('kitchen_visits') or result.get('total_kitchen_events')
            if kitchen_visits is not None:
                metadata['kitchen_visits'] = kitchen_visits

            if 'living_room_time' in result:
                metadata['living_room_time'] = result.get('living_room_time')
            if 'bedroom_time' in result:
                metadata['bedroom_time'] = result.get('bedroom_time')

            formatted_result = SearchResult(
                date=result.get('date', 'unknown'),
                score=result.get('score', 0.0),
                summary_text=result.get('summary_text', 'No summary available'),
                metadata=metadata if metadata else None
            )
            formatted_results.append(formatted_result)

        return SearchResponse(
            query=request.query,
            results=formatted_results
        )

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

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
