"""
Search related schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class SearchRequest(BaseModel):
    """Request model for search"""
    query: str = Field(..., description="Natural language search query")
    household_id: str = Field(..., description="Household ID to filter results")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    include_analysis: bool = Field(default=False, description="Include AI analysis of search results")


class SearchResult(BaseModel):
    """Individual search result"""
    date: str
    score: float
    summary_text: str
    metadata: Optional[dict] = None


class AnalysisResult(BaseModel):
    """LLM analysis of search results"""
    summary: str = Field(..., description="Main analysis summary")
    insights: List[str] = Field(default_factory=list, description="Key insights from the analysis")
    recommendations: Optional[str] = Field(None, description="Recommended actions based on analysis")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score of the analysis")
    analyzed_count: int = Field(..., description="Number of results analyzed")


class SearchResponse(BaseModel):
    """Response model for search"""
    query: str
    results: List[SearchResult]
    analysis: Optional[AnalysisResult] = None