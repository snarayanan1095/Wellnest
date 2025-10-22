#!/bin/bash

# Script to verify Wellnest deployment health
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Verifying Wellnest Deployment${NC}"
echo ""

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ kubectl is not configured or cluster is unreachable${NC}"
    exit 1
fi

echo -e "${GREEN}✅ kubectl is configured${NC}"

# Check namespace
if kubectl get namespace wellnest &> /dev/null; then
    echo -e "${GREEN}✅ Namespace 'wellnest' exists${NC}"
else
    echo -e "${RED}❌ Namespace 'wellnest' not found${NC}"
    exit 1
fi

# Check secrets
echo ""
echo -e "${BLUE}Checking Secrets...${NC}"
if kubectl get secret wellnest-secrets -n wellnest &> /dev/null; then
    echo -e "${GREEN}✅ Secrets exist${NC}"
else
    echo -e "${RED}❌ Secrets not found${NC}"
fi

# Check ConfigMap
echo ""
echo -e "${BLUE}Checking ConfigMap...${NC}"
if kubectl get configmap wellnest-config -n wellnest &> /dev/null; then
    echo -e "${GREEN}✅ ConfigMap exists${NC}"
else
    echo -e "${RED}❌ ConfigMap not found${NC}"
fi

# Check pods
echo ""
echo -e "${BLUE}Checking Pods...${NC}"
kubectl get pods -n wellnest

# Check pod status
ZOOKEEPER_STATUS=$(kubectl get pods -l app=zookeeper -n wellnest -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")
KAFKA_STATUS=$(kubectl get pods -l app=kafka -n wellnest -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")
API_STATUS=$(kubectl get pods -l app=wellnest-api -n wellnest -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")

echo ""
if [ "$ZOOKEEPER_STATUS" = "Running" ]; then
    echo -e "${GREEN}✅ Zookeeper is running${NC}"
else
    echo -e "${RED}❌ Zookeeper is $ZOOKEEPER_STATUS${NC}"
fi

if [ "$KAFKA_STATUS" = "Running" ]; then
    echo -e "${GREEN}✅ Kafka is running${NC}"
else
    echo -e "${RED}❌ Kafka is $KAFKA_STATUS${NC}"
fi

if [ "$API_STATUS" = "Running" ]; then
    echo -e "${GREEN}✅ API is running${NC}"
else
    echo -e "${RED}❌ API is $API_STATUS${NC}"
fi

# Check services
echo ""
echo -e "${BLUE}Checking Services...${NC}"
kubectl get svc -n wellnest

# Get external URL
echo ""
EXTERNAL_URL=$(kubectl get svc wellnest-api-service -n wellnest -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)

if [ -z "$EXTERNAL_URL" ]; then
    echo -e "${YELLOW}⚠️  LoadBalancer URL not yet available (may still be provisioning)${NC}"
else
    echo -e "${GREEN}✅ LoadBalancer URL: http://${EXTERNAL_URL}${NC}"

    # Test health endpoint
    echo ""
    echo -e "${BLUE}Testing health endpoint...${NC}"
    if curl -f -s "http://${EXTERNAL_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed!${NC}"
        HEALTH_RESPONSE=$(curl -s "http://${EXTERNAL_URL}/health")
        echo "Response: $HEALTH_RESPONSE"
    else
        echo -e "${YELLOW}⚠️  Health endpoint not reachable yet${NC}"
    fi
fi

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Count running pods
RUNNING_PODS=$(kubectl get pods -n wellnest --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')
TOTAL_PODS=$(kubectl get pods -n wellnest --no-headers 2>/dev/null | wc -l | tr -d ' ')

echo "Pods: $RUNNING_PODS/$TOTAL_PODS running"

if [ "$RUNNING_PODS" = "$TOTAL_PODS" ] && [ "$RUNNING_PODS" -gt 0 ]; then
    echo -e "${GREEN}✅ All pods are healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Some pods may not be ready yet${NC}"
fi

echo ""
echo "To view logs:"
echo "  kubectl logs -f -l app=wellnest-api -n wellnest"
echo ""
echo "To check events:"
echo "  kubectl get events -n wellnest --sort-by='.lastTimestamp'"
