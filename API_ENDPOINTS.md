# Wellnest API - Endpoint Reference

## 🌐 Base URL

**Production (EKS):**
```
http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com
```

**Local Development:**
```
http://localhost:8000
```

---

## 📚 Available Endpoints

### 1. Root Endpoint

**GET /** - Welcome message

```bash
curl http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/
```

**Response:**
```json
{
  "message": "Welcome to Wellnest API"
}
```

---

### 2. Health Check

**GET /health** - Check API health status

```bash
curl http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

**Use Case:**
- Kubernetes liveness/readiness probes
- Monitoring and alerting
- Load balancer health checks

---

### 3. Ingest Sensor Event

**POST /api/events** - Ingest a single sensor event

**Request Body:**
```json
{
  "household_id": "household_001",
  "sensor_id": "motion_kitchen",
  "sensor_type": "motion",
  "location": "kitchen",
  "resident": "grandma",
  "timestamp": "2025-10-21T22:00:00Z",
  "value": "true"
}
```

**cURL Example:**
```bash
curl -X POST http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "household_id": "household_001",
    "sensor_id": "motion_kitchen",
    "sensor_type": "motion",
    "location": "kitchen",
    "resident": "grandma",
    "timestamp": "2025-10-21T22:00:00Z",
    "value": "true"
  }'
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "Event from household household_001, sensor motion_kitchen ingested successfully",
  "event_id": "6224a2424094ca9c",
  "timestamp": "2025-10-21T22:00:00Z"
}
```

**Field Descriptions:**
- `household_id` (required): Unique identifier for the household
- `sensor_id` (required): Unique identifier for the sensor
- `sensor_type` (required): Type of sensor (motion, bed, door, etc.)
- `location` (required): Physical location of the sensor
- `resident` (required): Name/ID of the resident
- `timestamp` (required): ISO 8601 timestamp
- `value` (required): Sensor reading value

**What Happens:**
1. Event is validated and stored in MongoDB (`events` collection)
2. Event is published to Kafka topic `wellnest-events`
3. Unique event ID is generated (SHA256 hash)
4. Success response is returned

---

### 4. Trigger Routine Learning

**POST /api/routines/trigger** - Manually trigger routine learning process

```bash
curl -X POST http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/api/routines/trigger
```

**Response:**
```json
{
  "message": "Routine learning completed",
  "status": "success",
  "households_processed": 3,
  "daily_routines_created": 3,
  "baselines_updated": 3
}
```

**What Happens:**
1. Fetches events from the previous day from MongoDB
2. Groups events by `household_id`
3. Extracts routine metrics:
   - Wake-up time (first activity after 4 AM)
   - Bed time (last activity before 4 AM next day)
   - First kitchen activity
   - Bathroom visit count
   - Total activity duration
4. Stores daily routine in `daily_routines` collection
5. Aggregates last 7 days into baseline (`routine_baselines` collection)

**Use Case:**
- Testing routine learning without waiting for scheduled job (1 AM daily)
- Manual routine extraction after bulk data import
- Debugging routine learning logic

---

## 📊 API Documentation

### Interactive API Docs

FastAPI provides automatic interactive API documentation:

**Swagger UI:**
```
http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/docs
```

**ReDoc:**
```
http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/redoc
```

---

## 🔧 Background Services

### Automatic Sensor Simulator

**Status:** Running automatically on startup

**What it does:**
- Simulates realistic sensor data for 3 test households
- Sends events every 10 seconds (configurable)
- Generates motion, bed presence, and door sensor events
- Uses time-based probability (higher activity during day)
- Only sends events on state changes

**Test Households:**
- `household_001` - Smith Family (grandmom, granddad)
- `household_002` - Johnson Family (grandpa)
- `household_003` - Davis Family

**Disable:** Remove or comment out lines 128-131 in `app/main.py`

---

### Scheduled Routine Learner

**Status:** Running via APScheduler

**Schedule:** Daily at 1:00 AM

**What it does:**
- Automatically runs routine learning for previous day
- Creates daily routine profiles
- Updates 7-day baselines
- Logs results

**Manual Trigger:** Use `POST /api/routines/trigger` endpoint

---

## 🗄️ Data Storage

### MongoDB Collections

**1. events**
- Raw sensor events
- Indexed on: `household_id`, `timestamp`, `sensor_id`
- Event ID: SHA256 hash (prevents duplicates)

**2. daily_routines**
- Daily routine profiles per household
- Contains: wake_time, bed_time, kitchen_first_activity, bathroom_visits, etc.
- Indexed on: `household_id`, `date`

**3. routine_baselines**
- 7-day aggregated baselines
- Contains: median, mean, std_dev, min, max for each metric
- Includes data quality scores
- Indexed on: `household_id`

### Kafka Topics

**wellnest-events**
- All sensor events are published here
- Replication factor: 1
- Auto-create: enabled

---

## 🔐 Authentication

**Current Status:** No authentication required

**For Production:**
- Add API key authentication
- Implement OAuth2 / JWT tokens
- Rate limiting
- CORS configuration

---

## 📝 Response Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Successful GET request |
| 201 | Created | Event successfully ingested |
| 400 | Bad Request | Invalid request body or missing fields |
| 422 | Unprocessable Entity | Validation error (Pydantic) |
| 500 | Internal Server Error | Server-side error |

---

## 🧪 Testing Examples

### Test Suite

```bash
# Health check
curl http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/health

# Root endpoint
curl http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/

# Post motion event
curl -X POST http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "household_id": "test_household",
    "sensor_id": "motion_bedroom",
    "sensor_type": "motion",
    "location": "bedroom",
    "resident": "grandpa",
    "timestamp": "2025-10-21T08:30:00Z",
    "value": "true"
  }'

# Post bed sensor event
curl -X POST http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "household_id": "test_household",
    "sensor_id": "bed_bedroom1",
    "sensor_type": "bed",
    "location": "bedroom",
    "resident": "grandpa",
    "timestamp": "2025-10-21T23:00:00Z",
    "value": "occupied"
  }'

# Post door event
curl -X POST http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "household_id": "test_household",
    "sensor_id": "door_entrance",
    "sensor_type": "door",
    "location": "entrance",
    "resident": "grandpa",
    "timestamp": "2025-10-21T10:00:00Z",
    "value": "open"
  }'

# Trigger routine learning
curl -X POST http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/api/routines/trigger
```

---

## 📈 Monitoring

### View Logs

```bash
# API logs
kubectl logs -f -l app=wellnest-api -n wellnest

# Follow specific pod
kubectl logs -f wellnest-api-<pod-id> -n wellnest

# Last 100 lines
kubectl logs --tail=100 -l app=wellnest-api -n wellnest
```

### Check Pod Status

```bash
# All pods
kubectl get pods -n wellnest

# Specific service
kubectl get pods -l app=wellnest-api -n wellnest

# Detailed info
kubectl describe pod <pod-name> -n wellnest
```

---

## 🚀 Future Endpoints (Commented Out)

These endpoints are planned but not yet implemented:

### Batch Event Ingestion
```
POST /api/events/batch
```
Submit multiple events in a single request

### Get Events by Sensor
```
GET /api/events/{sensor_id}
```
Retrieve events for a specific sensor

### Get Routine Baselines
```
GET /api/routines/{household_id}
```
Retrieve routine baselines for a household

### Get Daily Routines
```
GET /api/routines/{household_id}/daily
```
Retrieve daily routine history

### Get Anomalies
```
GET /api/anomalies/{household_id}
```
Retrieve detected routine anomalies

---

## 🔗 Quick Links

- **API Docs (Swagger):** http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/docs
- **API Docs (ReDoc):** http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/redoc
- **Health Check:** http://a30b7dbc301984308a1cf002aea18f36-144205135.us-east-1.elb.amazonaws.com/health
- **MongoDB Atlas:** https://cloud.mongodb.com
- **AWS EKS Console:** https://console.aws.amazon.com/eks/home?region=us-east-1#/clusters/wellnest-cluster
- **AWS ECR:** https://console.aws.amazon.com/ecr/repositories?region=us-east-1

---

## 💡 Tips

1. **Use the interactive docs** at `/docs` for easy testing
2. **Check logs** if events aren't being processed
3. **Monitor MongoDB** to see stored events and routines
4. **Scale the API** if you need more throughput: `kubectl scale deployment wellnest-api -n wellnest --replicas=5`
5. **Set up monitoring** with Prometheus/Grafana for production

---

**Last Updated:** 2025-10-21
**API Version:** 0.1.0
**Deployment:** EKS (wellnest-cluster)
