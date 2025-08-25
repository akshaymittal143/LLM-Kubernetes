#!/bin/bash
# Optimized LLM Deployment Script
# This script deploys the optimized LLM configuration with vLLM and all optimizations

set -e

echo "=== Deploying Optimized LLM Configuration ==="

# Configuration
NAMESPACE="llm-test"
OPTIMIZED_LABEL="app=llm-optimized"

# Create namespace if it doesn't exist
echo "Creating namespace: $NAMESPACE"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy storage optimizations
echo "Deploying storage optimizations..."
kubectl apply -f kubernetes/storage/cache-config.yaml -n $NAMESPACE
kubectl apply -f kubernetes/storage/object-storage-setup.yaml -n $NAMESPACE

# Wait for Redis cache to be ready
echo "Waiting for Redis cache to be ready..."
kubectl wait --for=condition=available deployment/redis-cache -n $NAMESPACE --timeout=300s

# Deploy optimized service
echo "Deploying optimized service..."
kubectl apply -f kubernetes/optimized/service.yaml -n $NAMESPACE

# Deploy optimized deployment
echo "Deploying optimized deployment..."
kubectl apply -f kubernetes/optimized/deployment.yaml -n $NAMESPACE

# Wait for deployment to be ready
echo "Waiting for optimized deployment to be ready..."
kubectl wait --for=condition=available deployment/llm-optimized -n $NAMESPACE --timeout=900s

# Deploy KEDA autoscaler
echo "Deploying KEDA autoscaler..."
kubectl apply -f kubernetes/optimized/keda-scaler.yaml -n $NAMESPACE

# Deploy service mesh configuration
echo "Deploying service mesh configuration..."
kubectl apply -f kubernetes/optimized/service-mesh.yaml -n $NAMESPACE

# Check deployment status
echo "Checking deployment status..."
kubectl get pods -l $OPTIMIZED_LABEL -n $NAMESPACE

# Get service URL
SERVICE_URL=$(kubectl get service llm-optimized-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$SERVICE_URL" ]; then
    SERVICE_URL=$(kubectl get service llm-optimized-service -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    echo "Service available at: http://$SERVICE_URL:80"
    echo "For port-forwarding, run: kubectl port-forward service/llm-optimized-service 8080:80 -n $NAMESPACE"
else
    echo "Service available at: http://$SERVICE_URL:80"
fi

# Check GPU allocation
echo "Checking GPU allocation..."
kubectl get pods -l $OPTIMIZED_LABEL -n $NAMESPACE -o jsonpath='{.items[*].spec.containers[*].resources.requests.nvidia\.com/gpu}'

echo "=== Optimized Deployment Complete ==="
echo "To run load testing:"
echo "python scripts/load-testing/optimized-test.py --service-url http://localhost:8080"
echo ""
echo "To collect metrics:"
echo "python scripts/load-testing/metrics-collector.py --config optimized --service-url http://localhost:8080"
echo ""
echo "To run ablation study:"
echo "python scripts/benchmarking/latency-throughput.py"
