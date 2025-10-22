#!/bin/bash

# Script to create EKS cluster using eksctl
set -e

CLUSTER_NAME="${CLUSTER_NAME:-wellnest-cluster}"
AWS_REGION="${AWS_REGION:-us-east-1}"
NODE_TYPE="${NODE_TYPE:-t3.medium}"
NODE_COUNT="${NODE_COUNT:-2}"
NODE_MIN="${NODE_MIN:-2}"
NODE_MAX="${NODE_MAX:-4}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Creating EKS cluster: ${CLUSTER_NAME}${NC}"
echo ""
echo "Configuration:"
echo "  Region: ${AWS_REGION}"
echo "  Node Type: ${NODE_TYPE}"
echo "  Node Count: ${NODE_COUNT} (min: ${NODE_MIN}, max: ${NODE_MAX})"
echo ""

# Check if eksctl is installed
if ! command -v eksctl &> /dev/null; then
    echo -e "${YELLOW}⚠️  eksctl not found. Installing...${NC}"
    echo "Please install eksctl: https://eksctl.io/introduction/#installation"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${YELLOW}⚠️  kubectl not found.${NC}"
    echo "Please install kubectl: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Create EKS cluster
eksctl create cluster \
    --name ${CLUSTER_NAME} \
    --region ${AWS_REGION} \
    --nodegroup-name wellnest-nodes \
    --node-type ${NODE_TYPE} \
    --nodes ${NODE_COUNT} \
    --nodes-min ${NODE_MIN} \
    --nodes-max ${NODE_MAX} \
    --managed \
    --with-oidc \
    --ssh-access=false \
    --enable-ssm

echo -e "${GREEN}✅ EKS cluster created successfully!${NC}"
echo ""
echo "To configure kubectl:"
echo "  aws eks update-kubeconfig --name ${CLUSTER_NAME} --region ${AWS_REGION}"
echo ""
echo "To verify:"
echo "  kubectl get nodes"
echo ""
echo "To delete cluster (when done):"
echo "  eksctl delete cluster --name ${CLUSTER_NAME} --region ${AWS_REGION}"
