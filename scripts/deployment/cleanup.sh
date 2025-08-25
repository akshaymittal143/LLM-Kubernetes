#!/bin/bash
# Cleanup Script for LLM Kubernetes Optimization Study
# This script removes all deployments and resources created during testing

set -e

echo "=== Cleaning up LLM Test Environment ==="

# Configuration
NAMESPACE="llm-test"

# Check if namespace exists
if kubectl get namespace $NAMESPACE >/dev/null 2>&1; then
    echo "Removing namespace: $NAMESPACE"
    kubectl delete namespace $NAMESPACE
else
    echo "Namespace $NAMESPACE does not exist"
fi

# Remove any remaining resources outside namespace
echo "Cleaning up any remaining resources..."

# Remove baseline resources
kubectl delete deployment llm-baseline --ignore-not-found=true
kubectl delete service llm-baseline-service --ignore-not-found=true
kubectl delete pvc llm-pvc --ignore-not-found=true
kubectl delete pv llm-baseline-pv --ignore-not-found=true

# Remove optimized resources
kubectl delete deployment llm-optimized --ignore-not-found=true
kubectl delete service llm-optimized-service --ignore-not-found=true
kubectl delete scaledobject llm-optimized-scaler --ignore-not-found=true

# Remove storage resources
kubectl delete deployment redis-cache --ignore-not-found=true
kubectl delete service redis-service --ignore-not-found=true
kubectl delete daemonset model-cache-daemon --ignore-not-found=true

# Remove service mesh resources
kubectl delete virtualservice llm-optimized-vs --ignore-not-found=true
kubectl delete destinationrule llm-optimized-dr --ignore-not-found=true
kubectl delete authorizationpolicy llm-optimized-auth --ignore-not-found=true

# Remove config maps
kubectl delete configmap object-storage-config --ignore-not-found=true
kubectl delete configmap cache-config --ignore-not-found=true
kubectl delete configmap keda-prometheus-config --ignore-not-found=true

echo "=== Cleanup Complete ==="
echo "All test resources have been removed"
