"""
Test Configuration and Fixtures
Provides common fixtures and utilities for all tests
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, List, Any


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_household_id():
    """Sample household ID for testing"""
    return "household_001"


@pytest.fixture
def sample_event():
    """Sample event data for testing"""
    return {
        "event_id": "test_event_123",
        "household_id": "household_001",
        "timestamp": "2025-01-15T08:30:00",
        "sensor_id": "motion_kitchen",
        "sensor_type": "motion",
        "location": "kitchen",
        "value": "True",
        "resident": "grandmom"
    }


@pytest.fixture
def sample_event_create():
    """Sample EventCreate data"""
    return {
        "household_id": "household_001",
        "timestamp": "2025-01-15T08:30:00",
        "sensor_id": "motion_kitchen",
        "sensor_type": "motion",
        "location": "kitchen",
        "value": "True",
        "resident": "grandmom"
    }


@pytest.fixture
def sample_events_sequence():
    """Sample sequence of events for a day"""
    base_date = "2025-01-15"
    return [
        {
            "event_id": "evt_001",
            "household_id": "household_001",
            "timestamp": f"{base_date}T06:30:00",
            "sensor_id": "bed_bedroom1",
            "sensor_type": "bed_presence",
            "location": "bedroom1",
            "value": "False",  # Wake up
            "resident": "grandmom"
        },
        {
            "event_id": "evt_002",
            "household_id": "household_001",
            "timestamp": f"{base_date}T06:35:00",
            "sensor_id": "motion_bathroom1",
            "sensor_type": "motion",
            "location": "bathroom1",
            "value": "True",
            "resident": "grandmom"
        },
        {
            "event_id": "evt_003",
            "household_id": "household_001",
            "timestamp": f"{base_date}T07:00:00",
            "sensor_id": "motion_kitchen",
            "sensor_type": "motion",
            "location": "kitchen",
            "value": "True",
            "resident": "unknown"
        },
        {
            "event_id": "evt_004",
            "household_id": "household_001",
            "timestamp": f"{base_date}T10:00:00",
            "sensor_id": "motion_bathroom1",
            "sensor_type": "motion",
            "location": "bathroom1",
            "value": "True",
            "resident": "grandmom"
        },
        {
            "event_id": "evt_005",
            "household_id": "household_001",
            "timestamp": f"{base_date}T22:00:00",
            "sensor_id": "bed_bedroom1",
            "sensor_type": "bed_presence",
            "location": "bedroom1",
            "value": "True",  # Go to bed
            "resident": "grandmom"
        },
    ]


@pytest.fixture
def sample_baseline():
    """Sample baseline data for anomaly detection"""
    return {
        "_id": "household_001_2025-01-15_baseline7",
        "household_id": "household_001",
        "baseline_type": "rolling7",
        "computed_at": "2025-01-15T00:00:00",
        "wake_up_time": {
            "median": "06:30",
            "mean": "06:32",
            "std_dev_minutes": 15,
            "earliest": "06:00",
            "latest": "07:00"
        },
        "first_kitchen_time": {
            "median": "07:00",
            "mean": "07:05",
            "std_dev_minutes": 20,
            "earliest": "06:30",
            "latest": "08:00"
        },
        "bathroom_visits": {
            "daily_avg": 4.5,
            "daily_median": 4,
            "min_daily": 3,
            "max_daily": 6,
            "std_dev": 1.2
        },
        "bed_time": {
            "median": "22:00",
            "mean": "22:10",
            "std_dev_minutes": 25,
            "earliest": "21:30",
            "latest": "23:00"
        }
    }


@pytest.fixture
def sample_alert():
    """Sample alert data"""
    return {
        "type": "missed_kitchen_activity",
        "severity": "medium",
        "message": "No kitchen activity detected. Expected by 08:00.",
        "context": "Last seen in bedroom1",
        "household_id": "household_001",
        "timestamp": "2025-01-15T09:30:00",
        "actionable": "Check on resident or call to confirm well-being"
    }


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB client"""
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.read = AsyncMock(return_value=[])
    mock.write = AsyncMock(return_value="mock_id_123")
    mock.aggregate = AsyncMock(return_value=[])
    mock.distinct = AsyncMock(return_value=[])
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_kafka():
    """Mock Kafka client"""
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.publish_event = Mock()
    mock.close = Mock()
    return mock


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
    mock = MagicMock()
    mock.accept = AsyncMock()
    mock.send_json = AsyncMock()
    mock.send_text = AsyncMock()
    mock.receive_text = AsyncMock(return_value='{"ping": "pong"}')
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def daily_routine_sample():
    """Sample daily routine data"""
    return {
        "_id": "household_001_2025-01-14",
        "household_id": "household_001",
        "date": "2025-01-14",
        "wake_up_time": "06:30",
        "bed_time": "22:00",
        "first_kitchen_time": "07:00",
        "bathroom_first_time": "06:35",
        "total_bathroom_events": 4,
        "activity_start": "06:30",
        "activity_end": "22:00",
        "total_events": 45,
        "summary_text": "Woke up at 06:30. kitchen activity at 07:00. 4 bathroom visits (first at 06:35). went to bed at 22:00. Total 45 sensor events."
    }


@pytest.fixture
def multiple_daily_routines():
    """Multiple days of routine data for baseline calculation"""
    routines = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i+1)).strftime("%Y-%m-%d")
        routines.append({
            "_id": f"household_001_{date}",
            "household_id": "household_001",
            "date": date,
            "wake_up_time": f"06:{30 + (i % 3) * 5}",  # Slight variation
            "bed_time": f"22:{(i % 4) * 10}",
            "first_kitchen_time": f"07:{(i % 6) * 5}",
            "bathroom_first_time": f"06:{35 + (i % 3) * 5}",
            "total_bathroom_events": 3 + (i % 4),
            "activity_start": f"06:{30 + (i % 3) * 5}",
            "activity_end": f"22:{(i % 4) * 10}",
            "total_events": 40 + i * 2
        })
    return routines


# Helper functions for tests
def create_timestamp(hour: int, minute: int = 0, date: str = "2025-01-15") -> str:
    """Create a timestamp string"""
    return f"{date}T{hour:02d}:{minute:02d}:00"


def create_event(household_id: str, sensor_type: str, location: str,
                 value: str, timestamp: str, sensor_id: str = None) -> Dict[str, Any]:
    """Helper to create event dictionaries"""
    if sensor_id is None:
        sensor_id = f"{sensor_type}_{location}"

    return {
        "event_id": f"evt_{timestamp.replace(':', '').replace('-', '')}",
        "household_id": household_id,
        "timestamp": timestamp,
        "sensor_id": sensor_id,
        "sensor_type": sensor_type,
        "location": location,
        "value": value,
        "resident": "test_resident"
    }


def assert_alert_structure(alert: Dict[str, Any]):
    """Assert that an alert has the correct structure"""
    required_fields = ["type", "severity", "message", "household_id", "timestamp"]
    for field in required_fields:
        assert field in alert, f"Alert missing required field: {field}"

    assert alert["severity"] in ["low", "medium", "high"], \
        f"Invalid severity: {alert['severity']}"
