# from typing import Optional, List, Dict, Any
# import os

# class VectorDB:
#     """
#     Vector database client for semantic search
#     Supports Qdrant or Chroma
#     """
#     client: Optional[Any] = None
#     db_type: str = "qdrant"  # or "chroma"

#     @classmethod
#     async def connect(cls):
#         """Initialize vector database connection"""
#         cls.db_type = os.getenv("VECTOR_DB_TYPE", "qdrant")

#         if cls.db_type == "qdrant":
#             from qdrant_client import QdrantClient
#             qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
#             cls.client = QdrantClient(url=qdrant_url)
#             print(f"Connected to Qdrant at {qdrant_url}")
#         elif cls.db_type == "chroma":
#             import chromadb
#             chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
#             cls.client = chromadb.PersistentClient(path=chroma_path)
#             print(f"Connected to Chroma at {chroma_path}")
#         else:
#             raise ValueError(f"Unsupported vector DB type: {cls.db_type}")

#     @classmethod
#     async def close(cls):
#         """Close vector database connection"""
#         if cls.client:
#             # Cleanup if needed
#             print(f"{cls.db_type.capitalize()} connection closed")

#     @classmethod
#     async def search(cls, collection: str, vector: List[float], limit: int = 10) -> List[Dict]:
#         """Search for similar vectors"""
#         # TODO: Implement vector search based on db_type
#         pass

#     @classmethod
#     async def insert(cls, collection: str, vectors: List[List[float]], payloads: List[Dict]):
#         """Insert vectors with metadata"""
#         # TODO: Implement vector insertion based on db_type
#         pass
