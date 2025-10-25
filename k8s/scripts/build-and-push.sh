#!/bin/bash

# Script to build Docker image and push to Amazon ECR
set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
ECR_REPOSITORY="wellnest"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Building and pushing Wellnest to ECR...${NC}"

# Check if AWS_ACCOUNT_ID is set
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: AWS_ACCOUNT_ID environment variable is not set"
    echo "Usage: AWS_ACCOUNT_ID=123456789012 AWS_REGION=us-east-1 ./build-and-push.sh"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/../.."

# Step 1: Create ECR repository if it doesn't exist
echo -e "${BLUE}📦 Creating ECR repository...${NC}"
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} 2>/dev/null || \
    aws ecr create-repository \
        --repository-name ${ECR_REPOSITORY} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true

# Step 2: Authenticate Docker to ECR
echo -e "${BLUE}🔐 Authenticating Docker to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Step 3: Build Docker image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} .

# Step 4: Tag image for ECR
echo -e "${BLUE}🏷️  Tagging image...${NC}"
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}

# Step 5: Push to ECR
echo -e "${BLUE}⬆️  Pushing to ECR...${NC}"
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}

echo -e "${GREEN}✅ Successfully built and pushed image!${NC}"
echo ""
echo "Image URI: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
