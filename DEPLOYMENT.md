# Wellnest Dashboard + API Deployment Guide

Complete guide for deploying both the Wellnest API (FastAPI backend) and Dashboard (React frontend) to AWS EKS.

## 📋 What's Included

### Services
1. **Wellnest API** - FastAPI backend (port 8000)
2. **Wellnest Dashboard** - React frontend with nginx (port 80)
3. **Kafka** - Event streaming
4. **Zookeeper** - Kafka coordination
5. **MongoDB Atlas** - External database
6. **Qdrant Cloud** - External vector database

### AWS Resources
- 2 ECR Repositories (`wellnest`, `wellnest-dashboard`)
- 2 LoadBalancers (one for API, one for Dashboard)
- EKS Cluster with 2-4 nodes

---

## 🚀 Quick Start Deployment

### Prerequisites
```bash
# Install required tools
- AWS CLI
- kubectl
- Docker
- eksctl (optional, for cluster creation)
```

### Step 1: Set Environment Variables
```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
```

### Step 2: Build and Push Both Images
```bash
# Build and push API
cd k8s/scripts
./build-and-push.sh

# Build and push Dashboard
./build-and-push-dashboard.sh
```

### Step 3: Deploy to EKS
```bash
# Deploy everything (API + Dashboard + Kafka + Zookeeper)
./deploy-all.sh
```

### Step 4: Get URLs
```bash
# Get API URL
kubectl get svc wellnest-api-service -n wellnest

# Get Dashboard URL
kubectl get svc wellnest-dashboard-service -n wellnest
```

---

## 📦 What Was Created

### 1. Dashboard Dockerfile (`dashboard/Dockerfile`)
Multi-stage build:
- Stage 1: Build React app with Node.js
- Stage 2: Serve with nginx

### 2. Nginx Configuration (`dashboard/nginx.conf`)
- Serves React SPA
- Proxies `/api/*` to API service
- Proxies `/ws/*` for WebSocket connections
- Health check endpoint at `/health`
- Proper cache headers for static assets

### 3. Docker Compose (`docker-compose.yml`)
Added dashboard service:
```yaml
dashboard:
  build: ./dashboard
  ports:
    - "3000:80"
  depends_on:
    - api
```

### 4. Kubernetes Manifests (`k8s/base/dashboard-deployment.yaml`)
- Deployment with 2 replicas
- LoadBalancer service
- Resource limits (128Mi-256Mi RAM, 100m-200m CPU)
- Health checks

### 5. CI/CD Pipeline (`.github/workflows/deploy.yml`)
Updated to build and deploy both services:
- Builds API image → pushes to `wellnest` ECR
- Builds Dashboard image → pushes to `wellnest-dashboard` ECR
- Deploys both to EKS
- Shows both LoadBalancer URLs

### 6. Deployment Scripts
- `k8s/scripts/build-and-push-dashboard.sh` - Build and push dashboard image
- `k8s/scripts/deploy-all.sh` - Updated to deploy dashboard

---

## 🏗️ Architecture

```
┌─────────────────┐
│   CloudWatch    │
└────────┬────────┘
         │
┌────────▼────────────────────────────────┐
│          EKS Cluster                    │
│                                         │
│  ┌────────────────┐  ┌───────────────┐│
│  │   Dashboard    │  │   API         ││
│  │   (nginx)      │  │   (FastAPI)   ││
│  │   Port 80      │  │   Port 8000   ││
│  │   2 replicas   │  │   2 replicas  ││
│  └────────┬───────┘  └───────┬───────┘│
│           │                   │        │
│  ┌────────▼───────────────────▼──────┐│
│  │        LoadBalancers               ││
│  └────────────────────────────────────┘│
│                                         │
│  ┌────────────┐  ┌──────────────────┐ │
│  │   Kafka    │  │   Zookeeper      │ │
│  │ StatefulSet│  │   StatefulSet    │ │
│  └────────────┘  └──────────────────┘ │
└─────────────────────────────────────────┘
           │                   │
           ▼                   ▼
   ┌──────────────┐    ┌─────────────┐
   │MongoDB Atlas │    │Qdrant Cloud │
   └──────────────┘    └─────────────┘
```

---

## 🔌 How Dashboard Connects to API

The dashboard uses **nginx reverse proxy** to connect to the API:

### In Kubernetes:
```nginx
# nginx.conf
location /api/ {
    proxy_pass http://wellnest-api-service.wellnest.svc.cluster.local:80/api/;
}

location /ws/ {
    proxy_pass http://wellnest-api-service.wellnest.svc.cluster.local:80/ws/;
}
```

This means:
- Dashboard users access: `http://dashboard-loadbalancer/api/events`
- Nginx forwards to: `http://wellnest-api-service.wellnest.svc.cluster.local:80/api/events`
- No CORS issues!
- WebSocket connections work seamlessly

---

## 🔄 CI/CD Pipeline Flow

When you push to `main` branch:

1. **Trigger**: Changes to `app/**`, `dashboard/**`, `Dockerfile`, or `k8s/**`
2. **Build API**: `docker build -t wellnest .`
3. **Build Dashboard**: `docker build -t wellnest-dashboard ./dashboard`
4. **Push to ECR**: Both images pushed to separate repositories
5. **Deploy API**: `kubectl set image deployment/wellnest-api ...`
6. **Deploy Dashboard**: `kubectl set image deployment/wellnest-dashboard ...`
7. **Verify**: Check both services are running
8. **Output**: Display LoadBalancer URLs

---

## 💰 Cost Estimation

### AWS Resources:
- **EKS Cluster**: ~$73/month ($0.10/hour)
- **EC2 Nodes** (2x t3.medium): ~$60/month
- **LoadBalancers** (2): ~$32/month ($16 each)
- **ECR Storage**: ~$1/month (minimal)
- **Data Transfer**: Variable

**Total**: ~$166/month

### External Services:
- MongoDB Atlas: Free tier available
- Qdrant Cloud: Free tier available

---

## 📝 Local Development

### Run locally with Docker Compose:
```bash
# Start all services
docker-compose up -d

# Access:
# - API: http://localhost:8000
# - Dashboard: http://localhost:3000
# - API Docs: http://localhost:8000/docs
```

### Run dashboard in dev mode:
```bash
cd dashboard
npm install
npm run dev

# Access: http://localhost:3000
# Hot reload enabled
```

---

## 🔍 Monitoring and Debugging

### Check Pod Status
```bash
kubectl get pods -n wellnest
```

### View Logs
```bash
# API logs
kubectl logs -f -l app=wellnest-api -n wellnest

# Dashboard logs
kubectl logs -f -l app=wellnest-dashboard -n wellnest

# Specific pod
kubectl logs -f <pod-name> -n wellnest
```

### Check Services
```bash
kubectl get svc -n wellnest
```

### Exec into Pod
```bash
# API
kubectl exec -it deployment/wellnest-api -n wellnest -- /bin/bash

# Dashboard
kubectl exec -it deployment/wellnest-dashboard -n wellnest -- /bin/sh
```

### Test Dashboard Health
```bash
DASHBOARD_URL=$(kubectl get svc wellnest-dashboard-service -n wellnest -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$DASHBOARD_URL/health
```

---

## 🛠️ Common Issues and Fixes

### Dashboard shows "Cannot connect to API"
**Fix**: Check if API service is running:
```bash
kubectl get svc wellnest-api-service -n wellnest
kubectl get pods -l app=wellnest-api -n wellnest
```

### LoadBalancer stuck in "Pending"
**Fix**: Check AWS Load Balancer Controller:
```bash
kubectl get pods -n kube-system | grep aws-load-balancer
```

### Dashboard deployment fails
**Fix**: Check if ECR image exists:
```bash
aws ecr describe-images --repository-name wellnest-dashboard --region us-east-1
```

### WebSocket connection fails
**Fix**: Ensure nginx config has proper WebSocket headers:
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

---

## 🚦 Scaling

### Scale API
```bash
kubectl scale deployment wellnest-api -n wellnest --replicas=3
```

### Scale Dashboard
```bash
kubectl scale deployment wellnest-dashboard -n wellnest --replicas=3
```

### Auto-scaling
```bash
# Enable HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment wellnest-api -n wellnest --cpu-percent=70 --min=2 --max=10
kubectl autoscale deployment wellnest-dashboard -n wellnest --cpu-percent=70 --min=2 --max=5
```

---

## 🧹 Cleanup

### Delete deployments
```bash
kubectl delete namespace wellnest
```

### Delete ECR repositories
```bash
aws ecr delete-repository --repository-name wellnest --region us-east-1 --force
aws ecr delete-repository --repository-name wellnest-dashboard --region us-east-1 --force
```

### Delete EKS cluster
```bash
eksctl delete cluster --name wellnest-cluster --region us-east-1
```

---

## 📚 File Structure

```
Wellnest/
├── dashboard/
│   ├── Dockerfile                    # Multi-stage build
│   ├── nginx.conf                    # Nginx configuration
│   ├── src/                          # React source
│   └── package.json
├── k8s/
│   ├── base/
│   │   ├── dashboard-deployment.yaml # Dashboard K8s manifest
│   │   ├── wellnest-deployment.yaml  # API K8s manifest
│   │   └── ...
│   └── scripts/
│       ├── build-and-push.sh         # Build API image
│       ├── build-and-push-dashboard.sh # Build Dashboard image
│       └── deploy-all.sh             # Deploy everything
├── .github/
│   └── workflows/
│       └── deploy.yml                # CI/CD pipeline
├── docker-compose.yml                # Local development
└── DEPLOYMENT.md                     # This file
```

---

## ✅ Checklist

Before deploying:
- [ ] AWS CLI configured
- [ ] kubectl installed and configured
- [ ] ECR repositories created
- [ ] MongoDB Atlas accessible
- [ ] Qdrant Cloud accessible
- [ ] Secrets configured in K8s
- [ ] EKS cluster running

After deploying:
- [ ] Both pods are running
- [ ] Both LoadBalancers have external IPs
- [ ] Dashboard loads in browser
- [ ] Dashboard can connect to API
- [ ] WebSocket connection works
- [ ] Health checks pass

---

## 🎯 Next Steps

1. **Custom Domain**: Set up Route53 + SSL certificates
2. **CloudFront**: Add CDN for dashboard
3. **Monitoring**: Set up Prometheus + Grafana
4. **Alerts**: Configure CloudWatch alarms
5. **Backups**: Set up automated backups
6. **Security**: Enable Pod Security Standards

---

**Questions?** Check the K8s README or API documentation!
