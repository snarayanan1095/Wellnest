"""
Tests for Event Ingestion Service
Tests event ingestion API endpoint, validation, and database integration
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from app.api.event_ingestion_service import ingest_event
from app.schema.event import EventCreate


class TestEventIngestion:
    """Test event ingestion service"""

    @pytest.mark.asyncio
    async def test_ingest_event_success(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test successful event ingestion"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**sample_event_create)
                    response = await ingest_event(event_create)

                    assert response.status == "success"
                    assert "event_id" in response.model_dump()
                    assert response.event_id is not None

                    # Verify MongoDB write was called
                    mock_mongodb.write.assert_called_once()
                    # Verify Kafka publish was called
                    mock_kafka.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_event_generates_unique_id(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test that each event gets a unique ID"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**sample_event_create)
                    response = await ingest_event(event_create)

                    # Check that event_id was generated
                    assert response.event_id is not None
                    assert len(response.event_id) == 16  # Hash is truncated to 16 chars

    @pytest.mark.asyncio
    async def test_ingest_event_mongodb_failure(self, sample_event_create, mock_mongodb):
        """Test handling of MongoDB failure"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            mock_mongodb.write = AsyncMock(side_effect=Exception("MongoDB error"))

            with pytest.raises(HTTPException) as exc_info:
                event_create = EventCreate(**sample_event_create)
                await ingest_event(event_create)

            assert exc_info.value.status_code == 500
            assert "Failed to ingest event" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_ingest_event_kafka_failure_continues(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test that Kafka failure doesn't prevent event ingestion"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")
                    mock_kafka.publish_event = MagicMock(side_effect=Exception("Kafka down"))

                    event_create = EventCreate(**sample_event_create)
                    # Should not raise exception even though Kafka fails
                    response = await ingest_event(event_create)

                    assert response.status == "success"
                    # MongoDB write should have succeeded
                    mock_mongodb.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_event_anomaly_detector_failure_continues(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test that anomaly detector failure doesn't prevent ingestion"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock(side_effect=Exception("Detector error"))
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**sample_event_create)
                    # Should not raise exception
                    response = await ingest_event(event_create)

                    assert response.status == "success"

    @pytest.mark.asyncio
    async def test_ingest_event_updates_anomaly_detector(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test that anomaly detector is updated on event ingestion"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**sample_event_create)
                    await ingest_event(event_create)

                    # Verify detector was called
                    mock_detector.update_state_on_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_event_kafka_partitioning(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test that Kafka uses household_id as partition key"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**sample_event_create)
                    await ingest_event(event_create)

                    # Verify Kafka was called with household_id as key
                    mock_kafka.publish_event.assert_called_once()
                    call_kwargs = mock_kafka.publish_event.call_args[1]
                    assert call_kwargs["key"] == sample_event_create["household_id"]

    @pytest.mark.asyncio
    async def test_ingest_event_preserves_all_fields(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test that all event fields are preserved"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**sample_event_create)
                    await ingest_event(event_create)

                    # Check MongoDB write call
                    write_call_args = mock_mongodb.write.call_args[0]
                    event_dict = write_call_args[1]

                    # Verify all fields are present
                    assert event_dict["household_id"] == sample_event_create["household_id"]
                    assert event_dict["sensor_type"] == sample_event_create["sensor_type"]
                    assert event_dict["location"] == sample_event_create["location"]
                    assert event_dict["value"] == sample_event_create["value"]
                    assert event_dict["resident"] == sample_event_create["resident"]

    @pytest.mark.asyncio
    async def test_ingest_event_sets_mongodb_id(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test that event_id is set as MongoDB _id"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**sample_event_create)
                    await ingest_event(event_create)

                    # Check that _id was set
                    write_call_args = mock_mongodb.write.call_args[0]
                    event_dict = write_call_args[1]
                    assert "_id" in event_dict
                    assert event_dict["_id"] == event_dict["event_id"]

    @pytest.mark.asyncio
    async def test_ingest_event_response_format(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test response has correct format"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**sample_event_create)
                    response = await ingest_event(event_create)

                    assert response.status == "success"
                    assert "household" in response.message
                    assert "sensor" in response.message
                    assert response.event_id is not None
                    assert response.timestamp == sample_event_create["timestamp"]


class TestEventIngestionEdgeCases:
    """Test edge cases in event ingestion"""

    @pytest.mark.asyncio
    async def test_ingest_event_with_special_characters(self, mock_mongodb, mock_kafka):
        """Test ingesting events with special characters"""
        special_event = {
            "household_id": "h001",
            "timestamp": "2025-01-15T10:00:00",
            "sensor_id": "sensor!@#",
            "sensor_type": "motion",
            "location": "kitchen/dining",
            "value": "True&False",
            "resident": "test-user"
        }

        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**special_event)
                    response = await ingest_event(event_create)

                    assert response.status == "success"

    @pytest.mark.asyncio
    async def test_ingest_duplicate_event_same_id(self, sample_event_create, mock_mongodb, mock_kafka):
        """Test ingesting same event twice generates same ID"""
        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient', mock_kafka):
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_detector.update_state_on_event = AsyncMock()
                    mock_mongodb.write = AsyncMock(return_value="event_id_123")

                    event_create = EventCreate(**sample_event_create)
                    response1 = await ingest_event(event_create)

                    # Ingest same event again
                    event_create2 = EventCreate(**sample_event_create)
                    response2 = await ingest_event(event_create2)

                    # Should generate same event_id (deterministic hash)
                    assert response1.event_id == response2.event_id
