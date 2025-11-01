"""
Search related schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class SearchRequest(BaseModel):
    """Request model for search"""
    query: str = Field(..., description="Natural language search query")
    household_id: str = Field(..., description="Household ID to filter results")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")


class SearchResult(BaseModel):
    """Individual search result"""
    date: str
    score: float
    summary_text: str
    metadata: Optional[dict] = None


class SearchResponse(BaseModel):
    """Response model for search"""
    query: str
    results: List[SearchResult]