#!/bin/bash
# Baseline LLM Deployment Script
# This script deploys the baseline LLM configuration for performance testing

set -e

echo "=== Deploying Baseline LLM Configuration ==="

# Configuration
NAMESPACE="llm-test"
BASELINE_LABEL="app=llm-baseline"

# Create namespace if it doesn't exist
echo "Creating namespace: $NAMESPACE"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy storage
echo "Deploying storage configuration..."
kubectl apply -f kubernetes/baseline/pv-pvc.yaml -n $NAMESPACE

# Wait for PVC to be bound
echo "Waiting for PVC to be bound..."
kubectl wait --for=condition=bound pvc/llm-pvc -n $NAMESPACE --timeout=300s

# Deploy baseline service
echo "Deploying baseline service..."
kubectl apply -f kubernetes/baseline/service.yaml -n $NAMESPACE

# Deploy baseline deployment
echo "Deploying baseline deployment..."
kubectl apply -f kubernetes/baseline/deployment.yaml -n $NAMESPACE

# Wait for deployment to be ready
echo "Waiting for baseline deployment to be ready..."
kubectl wait --for=condition=available deployment/llm-baseline -n $NAMESPACE --timeout=600s

# Check deployment status
echo "Checking deployment status..."
kubectl get pods -l $BASELINE_LABEL -n $NAMESPACE

# Get service URL
SERVICE_URL=$(kubectl get service llm-baseline-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$SERVICE_URL" ]; then
    SERVICE_URL=$(kubectl get service llm-baseline-service -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    echo "Service available at: http://$SERVICE_URL:80"
    echo "For port-forwarding, run: kubectl port-forward service/llm-baseline-service 8080:80 -n $NAMESPACE"
else
    echo "Service available at: http://$SERVICE_URL:80"
fi

echo "=== Baseline Deployment Complete ==="
echo "To run load testing:"
echo "python scripts/load-testing/baseline-test.py --service-url http://localhost:8080"
echo ""
echo "To collect metrics:"
echo "python scripts/load-testing/metrics-collector.py --config baseline --service-url http://localhost:8080"
