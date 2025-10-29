# -*- coding: utf-8 -*-
from qdrant_client import QdrantClient as QdrantClientSDK
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class QdrantClient:
    """Qdrant vector database client for semantic search and embeddings storage"""

    client: Optional[QdrantClientSDK] = None
    _default_collection: str = "wellnest_vectors"

    @classmethod
    async def connect(cls):
        """Connect to Qdrant vector database"""
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY") 

        try:
            if qdrant_api_key:
                cls.client = QdrantClientSDK(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    timeout=10
                )
            else:
                cls.client = QdrantClientSDK(
                    url=qdrant_url,
                    timeout=10
                )

            # Test the connection by listing collections
            collections = cls.client.get_collections()
            print(f"✓ Qdrant connected to {qdrant_url}")
            print(f"✓ Available collections: {len(collections.collections)}")

        except Exception as e:
            print(f"✗ Qdrant connection failed: {e}")
            raise

    @classmethod
    async def close(cls):
        """Close Qdrant connection"""
        if cls.client:
            cls.client.close()
            print("✓ Qdrant connection closed")

    @classmethod
    async def create_collection(
        cls,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
        on_disk: bool = False
    ) -> bool:
        """
        Create a new collection for storing vectors

        Args:
            collection_name: Name of the collection to create
            vector_size: Dimension of the vectors (e.g., 384, 768, 1536)
            distance: Distance metric (COSINE, EUCLID, DOT)
            on_disk: Whether to store vectors on disk (useful for large collections)

        Returns:
            bool: True if collection was created successfully
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        try:
            # Check if collection already exists
            collections = cls.client.get_collections().collections
            collection_exists = any(col.name == collection_name for col in collections)

            if collection_exists:
                print(f"Collection '{collection_name}' already exists")
                # Create indexes even if collection exists (idempotent operation)
                await cls.create_payload_index(collection_name, "household_id")
                await cls.create_payload_index(collection_name, "baseline_id")
                return True

            # Create collection
            cls.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance,
                    on_disk=on_disk
                )
            )
            print(f"✓ Collection '{collection_name}' created successfully")

            # Create payload indexes for filtering
            await cls.create_payload_index(collection_name, "household_id")
            await cls.create_payload_index(collection_name, "baseline_id")

            return True

        except Exception as e:
            print(f"✗ Failed to create collection '{collection_name}': {e}")
            raise

    @classmethod
    async def create_payload_index(
        cls,
        collection_name: str,
        field_name: str,
        field_type: str = "keyword"
    ) -> bool:
        """
        Create an index on a payload field for faster filtering

        Args:
            collection_name: Name of the collection
            field_name: Name of the payload field to index
            field_type: Type of index (keyword, integer, float, geo, text)

        Returns:
            bool: True if index was created successfully
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        try:
            from qdrant_client.models import PayloadSchemaType

            # Map string types to Qdrant schema types
            schema_type_map = {
                "keyword": PayloadSchemaType.KEYWORD,
                "integer": PayloadSchemaType.INTEGER,
                "float": PayloadSchemaType.FLOAT,
                "geo": PayloadSchemaType.GEO,
                "text": PayloadSchemaType.TEXT
            }

            schema_type = schema_type_map.get(field_type, PayloadSchemaType.KEYWORD)

            cls.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema_type
            )
            print(f"✓ Created index on '{field_name}' in collection '{collection_name}'")
            return True

        except Exception as e:
            # Index might already exist, which is fine
            if "already exists" in str(e).lower():
                print(f"✓ Index on '{field_name}' already exists")
                return True
            print(f"⚠ Failed to create index on '{field_name}': {e}")
            return False

    @classmethod
    async def insert_vectors(
        cls,
        collection_name: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Insert vectors with metadata into a collection

        Args:
            collection_name: Name of the collection
            vectors: List of vector embeddings
            payloads: List of metadata dictionaries for each vector
            ids: Optional list of IDs for the vectors (auto-generated if not provided)

        Returns:
            List[str]: List of inserted point IDs
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        if len(vectors) != len(payloads):
            raise ValueError("Number of vectors must match number of payloads")

        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

        # Create points
        points = [
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]

        # Upsert points (insert or update)
        cls.client.upsert(
            collection_name=collection_name,
            points=points
        )

        print(f"✓ Inserted {len(points)} vectors into '{collection_name}'")
        return ids

    @classmethod
    async def search_vectors(
        cls,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in a collection

        Args:
            collection_name: Name of the collection to search
            query_vector: Query vector embedding
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0-1 for cosine)
            filter_conditions: Dictionary of field conditions to filter results

        Returns:
            List[Dict]: List of search results with scores and payloads
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        # Build filter if conditions provided
        query_filter = None
        if filter_conditions:
            must_conditions = []
            for field, value in filter_conditions.items():
                must_conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(value=value)
                    )
                )
            query_filter = Filter(must=must_conditions)

        # Perform search
        search_results = cls.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter
        )

        # Format results
        results = []
        for result in search_results:
            results.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            })

        return results

    @classmethod
    async def get_vector(
        cls,
        collection_name: str,
        point_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific vector by ID

        Args:
            collection_name: Name of the collection
            point_id: ID of the point to retrieve

        Returns:
            Dict: Point data with vector and payload, or None if not found
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        try:
            point = cls.client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
                with_vectors=True  # Explicitly request vectors
            )

            if point:
                return {
                    "id": point[0].id,
                    "vector": point[0].vector,
                    "payload": point[0].payload
                }
            return None

        except Exception as e:
            print(f"✗ Failed to retrieve vector '{point_id}': {e}")
            return None

    @classmethod
    async def delete_vectors(
        cls,
        collection_name: str,
        point_ids: List[str]
    ) -> bool:
        """
        Delete vectors by IDs

        Args:
            collection_name: Name of the collection
            point_ids: List of point IDs to delete

        Returns:
            bool: True if deletion was successful
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        try:
            cls.client.delete(
                collection_name=collection_name,
                points_selector=point_ids
            )
            print(f"✓ Deleted {len(point_ids)} vectors from '{collection_name}'")
            return True

        except Exception as e:
            print(f"✗ Failed to delete vectors: {e}")
            raise

    @classmethod
    async def delete_collection(cls, collection_name: str) -> bool:
        """
        Delete an entire collection

        Args:
            collection_name: Name of the collection to delete

        Returns:
            bool: True if deletion was successful
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        try:
            cls.client.delete_collection(collection_name=collection_name)
            print(f"✓ Collection '{collection_name}' deleted successfully")
            return True

        except Exception as e:
            print(f"✗ Failed to delete collection '{collection_name}': {e}")
            raise

    @classmethod
    async def get_collection_info(cls, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a collection

        Args:
            collection_name: Name of the collection

        Returns:
            Dict: Collection information including vector count and configuration
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        try:
            info = cls.client.get_collection(collection_name=collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance
            }

        except Exception as e:
            print(f"✗ Failed to get collection info: {e}")
            raise

    @classmethod
    async def list_collections(cls) -> List[str]:
        """
        List all available collections

        Returns:
            List[str]: List of collection names
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        collections = cls.client.get_collections()
        return [col.name for col in collections.collections]

    @classmethod
    async def search_by_household(
        cls,
        collection_name: str,
        household_id: str,
        query_vector: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors filtered by household_id

        Args:
            collection_name: Name of the collection to search
            household_id: Household ID to filter by
            query_vector: Query vector embedding
            limit: Maximum number of results to return

        Returns:
            List[Dict]: List of search results with scores and payloads
        """
        return await cls.search_vectors(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            filter_conditions={"household_id": household_id}
        )

    @classmethod
    async def get_baseline_by_id(
        cls,
        collection_name: str,
        baseline_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a baseline vector by its MongoDB baseline_id
        Uses deterministic UUID generation to find the point

        Args:
            collection_name: Name of the collection
            baseline_id: MongoDB baseline document ID (e.g., "household_001_2025-10-24_baseline7")

        Returns:
            Dict: Point data with vector and payload, or None if not found
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        import uuid
        # Generate the same UUID used during insertion
        point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, baseline_id))

        return await cls.get_vector(collection_name, point_uuid)

    @classmethod
    async def get_all_baselines_for_household(
        cls,
        collection_name: str,
        household_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all baseline vectors for a specific household

        Args:
            collection_name: Name of the collection
            household_id: Household ID to filter by

        Returns:
            List[Dict]: List of vectors with their payloads
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        # Scroll through all points with the household_id filter
        results = cls.client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="household_id",
                        match=MatchValue(value=household_id)
                    )
                ]
            ),
            limit=100,
            with_vectors=True  # Explicitly request vectors
        )

        points = results[0]  # First element contains the points
        return [{
            "id": point.id,
            "payload": point.payload,
            "vector": point.vector
        } for point in points]

    @classmethod
    async def semantic_search_routines(
        cls,
        query_text: str,
        embedding_service,
        collection_name: str = "routine_baselines",
        limit: int = 10,
        score_threshold: Optional[float] = 0.5,
        household_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on routine baselines using natural language queries.

        Examples:
        - "Find days that were unusual"
        - "Show routines with late kitchen activity and high bathroom visits"
        - "Days with disrupted sleep patterns"
        - "Routines with early wake-up times"

        Args:
            query_text: Natural language query from user
            embedding_service: NIMEmbeddingService class to generate embeddings
            collection_name: Name of the collection to search (default: routine_baselines)
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0-1, higher = more similar)
            household_id: Optional household ID to filter results

        Returns:
            List[Dict]: List of matching routines with relevance scores and full context
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        try:
            # Generate embedding for the user's query
            query_embedding = embedding_service.embed_query(query_text)

            # Prepare filter conditions
            filter_conditions = {}
            if household_id:
                filter_conditions["household_id"] = household_id

            # Perform semantic search
            search_results = await cls.search_vectors(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions if filter_conditions else None
            )

            # Enrich results with formatted information
            enriched_results = []
            for result in search_results:
                payload = result['payload']

                enriched_result = {
                    "relevance_score": round(result['score'], 4),
                    "household_id": payload.get('household_id'),
                    "baseline_id": payload.get('baseline_id'),
                    "period": {
                        "start": payload.get('baseline_period_start'),
                        "end": payload.get('baseline_period_end')
                    },
                    "computed_at": payload.get('computed_at'),
                    "summary": payload.get('embed_text', ''),
                    "qdrant_id": result['id']
                }

                enriched_results.append(enriched_result)

            return enriched_results

        except Exception as e:
            print(f"✗ Semantic search failed: {e}")
            raise

    @classmethod
    async def compare_routine_to_baseline(
        cls,
        daily_routine: Dict[str, Any],
        embedding_service,
        household_id: str,
        collection_name: str = "routine_baselines",
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        Compare a daily routine against stored baselines to detect anomalies.
        Returns the most similar baselines and a deviation score.

        Args:
            daily_routine: Daily routine document from MongoDB
            embedding_service: NIMEmbeddingService class
            household_id: Household ID to filter baselines
            collection_name: Collection name
            limit: Number of similar baselines to compare against

        Returns:
            Dict: Comparison results with similarity scores and deviation analysis
        """
        if cls.client is None:
            raise RuntimeError("Qdrant client is not connected. Call connect() first.")

        try:
            # Format the daily routine for embedding
            # Use the same formatter but adapt for daily routine structure
            routine_text = cls._format_daily_routine_for_search(daily_routine)

            # Generate embedding
            routine_embedding = embedding_service.embed_query(routine_text)

            # Search for similar baselines from the same household
            similar_baselines = await cls.search_by_household(
                collection_name=collection_name,
                household_id=household_id,
                query_vector=routine_embedding,
                limit=limit
            )

            # Calculate deviation metrics
            if similar_baselines:
                avg_similarity = sum(r['score'] for r in similar_baselines) / len(similar_baselines)
                max_similarity = max(r['score'] for r in similar_baselines)

                # Lower similarity = higher deviation (more unusual)
                deviation_score = 1 - avg_similarity

                is_unusual = avg_similarity < 0.75  # Threshold for "unusual"

                return {
                    "is_unusual": is_unusual,
                    "deviation_score": round(deviation_score, 4),
                    "average_similarity": round(avg_similarity, 4),
                    "max_similarity": round(max_similarity, 4),
                    "similar_baselines": [{
                        "baseline_id": r['payload']['baseline_id'],
                        "similarity": round(r['score'], 4),
                        "period": f"{r['payload'].get('baseline_period_start')} to {r['payload'].get('baseline_period_end')}"
                    } for r in similar_baselines],
                    "interpretation": cls._interpret_deviation(deviation_score)
                }
            else:
                return {
                    "is_unusual": True,
                    "deviation_score": 1.0,
                    "message": "No baselines found for comparison"
                }

        except Exception as e:
            print(f"✗ Routine comparison failed: {e}")
            raise

    @classmethod
    def _format_daily_routine_for_search(cls, routine: Dict[str, Any]) -> str:
        """
        Format a daily routine for semantic search (similar to baseline formatting)

        Args:
            routine: Daily routine document

        Returns:
            str: Formatted text representation
        """
        parts = []

        household_id = routine.get('household_id', 'unknown')
        date = routine.get('date', 'unknown')
        parts.append(f"Household {household_id} routine for {date}")

        wake = routine.get('wake_up_time')
        bed = routine.get('bed_time')
        if wake or bed:
            parts.append(f"Wake-up: {wake or 'N/A'}, bed time: {bed or 'N/A'}")

        kitchen = routine.get('first_kitchen_time')
        if kitchen:
            parts.append(f"First kitchen visit: {kitchen}")

        bathroom_count = routine.get('total_bathroom_events')
        bathroom_first = routine.get('bathroom_first_time')
        if bathroom_count:
            parts.append(f"Bathroom visits: {bathroom_count}, first at: {bathroom_first or 'N/A'}")

        activity_start = routine.get('activity_start')
        activity_end = routine.get('activity_end')
        if activity_start and activity_end:
            parts.append(f"Activity: {activity_start} to {activity_end}")

        total_events = routine.get('total_events')
        if total_events:
            parts.append(f"Total events: {total_events}")

        return ". ".join(parts) + "."

    @classmethod
    def _interpret_deviation(cls, deviation_score: float) -> str:
        """
        Provide human-readable interpretation of deviation score

        Args:
            deviation_score: Deviation score (0-1, higher = more unusual)

        Returns:
            str: Human-readable interpretation
        """
        if deviation_score < 0.15:
            return "Very similar to typical routine - no concerns"
        elif deviation_score < 0.25:
            return "Slightly different from typical routine - minor variation"
        elif deviation_score < 0.40:
            return "Moderately different - worth monitoring"
        elif deviation_score < 0.60:
            return "Significantly different - potential anomaly detected"
        else:
            return "Highly unusual - immediate attention recommended"
