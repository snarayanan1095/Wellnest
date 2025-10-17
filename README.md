# Wellnest

Mental wellness platform backend API built with FastAPI.

## Project Structure

```
wellnest/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/                 # API route handlers
│   ├── services/            # Business logic services
│   ├── db/                  # Database connections
│   │   ├── mongo.py         # MongoDB async connection
│   │   ├── vector_db.py     # Qdrant/Chroma setup
│   │   └── redis_client.py  # Redis connection
│   ├── models/              # Pydantic models
│   │   ├── event.py         # Event models
│   │   ├── routine.py       # Routine profile models
│   │   └── alert.py         # Alert models
│   ├── scheduler/           # Scheduled jobs
│   │   └── batch_jobs.py    # APScheduler cron tasks
│   └── utils/               # Utilities
│       └── logging.py       # Structured logging
├── tests/                   # Pytest tests
├── docker-compose.yml       # Local dev stack
├── Dockerfile               # FastAPI app container
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md
```

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

### Docker Development

1. Start all services:
```bash
docker-compose up -d
```

2. View logs:
```bash
docker-compose logs -f api
```

3. Stop services:
```bash
docker-compose down
```

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests with pytest:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## Technologies

- **FastAPI**: Modern Python web framework
- **MongoDB**: Document database for user data
- **Redis**: Caching and job queue
- **Qdrant/Chroma**: Vector database for semantic search
- **APScheduler**: Background job scheduling
- **Motor**: Async MongoDB driver
- **Pydantic**: Data validation

## License

MIT
