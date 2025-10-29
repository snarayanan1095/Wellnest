"""
Tests for Routine Learner
Tests routine extraction, baseline aggregation, and scheduling
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.scheduler.routine_learner import (
    extract_routine,
    generate_summary,
    save_profile,
    get_yesterday_range,
    batch_routine_learner_daily,
    aggregate_baselines
)


class TestRoutineExtraction:
    """Test routine extraction from events"""

    def test_extract_routine_wake_up(self, sample_events_sequence):
        """Test wake-up time extraction"""
        routine = extract_routine(sample_events_sequence)

        assert routine["wake_up_time"] == "06:30"
        assert routine["wake_up_time"] is not None

    def test_extract_routine_kitchen_visit(self, sample_events_sequence):
        """Test first kitchen visit extraction"""
        routine = extract_routine(sample_events_sequence)

        assert routine["first_kitchen_time"] == "07:00"

    def test_extract_routine_bathroom_count(self, sample_events_sequence):
        """Test bathroom visit counting"""
        routine = extract_routine(sample_events_sequence)

        assert routine["total_bathroom_events"] == 2
        assert routine["bathroom_first_time"] == "06:35"

    def test_extract_routine_bed_time(self, sample_events_sequence):
        """Test bed time extraction"""
        routine = extract_routine(sample_events_sequence)

        assert routine["bed_time"] == "22:00"

    def test_extract_routine_activity_window(self, sample_events_sequence):
        """Test activity start and end times"""
        routine = extract_routine(sample_events_sequence)

        assert routine["activity_start"] == "06:30"
        assert routine["activity_end"] == "22:00"

    def test_extract_routine_total_events(self, sample_events_sequence):
        """Test total event counting"""
        routine = extract_routine(sample_events_sequence)

        assert routine["total_events"] == len(sample_events_sequence)

    def test_extract_routine_empty_events(self):
        """Test extraction with no events"""
        routine = extract_routine([])

        assert routine["wake_up_time"] is None
        assert routine["bed_time"] is None
        assert routine["first_kitchen_time"] is None
        assert routine["total_bathroom_events"] == 0
        assert routine["total_events"] == 0

    def test_extract_routine_unsorted_events(self):
        """Test extraction with unsorted events"""
        events = [
            {
                "timestamp": "2025-01-15T22:00:00",
                "sensor_type": "bed_presence",
                "location": "bedroom1",
                "value": "True"
            },
            {
                "timestamp": "2025-01-15T06:30:00",
                "sensor_type": "bed_presence",
                "location": "bedroom1",
                "value": "False"
            }
        ]

        routine = extract_routine(events)

        # Should handle sorting internally
        assert routine["wake_up_time"] == "06:30"
        assert routine["bed_time"] == "22:00"

    def test_extract_routine_fallback_to_bedroom_motion(self):
        """Test fallback to bedroom motion when bed sensor missing"""
        events = [
            {
                "timestamp": "2025-01-15T06:45:00",
                "sensor_type": "motion",
                "location": "bedroom1",
                "value": "True"
            },
            {
                "timestamp": "2025-01-15T22:15:00",
                "sensor_type": "motion",
                "location": "bedroom2",
                "value": "True"
            }
        ]

        routine = extract_routine(events)

        # Should use bedroom motion as fallback
        assert routine["wake_up_time"] == "06:45"
        assert routine["bed_time"] == "22:15"


class TestSummaryGeneration:
    """Test summary text generation"""

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_summary_complete_data_no_llm(self, daily_routine_sample):
        """Test summary with complete routine data (template fallback)"""
        summary = generate_summary(daily_routine_sample)

        assert "Woke up at 06:30" in summary
        assert "kitchen activity at 07:00" in summary
        assert "4 bathroom visits" in summary
        assert "went to bed at 22:00" in summary
        assert "45 sensor events" in summary

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_summary_partial_data(self):
        """Test summary with partial routine data"""
        partial_routine = {
            "wake_up_time": "07:00",
            "first_kitchen_time": "07:30",
            "total_events": 20
        }

        summary = generate_summary(partial_routine)

        assert "Woke up at 07:00" in summary
        assert "kitchen activity at 07:30" in summary
        assert "20 sensor events" in summary

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_summary_no_data(self):
        """Test summary with no significant data"""
        empty_routine = {
            "total_events": 0
        }

        summary = generate_summary(empty_routine)

        assert "No significant activity detected" in summary

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_summary_activity_fallback(self):
        """Test summary uses activity_start when wake_up_time missing"""
        routine = {
            "activity_start": "08:00",
            "activity_end": "20:00",
            "total_events": 15
        }

        summary = generate_summary(routine)

        assert "First activity at 08:00" in summary
        assert "last activity at 20:00" in summary

    @patch.dict('os.environ', {"NIM_API_KEY": "test_key"})
    @patch('app.scheduler.routine_learner.NIMLLMService.get_llama3_summary')
    def test_generate_summary_with_llm_success(self, mock_llm_service, daily_routine_sample):
        """Test that generate_summary calls LLM service when API key is available"""
        mock_llm_service.return_value = "The household maintained a regular morning routine starting at 6:30 AM. Evening activities concluded normally with bedtime at 10:00 PM."

        summary = generate_summary(daily_routine_sample)

        # Verify LLM service was called
        mock_llm_service.assert_called_once_with(daily_routine_sample)

        # Verify we got the LLM summary
        assert summary == "The household maintained a regular morning routine starting at 6:30 AM. Evening activities concluded normally with bedtime at 10:00 PM."
        assert "Woke up at" not in summary  # Should not be template-based

    @patch.dict('os.environ', {"NIM_API_KEY": "test_key"})
    @patch('app.scheduler.routine_learner.NIMLLMService.get_llama3_summary')
    def test_generate_summary_llm_fallback_on_error(self, mock_llm_service, daily_routine_sample):
        """Test that generate_summary falls back to template when LLM fails"""
        mock_llm_service.side_effect = Exception("API Error")

        summary = generate_summary(daily_routine_sample)

        # Verify LLM service was attempted
        mock_llm_service.assert_called_once_with(daily_routine_sample)

        # Verify we got the template fallback
        assert "Woke up at 06:30" in summary
        assert "kitchen activity at 07:00" in summary

    @patch.dict('os.environ', {"NIM_API_KEY": "test_key"})
    @patch('app.scheduler.routine_learner.NIMLLMService.get_llama3_summary')
    def test_generate_summary_llm_with_api_key_error(self, mock_llm_service):
        """Test fallback when NIM_API_KEY is invalid"""
        mock_llm_service.side_effect = KeyError("NIM_API_KEY not found")

        routine = {
            "wake_up_time": "07:00",
            "bed_time": "22:00",
            "total_events": 50
        }

        summary = generate_summary(routine)

        # Should fallback to template
        assert "Woke up at 07:00" in summary
        assert "went to bed at 22:00" in summary

    @patch.dict('os.environ', {"NIM_API_KEY": "test_key"})
    @patch('app.scheduler.routine_learner.NIMLLMService.get_llama3_summary')
    def test_generate_summary_llm_returns_empty_string(self, mock_llm_service):
        """Test fallback when LLM returns empty string"""
        mock_llm_service.return_value = ""

        routine = {
            "wake_up_time": "07:00",
            "total_events": 50
        }

        summary = generate_summary(routine)

        # Empty string is valid, but should be returned
        assert summary == ""


class TestProfileSaving:
    """Test saving routine profiles"""

    @pytest.mark.asyncio
    async def test_save_profile_with_summary(self, mock_mongodb):
        """Test saving profile with provided summary"""
        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            household_id = "household_001"
            profile_dict = {
                "wake_up_time": "06:30",
                "bed_time": "22:00"
            }
            summary = "Test summary"

            await save_profile(household_id, profile_dict, summary)

            mock_mongodb.write.assert_called_once()
            call_args = mock_mongodb.write.call_args[0]
            assert call_args[0] == "daily_routines"

            saved_doc = call_args[1]
            assert saved_doc["household_id"] == household_id
            assert saved_doc["summary_text"] == summary
            assert "_id" in saved_doc
            assert "date" in saved_doc

    @pytest.mark.asyncio
    async def test_save_profile_generates_summary(self, mock_mongodb):
        """Test profile saves with auto-generated summary"""
        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            household_id = "household_001"
            profile_dict = {
                "wake_up_time": "06:30",
                "bed_time": "22:00",
                "total_events": 50
            }

            await save_profile(household_id, profile_dict)

            mock_mongodb.write.assert_called_once()
            saved_doc = mock_mongodb.write.call_args[0][1]
            assert "summary_text" in saved_doc
            assert len(saved_doc["summary_text"]) > 0


class TestBatchRoutineLearner:
    """Test batch routine learning"""

    @pytest.mark.asyncio
    async def test_batch_learner_no_events(self, mock_mongodb):
        """Test batch learner with no events"""
        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=[])

            result = await batch_routine_learner_daily()

            assert result["status"] == "no_data"
            assert result["events_found"] == 0
            assert result["households_processed"] == 0

    @pytest.mark.asyncio
    async def test_batch_learner_single_household(self, mock_mongodb, sample_events_sequence):
        """Test batch learner with single household"""
        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=sample_events_sequence)
            mock_mongodb.write = AsyncMock(return_value="profile_id")

            result = await batch_routine_learner_daily()

            assert result["status"] == "success"
            assert result["households_processed"] == 1
            assert result["events_found"] == len(sample_events_sequence)
            # Should have written one profile
            mock_mongodb.write.assert_called()

    @pytest.mark.asyncio
    async def test_batch_learner_multiple_households(self, mock_mongodb):
        """Test batch learner with multiple households"""
        events_h1 = [
            {"household_id": "household_001", "timestamp": "2025-01-15T08:00:00",
             "sensor_type": "motion", "location": "kitchen", "value": "True"}
        ]
        events_h2 = [
            {"household_id": "household_002", "timestamp": "2025-01-15T09:00:00",
             "sensor_type": "motion", "location": "bedroom", "value": "True"}
        ]

        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            mock_mongodb.read = AsyncMock(return_value=events_h1 + events_h2)
            mock_mongodb.write = AsyncMock(return_value="profile_id")

            result = await batch_routine_learner_daily()

            assert result["status"] == "success"
            assert result["households_processed"] == 2
            # Should have written two profiles
            assert mock_mongodb.write.call_count == 2

    def test_get_yesterday_range(self):
        """Test getting yesterday's date range"""
        start, end = get_yesterday_range()

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert start < end
        assert (end - start).days == 1
        # Start should be midnight yesterday
        assert start.hour == 0
        assert start.minute == 0
        # End should be midnight today
        assert end.hour == 0
        assert end.minute == 0


class TestBaselineAggregation:
    """Test baseline aggregation"""

    @pytest.mark.asyncio
    async def test_aggregate_baselines_single_household(self, mock_mongodb, multiple_daily_routines):
        """Test baseline aggregation for single household"""
        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            # Mock aggregate to return household IDs
            mock_mongodb.aggregate = AsyncMock(return_value=[{"_id": "household_001"}])
            # Mock read to return daily routines
            mock_mongodb.read = AsyncMock(return_value=multiple_daily_routines)
            mock_mongodb.write = AsyncMock(return_value="baseline_id")

            await aggregate_baselines(n_days=7)

            # Should write one baseline
            mock_mongodb.write.assert_called_once()
            baseline = mock_mongodb.write.call_args[0][1]

            assert baseline["household_id"] == "household_001"
            assert baseline["baseline_type"] == "rolling7"
            assert "wake_up_time" in baseline
            assert "bathroom_visits" in baseline
            assert "computed_at" in baseline

    @pytest.mark.asyncio
    async def test_aggregate_baselines_statistics(self, mock_mongodb, multiple_daily_routines):
        """Test that baseline contains statistical summaries"""
        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            mock_mongodb.aggregate = AsyncMock(return_value=[{"_id": "household_001"}])
            mock_mongodb.read = AsyncMock(return_value=multiple_daily_routines)
            mock_mongodb.write = AsyncMock(return_value="baseline_id")

            await aggregate_baselines(n_days=7)

            baseline = mock_mongodb.write.call_args[0][1]

            # Check wake time stats
            wake_stats = baseline["wake_up_time"]
            assert "median" in wake_stats
            assert "mean" in wake_stats
            assert "std_dev_minutes" in wake_stats
            assert "earliest" in wake_stats
            assert "latest" in wake_stats

            # Check bathroom stats
            bathroom_stats = baseline["bathroom_visits"]
            assert "daily_avg" in bathroom_stats
            assert "daily_median" in bathroom_stats
            assert "max_daily" in bathroom_stats

    @pytest.mark.asyncio
    async def test_aggregate_baselines_no_households(self, mock_mongodb):
        """Test baseline aggregation with no households"""
        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            mock_mongodb.aggregate = AsyncMock(return_value=[])

            await aggregate_baselines(n_days=7)

            # Should not write any baselines
            mock_mongodb.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_aggregate_baselines_data_quality(self, mock_mongodb, multiple_daily_routines):
        """Test that baseline includes data quality metrics"""
        with patch('app.scheduler.routine_learner.MongoDB', mock_mongodb):
            mock_mongodb.aggregate = AsyncMock(return_value=[{"_id": "household_001"}])
            mock_mongodb.read = AsyncMock(return_value=multiple_daily_routines)
            mock_mongodb.write = AsyncMock(return_value="baseline_id")

            await aggregate_baselines(n_days=7)

            baseline = mock_mongodb.write.call_args[0][1]

            assert "data_quality" in baseline
            quality = baseline["data_quality"]
            assert "days_with_complete_data" in quality
            assert "reliability_score" in quality
            assert quality["days_with_complete_data"] == len(multiple_daily_routines)


class TestScheduler:
    """Test scheduler functions"""

    def test_scheduler_initialization(self):
        """Test that scheduler is initialized"""
        from app.scheduler.routine_learner import scheduler
        assert scheduler is not None

    @patch('app.scheduler.routine_learner.scheduler')
    def test_start_scheduler(self, mock_scheduler):
        """Test starting the scheduler"""
        from app.scheduler.routine_learner import start_scheduler

        mock_scheduler.running = False
        mock_scheduler.add_job = MagicMock()
        mock_scheduler.start = MagicMock()

        start_scheduler()

        mock_scheduler.add_job.assert_called_once()
        mock_scheduler.start.assert_called_once()

    @patch('app.scheduler.routine_learner.scheduler')
    def test_start_scheduler_already_running(self, mock_scheduler):
        """Test starting scheduler when already running"""
        from app.scheduler.routine_learner import start_scheduler

        mock_scheduler.running = True

        start_scheduler()

        # Should not try to start again

    @patch('app.scheduler.routine_learner.scheduler')
    def test_shutdown_scheduler(self, mock_scheduler):
        """Test shutting down the scheduler"""
        from app.scheduler.routine_learner import shutdown_scheduler

        mock_scheduler.running = True
        mock_scheduler.shutdown = MagicMock()

        shutdown_scheduler()

        mock_scheduler.shutdown.assert_called_once_with(wait=True)
