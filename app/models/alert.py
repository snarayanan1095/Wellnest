from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertType(str, Enum):
    """Types of alerts"""
    ROUTINE_DEVIATION = "routine_deviation"
    MOOD_DECLINE = "mood_decline"
    SLEEP_PATTERN = "sleep_pattern"
    MEDICATION_REMINDER = "medication_reminder"
    CUSTOM = "custom"

class AlertStatus(str, Enum):
    """Alert status"""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class Alert(BaseModel):
    """Model for alerts and notifications"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User identifier")
    alert_type: AlertType = Field(..., description="Type of alert")
    severity: AlertSeverity = Field(default=AlertSeverity.INFO)
    status: AlertStatus = Field(default=AlertStatus.PENDING)
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional alert data")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True

class AlertCreate(BaseModel):
    """Model for creating an alert"""
    alert_type: AlertType
    severity: AlertSeverity = AlertSeverity.INFO
    title: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AlertUpdate(BaseModel):
    """Model for updating an alert"""
    status: Optional[AlertStatus] = None
    acknowledged_at: Optional[datetime] = None

class AlertResponse(Alert):
    """Model for alert API responses"""
    pass
