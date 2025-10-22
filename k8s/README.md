# Wellnest EKS Deployment Guide

Complete guide to deploy Wellnest application to Amazon EKS (Elastic Kubernetes Service).

## 📋 Prerequisites

Before starting, ensure you have:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
   ```bash
   aws configure
   ```
3. **Docker** installed locally
4. **kubectl** installed
5. **eksctl** installed (for EKS cluster creation)
6. **MongoDB Atlas** cluster configured (already have this)

## 🏗️ Architecture Overview

The deployment consists of:

- **Wellnest API** (2 replicas) - FastAPI application
- **Kafka** (StatefulSet) - Message queue for events
- **Zookeeper** (StatefulSet) - Kafka coordination service
- **MongoDB Atlas** - External managed database
- **LoadBalancer** - External access to API

## 🚀 Step-by-Step Deployment

### Step 1: Set Environment Variables

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1  # Change to your preferred region
```

### Step 2: Create EKS Cluster

Choose one of the following methods:

#### Option A: Using eksctl (Recommended for beginners)

```bash
cd k8s/scripts
chmod +x create-eks-cluster.sh
./create-eks-cluster.sh
```

This creates a cluster with:
- Name: `wellnest-cluster`
- Region: `us-east-1` (configurable)
- Node type: `t3.medium`
- Node count: 2-4 (auto-scaling)

#### Option B: Using existing EKS cluster

If you already have a cluster:
```bash
aws eks update-kubeconfig --name YOUR_CLUSTER_NAME --region YOUR_REGION
```

### Step 3: Verify Cluster Connection

```bash
kubectl get nodes
```

You should see 2+ nodes in `Ready` state.

### Step 4: Configure MongoDB Atlas Network Access

1. Go to MongoDB Atlas Console
2. Navigate to Network Access
3. Add your EKS cluster's IP range or use `0.0.0.0/0` (not recommended for production)
4. Save changes

### Step 5: Build and Push Docker Image to ECR

```bash
cd k8s/scripts
chmod +x build-and-push.sh

# Build and push
AWS_ACCOUNT_ID=YOUR_ACCOUNT_ID AWS_REGION=us-east-1 ./build-and-push.sh
```

This script will:
- Create ECR repository
- Build Docker image
- Push to Amazon ECR

### Step 6: Create Kubernetes Secrets

```bash
cd k8s/scripts
chmod +x create-secrets.sh
./create-secrets.sh
```

This reads your `.env` file and creates Kubernetes secrets for MongoDB credentials.

### Step 7: Deploy All Services

```bash
cd k8s/scripts
chmod +x deploy-all.sh

AWS_ACCOUNT_ID=YOUR_ACCOUNT_ID AWS_REGION=us-east-1 ./deploy-all.sh
```

This script deploys in order:
1. Namespace
2. Secrets
3. ConfigMap
4. Zookeeper
5. Kafka
6. Wellnest API

### Step 8: Get External URL

Wait for LoadBalancer to provision (2-3 minutes):

```bash
kubectl get svc wellnest-api-service -n wellnest -w
```

Get the external URL:
```bash
EXTERNAL_URL=$(kubectl get svc wellnest-api-service -n wellnest -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Wellnest API: http://${EXTERNAL_URL}"
```

### Step 9: Test the Deployment

```bash
# Test health endpoint
curl http://${EXTERNAL_URL}/health

# Test root endpoint
curl http://${EXTERNAL_URL}/

# Send a test event
curl -X POST http://${EXTERNAL_URL}/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "household_id": "household_001",
    "sensor_id": "motion_bedroom1",
    "sensor_type": "motion",
    "timestamp": "2025-10-21T10:00:00Z",
    "value": "true"
  }'
```

## 📊 Monitoring and Management

### View Logs

```bash
# API logs
kubectl logs -f -l app=wellnest-api -n wellnest

# Kafka logs
kubectl logs -f kafka-0 -n wellnest

# Zookeeper logs
kubectl logs -f zookeeper-0 -n wellnest
```

### Check Pod Status

```bash
kubectl get pods -n wellnest
```

### Scale the API

```bash
kubectl scale deployment wellnest-api -n wellnest --replicas=3
```

### View Events

```bash
kubectl get events -n wellnest --sort-by='.lastTimestamp'
```

### Access Pod Shell

```bash
kubectl exec -it deployment/wellnest-api -n wellnest -- /bin/bash
```

## 🔧 Troubleshooting

### Pods not starting

```bash
# Check pod details
kubectl describe pod <pod-name> -n wellnest

# Check logs
kubectl logs <pod-name> -n wellnest
```

### MongoDB connection issues

1. Verify secrets are created:
   ```bash
   kubectl get secrets -n wellnest
   kubectl describe secret wellnest-secrets -n wellnest
   ```

2. Check MongoDB Atlas network access allows EKS cluster

3. Test connection from pod:
   ```bash
   kubectl exec -it deployment/wellnest-api -n wellnest -- python -c "from app.db.mongo import get_database; import asyncio; asyncio.run(get_database())"
   ```

### Kafka connection issues

```bash
# Check if Kafka is ready
kubectl get pods -l app=kafka -n wellnest

# Test Kafka from API pod
kubectl exec -it deployment/wellnest-api -n wellnest -- \
  python -c "from kafka import KafkaProducer; KafkaProducer(bootstrap_servers='kafka-service:9092')"
```

### LoadBalancer stuck in pending

```bash
# Check service events
kubectl describe svc wellnest-api-service -n wellnest

# Verify AWS Load Balancer Controller is installed
kubectl get pods -n kube-system | grep aws-load-balancer
```

## 🧹 Cleanup

### Delete Wellnest deployment

```bash
kubectl delete namespace wellnest
```

### Delete EKS cluster

```bash
eksctl delete cluster --name wellnest-cluster --region us-east-1
```

This will delete all resources including:
- EKS cluster
- Worker nodes
- VPC
- Load balancers
- EBS volumes

### Delete ECR repository

```bash
aws ecr delete-repository --repository-name wellnest --region us-east-1 --force
```

## 📈 Production Recommendations

### 1. High Availability

- Increase Kafka replicas to 3
- Increase Zookeeper replicas to 3
- Use multiple availability zones
- Set pod anti-affinity rules

### 2. Resource Optimization

```yaml
# Adjust in wellnest-deployment.yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1500m"
```

### 3. Security

- Use AWS Secrets Manager instead of K8s secrets
- Enable Pod Security Standards
- Use IAM roles for service accounts (IRSA)
- Configure network policies
- Enable encryption at rest
- Use private subnets for worker nodes

### 4. Monitoring

Install monitoring stack:

```bash
# Prometheus + Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# CloudWatch Container Insights
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml
```

### 5. Autoscaling

```bash
# Horizontal Pod Autoscaler
kubectl autoscale deployment wellnest-api -n wellnest --cpu-percent=70 --min=2 --max=10

# Cluster Autoscaler (already enabled with eksctl)
```

### 6. Ingress Controller

For production, use AWS Application Load Balancer:

```bash
# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=wellnest-cluster
```

Then replace LoadBalancer service with Ingress.

### 7. Backup Strategy

- Enable EBS snapshots for persistent volumes
- Schedule MongoDB Atlas backups
- Store Kafka data with replication factor 3

### 8. CI/CD Integration

```bash
# Example GitHub Actions workflow structure
# .github/workflows/deploy.yml
# - Build Docker image
# - Push to ECR
# - Update K8s deployment
# - Run health checks
```

## 🔍 Cost Optimization

- Use Spot instances for non-critical workloads
- Right-size EC2 instances based on actual usage
- Enable cluster autoscaler
- Set pod resource requests/limits accurately
- Use AWS Savings Plans for predictable workloads

## 📚 Additional Resources

- [Amazon EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [eksctl Documentation](https://eksctl.io/)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)

## 🆘 Support

For issues with:
- **Wellnest application**: Check application logs
- **Kubernetes**: `kubectl describe` and `kubectl logs`
- **AWS resources**: CloudFormation console for eksctl stacks
- **MongoDB**: MongoDB Atlas console logs

---

**Note**: This deployment uses development-grade configurations. For production, implement all security and high-availability recommendations above.
