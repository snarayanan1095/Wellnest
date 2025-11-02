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
from app.services.nim_llm_service import NIMLLMService
from app.schema.search import SearchRequest, SearchResponse, SearchResult, AnalysisResult
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

def build_analysis_prompt(query: str, search_results: list) -> str:
    """Build a prompt for LLM to analyze search results"""
    # Format the search results for the prompt
    results_summary = []
    for i, result in enumerate(search_results[:5], 1):  # Limit to top 5 for analysis
        summary = f"- Day {i} ({result.get('date', 'unknown')}): "

        # Add key metrics if available
        if 'total_bathroom_events' in result or 'bathroom_visits' in result:
            bathroom = result.get('total_bathroom_events') or result.get('bathroom_visits')
            summary += f"{bathroom} bathroom visits"

        if 'wake_up_time' in result:
            summary += f", woke at {result.get('wake_up_time')}"

        if 'bed_time' in result:
            summary += f", slept at {result.get('bed_time')}"

        if 'total_kitchen_events' in result or 'kitchen_visits' in result:
            kitchen = result.get('total_kitchen_events') or result.get('kitchen_visits')
            summary += f", {kitchen} kitchen visits"

        results_summary.append(summary)

    prompt = f"""The user searched for: '{query}'

Found {len(search_results)} matching days with these patterns:
{chr(10).join(results_summary)}

Please provide a concise analysis with:

SUMMARY (1-2 sentences):
Describe the overall pattern observed.

KEY PATTERNS:
- List 2-3 specific patterns you observe
- Be specific with numbers and trends

HEALTH IMPLICATIONS:
- List 2-3 potential health concerns
- Focus on what these patterns might indicate

RECOMMENDATIONS:
- List 2-3 actionable steps for caregivers
- Be specific and practical"""

    return prompt


# Search endpoint using NIM embedding service directly
@api_router.post("/search", response_model=SearchResponse, tags=["search"], summary="Semantic search")
async def search(request: SearchRequest):
    """
    Perform semantic search using NIM embedding service's semantic_search method directly.
    This searches through daily routines using natural language queries.
    Optionally includes AI analysis of the results.
    """
    try:
        logger.info(f"Searching for query: '{request.query}' in household: {request.household_id}, include_analysis: {request.include_analysis}")

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

        # Optionally get LLM analysis
        analysis = None
        if request.include_analysis and len(search_results) > 0:
            try:
                logger.info("Generating LLM analysis of search results...")

                # Build prompt with search results
                prompt = build_analysis_prompt(request.query, search_results)

                # Get LLM analysis
                llm_response = NIMLLMService.get_custom_summary(
                    prompt=prompt,
                    max_tokens=250,
                    temperature=0.7
                )

                # Parse the LLM response based on our structured prompt
                insights = []
                recommendations = ""
                summary = ""

                # Split response into lines for parsing
                lines = llm_response.strip().split('\n')
                current_section = None

                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    line_upper = line_stripped.upper()

                    # Identify sections by headers
                    if 'SUMMARY' in line_upper and ':' in line:
                        current_section = 'summary'
                        # Get the content after the colon if on same line
                        content_after = line.split(':', 1)[1].strip() if ':' in line else ''
                        if content_after:
                            summary = content_after
                        continue
                    elif 'KEY PATTERN' in line_upper:
                        current_section = 'patterns'
                        continue
                    elif 'HEALTH IMPLICATION' in line_upper:
                        current_section = 'health'
                        continue
                    elif 'RECOMMENDATION' in line_upper:
                        current_section = 'recommendations'
                        continue

                    # Parse content based on current section
                    if current_section == 'summary' and line_stripped and not summary:
                        # Remove markdown formatting from summary
                        summary = line_stripped.replace('**', '').replace('__', '')
                    elif current_section == 'patterns' and (line_stripped.startswith('-') or line_stripped.startswith('*')):
                        pattern = line_stripped.lstrip('-*').strip()
                        # Remove markdown formatting
                        pattern = pattern.replace('**', '').replace('__', '')
                        if pattern:
                            insights.append(pattern)
                    elif current_section == 'health' and (line_stripped.startswith('-') or line_stripped.startswith('*')):
                        health = line_stripped.lstrip('-*').strip()
                        # Remove markdown formatting
                        health = health.replace('**', '').replace('__', '')
                        if health:
                            insights.append(f"Health: {health}")
                    elif current_section == 'recommendations' and (line_stripped.startswith('-') or line_stripped.startswith('*')):
                        rec = line_stripped.lstrip('-*').strip()
                        # Remove markdown formatting
                        rec = rec.replace('**', '').replace('__', '')
                        if rec:
                            if not recommendations:
                                recommendations = rec
                            else:
                                recommendations += f"; {rec}"

                # Fallback if parsing didn't work well
                if not summary:
                    # Try to extract first non-header paragraph
                    for line in lines:
                        if line.strip() and not any(header in line.upper() for header in ['SUMMARY', 'PATTERN', 'HEALTH', 'RECOMMENDATION']):
                            summary = line.strip()[:200]
                            break
                    if not summary:
                        summary = "Analysis of search results based on the query patterns."

                # Clean up and limit insights
                clean_insights = []
                seen = set()
                for insight in insights[:5]:  # Max 5 insights
                    # Remove any remaining markdown formatting
                    insight = insight.replace('**', '').replace('__', '').replace('*', '').strip()
                    # Clean and truncate
                    insight = insight[:150] + "..." if len(insight) > 150 else insight
                    if insight not in seen and len(insight) > 10:
                        clean_insights.append(insight)
                        seen.add(insight)

                # Clean summary of any remaining markdown
                summary = summary.replace('**', '').replace('__', '').replace('*', '').strip()

                # Clean recommendations of any remaining markdown
                if recommendations:
                    recommendations = recommendations.replace('**', '').replace('__', '').replace('*', '').strip()

                analysis = AnalysisResult(
                    summary=summary,
                    insights=clean_insights if clean_insights else ["Pattern analysis completed based on search results."],
                    recommendations=recommendations if recommendations else None,
                    confidence=0.85 if len(clean_insights) > 0 else 0.7,
                    analyzed_count=min(len(search_results), 5)
                )

                logger.info("LLM analysis generated successfully")

            except Exception as e:
                logger.error(f"Failed to generate LLM analysis: {str(e)}")
                # Continue without analysis if LLM fails

        return SearchResponse(
            query=request.query,
            results=formatted_results,
            analysis=analysis
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
