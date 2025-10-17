from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB"""
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        cls.client = AsyncIOMotorClient(mongo_url)
        print(f"Connected to MongoDB at {mongo_url}")

    @classmethod
    async def close(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("MongoDB connection closed")

    @classmethod
    def get_database(cls, db_name: str = None):
        """Get database instance"""
        db_name = db_name or os.getenv("MONGODB_DATABASE", "wellnest")
        return cls.client[db_name]

    @classmethod
    def get_collection(cls, collection_name: str, db_name: str = None):
        """Get collection instance"""
        db = cls.get_database(db_name)
        return db[collection_name]
