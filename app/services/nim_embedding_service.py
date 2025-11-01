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

    @classmethod
    def format_daily_routine_for_embedding(cls, routine: Dict[str, Any]) -> str:
        """
        Format daily routine data into a text string for embedding

        Args:
            routine: Daily routine dictionary from MongoDB

        Returns:
            str: Formatted text representation of the daily routine
        """
        text_parts = []

        # Household and date info
        household_id = routine.get('household_id', 'unknown')
        date = routine.get('date', 'unknown')
        text_parts.append(f"Household {household_id} routine for {date}")

        # Wake and bed times
        wake_time = routine.get('wake_up_time')
        bed_time = routine.get('bed_time')
        if wake_time or bed_time:
            text_parts.append(f"Wake-up time: {wake_time or 'N/A'}, bed time: {bed_time or 'N/A'}")

        # Kitchen and bathroom times
        kitchen_time = routine.get('first_kitchen_time')
        bathroom_time = routine.get('bathroom_first_time')
        if kitchen_time or bathroom_time:
            text_parts.append(f"First kitchen visit: {kitchen_time or 'N/A'}, first bathroom visit: {bathroom_time or 'N/A'}")

        # Bathroom visits
        bathroom_visits = routine.get('total_bathroom_events', 0)
        if bathroom_visits:
            text_parts.append(f"Bathroom visits: {bathroom_visits}")

        # Kitchen visits
        kitchen_visits = routine.get('total_kitchen_events', 0)
        if kitchen_visits:
            text_parts.append(f"Kitchen visits: {kitchen_visits}")

        # Room durations
        living_room_time = routine.get('living_room_time', 0)
        bedroom_time = routine.get('bedroom_time', 0)

        if living_room_time > 0:
            text_parts.append(f"Living room time: {living_room_time} minutes")
        if bedroom_time > 0:
            text_parts.append(f"Bedroom time: {bedroom_time} minutes")

        # Activity duration
        activity_start = routine.get('activity_start')
        activity_end = routine.get('activity_end')
        if activity_start and activity_end:
            text_parts.append(f"Activity period: {activity_start} to {activity_end}")

        # Total events
        total_events = routine.get('total_events', 0)
        if total_events:
            text_parts.append(f"Total daily events: {total_events}")

        # Activity level classification
        if bathroom_visits > 10:
            text_parts.append("Activity level: Very High")
        elif bathroom_visits > 7:
            text_parts.append("Activity level: High")
        elif bathroom_visits > 4:
            text_parts.append("Activity level: Normal")
        else:
            text_parts.append("Activity level: Low")

        return ". ".join(text_parts) + "."

    @classmethod
    async def semantic_search(cls, query, household_id, top_k=5):
        """
        1. Embed user query using NVIDIAEmbeddings
        2. Search MongoDB for similar content (simulating vector search)
        3. Return results for dashboard display
        """
        # Import MongoDB here to avoid circular imports
        from app.db.mongo import MongoDB
        from datetime import datetime

        # 1. Create embedding for user's query (this would be used for vector similarity)
        try:
            query_embedding = cls.client.embed_query(query)  # <-- THIS IS THE KEY FUNCTION
            print(f"Generated embedding for query: '{query}' (dimension: {len(query_embedding)})")
        except Exception as e:
            print(f"Error generating embedding: {e}")
            query_embedding = None

        # 2. Since Qdrant isn't set up, we'll do keyword-based search in MongoDB
        # In production, this would be: search_results = QdrantClient.search(query_embedding, ...)

        results = []
        query_lower = query.lower()

        try:
            # Search for relevant data based on keywords
            if any(word in query_lower for word in ['bathroom', 'toilet', 'restroom']):
                # Get bathroom-related data
                routines = await MongoDB.read(
                    "daily_routines",
                    query={"household_id": household_id} if household_id else {},
                    sort=[("date", -1)],
                    limit=top_k
                )
                for r in routines:
                    results.append({
                        "date": r.get("date", ""),
                        "summary_text": f"Bathroom visits: {r.get('total_bathroom_events', 0)}",
                        "score": 0.9  # High relevance for bathroom queries
                    })

            elif any(word in query_lower for word in ['sleep', 'wake', 'bed']):
                # Get sleep-related data
                routines = await MongoDB.read(
                    "daily_routines",
                    query={"household_id": household_id} if household_id else {},
                    sort=[("date", -1)],
                    limit=top_k
                )
                for r in routines:
                    results.append({
                        "date": r.get("date", ""),
                        "summary_text": f"Wake: {r.get('wake_up_time')}, Bed: {r.get('bed_time')}",
                        "score": 0.9
                    })

            elif any(word in query_lower for word in ['irregular', 'unusual', 'anomaly']):
                # Get anomalies
                alerts = await MongoDB.read(
                    "alerts",
                    query={"household_id": household_id} if household_id else {},
                    sort=[("timestamp", -1)],
                    limit=top_k
                )
                for a in alerts:
                    results.append({
                        "date": a.get("timestamp", ""),
                        "summary_text": f"{a.get('title')}: {a.get('message')}",
                        "score": 0.85
                    })

            else:
                # General search - return recent routines
                routines = await MongoDB.read(
                    "daily_routines",
                    query={"household_id": household_id} if household_id else {},
                    sort=[("date", -1)],
                    limit=top_k
                )
                for r in routines:
                    results.append({
                        "date": r.get("date", ""),
                        "summary_text": r.get("summary_text", "No summary available"),
                        "score": 0.7
                    })

        except Exception as e:
            print(f"Error searching MongoDB: {e}")

        return results