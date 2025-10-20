from pydantic import BaseModel, Field
from typing import Optional

class Event(BaseModel):
    """Model for sensor events - all fields are strings"""
    household_id: Optional[str] = Field(None, alias="_id", description="Household identifier")
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: str = Field(..., description="Event timestamp as string")
    sensor_id: str = Field(..., description="Sensor identifier")
    sensor_type: str = Field(..., description="Type of sensor")
    location: str = Field(..., description="Sensor location")
    value: str = Field(..., description="Sensor value as string")
    resident: Optional[str] = Field(None, description="Associated resident identifier")

    class Config:
        populate_by_name = True

class EventCreate(BaseModel):
    """Model for creating a new event from sensor client"""
    household_id: str
    timestamp: str
    sensor_id: str
    sensor_type: str
    location: str
    value: str
    resident: str

class EventResponse(Event):
    """Model for event API responses"""
    pass
