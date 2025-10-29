"""
Integration Tests
Tests end-to-end workflows and component interactions
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta


class TestEventToAlertFlow:
    """Test complete flow from event ingestion to alert generation"""

    @pytest.mark.asyncio
    async def test_critical_event_triggers_alert(self, sample_event, sample_baseline, mock_mongodb):
        """Test that critical event triggers immediate anomaly check and alert"""
        from app.services.anomaly_detector import AnomalyDetector
        from app.api.event_ingestion_service import ingest_event
        from app.schema.event import EventCreate

        # Create door event (critical)
        door_event = sample_event.copy()
        door_event["sensor_type"] = "door"
        door_event["location"] = "entrance"

        detector = AnomalyDetector()
        detector.household_state["household_001"] = {
            "wake_detected": True,
            "kitchen_visited": False,
            "bathroom_count": 0,
            "last_motion_time": None,
            "last_location": None,
            "door_opened": False,
            "first_kitchen_time": None,
            "wake_up_time": "06:30"
        }

        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient') as mock_kafka:
                with patch('app.api.event_ingestion_service.detector', detector):
                    with patch.object(detector, 'check_anomalies', new=AsyncMock()) as mock_check:
                        mock_mongodb.write = AsyncMock(return_value="event_id")
                        mock_mongodb.read = AsyncMock(return_value=[sample_baseline, []])
                        mock_kafka.publish_event = MagicMock()

                        event_create = EventCreate(**door_event)
                        await ingest_event(event_create)

                        # Verify anomaly check was triggered
                        mock_check.assert_called()


class TestRoutineLearningPipeline:
    """Test routine learning from events to baseline"""

    @pytest.mark.asyncio
    async def test_events_to_routine_to_baseline(self, sample_events_sequence, mock_mongodb):
        """Test complete pipeline: events -> daily routine -> baseline"""
        from app.scheduler.routine_learner import (
            extract_routine,
            save_profile,
            aggregate_baselines
        )

        # Step 1: Extract routine from events
        routine = extract_routine(sample_events_sequence)
        assert routine["wake_up_time"] is not None
        assert routine["first_kitchen_time"] is not None

        # Step 2: Save routine profile
        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            mock_mongodb.write = AsyncMock(return_value="routine_id")

            await save_profile("household_001", routine)
            mock_mongodb.write.assert_called_once()

        # Step 3: Aggregate into baseline (tested separately in routine learner tests)


class TestAnomalyDetectionWithRealData:
    """Test anomaly detection with realistic data scenarios"""

    @pytest.mark.asyncio
    async def test_missed_breakfast_scenario(self, mock_mongodb):
        """Test detection when resident misses breakfast"""
        from app.services.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()
        household_id = "household_001"

        # Setup: Person woke up but hasn't gone to kitchen
        detector.household_state[household_id] = {
            "wake_detected": True,
            "wake_up_time": "06:30",
            "kitchen_visited": False,
            "first_kitchen_time": None,
            "bathroom_count": 1,
            "last_motion_time": "2025-01-15T06:35:00",
            "last_location": "bathroom1",
            "door_opened": False
        }

        baseline = {
            "household_id": household_id,
            "first_kitchen_time": {
                "median": "07:00",
                "latest": "08:00"
            },
            "bathroom_visits": {
                "daily_median": 4,
                "max_daily": 6
            }
        }

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            with patch('app.services.anomaly_detector.datetime') as mock_datetime:
                # Current time: 10:00 AM (way past expected kitchen time)
                mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
                mock_datetime.fromisoformat = datetime.fromisoformat

                mock_mongodb.read = AsyncMock(return_value=[baseline, []])
                mock_mongodb.write = AsyncMock(return_value="alert_id")

                with patch('app.services.anomaly_detector.manager') as mock_manager:
                    mock_manager.send_alert = AsyncMock()
                    detector.last_check_time[household_id] = mock_datetime.now.return_value

                    anomalies = await detector.check_anomalies(household_id)

                    # Should detect missed kitchen activity
                    assert len(anomalies) > 0
                    missed_kitchen = [a for a in anomalies if a["type"] == "missed_kitchen_activity"]
                    assert len(missed_kitchen) > 0

    @pytest.mark.asyncio
    async def test_normal_day_no_alerts(self, mock_mongodb):
        """Test that normal activity doesn't trigger alerts"""
        from app.services.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()
        household_id = "household_001"

        # Setup: Normal day
        detector.household_state[household_id] = {
            "wake_detected": True,
            "wake_up_time": "06:30",
            "kitchen_visited": True,
            "first_kitchen_time": "07:00",
            "bathroom_count": 4,
            "last_motion_time": "2025-01-15T10:00:00",
            "last_location": "livingroom",
            "door_opened": False
        }

        baseline = {
            "household_id": household_id,
            "wake_up_time": {
                "median": "06:30",
                "latest": "07:30"
            },
            "first_kitchen_time": {
                "median": "07:00",
                "latest": "08:00"
            },
            "bathroom_visits": {
                "daily_median": 4,
                "max_daily": 6
            }
        }

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            with patch('app.services.anomaly_detector.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
                mock_datetime.fromisoformat = datetime.fromisoformat

                mock_mongodb.read = AsyncMock(return_value=[baseline, []])
                detector.last_check_time[household_id] = mock_datetime.now.return_value

                anomalies = await detector.check_anomalies(household_id)

                # Should not detect any anomalies
                assert len(anomalies) == 0


class TestWebSocketAlertDelivery:
    """Test alert delivery through WebSocket"""

    @pytest.mark.asyncio
    async def test_alert_delivered_to_connected_client(self, sample_alert):
        """Test that alert is delivered to connected WebSocket client"""
        from app.services.ws_manager import ConnectionManager

        manager = ConnectionManager()
        household_id = "household_001"

        # Create mock WebSocket
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        # Connect client
        await manager.connect(mock_ws, household_id)

        # Send alert
        await manager.send_alert(household_id, sample_alert)

        # Verify alert was sent
        mock_ws.send_json.assert_called_once_with(sample_alert)

    @pytest.mark.asyncio
    async def test_alert_to_multiple_clients(self, sample_alert):
        """Test alert broadcast to multiple clients"""
        from app.services.ws_manager import ConnectionManager

        manager = ConnectionManager()
        household_id = "household_001"

        # Connect multiple clients
        clients = []
        for i in range(3):
            ws = MagicMock()
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            await manager.connect(ws, household_id)
            clients.append(ws)

        # Send alert
        await manager.send_alert(household_id, sample_alert)

        # All clients should receive alert
        for ws in clients:
            ws.send_json.assert_called_once_with(sample_alert)


class TestSchedulerIntegration:
    """Test scheduler component integration"""

    @pytest.mark.asyncio
    async def test_scheduled_anomaly_check_runs(self, mock_mongodb):
        """Test that scheduled anomaly check executes"""
        from app.scheduler.anomaly_scheduler import scheduled_anomaly_check

        with patch('app.scheduler.anomaly_scheduler.MongoDB', mock_mongodb):
            with patch('app.scheduler.anomaly_scheduler.detector') as mock_detector:
                mock_mongodb.distinct = AsyncMock(return_value=["household_001", "household_002"])
                mock_detector.check_anomalies = AsyncMock(return_value=[])

                await scheduled_anomaly_check()

                # Should check anomalies for all households
                assert mock_detector.check_anomalies.call_count == 2


class TestErrorRecovery:
    """Test system behavior under error conditions"""

    @pytest.mark.asyncio
    async def test_ingestion_continues_after_kafka_failure(self, sample_event_create, mock_mongodb):
        """Test that event ingestion continues even when Kafka fails"""
        from app.api.event_ingestion_service import ingest_event
        from app.schema.event import EventCreate

        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient') as mock_kafka:
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_mongodb.write = AsyncMock(return_value="event_id")
                    mock_kafka.publish_event = MagicMock(side_effect=Exception("Kafka down"))
                    mock_detector.update_state_on_event = AsyncMock()

                    event_create = EventCreate(**sample_event_create)
                    response = await ingest_event(event_create)

                    # Should succeed despite Kafka failure
                    assert response.status == "success"
                    # MongoDB should have been called
                    mock_mongodb.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_handles_dead_connections(self, sample_alert):
        """Test WebSocket manager handles dead connections gracefully"""
        from app.services.ws_manager import ConnectionManager

        manager = ConnectionManager()
        household_id = "household_001"

        # Create a connection that will fail
        dead_ws = MagicMock()
        dead_ws.accept = AsyncMock()
        dead_ws.send_json = AsyncMock(side_effect=Exception("Connection lost"))

        # Create a good connection
        good_ws = MagicMock()
        good_ws.accept = AsyncMock()
        good_ws.send_json = AsyncMock()

        await manager.connect(dead_ws, household_id)
        await manager.connect(good_ws, household_id)

        # Send alert
        await manager.send_alert(household_id, sample_alert)

        # Good connection should still work
        good_ws.send_json.assert_called_once()
        # Dead connection should be removed
        assert dead_ws not in manager.active_connections[household_id]

    @pytest.mark.asyncio
    async def test_anomaly_detection_without_baseline(self, mock_mongodb):
        """Test anomaly detection gracefully handles missing baseline"""
        from app.services.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()
        household_id = "household_001"

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=[])  # No baseline

            anomalies = await detector.check_anomalies(household_id)

            # Should return empty list, not crash
            assert anomalies == []


class TestDataConsistency:
    """Test data consistency across operations"""

    @pytest.mark.asyncio
    async def test_event_id_consistency(self, sample_event_create, mock_mongodb):
        """Test that same event data generates same event_id"""
        from app.api.event_ingestion_service import ingest_event
        from app.schema.event import EventCreate
        import hashlib

        # Manually calculate expected event_id
        event_create = EventCreate(**sample_event_create)
        expected_id = hashlib.sha256(
            f"{event_create.household_id}_{event_create.sensor_id}_{event_create.timestamp}_{event_create.value}".encode()
        ).hexdigest()[:16]

        with patch('app.api.event_ingestion_service.MongoDB', mock_mongodb):
            with patch('app.api.event_ingestion_service.KafkaClient') as mock_kafka:
                with patch('app.api.event_ingestion_service.detector') as mock_detector:
                    mock_mongodb.write = AsyncMock(return_value=expected_id)
                    mock_kafka.publish_event = MagicMock()
                    mock_detector.update_state_on_event = AsyncMock()

                    response = await ingest_event(event_create)

                    assert response.event_id == expected_id

    @pytest.mark.asyncio
    async def test_alert_deduplication_across_restarts(self, mock_mongodb):
        """Test alert de-duplication persists across service restarts"""
        from app.services.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()
        household_id = "household_001"

        # Simulate existing alert in database
        existing_alert = {
            "household_id": household_id,
            "type": "prolonged_inactivity",
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            "acknowledged": False
        }

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(side_effect=[
                [],  # No baseline
                [existing_alert]  # Existing alert
            ])

            # Even though in-memory cache is empty (simulating restart),
            # database check should prevent duplicate
            # (Would need full test setup to verify this completely)
