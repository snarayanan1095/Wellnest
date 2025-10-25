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
    --from-literal=MONGODB_URL="${MONGODB_URL}" \
    --namespace=wellnest \
    --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secrets created successfully!"
echo ""
echo "To verify: kubectl get secrets -n wellnest"
