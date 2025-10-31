"""
Dashboard-specific API endpoints
Provides data aggregation and queries for the dashboard UI
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.mongo import MongoDB
from pydantic import BaseModel, Field

router = APIRouter(tags=["dashboard"])


# Pydantic Models
class EventResponse(BaseModel):
    id: str = Field(alias="_id")
    household_id: str
    sensor_id: str
    sensor_type: str
    location: str
    timestamp: datetime
    value: Optional[str] = None

    class Config:
        populate_by_name = True


class AlertResponse(BaseModel):
    id: str = Field(alias="_id")
    household_id: str
    type: str
    severity: str
    message: str  # Changed from title/description to match actual DB schema
    context: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    created_at: Optional[datetime] = None
    # Optional fields for compatibility
    title: Optional[str] = None
    description: Optional[str] = None
    actionable: Optional[str] = None

    class Config:
        populate_by_name = True


class WeeklyTrendResponse(BaseModel):
    date: str
    score: float
    status: str
    key_activities: int
    anomalies: int


@router.get("/events", response_model=List[EventResponse], summary="Get recent events")
async def get_events(
    household_id: str = Query(..., description="Household ID"),
    limit: int = Query(50, ge=1, le=500, description="Max number of events"),
    since: Optional[datetime] = Query(None, description="Get events since this timestamp")
):
    """
    Get recent sensor events for a household
    Used for the live activity feed
    """
    # Build query
    query = {"household_id": household_id}
    if since:
        query["timestamp"] = {"$gte": since.isoformat()}

    # Get events sorted by timestamp descending
    events = await MongoDB.read("events", query=query, sort=[("timestamp", -1)], limit=limit)

    return events


@router.get("/alerts", response_model=List[AlertResponse], summary="Get alerts")
async def get_alerts(
    household_id: str = Query(..., description="Household ID"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get alerts for a household
    Can filter by acknowledged status
    """
    # Build query
    query = {"household_id": household_id}
    if acknowledged is not None:
        query["acknowledged"] = acknowledged

    # Get alerts sorted by timestamp descending
    alerts = await MongoDB.read("alerts", query=query, sort=[("timestamp", -1)], limit=limit)

    return alerts


@router.post("/alerts/{alert_id}/acknowledge", summary="Acknowledge an alert")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: Optional[str] = Query(None, description="User who acknowledged")
):
    """
    Mark an alert as acknowledged
    """
    # Update alert
    modified_count = await MongoDB.update(
        "alerts",
        query={"_id": alert_id},
        update={
            "$set": {
                "acknowledged": True,
                "acknowledged_at": datetime.utcnow(),
                "acknowledged_by": acknowledged_by
            }
        }
    )

    if modified_count == 0:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    return {"status": "success", "message": "Alert acknowledged"}


@router.get("/trends/weekly", response_model=List[WeeklyTrendResponse], summary="Get weekly trends")
async def get_weekly_trends(
    household_id: str = Query(..., description="Household ID")
):
    """
    Get weekly trend data for charts
    Returns last 7 days of scores and statistics
    """
    # Get last 7 days
    trends = []
    today = datetime.utcnow().date()

    for i in range(6, -1, -1):  # 6 days ago to today
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")

        # Get daily routine
        routines = await MongoDB.read(
            "daily_routines",
            query={
                "household_id": household_id,
                "date": date_str
            },
            limit=1
        )
        routine = routines[0] if routines else None

        # Count anomalies for this day
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        anomaly_count = await MongoDB.count(
            "alerts",
            query={
                "household_id": household_id,
                "type": "anomaly",
                "timestamp": {"$gte": start_of_day.isoformat(), "$lte": end_of_day.isoformat()}
            }
        )

        if routine:
            score = calculate_daily_score(routine)
            status = "normal" if score >= 80 else ("caution" if score >= 60 else "alert")
            key_activities = routine.get("total_daily_events", 0)
        else:
            score = 0.0
            status = "alert"
            key_activities = 0

        trends.append({
            "date": date_str,
            "score": score,
            "status": status,
            "key_activities": key_activities,
            "anomalies": anomaly_count
        })

    return trends


@router.get("/details/day", summary="Get detailed day information")
async def get_day_details(
    household_id: str = Query(..., description="Household ID"),
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """
    Get comprehensive details for a specific day
    Includes routine, anomalies, and similar days
    """
    # Get routine for the day
    routines = await MongoDB.read(
        "daily_routines",
        query={
            "household_id": household_id,
            "date": date
        },
        limit=1
    )

    if not routines:
        raise HTTPException(status_code=404, detail=f"No data found for {date}")

    routine = routines[0]

    # Get anomalies for this day
    target_date = datetime.strptime(date, "%Y-%m-%d")
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    anomalies = await MongoDB.read(
        "alerts",
        query={
            "household_id": household_id,
            "timestamp": {"$gte": start_of_day.isoformat(), "$lte": end_of_day.isoformat()}
        },
        limit=100
    )

    # Extract routine activities
    routine_activities = []

    if routine.get("wake_up_time"):
        routine_activities.append({
            "activity": "Wake Up",
            "expected_time": routine.get("wake_up_time"),
            "actual_time": routine.get("wake_up_time"),
            "status": "on-time",
            "deviation": 0
        })

    if routine.get("first_kitchen_time"):
        routine_activities.append({
            "activity": "First Kitchen Visit",
            "expected_time": routine.get("first_kitchen_time"),
            "actual_time": routine.get("first_kitchen_time"),
            "status": "on-time",
            "deviation": 0
        })

    if routine.get("bed_time"):
        routine_activities.append({
            "activity": "Bed Time",
            "expected_time": routine.get("bed_time"),
            "actual_time": routine.get("bed_time"),
            "status": "on-time",
            "deviation": 0
        })

    # TODO: Find similar days using vector search on Qdrant
    similar_days = []

    # Generate AI summary
    score = calculate_daily_score(routine)
    summary = f"Day had a score of {score:.0f}/100. Total events: {routine.get('total_daily_events', 0)}. Bathroom visits: {routine.get('bathroom_visits', 0)}."

    return {
        "date": date,
        "routine": routine_activities,
        "anomalies": anomalies,
        "similar_days": similar_days,
        "summary": summary
    }


def calculate_daily_score(routine_data: dict) -> float:
    """Calculate a 0-100 score for a household's daily routine"""
    score = 100.0

    # Penalize for missing key times
    if not routine_data.get("wake_up_time"):
        score -= 10
    if not routine_data.get("bed_time"):
        score -= 10
    if not routine_data.get("first_kitchen_time"):
        score -= 5

    # Penalize for low activity
    total_events = routine_data.get("total_daily_events", 0)
    if total_events < 100:
        score -= 20
    elif total_events < 500:
        score -= 10

    # Bonus for consistent bathroom visits
    bathroom_visits = routine_data.get("bathroom_visits", 0)
    if 3 <= bathroom_visits <= 15:
        score += 5

    return max(0.0, min(100.0, score))
