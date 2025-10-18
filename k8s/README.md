# Wellnest EKS Deployment Guide

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **kubectl** installed
3. **Docker** installed and running
4. **EKS cluster** created in your AWS account
5. **MongoDB Atlas** (or external MongoDB) with connection string

## Quick Start

### 1. Update Configuration

**Update MongoDB connection in `k8s/secret.yaml`:**
```yaml
stringData:
  MONGODB_URL: "mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/..."
```

**Update environment variables (optional) in `deploy.sh`:**
```bash
export ECR_REGISTRY="123456789.dkr.ecr.us-east-1.amazonaws.com"
export IMAGE_NAME="wellnest-backend"
export IMAGE_TAG="latest"
export AWS_REGION="us-east-1"
export CLUSTER_NAME="wellnest-cluster"
```

### 2. Deploy

```bash
cd k8s
./deploy.sh
```

The script will:
- Build Docker image
- Push to ECR
- Deploy to EKS cluster
- Create LoadBalancer service

### 3. Get External URL

```bash
kubectl get service wellnest-backend
```

Wait for `EXTERNAL-IP` to be assigned (may take 2-3 minutes).

## Manual Deployment Steps

If you prefer manual deployment:

### 1. Build and Push Image

```bash
# Build
docker build -t wellnest-backend:latest .

# Tag for ECR
docker tag wellnest-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/wellnest-backend:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Push
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/wellnest-backend:latest
```

### 2. Update Deployment Manifest

Edit `k8s/deployment.yaml` and replace:
```yaml
image: YOUR_ECR_REGISTRY/wellnest-backend:latest
```

### 3. Apply Manifests

```bash
# Update kubeconfig
aws eks update-kubeconfig --name wellnest-cluster --region us-east-1

# Apply in order
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Useful Commands

### View Resources
```bash
# Get all resources
kubectl get all -l app=wellnest

# Get pods
kubectl get pods -l app=wellnest

# Get service details
kubectl get service wellnest-backend

# Get external URL
kubectl get service wellnest-backend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### Debugging
```bash
# View logs
kubectl logs -f deployment/wellnest-backend

# View logs for specific pod
kubectl logs -f <pod-name>

# Exec into pod
kubectl exec -it <pod-name> -- /bin/bash

# Describe pod (check events)
kubectl describe pod <pod-name>

# Check deployment status
kubectl rollout status deployment/wellnest-backend
```

### Updates
```bash
# Update image
kubectl set image deployment/wellnest-backend wellnest-api=123456789.dkr.ecr.us-east-1.amazonaws.com/wellnest-backend:v2

# Restart deployment
kubectl rollout restart deployment/wellnest-backend

# Scale deployment
kubectl scale deployment/wellnest-backend --replicas=3
```

### Cleanup
```bash
# Delete all resources
kubectl delete -f k8s/

# Or delete individually
kubectl delete deployment wellnest-backend
kubectl delete service wellnest-backend
kubectl delete configmap wellnest-config
kubectl delete secret wellnest-secrets
```

## Architecture

```
┌─────────────────────────────────────┐
│         LoadBalancer (ELB)          │
│              Port 80                │
└────────────┬────────────────────────┘
             │
             │
┌────────────▼────────────────────────┐
│      Kubernetes Service             │
│    wellnest-backend:80              │
└────────────┬────────────────────────┘
             │
             │
┌────────────▼────────────────────────┐
│       Pod (wellnest-api)            │
│   FastAPI + Simulator (Port 8000)  │
│                                     │
│   Environment:                      │
│   - MONGODB_URL (from Secret)       │
│   - MONGODB_DATABASE (from ConfigMap│
└────────────┬────────────────────────┘
             │
             │
┌────────────▼────────────────────────┐
│    MongoDB Atlas (External)         │
└─────────────────────────────────────┘
```

## Configuration Details

### ConfigMap (`configmap.yaml`)
- Non-sensitive configuration
- Database name, app settings

### Secret (`secret.yaml`)
- **Sensitive data** (MongoDB URL, API keys)
- **WARNING**: Never commit actual secrets to git!
- In production, use AWS Secrets Manager or External Secrets Operator

### Deployment (`deployment.yaml`)
- 1 replica (scale as needed)
- Health checks on `/health` endpoint
- Resource limits: 256Mi-512Mi RAM, 250m-500m CPU
- Security context enabled

### Service (`service.yaml`)
- Type: LoadBalancer (external access)
- Maps port 80 → 8000

## Security Best Practices

1. **Never commit secrets**: Use AWS Secrets Manager
2. **Use HTTPS**: Add Ingress with TLS/SSL certificate
3. **Network policies**: Restrict pod-to-pod communication
4. **RBAC**: Use service accounts with minimal permissions
5. **Image scanning**: Enable ECR vulnerability scanning

## Production Considerations

1. **Scaling**: Increase replicas in `deployment.yaml`
2. **Monitoring**: Add Prometheus/Grafana
3. **Logging**: Configure CloudWatch Container Insights
4. **Ingress**: Use ALB Ingress Controller instead of LoadBalancer
5. **Auto-scaling**: Add Horizontal Pod Autoscaler (HPA)
6. **CI/CD**: Integrate with GitHub Actions or AWS CodePipeline

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Can't connect to MongoDB
- Check secret is applied: `kubectl get secret wellnest-secrets`
- Verify connection string format
- Check MongoDB Atlas IP whitelist (allow 0.0.0.0/0 or EKS node IPs)

### LoadBalancer stuck in pending
- Check AWS service limits
- Verify EKS cluster has proper IAM roles
- Check subnet configuration

## Cost Optimization

- Use spot instances for non-critical workloads
- Scale down replicas during low traffic
- Use Fargate for serverless pods (if applicable)
- Monitor ECR storage costs
