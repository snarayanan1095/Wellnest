#!/bin/bash

# Script to create Kubernetes secrets from docker-compose.yml environment variables
# This keeps sensitive data secure and out of version control

set -e

echo "Creating Kubernetes secrets for Wellnest..."

# Source .env file if it exists (for NIM_API_KEY and other optional overrides)
if [ -f .env ]; then
    source .env
fi

# Check if NIM_API_KEY is set
if [ -z "${NIM_API_KEY}" ]; then
    echo "Warning: NIM_API_KEY not set. Please set it in .env or export it."
fi

# Use the same values as in docker-compose.yml
MONGODB_USERNAME="shwethanarayanan1095_db_user"
MONGODB_PASSWORD="v474guUVluCMOx8Y"
MONGODB_CLUSTER="cluster0.btmrgvr.mongodb.net"
MONGODB_URL="mongodb+srv://shwethanarayanan1095_db_user:v474guUVluCMOx8Y@cluster0.btmrgvr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DATABASE="wellnest"
REDIS_URL="redis://redis:6379"
QDRANT_URL="https://e449595f-1fe4-4d83-a42b-c510c7fad9f8.us-east-1-1.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.JDXQrogS4zwkkDNjHgZx-6WrgSUO55EY1DaVjyTz_Rc"
VECTOR_DB_TYPE="qdrant"
KAFKA_BOOTSTRAP_SERVERS="kafka:29092"
KAFKA_TOPIC_EVENTS="wellnest-events"
NIM_MODEL_NAME="nvidia/nv-embedqa-e5-v5"

# Create namespace if it doesn't exist
kubectl create namespace wellnest --dry-run=client -o yaml | kubectl apply -f -

# Create the secret (using only variables from docker-compose.yml)
kubectl create secret generic wellnest-secrets \
    --from-literal=MONGODB_USERNAME="${MONGODB_USERNAME}" \
    --from-literal=MONGODB_PASSWORD="${MONGODB_PASSWORD}" \
    --from-literal=MONGODB_CLUSTER="${MONGODB_CLUSTER}" \
    --from-literal=MONGODB_URL="${MONGODB_URL}" \
    --from-literal=MONGODB_DATABASE="${MONGODB_DATABASE}" \
    --from-literal=REDIS_URL="${REDIS_URL}" \
    --from-literal=QDRANT_URL="${QDRANT_URL}" \
    --from-literal=QDRANT_API_KEY="${QDRANT_API_KEY}" \
    --from-literal=VECTOR_DB_TYPE="${VECTOR_DB_TYPE}" \
    --from-literal=KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS}" \
    --from-literal=KAFKA_TOPIC_EVENTS="${KAFKA_TOPIC_EVENTS}" \
    --from-literal=NIM_MODEL_NAME="${NIM_MODEL_NAME}" \
    --from-literal=NIM_API_KEY="${NIM_API_KEY}" \
    --namespace=wellnest \
    --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secrets created successfully!"
echo ""
echo "To verify: kubectl get secrets -n wellnest"
