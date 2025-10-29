"""
Tests for NIM LLM Service
Tests LLM integration for generating routine summaries using NVIDIA NIM API
"""
import pytest
import os
from unittest.mock import patch, Mock, MagicMock
import requests
from app.services.nim_llm_service import NIMLLMService


class TestNIMLLMService:
    """Test NIM LLM Service functionality"""

    def test_build_llama3_prompt_basic(self):
        """Test building a basic prompt from routine data"""
        routine = {
            "wake_up_time": "07:30",
            "bed_time": "22:00",
            "first_kitchen_time": "07:45",
            "total_bathroom_events": 4,
            "total_events": 100
        }

        prompt = NIMLLMService.build_llama3_prompt(routine)

        assert isinstance(prompt, str)
        assert "daily routine record" in prompt.lower()
        assert "summarize" in prompt.lower()
        assert str(routine) in prompt
        assert "Summary:" in prompt

    def test_build_llama3_prompt_empty_routine(self):
        """Test building prompt with empty routine"""
        routine = {}

        prompt = NIMLLMService.build_llama3_prompt(routine)

        assert isinstance(prompt, str)
        assert "{}" in prompt
        assert "Summary:" in prompt

    def test_build_llama3_prompt_contains_instructions(self):
        """Test that prompt contains proper instructions"""
        routine = {"wake_up_time": "08:00"}

        prompt = NIMLLMService.build_llama3_prompt(routine)

        # Check for key instruction elements
        assert "2 sentences" in prompt or "two sentences" in prompt
        assert "unusual" in prompt.lower()
        assert "reasons" in prompt.lower()

    @patch.dict(os.environ, {"NIM_API_KEY": "test_api_key_12345"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_get_llama3_summary_success(self, mock_post):
        """Test successful LLM API call"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "The household had a normal morning routine starting at 7:30 AM. Evening activities concluded with bedtime at 10:00 PM."
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        routine = {
            "wake_up_time": "07:30",
            "bed_time": "22:00",
            "total_events": 80
        }

        summary = NIMLLMService.get_llama3_summary(routine)

        # Verify API was called correctly
        assert mock_post.called
        call_args = mock_post.call_args

        # Check endpoint
        assert call_args[0][0] == NIMLLMService.LLAMA3_ENDPOINT

        # Check headers
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test_api_key_12345" in headers["Authorization"]
        assert headers["Content-Type"] == "application/json"

        # Check request data
        data = call_args[1]["json"]
        assert data["model"] == "meta/llama-3.1-8b-instruct"
        assert "messages" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "user"
        assert data["max_tokens"] == 128
        assert data["temperature"] == 0.6

        # Check response
        assert isinstance(summary, str)
        assert "household" in summary.lower()
        assert len(summary) > 0

    @patch.dict(os.environ, {}, clear=True)
    def test_get_llama3_summary_no_api_key(self):
        """Test that missing API key raises error"""
        routine = {"wake_up_time": "07:30"}

        with pytest.raises(KeyError) as exc_info:
            NIMLLMService.get_llama3_summary(routine)

        assert "NIM_API_KEY" in str(exc_info.value)

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_get_llama3_summary_api_error(self, mock_post):
        """Test handling of API errors"""
        # Mock API error
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        routine = {"wake_up_time": "07:30"}

        with pytest.raises(requests.exceptions.RequestException):
            NIMLLMService.get_llama3_summary(routine)

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_get_llama3_summary_http_error(self, mock_post):
        """Test handling of HTTP errors (4xx, 5xx)"""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response

        routine = {"wake_up_time": "07:30"}

        with pytest.raises(requests.exceptions.HTTPError):
            NIMLLMService.get_llama3_summary(routine)

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_get_llama3_summary_timeout(self, mock_post):
        """Test handling of timeout errors"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        routine = {"wake_up_time": "07:30"}

        with pytest.raises(requests.exceptions.Timeout):
            NIMLLMService.get_llama3_summary(routine)

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_get_llama3_summary_malformed_response(self, mock_post):
        """Test handling of malformed API response"""
        # Mock malformed response
        mock_response = Mock()
        mock_response.json.return_value = {"error": "invalid"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        routine = {"wake_up_time": "07:30"}

        with pytest.raises(KeyError):
            NIMLLMService.get_llama3_summary(routine)

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_get_llama3_summary_strips_whitespace(self, mock_post):
        """Test that response content is stripped of whitespace"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "  \n  Summary with whitespace.  \n  "
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        routine = {"wake_up_time": "07:30"}
        summary = NIMLLMService.get_llama3_summary(routine)

        assert summary == "Summary with whitespace."
        assert not summary.startswith(" ")
        assert not summary.endswith(" ")

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_get_llama3_summary_complete_routine(self, mock_post):
        """Test with a complete routine dictionary"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Normal daily routine with consistent wake and sleep times. All activities appear typical."
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        routine = {
            "wake_up_time": "06:30",
            "bed_time": "22:00",
            "first_kitchen_time": "07:00",
            "bathroom_first_time": "06:35",
            "total_bathroom_events": 5,
            "activity_start": "06:30",
            "activity_end": "22:00",
            "total_events": 127
        }

        summary = NIMLLMService.get_llama3_summary(routine)

        # Verify the prompt includes all routine data
        call_args = mock_post.call_args
        prompt = call_args[1]["json"]["messages"][0]["content"]
        assert "06:30" in prompt
        assert "22:00" in prompt
        assert "127" in prompt

        assert isinstance(summary, str)
        assert len(summary) > 0

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_get_llama3_summary_request_timeout_parameter(self, mock_post):
        """Test that timeout parameter is set correctly"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test summary"}}]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        routine = {"wake_up_time": "07:30"}
        NIMLLMService.get_llama3_summary(routine)

        # Verify timeout is set
        call_args = mock_post.call_args
        assert call_args[1]["timeout"] == 30

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_get_llama3_summary_stream_disabled(self, mock_post):
        """Test that streaming is disabled in the request"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test summary"}}]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        routine = {"wake_up_time": "07:30"}
        NIMLLMService.get_llama3_summary(routine)

        # Verify stream is False
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert data["stream"] is False


class TestNIMLLMServiceEdgeCases:
    """Test edge cases and unusual inputs"""

    def test_build_prompt_with_none_values(self):
        """Test building prompt with None values in routine"""
        routine = {
            "wake_up_time": None,
            "bed_time": "22:00",
            "total_events": None
        }

        prompt = NIMLLMService.build_llama3_prompt(routine)
        assert isinstance(prompt, str)
        assert "None" in prompt

    def test_build_prompt_with_very_large_routine(self):
        """Test with a routine containing many fields"""
        routine = {f"field_{i}": f"value_{i}" for i in range(100)}

        prompt = NIMLLMService.build_llama3_prompt(routine)
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    @patch.dict(os.environ, {"NIM_API_KEY": "test_key"})
    @patch('app.services.nim_llm_service.requests.post')
    def test_empty_response_content(self, mock_post):
        """Test handling of empty content in response"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "   "}}]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        routine = {"wake_up_time": "07:30"}
        summary = NIMLLMService.get_llama3_summary(routine)

        assert summary == ""
