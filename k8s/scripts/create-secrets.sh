#!/bin/bash

# Script to create Kubernetes secrets from .env file
# This keeps sensitive data secure and out of version control

set -e

echo "Creating Kubernetes secrets for Wellnest..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with MongoDB credentials"
    exit 1
fi

# Source the .env file
source .env

# Create namespace if it doesn't exist
kubectl create namespace wellnest --dry-run=client -o yaml | kubectl apply -f -

# Create the secret
kubectl create secret generic wellnest-secrets \
    --from-literal=MONGODB_USERNAME="${MONGODB_USERNAME}" \
    --from-literal=MONGODB_PASSWORD="${MONGODB_PASSWORD}" \
    --from-literal=MONGODB_CLUSTER="${MONGODB_CLUSTER}" \
    --from-literal=MONGODB_DATABASE="${MONGODB_DATABASE}" \
    --from-literal=MONGODB_URL="${MONGODB_URL}" \
    --from-literal=REDIS_URL="${REDIS_URL}" \
    --from-literal=VECTOR_DB_TYPE="${VECTOR_DB_TYPE}" \
    --from-literal=QDRANT_URL="${QDRANT_URL}" \
    --from-literal=QDRANT_API_KEY="${QDRANT_API_KEY}" \
    --from-literal=NIM_MODEL_NAME="${NIM_MODEL_NAME}" \
    --from-literal=NIM_API_KEY="${NIM_API_KEY}" \
    --from-literal=LOG_LEVEL="${LOG_LEVEL}" \
    --from-literal=USE_JSON_LOGGING="${USE_JSON_LOGGING}" \
    --from-literal=API_HOST="${API_HOST}" \
    --from-literal=API_PORT="${API_PORT}" \
    --from-literal=KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS}" \
    --from-literal=KAFKA_TOPIC_EVENTS="${KAFKA_TOPIC_EVENTS}" \
    --from-literal=KAFKA_BROKER_ID="${KAFKA_BROKER_ID}" \
    --from-literal=KAFKA_ZOOKEEPER_CONNECT="${KAFKA_ZOOKEEPER_CONNECT}" \
    --from-literal=KAFKA_LISTENER_SECURITY_PROTOCOL_MAP="${KAFKA_LISTENER_SECURITY_PROTOCOL_MAP}" \
    --from-literal=KAFKA_ADVERTISED_LISTENERS="${KAFKA_ADVERTISED_LISTENERS}" \
    --from-literal=KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR="${KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR}" \
    --from-literal=KAFKA_TRANSACTION_STATE_LOG_MIN_ISR="${KAFKA_TRANSACTION_STATE_LOG_MIN_ISR}" \
    --from-literal=KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR="${KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR}" \
    --from-literal=KAFKA_AUTO_CREATE_TOPICS_ENABLE="${KAFKA_AUTO_CREATE_TOPICS_ENABLE}" \
    --namespace=wellnest \
    --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secrets created successfully!"
echo ""
echo "To verify: kubectl get secrets -n wellnest"
