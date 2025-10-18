# from redis.asyncio import Redis
# from typing import Optional
# import os

# class RedisClient:
#     """Redis client for caching and job scheduling"""
#     client: Optional[Redis] = None

#     @classmethod
#     async def connect(cls):
#         """Connect to Redis"""
#         redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
#         try:
#             cls.client = Redis.from_url(
#                 redis_url,
#                 encoding="utf-8",
#                 decode_responses=True
#             )
#             await cls.client.ping()
#             print(f"Connected to Redis at {redis_url}")
#         except Exception as e:
#             print(f"⚠ Redis not available: {e}")
#             print("⚠ Running without Redis (some features may be limited)")
#             cls.client = None

#     @classmethod
#     async def close(cls):
#         """Close Redis connection"""
#         if cls.client:
#             await cls.client.close()
#             print("Redis connection closed")

#     @classmethod
#     async def get(cls, key: str) -> Optional[str]:
#         """Get value by key"""
#         if cls.client is None:
#             return None
#         return await cls.client.get(key)

#     @classmethod
#     async def set(cls, key: str, value: str, ex: int = None):
#         """Set key-value pair with optional expiration"""
#         if cls.client is None:
#             return
#         await cls.client.set(key, value, ex=ex)

#     @classmethod
#     async def delete(cls, key: str):
#         """Delete key"""
#         if cls.client is None:
#             return
#         await cls.client.delete(key)
