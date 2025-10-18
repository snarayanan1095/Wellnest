"""
API Schemas
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Event Ingestion Schemas
class EventIngestResponse(BaseModel):
    """Response after successful event ingestion"""
    status: str = "success"
    message: str
    event_id: str
    timestamp: str  # Changed from datetime to str to match Event model

class BatchIngestResponse(BaseModel):
    """Response after batch event ingestion"""
    status: str = "success"
    message: str
    total_received: int
    total_stored: int
    failed: int
    event_ids: List[str]

class EventListResponse(BaseModel):
    """Response for event list queries"""
    total: int
    events: List["EventResponse"]  # Forward reference
    user_id: Optional[str] = None

# Import EventResponse to resolve forward reference
from app.models.event import EventResponse

# Update forward references
EventListResponse.model_rebuild()