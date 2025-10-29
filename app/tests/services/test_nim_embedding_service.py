"""
Tests for NIM Embedding Service
Tests embedding generation for baseline routines using NVIDIA NIM API
"""
import pytest
import os
from unittest.mock import patch, Mock, MagicMock
from app.services.nim_embedding_service import NIMEmbeddingService


class TestNIMEmbeddingServiceInitialization:
    """Test NIM Embedding Service initialization"""

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key", "NIM_MODEL_NAME": "test-model"})
    @patch('app.services.nim_embedding_service.NVIDIAEmbeddings')
    def test_initialize_success(self, mock_embeddings):
        """Test successful initialization"""
        mock_client = Mock()
        mock_embeddings.return_value = mock_client

        NIMEmbeddingService.initialize()

        assert NIMEmbeddingService.client == mock_client
        assert NIMEmbeddingService._api_key == "test_key"
        assert NIMEmbeddingService._model_name == "test-model"

        # Verify NVIDIAEmbeddings was called with correct params
        mock_embeddings.assert_called_once_with(
            model="test-model",
            api_key="test_key",
            truncate="NONE"
        )

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"}, clear=True)
    @patch('app.services.nim_embedding_service.NVIDIAEmbeddings')
    def test_initialize_default_model(self, mock_embeddings):
        """Test initialization with default model name"""
        mock_client = Mock()
        mock_embeddings.return_value = mock_client

        NIMEmbeddingService.initialize()

        # Should use default model
        assert NIMEmbeddingService._model_name == "nvidia/nv-embedqa-e5-v5"
        mock_embeddings.assert_called_once_with(
            model="nvidia/nv-embedqa-e5-v5",
            api_key="test_key",
            truncate="NONE"
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_missing_api_key(self):
        """Test that missing API key raises error"""
        with pytest.raises(ValueError) as exc_info:
            NIMEmbeddingService.initialize()

        assert "NIM_API_KEY" in str(exc_info.value)

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_embedding_service.NVIDIAEmbeddings')
    def test_initialize_embedding_client_error(self, mock_embeddings):
        """Test handling of embedding client initialization error"""
        mock_embeddings.side_effect = Exception("Client initialization failed")

        with pytest.raises(Exception) as exc_info:
            NIMEmbeddingService.initialize()

        assert "Client initialization failed" in str(exc_info.value)


class TestNIMEmbeddingServiceEmbedQuery:
    """Test embedding generation for single queries"""

    def test_embed_query_without_initialization(self):
        """Test that calling embed_query without initialization raises error"""
        # Reset client
        NIMEmbeddingService.client = None

        with pytest.raises(RuntimeError) as exc_info:
            NIMEmbeddingService.embed_query("test text")

        assert "not initialized" in str(exc_info.value)

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    def test_embed_query_success(self):
        """Test successful query embedding"""
        # Mock client
        mock_client = Mock()
        mock_client.embed_query.return_value = [0.1, 0.2, 0.3, 0.4]
        NIMEmbeddingService.client = mock_client

        result = NIMEmbeddingService.embed_query("test text")

        mock_client.embed_query.assert_called_once_with("test text")
        assert result == [0.1, 0.2, 0.3, 0.4]
        assert isinstance(result, list)

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    def test_embed_query_empty_string(self):
        """Test embedding empty string"""
        mock_client = Mock()
        mock_client.embed_query.return_value = [0.0] * 1024
        NIMEmbeddingService.client = mock_client

        result = NIMEmbeddingService.embed_query("")

        mock_client.embed_query.assert_called_once_with("")
        assert len(result) == 1024

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    def test_embed_query_long_text(self):
        """Test embedding long text"""
        mock_client = Mock()
        mock_client.embed_query.return_value = [0.5] * 1024
        NIMEmbeddingService.client = mock_client

        long_text = "test " * 1000
        result = NIMEmbeddingService.embed_query(long_text)

        mock_client.embed_query.assert_called_once_with(long_text)
        assert isinstance(result, list)


class TestNIMEmbeddingServiceEmbedDocuments:
    """Test embedding generation for multiple documents"""

    def test_embed_documents_without_initialization(self):
        """Test that calling embed_documents without initialization raises error"""
        NIMEmbeddingService.client = None

        with pytest.raises(RuntimeError) as exc_info:
            NIMEmbeddingService.embed_documents(["text1", "text2"])

        assert "not initialized" in str(exc_info.value)

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    def test_embed_documents_success(self):
        """Test successful document embeddings"""
        mock_client = Mock()
        mock_client.embed_documents.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        NIMEmbeddingService.client = mock_client

        texts = ["text1", "text2"]
        result = NIMEmbeddingService.embed_documents(texts)

        mock_client.embed_documents.assert_called_once_with(texts)
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    def test_embed_documents_empty_list(self):
        """Test embedding empty list of documents"""
        mock_client = Mock()
        mock_client.embed_documents.return_value = []
        NIMEmbeddingService.client = mock_client

        result = NIMEmbeddingService.embed_documents([])

        mock_client.embed_documents.assert_called_once_with([])
        assert result == []

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    def test_embed_documents_single_document(self):
        """Test embedding single document in list"""
        mock_client = Mock()
        mock_client.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        NIMEmbeddingService.client = mock_client

        result = NIMEmbeddingService.embed_documents(["single text"])

        assert len(result) == 1


class TestFormatBaselineRoutine:
    """Test formatting baseline routine for embedding"""

    def test_format_complete_baseline(self):
        """Test formatting a complete baseline with all fields"""
        baseline = {
            "household_id": "household_001",
            "baseline_period": {
                "days": 7,
                "start_date": "2025-01-08",
                "end_date": "2025-01-15"
            },
            "wake_up_time": {
                "median": "06:30",
                "mean": "06:32",
                "std_dev_minutes": 15
            },
            "bed_time": {
                "median": "22:00",
                "mean": "22:10"
            },
            "first_kitchen_time": {
                "median": "07:00"
            },
            "bathroom_first_time": {
                "median": "06:35"
            },
            "bathroom_visits": {
                "daily_avg": 4.5,
                "daily_median": 4,
                "min_daily": 3,
                "max_daily": 6
            },
            "activity_duration": {
                "median_minutes": 900,
                "earliest_start": "06:30",
                "latest_end": "22:00"
            },
            "total_daily_events": {
                "avg": 127.5,
                "median": 125,
                "min": 100,
                "max": 150
            },
            "data_quality": {
                "days_with_complete_data": 7,
                "days_with_missing_wake": 0,
                "days_with_missing_kitchen": 0,
                "reliability_score": 1.0
            }
        }

        text = NIMEmbeddingService.format_baseline_routine_for_embedding(baseline)

        # Check all key information is included
        assert "household_001" in text
        assert "7 days" in text
        assert "2025-01-08" in text
        assert "2025-01-15" in text
        assert "06:30" in text
        assert "22:00" in text
        assert "07:00" in text
        assert "06:35" in text
        assert "4.5" in text
        assert "900" in text
        assert "127.5" in text
        assert "reliability: 1.0" in text

        # Check it's properly formatted
        assert text.endswith(".")
        assert ". " in text  # Should have sentence separators

    def test_format_minimal_baseline(self):
        """Test formatting baseline with minimal fields"""
        baseline = {
            "household_id": "household_002",
            "baseline_period": {
                "days": 3,
                "start_date": "2025-01-12",
                "end_date": "2025-01-15"
            }
        }

        text = NIMEmbeddingService.format_baseline_routine_for_embedding(baseline)

        assert "household_002" in text
        assert "3 days" in text
        assert text.endswith(".")

    def test_format_baseline_with_missing_nested_fields(self):
        """Test formatting baseline with some missing nested fields"""
        baseline = {
            "household_id": "household_003",
            "baseline_period": {
                "days": 5
            },
            "wake_up_time": {
                "median": "07:00"
            },
            "bathroom_visits": {
                "daily_avg": 3.5
            }
        }

        text = NIMEmbeddingService.format_baseline_routine_for_embedding(baseline)

        assert "household_003" in text
        assert "07:00" in text
        assert "3.5" in text
        # Missing fields should show as N/A
        assert "N/A" in text

    def test_format_baseline_empty_dict(self):
        """Test formatting empty baseline dictionary"""
        baseline = {}

        text = NIMEmbeddingService.format_baseline_routine_for_embedding(baseline)

        assert isinstance(text, str)
        assert "unknown" in text
        assert text.endswith(".")

    def test_format_baseline_safe_get_helper(self):
        """Test that safe_get handles missing keys gracefully"""
        baseline = {
            "wake_up_time": {
                "median": "06:30"
            }
        }

        text = NIMEmbeddingService.format_baseline_routine_for_embedding(baseline)

        # Should not crash and should handle missing fields
        assert isinstance(text, str)
        assert "06:30" in text

    def test_format_baseline_all_na_values(self):
        """Test baseline where all nested values are missing"""
        baseline = {
            "household_id": "household_004",
            "wake_up_time": {},
            "bed_time": {},
            "bathroom_visits": {},
            "data_quality": {}
        }

        text = NIMEmbeddingService.format_baseline_routine_for_embedding(baseline)

        assert "household_004" in text
        assert isinstance(text, str)

    def test_format_baseline_text_structure(self):
        """Test that formatted text has proper structure"""
        baseline = {
            "household_id": "household_005",
            "baseline_period": {"days": 7, "start_date": "2025-01-08", "end_date": "2025-01-15"},
            "wake_up_time": {"median": "06:30"},
            "bed_time": {"median": "22:00"}
        }

        text = NIMEmbeddingService.format_baseline_routine_for_embedding(baseline)

        # Should be sentences separated by periods
        sentences = text.split(". ")
        assert len(sentences) >= 2
        assert text.endswith(".")
        # First sentence should be about household and period
        assert "Household" in sentences[0]
        assert "baseline summary" in sentences[0]


class TestNIMEmbeddingServiceIntegration:
    """Integration tests for the embedding service"""

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_embedding_service.NVIDIAEmbeddings')
    def test_full_workflow_baseline_embedding(self, mock_embeddings):
        """Test complete workflow: format baseline and generate embedding"""
        # Setup mock
        mock_client = Mock()
        mock_client.embed_query.return_value = [0.1] * 1024
        mock_embeddings.return_value = mock_client

        # Initialize service
        NIMEmbeddingService.initialize()

        # Create baseline
        baseline = {
            "household_id": "household_001",
            "baseline_period": {"days": 7, "start_date": "2025-01-08", "end_date": "2025-01-15"},
            "wake_up_time": {"median": "06:30"},
            "bed_time": {"median": "22:00"}
        }

        # Format and embed
        text = NIMEmbeddingService.format_baseline_routine_for_embedding(baseline)
        embedding = NIMEmbeddingService.embed_query(text)

        # Verify
        assert isinstance(text, str)
        assert "household_001" in text
        assert isinstance(embedding, list)
        assert len(embedding) == 1024
        mock_client.embed_query.assert_called_once_with(text)
