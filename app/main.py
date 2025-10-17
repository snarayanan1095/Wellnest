from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.db.mongo import MongoDB
from app.db.redis_client import RedisClient
from app.db.vector_db import VectorDB

app = FastAPI(
    title="Wellnest API",
    description="Mental wellness platform API",
    version="0.1.0"
)

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


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    try:
        # Initialize MongoDB
        await MongoDB.connect()
        print("✓ MongoDB connected")

        # Initialize Redis
        await RedisClient.connect()
        print("✓ Redis connected")

        # Initialize Vector DB
        await VectorDB.connect()
        print("✓ Vector DB connected")

    except Exception as e:
        print(f"✗ Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        # Close MongoDB
        await MongoDB.close()
        print("✓ MongoDB disconnected")

        # Close Redis
        await RedisClient.close()
        print("✓ Redis disconnected")

        # Close Vector DB
        await VectorDB.close()
        print("✓ Vector DB disconnected")

    except Exception as e:
        print(f"✗ Error during shutdown: {e}")


@app.get("/")
async def root():
    return {"message": "Welcome to Wellnest API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
