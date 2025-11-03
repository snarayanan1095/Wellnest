# app/api/alerts.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timedelta
from app.db.mongo import MongoDB
from pydantic import BaseModel

router = APIRouter()

class Alert(BaseModel):
    alert_id: str
    household_id: str
    type: str
    severity: str
    title: str
    message: str
    timestamp: str
    acknowledged: bool
    created_at: str

class AlertUpdateRequest(BaseModel):
    acknowledged: bool

@router.get("/alerts/{household_id}", response_model=List[Alert])
async def get_household_alerts(
    household_id: str,
    limit: int = Query(default=20, description="Maximum number of alerts to return"),
    severity: Optional[str] = Query(default=None, description="Filter by severity (high, medium, low)"),
    acknowledged: Optional[bool] = Query(default=None, description="Filter by acknowledged status"),
    hours: int = Query(default=24, description="Get alerts from last N hours"),
    include_resolved: bool = Query(default=False, description="Include auto-resolved alerts")
):
    """Get alerts for a specific household"""
    try:
        # Build query
        query = {"household_id": household_id}

        # Add time filter
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        query["timestamp"] = {"$gte": time_threshold.isoformat()}

        # Add optional filters
        if severity:
            query["severity"] = severity
        if acknowledged is not None:
            query["acknowledged"] = acknowledged

        # By default, exclude auto-resolved alerts unless specifically requested
        if not include_resolved:
            query["$or"] = [
                {"auto_resolved": {"$exists": False}},
                {"auto_resolved": False}
            ]

        # Get alerts from MongoDB
        alerts = await MongoDB.read(
            "alerts",
            query=query,
            sort=[("timestamp", -1)],
            limit=limit
        )

        # Transform alerts to response format
        result = []
        for alert in alerts:
            # Get alert title based on type
            title = _get_alert_title(alert.get("type", "unknown"))

            result.append(Alert(
                alert_id=alert.get("_id", ""),
                household_id=alert.get("household_id", ""),
                type=alert.get("type", ""),
                severity=alert.get("severity", "info"),
                title=title,
                message=alert.get("message", ""),
                timestamp=alert.get("timestamp", ""),
                acknowledged=alert.get("acknowledged", False),
                created_at=alert.get("created_at", alert.get("timestamp", ""))
            ))

        return result

    except Exception as e:
        print(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/alerts/{alert_id}")
async def update_alert(alert_id: str, update_request: AlertUpdateRequest):
    """Update an alert (e.g., mark as acknowledged)"""
    try:
        # Update the alert
        result = await MongoDB.update(
            "alerts",
            {"_id": alert_id},
            {"$set": {"acknowledged": update_request.acknowledged}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"message": "Alert updated successfully"}

    except Exception as e:
        print(f"Error updating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/{household_id}/count")
async def get_alert_count(
    household_id: str,
    hours: int = Query(default=24, description="Count alerts from last N hours")
):
    """Get alert counts by severity for a household"""
    try:
        # Build base query - exclude auto-resolved alerts from counts
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        base_query = {
            "household_id": household_id,
            "timestamp": {"$gte": time_threshold.isoformat()},
            "acknowledged": False,
            "$or": [
                {"auto_resolved": {"$exists": False}},
                {"auto_resolved": False}
            ]
        }

        # Count by severity (matching actual severity levels from anomaly detector)
        high_count = await MongoDB.count(
            "alerts",
            {**base_query, "severity": "high"}
        )

        medium_count = await MongoDB.count(
            "alerts",
            {**base_query, "severity": "medium"}
        )

        low_count = await MongoDB.count(
            "alerts",
            {**base_query, "severity": "low"}
        )

        return {
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
            "total": high_count + medium_count + low_count
        }

    except Exception as e:
        print(f"Error counting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_alert_title(alert_type: str) -> str:
    """Get human-readable title for alert type"""
    titles = {
        "sos": "Emergency SOS",
        "door_open_night": "Door Open at Night",
        "prolonged_bathroom": "Extended Bathroom Visit",
        "no_movement": "No Movement Detected",
        "missed_routine": "Routine Activity Missed",
        "unusual_activity": "Unusual Activity Pattern",
        "fall_detected": "Potential Fall Detected",
        "wandering": "Potential Wandering",
        "medication_missed": "Medication Schedule Missed",
        "prolonged_inactivity": "Prolonged Inactivity",
        "missed_kitchen_activity": "Missed Kitchen Activity",
        "excessive_bathroom_visits": "Excessive Bathroom Visits",
        "late_wake_up": "Late Wake Up"
    }
    return titles.get(alert_type, alert_type.replace("_", " ").title())

@router.post("/alerts/{household_id}/resolve-inactivity")
async def manually_resolve_inactivity_alerts(household_id: str):
    """Manually trigger resolution of prolonged inactivity alerts for testing"""
    try:
        from app.services.anomaly_detector import detector
        await detector.resolve_inactivity_alerts(household_id)

        # Check how many alerts remain unresolved
        remaining = await MongoDB.count(
            "alerts",
            {
                "household_id": household_id,
                "type": "prolonged_inactivity",
                "acknowledged": False
            }
        )

        return {
            "message": "Inactivity alert resolution triggered",
            "household_id": household_id,
            "remaining_unresolved": remaining
        }
    except Exception as e:
        print(f"Error in manual resolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))