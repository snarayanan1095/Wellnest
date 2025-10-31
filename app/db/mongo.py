# -*- coding: utf-8 -*-
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    _db_name: str = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB Atlas"""
        mongo_url = os.getenv("MONGODB_URL")
        cls._db_name = os.getenv("MONGODB_DATABASE", "wellnest")

        if not mongo_url:
            raise ValueError("MONGODB_URL not found in environment variables")

        # Mask password for logging
        display_url = mongo_url.split("://")[0] + "://****:****@" + mongo_url.split("@")[1]

        try:
            cls.client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
            # Test the connection
            await cls.client.admin.command('ping')
            print(f"✓ MongoDB connected to {display_url}")
            print(f"✓ Database: {cls._db_name}")
        except Exception as e:
            print(f"✗ MongoDB connection failed: {e}")
            raise

    @classmethod
    async def write(cls, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Write a document to a collection

        Args:
            collection_name: Name of the collection
            document: Document to insert

        Returns:
            str: Inserted document ID
        """
        if cls.client is None:
            raise RuntimeError("MongoDB client is not connected. Call connect() first.")

        db = cls.client[cls._db_name]
        collection = db[collection_name]
        result = await collection.insert_one(document)
        return str(result.inserted_id)

    @classmethod
    async def read(cls, collection_name: str, query: Dict[str, Any] = None, limit: int = 100, sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """
        Read documents from a collection

        Args:
            collection_name: Name of the collection
            query: Query filter (default: {} - returns all documents)
            limit: Maximum number of documents to return
            sort: List of tuples (field, direction) for sorting, e.g., [("timestamp", 1)]

        Returns:
            List[Dict]: List of documents
        """
        if cls.client is None:
            raise RuntimeError("MongoDB client is not connected. Call connect() first.")

        query = query or {}
        db = cls.client[cls._db_name]
        collection = db[collection_name]
        cursor = collection.find(query)

        # Apply sorting if provided
        if sort:
            cursor = cursor.sort(sort)

        # Apply limit if not None/0
        if limit:
            cursor = cursor.limit(limit)

        documents = await cursor.to_list(length=limit if limit else None)

        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        return documents

    @classmethod
    async def distinct(cls, collection_name: str, field: str, query: Dict[str, Any] = None) -> List[Any]:
        """
        Get distinct values for a field in a collection

        Args:
            collection_name: Name of the collection
            field: Field name to get distinct values from
            query: Query filter (optional)

        Returns:
            List: List of distinct values
        """
        if cls.client is None:
            raise RuntimeError("MongoDB client is not connected. Call connect() first.")

        query = query or {}
        db = cls.client[cls._db_name]
        collection = db[collection_name]
        distinct_values = await collection.distinct(field, query)
        return distinct_values

    @classmethod
    async def aggregate(cls, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run an aggregation pipeline on a collection

        Args:
            collection_name: Name of the collection
            pipeline: Aggregation pipeline stages

        Returns:
            List[Dict]: List of aggregation results
        """
        if cls.client is None:
            raise RuntimeError("MongoDB client is not connected. Call connect() first.")

        db = cls.client[cls._db_name]
        collection = db[collection_name]
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)

        # Convert ObjectId to string for JSON serialization
        for doc in results:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        return results

    @classmethod
    async def update(cls, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """
        Update documents in a collection

        Args:
            collection_name: Name of the collection
            query: Query filter to match documents
            update: Update operations to apply (should include $set, $inc, etc.)

        Returns:
            int: Number of documents modified
        """
        if cls.client is None:
            raise RuntimeError("MongoDB client is not connected. Call connect() first.")

        db = cls.client[cls._db_name]
        collection = db[collection_name]
        result = await collection.update_many(query, update)
        return result.modified_count

    @classmethod
    async def count(cls, collection_name: str, query: Dict[str, Any] = None) -> int:
        """
        Count documents in a collection matching a query

        Args:
            collection_name: Name of the collection
            query: Query filter (default: {} - counts all documents)

        Returns:
            int: Number of documents matching the query
        """
        if cls.client is None:
            raise RuntimeError("MongoDB client is not connected. Call connect() first.")

        query = query or {}
        db = cls.client[cls._db_name]
        collection = db[collection_name]
        count = await collection.count_documents(query)
        return count

    @classmethod
    async def close(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("✓ MongoDB connection closed")
