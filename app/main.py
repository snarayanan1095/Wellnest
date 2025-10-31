from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.mongo import MongoDB
from app.db.kafka_client import KafkaClient
from app.db.qdrant_client import QdrantClient
from app.services.nim_embedding_service import NIMEmbeddingService
from app.scheduler import start_scheduler, shutdown_scheduler
from app.services.events_consumer import start_events_consumer
import threading
import asyncio
# from app.db.redis_client import RedisClient
# from app.db.vector_db import VectorDB

app = FastAPI(
    title="Wellnest API",
    description="Mental wellness platform API",
    version="0.1.0"
)

# Background task to run the simulator
simulator_thread = None

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)


# @app.on_event("startup")
# async def startup_event():
#     """Initialize connections on startup"""
#     try:
#         # Initialize MongoDB
#         await MongoDB.connect()
#         print("✓ MongoDB connected")

#         # Initialize Redis (optional)
#         await RedisClient.connect()
#         if RedisClient.client:
#             print("✓ Redis connected")

#         # Initialize Vector DB (optional)
#         try:
#             await VectorDB.connect()
#             print("✓ Vector DB connected")
#         except Exception as e:
#             print(f"⚠ Vector DB not available: {e}")
#             print("⚠ Running without Vector DB (some features may be limited)")

#     except Exception as e:
#         print(f"✗ Error during startup: {e}")
#         raise


# @app.on_event("shutdown")
# async def shutdown_event():
#     """Cleanup on shutdown"""
#     try:
#         # Close MongoDB
#         await MongoDB.close()
#         print("✓ MongoDB disconnected")

#         # Close Redis
#         await RedisClient.close()
#         print("✓ Redis disconnected")

#         # Close Vector DB
#         await VectorDB.close()
#         print("✓ Vector DB disconnected")

#     except Exception as e:
#         print(f"✗ Error during shutdown: {e}")


@app.get("/")
async def root():
    return {"message": "Welcome to Wellnest API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def run_simulator_in_background():
    """Run the sensor simulator in a background thread"""
    import time
    from simulator.sensor_simulator import run_continuous_simulation

    # Wait a bit for the server to fully start
    time.sleep(3)

    print("\n" + "="*60)
    print("🚀 Starting automatic sensor simulation...")
    print("="*60 + "\n")

    # Run the continuous simulation with anomaly mode enabled for household_003
    run_continuous_simulation("http://localhost:8000/api/events", check_interval=10, anomaly_for_003=True)


@app.on_event("startup")
async def startup_event():
    """Initialize connections and start background tasks on startup"""
    global simulator_thread

    print("\n" + "="*60)
    print("🏥 Wellnest API Starting Up...")
    print("="*60)

    # Initialize MongoDB
    try:
        await MongoDB.connect()
    except Exception as e:
        print(f"✗ Error connecting to MongoDB: {e}")
        raise

    # Initialize Kafka
    try:
        await KafkaClient.connect()
    except Exception as e:
        print(f"⚠ Kafka not available: {e}")
        print("⚠ Running without Kafka (events won't be published to message queue)")

    # Initialize Qdrant
    try:
        await QdrantClient.connect()
        # Create routine_baselines collection if it doesn't exist
        # Note: You need to know the embedding dimension. nvidia/nv-embedqa-e5-v5 uses 1024 dimensions
        from qdrant_client.models import Distance
        await QdrantClient.create_collection(
            collection_name="routine_baselines",
            vector_size=1024,  # nvidia/nv-embedqa-e5-v5 embedding size
            distance=Distance.COSINE
        )
    except Exception as e:
        print(f"⚠ Qdrant not available: {e}")
        print("⚠ Running without Qdrant (vector search features will be disabled)")

    # Initialize NIM Embedding Service
    try:
        NIMEmbeddingService.initialize()
    except Exception as e:
        print(f"⚠ NIM Embedding Service not available: {e}")
        print("⚠ Running without NIM embeddings (semantic search features will be disabled)")

    # Start the simulator in a background thread
    simulator_thread = threading.Thread(target=run_simulator_in_background, daemon=True)
    simulator_thread.start()
    print("✓ Sensor simulator scheduled to start")

    # Start the routine learner scheduler
    try:
        start_scheduler()
    except Exception as e:
        print(f"⚠ Error starting routine learner scheduler: {e}")

    # Start the events consumer for WebSocket streaming
    try:
        asyncio.create_task(start_events_consumer())
        print("✓ Events consumer started for WebSocket streaming")
    except Exception as e:
        print(f"⚠ Error starting events consumer: {e}")

    # Initialize other databases when needed
    # try:
    #     # Initialize Redis (optional)
    #     await RedisClient.connect()
    #     if RedisClient.client:
    #         print("✓ Redis connected")
    #
    #     # Initialize Vector DB (optional)
    #     try:
    #         await VectorDB.connect()
    #         print("✓ Vector DB connected")
    #     except Exception as e:
    #         print(f"⚠ Vector DB not available: {e}")
    #         print("⚠ Running without Vector DB (some features may be limited)")
    #
    # except Exception as e:
    #     print(f"✗ Error during startup: {e}")
    #     raise

    print("="*60)
    print("✓ Wellnest API Ready!")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n" + "="*60)
    print("🛑 Wellnest API Shutting Down...")
    print("="*60)

    # The simulator thread will automatically stop since it's a daemon thread

    # Stop the routine learner scheduler
    try:
        shutdown_scheduler()
    except Exception as e:
        print(f"✗ Error stopping routine learner scheduler: {e}")

    # Close MongoDB connection
    try:
        await MongoDB.close()
    except Exception as e:
        print(f"✗ Error closing MongoDB: {e}")

    # Close Kafka producer
    try:
        KafkaClient.close()
    except Exception as e:
        print(f"✗ Error closing Kafka: {e}")

    # Close Qdrant connection
    try:
        await QdrantClient.close()
    except Exception as e:
        print(f"✗ Error closing Qdrant: {e}")

    # Close other databases when needed
    # try:
    #     # Close Redis
    #     await RedisClient.close()
    #     print("✓ Redis disconnected")
    #
    #     # Close Vector DB
    #     await VectorDB.close()
    #     print("✓ Vector DB disconnected")
    #
    # except Exception as e:
    #     print(f"✗ Error during shutdown: {e}")

    print("="*60)
    print("✓ Shutdown Complete")
    print("="*60 + "\n")
