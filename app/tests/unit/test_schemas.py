"""
Tests for Pydantic Schemas
Tests data validation, serialization, and model behavior
"""
import pytest
from pydantic import ValidationError
from app.schema.event import Event, EventCreate, EventResponse
from app.api.api_schema import EventIngestResponse, BatchIngestResponse


class TestEventSchemas:
    """Test Event schema models"""

    def test_event_create_valid(self, sample_event_create):
        """Test creating valid EventCreate"""
        event = EventCreate(**sample_event_create)

        assert event.household_id == sample_event_create["household_id"]
        assert event.sensor_type == sample_event_create["sensor_type"]
        assert event.timestamp == sample_event_create["timestamp"]

    def test_event_create_missing_required_field(self):
        """Test EventCreate fails without required fields"""
        with pytest.raises(ValidationError):
            EventCreate(household_id="test", sensor_id="sensor1")

    def test_event_full_valid(self, sample_event):
        """Test creating full Event model"""
        event = Event(**sample_event)

        assert event.event_id == sample_event["event_id"]
        assert event.household_id == sample_event["household_id"]
        assert event.sensor_type == sample_event["sensor_type"]

    def test_event_optional_fields(self):
        """Test Event with optional fields"""
        event = Event(
            event_id="evt_123",
            timestamp="2025-01-15T10:00:00",
            sensor_id="motion_kitchen",
            sensor_type="motion",
            location="kitchen",
            value="True"
            # resident is optional
        )

        assert event.resident is None

    def test_event_response_inherits_event(self, sample_event):
        """Test EventResponse is based on Event"""
        event_response = EventResponse(**sample_event)

        assert isinstance(event_response, Event)
        assert event_response.event_id == sample_event["event_id"]

    def test_event_serialization(self, sample_event):
        """Test Event can be serialized to dict"""
        event = Event(**sample_event)
        event_dict = event.model_dump()

        assert isinstance(event_dict, dict)
        assert "event_id" in event_dict
        assert "household_id" in event_dict

    def test_event_with_alias(self):
        """Test Event uses alias for household_id"""
        event_data = {
            "_id": "household_001",  # Using alias
            "event_id": "evt_123",
            "timestamp": "2025-01-15T10:00:00",
            "sensor_id": "motion_kitchen",
            "sensor_type": "motion",
            "location": "kitchen",
            "value": "True"
        }

        event = Event(**event_data)
        assert event.household_id == "household_001"


class TestAPISchemas:
    """Test API response schemas"""

    def test_event_ingest_response_valid(self):
        """Test creating EventIngestResponse"""
        response = EventIngestResponse(
            status="success",
            message="Event ingested",
            event_id="evt_123",
            timestamp="2025-01-15T10:00:00"
        )

        assert response.status == "success"
        assert response.event_id == "evt_123"

    def test_event_ingest_response_default_status(self):
        """Test EventIngestResponse has default status"""
        response = EventIngestResponse(
            message="Test",
            event_id="evt_123",
            timestamp="2025-01-15T10:00:00"
        )

        assert response.status == "success"

    def test_batch_ingest_response_valid(self):
        """Test creating BatchIngestResponse"""
        response = BatchIngestResponse(
            message="Batch processed",
            total_received=100,
            total_stored=98,
            failed=2,
            event_ids=["evt_1", "evt_2", "evt_3"]
        )

        assert response.total_received == 100
        assert response.total_stored == 98
        assert response.failed == 2
        assert len(response.event_ids) == 3

    def test_batch_ingest_response_missing_required(self):
        """Test BatchIngestResponse requires all fields"""
        with pytest.raises(ValidationError):
            BatchIngestResponse(
                message="Test",
                total_received=10
                # Missing other required fields
            )

    def test_event_ingest_response_serialization(self):
        """Test response can be serialized for API"""
        response = EventIngestResponse(
            message="Test",
            event_id="evt_123",
            timestamp="2025-01-15T10:00:00"
        )

        response_dict = response.model_dump()
        assert isinstance(response_dict, dict)
        assert "status" in response_dict
        assert "event_id" in response_dict

    def test_timestamp_as_string(self):
        """Test that timestamp is string, not datetime"""
        response = EventIngestResponse(
            message="Test",
            event_id="evt_123",
            timestamp="2025-01-15T10:00:00"
        )

        # Should accept string
        assert isinstance(response.timestamp, str)


class TestSchemaValidation:
    """Test schema validation rules"""

    def test_event_empty_strings_accepted(self):
        """Test that empty strings are accepted in fields"""
        event = EventCreate(
            household_id="h001",
            timestamp="2025-01-15T10:00:00",
            sensor_id="",
            sensor_type="motion",
            location="",
            value="",
            resident=""
        )

        # Empty strings are valid
        assert event.sensor_id == ""
        assert event.location == ""

    def test_event_create_extra_fields_ignored(self):
        """Test that extra fields are ignored by default"""
        event_data = {
            "household_id": "h001",
            "timestamp": "2025-01-15T10:00:00",
            "sensor_id": "s001",
            "sensor_type": "motion",
            "location": "kitchen",
            "value": "True",
            "resident": "test",
            "extra_field": "ignored"  # Should be ignored
        }

        event = EventCreate(**event_data)
        assert not hasattr(event, "extra_field")

    def test_type_coercion(self):
        """Test that Pydantic coerces types"""
        # Integer value should be converted to string
        event_data = {
            "household_id": "h001",
            "timestamp": "2025-01-15T10:00:00",
            "sensor_id": "s001",
            "sensor_type": "motion",
            "location": "kitchen",
            "value": 123,  # Integer instead of string
            "resident": "test"
        }

        event = EventCreate(**event_data)
        # Should be coerced to string
        assert event.value == "123"
        assert isinstance(event.value, str)


class TestSchemaEdgeCases:
    """Test edge cases and special scenarios"""

    def test_very_long_strings(self):
        """Test handling of very long string values"""
        long_string = "x" * 10000

        event = EventCreate(
            household_id="h001",
            timestamp="2025-01-15T10:00:00",
            sensor_id=long_string,
            sensor_type="motion",
            location="kitchen",
            value="True",
            resident="test"
        )

        assert len(event.sensor_id) == 10000

    def test_special_characters_in_strings(self):
        """Test handling of special characters"""
        event = EventCreate(
            household_id="h001",
            timestamp="2025-01-15T10:00:00",
            sensor_id="sensor!@#$%^&*()",
            sensor_type="motion",
            location="kitchen/living-room",
            value="True",
            resident="test"
        )

        assert "!" in event.sensor_id
        assert "/" in event.location

    def test_unicode_characters(self):
        """Test handling of unicode characters"""
        event = EventCreate(
            household_id="家庭001",
            timestamp="2025-01-15T10:00:00",
            sensor_id="センサー",
            sensor_type="motion",
            location="キッチン",
            value="True",
            resident="祖母"
        )

        assert event.household_id == "家庭001"
        assert event.location == "キッチン"
