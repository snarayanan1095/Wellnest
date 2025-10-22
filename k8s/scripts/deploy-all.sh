#!/bin/bash

# Complete deployment script for Wellnest on EKS
set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying Wellnest to EKS...${NC}"

# Check prerequisites
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: AWS_ACCOUNT_ID is required"
    exit 1
fi

# Navigate to k8s directory
cd "$(dirname "$0")/.."

# Step 1: Create namespace
echo -e "${BLUE}📦 Creating namespace...${NC}"
kubectl apply -f base/namespace.yaml

# Step 2: Create secrets
echo -e "${BLUE}🔐 Creating secrets...${NC}"
../scripts/create-secrets.sh

# Step 3: Create ConfigMap
echo -e "${BLUE}⚙️  Creating ConfigMap...${NC}"
kubectl apply -f base/configmap.yaml

# Step 4: Deploy Zookeeper
echo -e "${BLUE}🐘 Deploying Zookeeper...${NC}"
kubectl apply -f base/zookeeper-statefulset.yaml
echo "Waiting for Zookeeper to be ready..."
kubectl wait --for=condition=ready pod -l app=zookeeper -n wellnest --timeout=300s

# Step 5: Deploy Kafka
echo -e "${BLUE}📨 Deploying Kafka...${NC}"
kubectl apply -f base/kafka-statefulset.yaml
echo "Waiting for Kafka to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka -n wellnest --timeout=300s

# Step 6: Update deployment with ECR image
echo -e "${BLUE}📝 Updating deployment manifest with ECR image...${NC}"
sed "s/\${AWS_ACCOUNT_ID}/${AWS_ACCOUNT_ID}/g; s/\${AWS_REGION}/${AWS_REGION}/g" \
    base/wellnest-deployment.yaml | kubectl apply -f -

# Step 7: Wait for deployment
echo -e "${BLUE}⏳ Waiting for Wellnest API to be ready...${NC}"
kubectl wait --for=condition=available deployment/wellnest-api -n wellnest --timeout=300s

# Step 8: Get service URL
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${YELLOW}Getting service information...${NC}"
kubectl get svc wellnest-api-service -n wellnest

echo ""
echo "To get the external URL, run:"
echo "  kubectl get svc wellnest-api-service -n wellnest -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"
echo ""
echo "To view logs:"
echo "  kubectl logs -f -l app=wellnest-api -n wellnest"
echo ""
echo "To check pod status:"
echo "  kubectl get pods -n wellnest"
