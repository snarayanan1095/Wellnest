# Wellnest Deployment - Quick Reference

## 🚀 Deploy to AWS EKS

```bash
# 1. Set variables
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1

# 2. Build and push images
cd k8s/scripts
./build-and-push.sh              # API
./build-and-push-dashboard.sh    # Dashboard

# 3. Deploy everything
./deploy-all.sh

# 4. Get URLs
kubectl get svc -n wellnest
```

## 🏠 Run Locally

```bash
# With Docker Compose
docker-compose up -d

# Dashboard dev mode
cd dashboard && npm run dev
```

## 📦 What Was Integrated

### New Files Created
- `dashboard/Dockerfile` - Multi-stage build (Node.js → nginx)
- `dashboard/nginx.conf` - Reverse proxy config
- `k8s/base/dashboard-deployment.yaml` - K8s manifest
- `k8s/scripts/build-and-push-dashboard.sh` - Build script
- `DEPLOYMENT.md` - Complete guide

### Files Modified
- `docker-compose.yml` - Added dashboard service
- `.github/workflows/deploy.yml` - Build & deploy both services
- `k8s/scripts/deploy-all.sh` - Deploy both services

## 🔌 How It Works

```
User → Dashboard LoadBalancer (port 80)
         ↓ nginx reverse proxy
         → API Service (internal, port 80)
            → API Pods (port 8000)
```

**No CORS issues!** Dashboard proxies all `/api/*` and `/ws/*` requests to API.

## 📊 Resources

| Service | Image | Replicas | Resources | Port |
|---------|-------|----------|-----------|------|
| API | `wellnest:latest` | 2 | 512Mi-1Gi, 250m-1000m | 8000 |
| Dashboard | `wellnest-dashboard:latest` | 2 | 128Mi-256Mi, 100m-200m | 80 |
| Kafka | StatefulSet | 1 | - | 9092 |
| Zookeeper | StatefulSet | 1 | - | 2181 |

## 🔍 Debugging

```bash
# Check status
kubectl get pods -n wellnest
kubectl get svc -n wellnest

# View logs
kubectl logs -f -l app=wellnest-api -n wellnest
kubectl logs -f -l app=wellnest-dashboard -n wellnest

# Test health
DASH_URL=$(kubectl get svc wellnest-dashboard-service -n wellnest -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$DASH_URL/health

# Exec into pod
kubectl exec -it deployment/wellnest-dashboard -n wellnest -- /bin/sh
```

## 💰 Cost

~$166/month for AWS resources (EKS + EC2 + LoadBalancers)

## 🧹 Cleanup

```bash
# Delete namespace
kubectl delete namespace wellnest

# Delete ECR repos
aws ecr delete-repository --repository-name wellnest --force
aws ecr delete-repository --repository-name wellnest-dashboard --force

# Delete cluster
eksctl delete cluster --name wellnest-cluster
```

## 📋 Checklist

### Before Deploy
- [ ] AWS CLI configured
- [ ] Docker running
- [ ] kubectl configured
- [ ] EKS cluster exists
- [ ] MongoDB Atlas accessible

### After Deploy
- [ ] Pods running: `kubectl get pods -n wellnest`
- [ ] Services have external IPs: `kubectl get svc -n wellnest`
- [ ] Dashboard loads in browser
- [ ] Dashboard connects to API

## 🔗 URLs

After deployment, get URLs:
```bash
# API
kubectl get svc wellnest-api-service -n wellnest -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Dashboard
kubectl get svc wellnest-dashboard-service -n wellnest -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

---

**Full guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
