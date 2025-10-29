"""
Semantic Search API Endpoints
Natural language search over routine baselines and anomaly detection
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.db.qdrant_client import QdrantClient
from app.db.mongo import MongoDB
from app.services.nim_embedding_service import NIMEmbeddingService

router = APIRouter(prefix="/search", tags=["semantic-search"])


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., description="Natural language query", example="Find days with unusual sleep patterns")
    household_id: Optional[str] = Field(None, description="Filter by household ID")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")
    score_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity score")


class SemanticSearchResult(BaseModel):
    """Individual search result"""
    relevance_score: float = Field(..., description="Similarity score (0-1)")
    household_id: str
    baseline_id: str
    period: Dict[str, str]
    summary: str
    computed_at: str


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search"""
    query: str
    results: List[SemanticSearchResult]
    count: int
    message: str


class AnomalyCheckRequest(BaseModel):
    """Request model for anomaly detection"""
    household_id: str = Field(..., description="Household ID to check")
    date: str = Field(..., description="Date of routine to check (YYYY-MM-DD)")


class AnomalyCheckResponse(BaseModel):
    """Response model for anomaly detection"""
    household_id: str
    date: str
    is_unusual: bool
    deviation_score: float = Field(..., description="0-1, higher means more unusual")
    average_similarity: Optional[float] = None
    max_similarity: Optional[float] = None
    interpretation: str
    similar_baselines: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None


@router.post("/routines", response_model=SemanticSearchResponse, summary="Semantic search for routines")
async def search_routines(request: SemanticSearchRequest):
    """
    Perform semantic search on routine baselines using natural language.

    **Example queries:**
    - "Find days that were unusual"
    - "Show routines with late kitchen activity and high bathroom visits"
    - "Days with disrupted sleep patterns"
    - "Routines with early wake-up times"
    - "High activity days with frequent bathroom visits"
    - "Days with missed morning kitchen activity"

    **How it works:**
    1. Your query is converted to an embedding using NIM
    2. Vector similarity search finds matching routines
    3. Results are ranked by relevance score (higher = more similar)
    """
    try:
        # Perform semantic search
        results = await QdrantClient.semantic_search_routines(
            query_text=request.query,
            embedding_service=NIMEmbeddingService,
            collection_name="routine_baselines",
            limit=request.limit,
            score_threshold=request.score_threshold,
            household_id=request.household_id
        )

        return SemanticSearchResponse(
            query=request.query,
            results=results,
            count=len(results),
            message=f"Found {len(results)} matching routines"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.get("/routines/household/{household_id}", summary="Search routines by household")
async def search_household_routines(
    household_id: str,
    query: str = Query(..., description="Natural language query"),
    limit: int = Query(10, ge=1, le=50),
    score_threshold: float = Query(0.5, ge=0.0, le=1.0)
):
    """
    Search routines for a specific household using natural language.
    Convenience endpoint that combines household filtering with semantic search.
    """
    request = SemanticSearchRequest(
        query=query,
        household_id=household_id,
        limit=limit,
        score_threshold=score_threshold
    )
    return await search_routines(request)


@router.post("/anomaly/detect", response_model=AnomalyCheckResponse, summary="Detect routine anomalies")
async def detect_anomaly(request: AnomalyCheckRequest):
    """
    Check if a specific daily routine is unusual compared to baselines.

    **Use case:**
    After processing a day's events, check if the routine deviates significantly
    from the household's typical patterns.

    **Returns:**
    - `is_unusual`: Boolean flag for quick checks
    - `deviation_score`: 0-1 score (higher = more unusual)
    - `interpretation`: Human-readable explanation
    - `similar_baselines`: Most similar baseline periods for comparison

    **Deviation score interpretation:**
    - < 0.15: Very similar - no concerns
    - 0.15-0.25: Slightly different - minor variation
    - 0.25-0.40: Moderately different - worth monitoring
    - 0.40-0.60: Significantly different - potential anomaly
    - > 0.60: Highly unusual - immediate attention recommended
    """
    try:
        # Fetch the daily routine from MongoDB
        routine_id = f"{request.household_id}_{request.date}"
        routines = await MongoDB.read(
            "daily_routines",
            query={"_id": routine_id},
            limit=1
        )

        if not routines:
            raise HTTPException(
                status_code=404,
                detail=f"No routine found for household {request.household_id} on {request.date}"
            )

        daily_routine = routines[0]

        # Compare against baselines
        comparison = await QdrantClient.compare_routine_to_baseline(
            daily_routine=daily_routine,
            embedding_service=NIMEmbeddingService,
            household_id=request.household_id,
            collection_name="routine_baselines"
        )

        return AnomalyCheckResponse(
            household_id=request.household_id,
            date=request.date,
            **comparison
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Anomaly detection failed: {str(e)}"
        )


@router.get("/anomaly/recent/{household_id}", summary="Check recent routines for anomalies")
async def check_recent_anomalies(
    household_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of recent days to check")
):
    """
    Check the most recent N days for a household and identify any anomalies.

    **Use case:**
    Daily dashboard check to see if there have been any unusual patterns recently.

    **Returns:**
    List of recent days with their anomaly status, sorted by most recent first.
    """
    try:
        # Fetch recent daily routines from MongoDB
        routines = await MongoDB.read(
            "daily_routines",
            query={"household_id": household_id},
            limit=days,
            sort=[("date", -1)]  # Most recent first
        )

        if not routines:
            return {
                "household_id": household_id,
                "checked_days": 0,
                "anomalies_found": 0,
                "results": [],
                "message": f"No routines found for household {household_id}"
            }

        # Check each routine for anomalies
        anomaly_results = []
        anomalies_count = 0

        for routine in routines:
            try:
                comparison = await QdrantClient.compare_routine_to_baseline(
                    daily_routine=routine,
                    embedding_service=NIMEmbeddingService,
                    household_id=household_id,
                    collection_name="routine_baselines"
                )

                if comparison.get('is_unusual'):
                    anomalies_count += 1

                anomaly_results.append({
                    "date": routine.get('date'),
                    "is_unusual": comparison.get('is_unusual'),
                    "deviation_score": comparison.get('deviation_score'),
                    "interpretation": comparison.get('interpretation'),
                    "summary": routine.get('summary_text', '')
                })

            except Exception as e:
                # Skip this routine if comparison fails
                print(f"Warning: Failed to check anomaly for {routine.get('date')}: {e}")
                continue

        return {
            "household_id": household_id,
            "checked_days": len(anomaly_results),
            "anomalies_found": anomalies_count,
            "results": anomaly_results,
            "message": f"Checked {len(anomaly_results)} days, found {anomalies_count} anomalies"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recent anomaly check failed: {str(e)}"
        )
