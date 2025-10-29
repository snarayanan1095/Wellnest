# -*- coding: utf-8 -*-
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NIMEmbeddingService:
    """NVIDIA NIM Embedding Service for generating text embeddings"""

    client: Optional[NVIDIAEmbeddings] = None
    _model_name: str = None
    _api_key: str = None

    @classmethod
    def initialize(cls):
        """Initialize the NIM embedding client"""
        cls._model_name = os.getenv("NIM_MODEL_NAME", "nvidia/nv-embedqa-e5-v5")
        cls._api_key = os.getenv("NIM_API_KEY")

        if not cls._api_key:
            raise ValueError("NIM_API_KEY not found in environment variables")

        try:
            cls.client = NVIDIAEmbeddings(
                model=cls._model_name,
                api_key=cls._api_key,
                truncate="NONE",
            )
            print(f"✓ NIM Embedding Service initialized with model: {cls._model_name}")
        except Exception as e:
            print(f"✗ NIM Embedding Service initialization failed: {e}")
            raise

    @classmethod
    def embed_query(cls, text: str) -> List[float]:
        """
        Generate embedding for a single text query

        Args:
            text: Input text to embed

        Returns:
            List[float]: Embedding vector
        """
        if cls.client is None:
            raise RuntimeError("NIM client is not initialized. Call initialize() first.")

        return cls.client.embed_query(text)

    @classmethod
    def embed_documents(cls, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents

        Args:
            texts: List of input texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        if cls.client is None:
            raise RuntimeError("NIM client is not initialized. Call initialize() first.")

        return cls.client.embed_documents(texts)

    @classmethod
    def format_baseline_routine_for_embedding(cls, baseline: Dict[str, Any]) -> str:
        """
        Format baseline routine data into a text string for embedding

        Args:
            baseline: Baseline routine dictionary from MongoDB

        Returns:
            str: Formatted text representation of the baseline
        """
        b = baseline

        # Helper to safely get nested values
        def safe_get(data, *keys, default="N/A"):
            for key in keys:
                if isinstance(data, dict):
                    data = data.get(key, {})
                else:
                    return default
            return data if data != {} else default

        # Build the text representation with safe field access
        text_parts = []

        # Household and period info
        household_id = b.get('household_id', 'unknown')
        days = safe_get(b, 'baseline_period', 'days', default=0)
        start_date = safe_get(b, 'baseline_period', 'start_date')
        end_date = safe_get(b, 'baseline_period', 'end_date')
        text_parts.append(f"Household {household_id} baseline summary for {days} days from {start_date} to {end_date}")

        # Wake and bed times
        wake_median = safe_get(b, 'wake_up_time', 'median')
        bed_median = safe_get(b, 'bed_time', 'median')
        if wake_median != "N/A" or bed_median != "N/A":
            text_parts.append(f"Wake-up time: {wake_median}, bed time: {bed_median}")

        # Kitchen and bathroom times
        kitchen_median = safe_get(b, 'first_kitchen_time', 'median')
        bathroom_median = safe_get(b, 'bathroom_first_time', 'median')
        if kitchen_median != "N/A" or bathroom_median != "N/A":
            text_parts.append(f"First kitchen visit: {kitchen_median}, first bathroom visit: {bathroom_median}")

        # Bathroom visits
        bath_avg = safe_get(b, 'bathroom_visits', 'daily_avg')
        bath_median = safe_get(b, 'bathroom_visits', 'daily_median')
        bath_min = safe_get(b, 'bathroom_visits', 'min_daily')
        bath_max = safe_get(b, 'bathroom_visits', 'max_daily')
        if bath_avg != "N/A":
            text_parts.append(f"Bathroom visits - avg: {bath_avg}, median: {bath_median}, range: {bath_min}-{bath_max}")

        # Activity duration
        activity_median = safe_get(b, 'activity_duration', 'median_minutes')
        activity_earliest = safe_get(b, 'activity_duration', 'earliest_start')
        activity_latest = safe_get(b, 'activity_duration', 'latest_end')
        if activity_median != "N/A":
            text_parts.append(f"Activity duration: {activity_median} minutes, earliest start: {activity_earliest}, latest end: {activity_latest}")

        # Daily events
        events_avg = safe_get(b, 'total_daily_events', 'avg')
        events_median = safe_get(b, 'total_daily_events', 'median')
        events_min = safe_get(b, 'total_daily_events', 'min')
        events_max = safe_get(b, 'total_daily_events', 'max')
        if events_avg != "N/A":
            text_parts.append(f"Daily events - avg: {events_avg}, median: {events_median}, range: {events_min}-{events_max}")

        # Data quality
        complete_days = safe_get(b, 'data_quality', 'days_with_complete_data')
        missing_wake = safe_get(b, 'data_quality', 'days_with_missing_wake')
        missing_kitchen = safe_get(b, 'data_quality', 'days_with_missing_kitchen')
        reliability = safe_get(b, 'data_quality', 'reliability_score')
        if complete_days != "N/A":
            text_parts.append(f"Data quality: {complete_days} complete days, {missing_wake} missing wake, {missing_kitchen} missing kitchen, reliability: {reliability}")

        return ". ".join(text_parts) + "."
