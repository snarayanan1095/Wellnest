#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
ECR_REGISTRY="${ECR_REGISTRY:-YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com}"
IMAGE_NAME="${IMAGE_NAME:-wellnest-backend}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="${CLUSTER_NAME:-wellnest-cluster}"

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   Wellnest EKS Deployment Script${NC}"
echo -e "${BLUE}==================================================${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"
for cmd in docker aws kubectl; do
    if ! command_exists "$cmd"; then
        echo -e "${RED}Error: $cmd is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ $cmd found${NC}"
done

# Step 1: Build Docker image
echo -e "\n${BLUE}Step 1: Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
echo -e "${GREEN}✓ Docker image built successfully${NC}"

# Step 2: Tag image for ECR
echo -e "\n${BLUE}Step 2: Tagging image for ECR...${NC}"
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
echo -e "${GREEN}✓ Image tagged${NC}"

# Step 3: Login to ECR
echo -e "\n${BLUE}Step 3: Logging into ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
echo -e "${GREEN}✓ Logged into ECR${NC}"

# Step 4: Create ECR repository if it doesn't exist
echo -e "\n${BLUE}Step 4: Checking ECR repository...${NC}"
if ! aws ecr describe-repositories --repository-names ${IMAGE_NAME} --region ${AWS_REGION} >/dev/null 2>&1; then
    echo "Creating ECR repository..."
    aws ecr create-repository --repository-name ${IMAGE_NAME} --region ${AWS_REGION}
    echo -e "${GREEN}✓ ECR repository created${NC}"
else
    echo -e "${GREEN}✓ ECR repository exists${NC}"
fi

# Step 5: Push image to ECR
echo -e "\n${BLUE}Step 5: Pushing image to ECR...${NC}"
docker push ${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
echo -e "${GREEN}✓ Image pushed to ECR${NC}"

# Step 6: Update kubeconfig
echo -e "\n${BLUE}Step 6: Updating kubeconfig for EKS...${NC}"
aws eks update-kubeconfig --name ${CLUSTER_NAME} --region ${AWS_REGION}
echo -e "${GREEN}✓ Kubeconfig updated${NC}"

# Step 7: Update deployment.yaml with ECR image URL
echo -e "\n${BLUE}Step 7: Updating deployment manifest...${NC}"
sed -i.bak "s|YOUR_ECR_REGISTRY/wellnest-backend:latest|${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/deployment.yaml
echo -e "${GREEN}✓ Deployment manifest updated${NC}"

# Step 8: Apply Kubernetes manifests
echo -e "\n${BLUE}Step 8: Deploying to Kubernetes...${NC}"

# Apply ConfigMap
kubectl apply -f k8s/configmap.yaml
echo -e "${GREEN}✓ ConfigMap applied${NC}"

# Apply Secret (warn user to update it first)
echo -e "${YELLOW}⚠ Make sure you've updated k8s/secret.yaml with your MongoDB URL!${NC}"
read -p "Press enter to continue or Ctrl+C to abort..."
kubectl apply -f k8s/secret.yaml
echo -e "${GREEN}✓ Secret applied${NC}"

# Apply Deployment
kubectl apply -f k8s/deployment.yaml
echo -e "${GREEN}✓ Deployment applied${NC}"

# Apply Service
kubectl apply -f k8s/service.yaml
echo -e "${GREEN}✓ Service applied${NC}"

# Step 9: Wait for deployment
echo -e "\n${BLUE}Step 9: Waiting for deployment to be ready...${NC}"
kubectl rollout status deployment/wellnest-backend --timeout=300s
echo -e "${GREEN}✓ Deployment is ready${NC}"

# Step 10: Get service info
echo -e "\n${BLUE}Step 10: Getting service information...${NC}"
kubectl get service wellnest-backend

echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}   Deployment Complete! 🎉${NC}"
echo -e "${GREEN}==================================================${NC}"

echo -e "\n${YELLOW}To get the LoadBalancer URL, run:${NC}"
echo -e "  kubectl get service wellnest-backend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'\n"

echo -e "${YELLOW}To view logs:${NC}"
echo -e "  kubectl logs -f deployment/wellnest-backend\n"

echo -e "${YELLOW}To check pod status:${NC}"
echo -e "  kubectl get pods -l app=wellnest\n"
