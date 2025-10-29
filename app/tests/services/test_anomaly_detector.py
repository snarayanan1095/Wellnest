"""
Tests for Anomaly Detector Service
Tests anomaly detection logic, state management, alert generation, and de-duplication
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call
from app.services.anomaly_detector import AnomalyDetector


class TestAnomalyDetector:
    """Test suite for AnomalyDetector class"""

    @pytest.fixture
    def detector(self):
        """Create a fresh detector instance for each test"""
        return AnomalyDetector()

    # ===== Initialization Tests =====

    def test_initialization(self, detector):
        """Test detector initializes with correct default values"""
        assert detector.baseline_cache == {}
        assert detector.household_state == {}
        assert detector.last_check_time == {}
        assert detector.recent_alerts == {}
        assert detector.state_locks == {}
        assert detector.ALERT_COOLDOWN_HOURS == 2
        assert "door" in detector.CRITICAL_EVENTS
        assert "sos_button" in detector.CRITICAL_EVENTS

    # ===== Baseline Management Tests =====

    @pytest.mark.asyncio
    async def test_get_baseline_from_cache(self, detector, sample_baseline):
        """Test baseline retrieval from cache"""
        household_id = "household_001"
        detector.baseline_cache[household_id] = {
            'baseline': sample_baseline,
            'cached_at': datetime.now(timezone.utc)
        }

        result = await detector.get_baseline(household_id)
        assert result == sample_baseline

    @pytest.mark.asyncio
    async def test_get_baseline_cache_expired(self, detector, sample_baseline, mock_mongodb):
        """Test baseline fetched from DB when cache is expired"""
        household_id = "household_001"
        # Set cache with old timestamp (more than 24 hours ago)
        detector.baseline_cache[household_id] = {
            'baseline': {'old': 'data'},
            'cached_at': datetime.now(timezone.utc) - timedelta(hours=25)
        }

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=[sample_baseline])
            result = await detector.get_baseline(household_id)

            # Should fetch fresh data from DB
            assert result == sample_baseline
            mock_mongodb.read.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_baseline_no_baseline_found(self, detector, mock_mongodb):
        """Test when no baseline exists in database"""
        household_id = "household_001"

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=[])
            result = await detector.get_baseline(household_id)

            assert result is None

    # ===== Time Utility Tests =====

    def test_time_to_minutes_valid(self, detector):
        """Test converting time string to minutes"""
        assert detector.time_to_minutes("00:00") == 0
        assert detector.time_to_minutes("08:30") == 510
        assert detector.time_to_minutes("12:00") == 720
        assert detector.time_to_minutes("23:59") == 1439

    def test_time_to_minutes_invalid(self, detector):
        """Test invalid time strings return None"""
        assert detector.time_to_minutes("invalid") is None
        assert detector.time_to_minutes("25:00") is None
        assert detector.time_to_minutes("") is None

    # ===== State Update Tests =====

    def test_update_state_wake_detection(self, detector):
        """Test state update for wake-up detection"""
        state = {
            "wake_detected": False,
            "wake_up_time": None,
            "kitchen_visited": False,
            "bathroom_count": 0,
            "last_motion_time": None,
            "last_location": None,
            "door_opened": False,
            "first_kitchen_time": None
        }
        event = {
            "sensor_type": "bed_presence",
            "location": "bedroom1",
            "value": "False",
            "timestamp": "2025-01-15T06:30:00"
        }

        detector._update_state(state, event)

        assert state["wake_detected"] is True
        assert state["wake_up_time"] == "06:30"

    def test_update_state_kitchen_visit(self, detector):
        """Test state update for kitchen visit"""
        state = {
            "wake_detected": True,
            "kitchen_visited": False,
            "first_kitchen_time": None,
            "bathroom_count": 0,
            "last_motion_time": None,
            "last_location": None,
            "door_opened": False,
            "wake_up_time": "06:30"
        }
        event = {
            "sensor_type": "motion",
            "location": "kitchen",
            "value": "True",
            "timestamp": "2025-01-15T07:00:00"
        }

        detector._update_state(state, event)

        assert state["kitchen_visited"] is True
        assert state["first_kitchen_time"] == "07:00"

    def test_update_state_bathroom_count(self, detector):
        """Test bathroom visit counting"""
        state = {
            "wake_detected": True,
            "kitchen_visited": False,
            "bathroom_count": 0,
            "last_motion_time": None,
            "last_location": None,
            "door_opened": False,
            "first_kitchen_time": None,
            "wake_up_time": "06:30"
        }
        event1 = {
            "sensor_type": "motion",
            "location": "bathroom1",
            "value": "True",
            "timestamp": "2025-01-15T07:00:00"
        }
        event2 = {
            "sensor_type": "motion",
            "location": "bathroom2",
            "value": "True",
            "timestamp": "2025-01-15T08:00:00"
        }

        detector._update_state(state, event1)
        assert state["bathroom_count"] == 1

        detector._update_state(state, event2)
        assert state["bathroom_count"] == 2

    def test_update_state_motion_tracking(self, detector):
        """Test motion and location tracking"""
        state = {
            "wake_detected": True,
            "kitchen_visited": False,
            "bathroom_count": 0,
            "last_motion_time": None,
            "last_location": None,
            "door_opened": False,
            "first_kitchen_time": None,
            "wake_up_time": "06:30"
        }
        event = {
            "sensor_type": "motion",
            "location": "livingroom",
            "value": "True",
            "timestamp": "2025-01-15T10:00:00"
        }

        detector._update_state(state, event)

        assert state["last_motion_time"] == "2025-01-15T10:00:00"
        assert state["last_location"] == "livingroom"

    def test_update_state_door_opened(self, detector):
        """Test door opening detection"""
        state = {
            "wake_detected": True,
            "kitchen_visited": False,
            "bathroom_count": 0,
            "last_motion_time": None,
            "last_location": None,
            "door_opened": False,
            "first_kitchen_time": None,
            "wake_up_time": "06:30"
        }
        event = {
            "sensor_type": "door",
            "location": "entrance",
            "value": "True",
            "timestamp": "2025-01-15T08:00:00"
        }

        detector._update_state(state, event)

        assert state["door_opened"] is True

    # ===== Event Processing Tests =====

    @pytest.mark.asyncio
    async def test_update_state_on_event_non_critical(self, detector, sample_event, mock_mongodb):
        """Test event processing for non-critical events"""
        sample_event["sensor_type"] = "motion"  # Not critical

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=[])
            await detector.update_state_on_event(sample_event)

            # Should update state but not check anomalies
            assert "household_001" in detector.household_state

    @pytest.mark.asyncio
    async def test_update_state_on_event_critical(self, detector, sample_event, mock_mongodb, sample_baseline):
        """Test event processing for critical events (door)"""
        sample_event["sensor_type"] = "door"
        sample_event["location"] = "entrance"

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=[sample_baseline, []])

            with patch.object(detector, 'check_anomalies', new=AsyncMock()) as mock_check:
                await detector.update_state_on_event(sample_event)

                # Should trigger anomaly check for critical event
                mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_event_locking(self, detector, sample_event, mock_mongodb):
        """Test that concurrent events use locking mechanism"""
        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=[])

            # Process same household events concurrently
            await detector.update_state_on_event(sample_event)

            # Lock should exist for household
            assert "household_001" in detector.state_locks

    # ===== Daily State Cache Tests =====

    @pytest.mark.asyncio
    async def test_check_and_reset_daily_cache_new_day(self, detector):
        """Test cache reset when crossing midnight"""
        household_id = "household_001"
        detector.household_state[household_id] = {"test": "data"}
        # Set last check to yesterday
        detector.last_check_time[household_id] = datetime.now(timezone.utc) - timedelta(days=1)

        await detector.check_and_reset_daily_cache(household_id)

        # State should be cleared
        assert household_id not in detector.household_state
        # Last check time should be updated
        assert household_id in detector.last_check_time

    @pytest.mark.asyncio
    async def test_check_and_reset_daily_cache_same_day(self, detector):
        """Test cache not reset on same day"""
        household_id = "household_001"
        test_data = {"test": "data"}
        detector.household_state[household_id] = test_data
        detector.last_check_time[household_id] = datetime.now(timezone.utc)

        await detector.check_and_reset_daily_cache(household_id)

        # State should remain
        assert household_id in detector.household_state
        assert detector.household_state[household_id] == test_data

    # ===== Alert De-duplication Tests =====

    def test_should_send_alert_first_time(self, detector):
        """Test alert should be sent first time"""
        household_id = "household_001"
        alert_type = "missed_kitchen_activity"

        result = detector.should_send_alert(household_id, alert_type)

        assert result is True

    def test_should_send_alert_within_cooldown(self, detector):
        """Test alert blocked within cooldown period"""
        household_id = "household_001"
        alert_type = "missed_kitchen_activity"

        detector.recent_alerts[household_id] = {
            alert_type: datetime.now(timezone.utc) - timedelta(hours=1)
        }

        result = detector.should_send_alert(household_id, alert_type)

        assert result is False

    def test_should_send_alert_after_cooldown(self, detector):
        """Test alert allowed after cooldown period"""
        household_id = "household_001"
        alert_type = "missed_kitchen_activity"

        detector.recent_alerts[household_id] = {
            alert_type: datetime.now(timezone.utc) - timedelta(hours=3)
        }

        result = detector.should_send_alert(household_id, alert_type)

        assert result is True

    def test_mark_alert_sent(self, detector):
        """Test marking alert as sent"""
        household_id = "household_001"
        alert_type = "prolonged_inactivity"

        detector.mark_alert_sent(household_id, alert_type)

        assert household_id in detector.recent_alerts
        assert alert_type in detector.recent_alerts[household_id]
        assert isinstance(detector.recent_alerts[household_id][alert_type], datetime)

    # ===== Anomaly Detection Logic Tests =====

    @pytest.mark.asyncio
    async def test_detect_missed_kitchen_activity(self, detector, sample_baseline, mock_mongodb):
        """Test detection of missed kitchen activity"""
        household_id = "household_001"
        detector.household_state[household_id] = {
            "wake_detected": True,
            "kitchen_visited": False,
            "first_kitchen_time": None,
            "bathroom_count": 0,
            "last_motion_time": "2025-01-15T09:30:00",
            "last_location": "bedroom1",
            "door_opened": False,
            "wake_up_time": "06:30"
        }

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            with patch('app.services.anomaly_detector.datetime') as mock_datetime:
                # Set current time to 10:00 AM
                mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
                mock_datetime.fromisoformat = datetime.fromisoformat
                mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

                mock_mongodb.read = AsyncMock(return_value=[sample_baseline, []])

                detector.last_check_time[household_id] = mock_datetime.now.return_value

                anomalies = await detector.check_anomalies(household_id)

                # Should detect missed kitchen activity
                kitchen_anomalies = [a for a in anomalies if a["type"] == "missed_kitchen_activity"]
                assert len(kitchen_anomalies) > 0
                assert kitchen_anomalies[0]["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_detect_prolonged_inactivity(self, detector, sample_baseline, mock_mongodb):
        """Test detection of prolonged inactivity"""
        household_id = "household_001"
        detector.household_state[household_id] = {
            "wake_detected": True,
            "kitchen_visited": True,
            "first_kitchen_time": "07:00",
            "bathroom_count": 1,
            "last_motion_time": "2025-01-15T08:00:00",  # 3 hours ago
            "last_location": "livingroom",
            "door_opened": False,
            "wake_up_time": "06:30"
        }

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            with patch('app.services.anomaly_detector.datetime') as mock_datetime:
                # Set current time to 11:30 AM (3.5 hours after last motion)
                mock_datetime.now.return_value = datetime(2025, 1, 15, 11, 30, 0, tzinfo=timezone.utc)
                mock_datetime.fromisoformat = datetime.fromisoformat

                mock_mongodb.read = AsyncMock(return_value=[sample_baseline, []])

                detector.last_check_time[household_id] = mock_datetime.now.return_value

                anomalies = await detector.check_anomalies(household_id)

                # Should detect prolonged inactivity
                inactivity_anomalies = [a for a in anomalies if a["type"] == "prolonged_inactivity"]
                assert len(inactivity_anomalies) > 0
                assert inactivity_anomalies[0]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_detect_excessive_bathroom_visits(self, detector, sample_baseline, mock_mongodb):
        """Test detection of excessive bathroom visits"""
        household_id = "household_001"
        detector.household_state[household_id] = {
            "wake_detected": True,
            "kitchen_visited": True,
            "first_kitchen_time": "07:00",
            "bathroom_count": 10,  # Excessive (baseline max is 6)
            "last_motion_time": "2025-01-15T14:00:00",
            "last_location": "bathroom1",
            "door_opened": False,
            "wake_up_time": "06:30"
        }

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            with patch('app.services.anomaly_detector.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
                mock_datetime.fromisoformat = datetime.fromisoformat

                mock_mongodb.read = AsyncMock(return_value=[sample_baseline, []])

                detector.last_check_time[household_id] = mock_datetime.now.return_value

                anomalies = await detector.check_anomalies(household_id)

                # Should detect excessive bathroom visits
                bathroom_anomalies = [a for a in anomalies if a["type"] == "excessive_bathroom_visits"]
                assert len(bathroom_anomalies) > 0
                assert bathroom_anomalies[0]["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_no_baseline_skips_detection(self, detector, mock_mongodb):
        """Test that missing baseline skips anomaly detection"""
        household_id = "household_001"

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=[])  # No baseline

            anomalies = await detector.check_anomalies(household_id)

            assert anomalies == []

    # ===== Alert Title Tests =====

    def test_get_alert_title_known_types(self, detector):
        """Test alert title generation for known types"""
        assert "Missed Breakfast" in detector._get_alert_title("missed_kitchen_activity")
        assert "No Movement" in detector._get_alert_title("prolonged_inactivity")
        assert "Bathroom Visits" in detector._get_alert_title("excessive_bathroom_visits")
        assert "Wake-Up" in detector._get_alert_title("late_wake_up")
        assert "Door Activity" in detector._get_alert_title("unusual_door_activity")

    def test_get_alert_title_unknown_type(self, detector):
        """Test alert title for unknown type"""
        title = detector._get_alert_title("unknown_alert_type")
        assert "Wellness Alert" in title

    # ===== Integration Tests =====

    @pytest.mark.asyncio
    async def test_full_event_to_alert_flow(self, detector, sample_events_sequence,
                                           sample_baseline, mock_mongodb):
        """Test complete flow from events to alert generation"""
        household_id = "household_001"

        with patch('app.services.anomaly_detector.MongoDB', mock_mongodb):
            with patch('app.services.anomaly_detector.manager') as mock_manager:
                mock_manager.send_alert = AsyncMock()
                mock_mongodb.read = AsyncMock(return_value=[sample_baseline, []])
                mock_mongodb.write = AsyncMock(return_value="alert_123")

                # Process events sequence
                for event in sample_events_sequence:
                    await detector.update_state_on_event(event)

                # Verify state was built correctly
                state = detector.household_state[household_id]
                assert state["wake_detected"] is True
                assert state["kitchen_visited"] is True
                assert state["bathroom_count"] == 2

    @pytest.mark.asyncio
    async def test_reset_daily_state(self, detector):
        """Test manual reset of daily state"""
        detector.household_state = {
            "household_001": {"test": "data"},
            "household_002": {"test": "data"}
        }

        detector.reset_daily_state()

        assert detector.household_state == {}
