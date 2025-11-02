# Wellnest

Our AI software keeps families connected to aging loved ones by learning routines, detecting changes, and sending alerts—privacy-first, no cameras, just smarter, safer independent living.

## Key Features
- Smart Routine Learning: AI learns daily patterns from motion sensors (no cameras)
- Anomaly Detection: Detects unusual behaviors and deviations from baseline
- Real-time Monitoring: Live location tracking and activity status
- Intelligent Alerts: Three-tier alert system (High/Medium/Low priority)
- Natural Language Insights: AI-generated summaries of daily activities
- Semantic Search: Vector-based search for finding specific routine patterns
- Trend Analysis: 7-day rolling baseline comparison

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Node.js 18+ (for dashboard)
- 8GB RAM minimum
- 10GB free disk space

### Required API Keys & Credentials

You'll need to obtain the following credentials:

1. **NVIDIA NIM API Key** (Required)
   - Sign up at https://build.nvidia.com/
   - Get your API key from the dashboard
   - Used for AI embeddings and LLM services

2. **MongoDB Atlas** (Required)
   - Create a free cluster at https://www.mongodb.com/cloud/atlas
   - Get your connection string
   - Whitelist your IP address

3. **Qdrant Cloud** (Optional - can run locally)
   - Sign up at https://cloud.qdrant.io/
   - Create a free cluster
   - Get your API key and URL

4. **AWS Credentials** (Optional - for production deployment)
   - AWS Access Key ID
   - AWS Secret Access Key
   - AWS Region

## 📦 Complete Local Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/Wellnest.git
cd Wellnest
```

### Step 2: Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# NVIDIA NIM API Configuration (REQUIRED)
# Get your key from: https://build.nvidia.com/
NIM_API_KEY=nvapi-YOUR_KEY_HERE  # <-- REPLACE WITH YOUR NVIDIA API KEY
NIM_MODEL_NAME=nvidia/nv-embedqa-e5-v5

# MongoDB Configuration (REQUIRED)
# Format: mongodb+srv://username:password@cluster.mongodb.net/dbname
MONGO_URL=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/wellnest?retryWrites=true&w=majority  # <-- REPLACE
MONGO_DB_NAME=wellnest

# Qdrant Configuration (OPTIONAL - comment out to skip)
# Get credentials from: https://cloud.qdrant.io/
QDRANT_URL=https://YOUR_CLUSTER.qdrant.io  # <-- REPLACE or use localhost:6333 for local
QDRANT_API_KEY=YOUR_QDRANT_KEY  # <-- REPLACE or leave empty for local

# Kafka Configuration (auto-configured with Docker)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis Configuration (auto-configured with Docker)
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# AWS Configuration (OPTIONAL - for deployment only)
AWS_ACCOUNT_ID=YOUR_ACCOUNT_ID  # <-- REPLACE if deploying to AWS
AWS_REGION=us-east-1  # <-- REPLACE with your region
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY  # <-- REPLACE if deploying to AWS
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY  # <-- REPLACE if deploying to AWS

# Dashboard Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Step 3: Start Infrastructure Services

```bash
# Start Kafka, Zookeeper, and optionally Qdrant
docker-compose up -d kafka zookeeper

# Optional: Start local Qdrant if not using cloud
docker-compose up -d qdrant

# Verify Kafka is running
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

### Step 4: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Start the Backend API

```bash
# Run the FastAPI application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Step 6: Set Up and Start the Dashboard

In a new terminal:

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install

# Create dashboard environment file
cat > .env.local << EOF
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF

# Start the dashboard
npm run dev
```

The dashboard will be available at: http://localhost:5173

## 🧪 Testing the Application

### Step 1: Verify All Services Are Running

```bash
# Check Docker services
docker-compose ps

# Should show:
# - kafka: Up
# - zookeeper: Up
# - qdrant: Up (if using local)

# Check API health
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

### Step 2: Test the Sensor Simulator

The application includes an automatic sensor simulator that creates realistic data:

```bash
# The simulator starts automatically with the API
# You should see in the API logs:
# "🚀 Starting automatic sensor simulation..."

# To manually test event ingestion:
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "household_id": "household_001",
    "sensor_id": "motion_bedroom",
    "sensor_type": "motion",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "value": "true"
  }'
```

### Step 3: View Real-Time Data

1. Open the dashboard at http://localhost:5173
2. Select "Household 001" from the dropdown
3. You should see:
   - Real-time location updates
   - Activity timeline
   - Alert notifications
   - Routine comparison charts

### Step 4: Test AI Features

```bash
# Test routine analysis (after simulator has run for a few minutes)
curl http://localhost:8000/api/routine-comparison/household_003

# Test semantic search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "bathroom visits today",
    "household_id": "household_003"
  }'
```

### Step 5: Generate Test Alerts

The simulator automatically generates anomalies for `household_003`. To see alerts:

1. In the dashboard, select "Household 003"
2. Wait 1-2 minutes for anomaly detection
3. Alerts will appear in the right panel

## 🏗️ Project Structure

```
wellnest/
├── app/                     # Backend API
│   ├── main.py             # FastAPI entry point
│   ├── api/                # API endpoints
│   │   ├── router.py       # Main router
│   │   ├── events.py       # Event ingestion
│   │   ├── households.py   # Household management
│   │   └── routine_comparison.py  # AI analysis
│   ├── services/           # Business logic
│   │   ├── nim_embedding_service.py  # NVIDIA embeddings
│   │   ├── nim_llm_service.py       # NVIDIA LLM
│   │   ├── anomaly_detector.py      # Anomaly detection
│   │   └── events_consumer.py       # WebSocket streaming
│   ├── db/                 # Database connections
│   │   ├── mongo.py        # MongoDB client
│   │   ├── qdrant_client.py # Vector DB
│   │   └── kafka_client.py  # Message queue
│   ├── models/             # Data models
│   └── scheduler/          # Background jobs
├── dashboard/              # React frontend
│   ├── src/
│   │   ├── App.tsx        # Main component
│   │   ├── components/    # UI components
│   │   └── services/      # API clients
│   ├── package.json
│   └── vite.config.ts
├── simulator/              # Test data generator
│   └── sensor_simulator.py
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Python dependencies
└── README.md
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. MongoDB Connection Error
```
Error: MongoDB connection failed
```
**Solution:**
- Check your MongoDB Atlas connection string in `.env`
- Ensure your IP is whitelisted in MongoDB Atlas Network Access
- Verify credentials are correct

#### 2. NVIDIA NIM API Error
```
Error: NIM_API_KEY not found or invalid
```
**Solution:**
- Verify your NVIDIA API key in `.env`
- Ensure the key starts with `nvapi-`
- Check your quota at https://build.nvidia.com/

#### 3. Kafka Connection Issues
```
Error: Cannot connect to Kafka broker
```
**Solution:**
```bash
# Restart Kafka services
docker-compose down
docker-compose up -d kafka zookeeper

# Wait 30 seconds for services to initialize
sleep 30

# Verify Kafka is running
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

#### 4. Dashboard Not Showing Data
**Solution:**
- Check browser console for WebSocket errors
- Ensure API is running: `curl http://localhost:8000/health`
- Verify CORS settings allow localhost:5173
- Clear browser cache and refresh

#### 5. Qdrant Connection Issues (if using)
```
Error: Qdrant client initialization failed
```
**Solution:**
- For local Qdrant: `docker-compose up -d qdrant`
- For cloud: Verify API key and URL in `.env`
- Can disable by commenting out Qdrant sections in `.env`

### Checking Logs

```bash
# API logs
docker-compose logs -f api

# Kafka logs
docker-compose logs -f kafka

# All services
docker-compose logs -f

# Python application logs (if running directly)
# Logs are printed to console
```

## 🎮 Demo Mode

For hackathon demonstrations, the simulator automatically:

1. Creates 3 test households (001, 002, 003)
2. Generates realistic sensor data every 10 seconds
3. Creates anomalies for household_003
4. Triggers various alert types

To customize demo behavior:

```python
# Edit simulator/sensor_simulator.py
# Adjust these parameters:
check_interval=10  # Seconds between events
anomaly_for_003=True  # Enable anomalies
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api.py -v

# Run integration tests (requires services running)
pytest tests/integration/ -v
```

## 📊 Performance Metrics

Expected performance on a standard laptop:
- Event ingestion: 1000+ events/second
- Alert latency: < 1 second
- Dashboard update: Real-time (WebSocket)
- AI inference: < 2 seconds
- Memory usage: ~500MB (API) + 200MB (Dashboard)

## 🔒 Security Notes

For local testing only:
- Default setup uses permissive CORS settings
- MongoDB connection may use public IP whitelist
- API keys are stored in `.env` (never commit this file)

For production:
- Use environment-specific configurations
- Implement proper authentication
- Restrict CORS origins
- Use secrets management service

## 📝 Additional Resources

- [API Documentation](http://localhost:8000/docs) - Interactive Swagger UI
- [MongoDB Atlas Setup](https://www.mongodb.com/docs/atlas/getting-started/)
- [NVIDIA NIM Documentation](https://docs.nvidia.com/nim/)
- [Docker Compose Guide](https://docs.docker.com/compose/)

## 🤝 Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review logs for error messages
3. Ensure all prerequisites are installed
4. Verify all API keys are correctly set

## Note
- For the sake of the hackathon, we have some commented code and commented notions. These are for future use cases if we take the route of actually making this a product. **#FUTURE** usage throughout the codebase signifies additional features if we take the above route.

## License

MIT
