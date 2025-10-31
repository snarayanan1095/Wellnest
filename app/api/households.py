"""
Household API endpoints
Provides CRUD operations for households and related data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.mongo import MongoDB
from pydantic import BaseModel, Field

router = APIRouter(prefix="/households", tags=["households"])


# Pydantic Models
class Resident(BaseModel):
    id: str
    name: str
    age: int


class HouseholdResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    residents: List[Resident]
    status: str = "normal"
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class HouseholdListResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    residents: List[Resident]
    status: str  # 'active' or 'inactive'
    last_update: Optional[datetime] = None

    class Config:
        populate_by_name = True


@router.get("", response_model=List[HouseholdListResponse], summary="List all households")
async def list_households():
    """
    Get list of all households
    """
    # Get all households
    households = await MongoDB.read("households", query={}, limit=100)

    # Check recent activity to determine active/inactive status
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    cutoff_time_str = cutoff_time.isoformat()

    for household in households:
        # Check if there are any events in last 24 hours
        recent_events = await MongoDB.read(
            "events",
            query={
                "household_id": household["_id"],
                "timestamp": {"$gte": cutoff_time_str}
            },
            limit=1
        )

    return households


@router.get("/{household_id}", response_model=HouseholdResponse, summary="Get household details")
async def get_household(household_id: str):
    """
    Get detailed information about a specific household
    """
    households = await MongoDB.read("households", query={"_id": household_id}, limit=1)

    if not households:
        raise HTTPException(status_code=404, detail=f"Household {household_id} not found")

    return households[0]
