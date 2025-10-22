#!/bin/bash

# Script to teardown Wellnest deployment
set -e

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  This will delete all Wellnest resources from Kubernetes${NC}"
echo ""
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo -e "${RED}🗑️  Deleting Wellnest namespace and all resources...${NC}"

kubectl delete namespace wellnest

echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo ""
echo "Note: This does NOT delete:"
echo "  - EKS cluster (use: eksctl delete cluster --name wellnest-cluster)"
echo "  - ECR repository (use: aws ecr delete-repository --repository-name wellnest --force)"
echo "  - MongoDB Atlas data"
