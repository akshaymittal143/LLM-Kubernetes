#!/usr/bin/env python3
"""
Metrics Collection Script for LLM Kubernetes Optimization Study

This script collects and analyzes performance metrics from both baseline
and optimized LLM deployments for comparison and analysis.
"""

import asyncio
import aiohttp
import time
import json
import statistics
import subprocess
import argparse
import logging
from typing import Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self, config: str = "baseline"):
        self.config = config
        self.metrics = {}
        
    async def collect_kubernetes_metrics(self) -> Dict[str, Any]:
        """Collect Kubernetes resource metrics."""
        try:
            # Get pod metrics
            result = subprocess.run([
                "kubectl", "top", "pods", 
                "-l", f"app=llm-{self.config}",
                "--no-headers"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                pod_metrics = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            pod_metrics.append({
                                "pod": parts[0],
                                "cpu": parts[1],
                                "memory": parts[2],
                                "cpu_percent": parts[3]
                            })
                
                return {"pod_metrics": pod_metrics}
            else:
                logger.warning(f"Failed to collect pod metrics: {result.stderr}")
                return {"pod_metrics": []}
                
        except Exception as e:
            logger.error(f"Error collecting Kubernetes metrics: {e}")
            return {"pod_metrics": []}
    
    async def collect_gpu_metrics(self) -> Dict[str, Any]:
        """Collect GPU utilization metrics."""
        try:
            # Get GPU metrics using nvidia-smi
            result = subprocess.run([
                "nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpu_metrics = []
                for i, line in enumerate(lines):
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            gpu_metrics.append({
                                "gpu_id": i,
                                "utilization": int(parts[0]),
                                "memory_used": int(parts[1]),
                                "memory_total": int(parts[2]),
                                "memory_percent": (int(parts[1]) / int(parts[2])) * 100
                            })
                
                return {"gpu_metrics": gpu_metrics}
            else:
                logger.warning(f"Failed to collect GPU metrics: {result.stderr}")
                return {"gpu_metrics": []}
                
        except Exception as e:
            logger.error(f"Error collecting GPU metrics: {e}")
            return {"gpu_metrics": []}
    
    async def collect_service_metrics(self, service_url: str) -> Dict[str, Any]:
        """Collect service-level metrics."""
        try:
            async with aiohttp.ClientSession() as session:
                # Health check
                start_time = time.time()
                async with session.get(f"{service_url}/health", timeout=10) as response:
                    health_latency = (time.time() - start_time) * 1000
                    health_status = response.status
                
                # Metrics endpoint (if available)
                metrics_data = {}
                try:
                    async with session.get(f"{service_url}/metrics", timeout=10) as response:
                        if response.status == 200:
                            metrics_text = await response.text()
                            # Parse basic metrics
                            for line in metrics_text.split('\n'):
                                if 'requests_total' in line or 'latency' in line:
                                    metrics_data[line.split()[0]] = line.split()[-1]
                except:
                    pass  # Metrics endpoint not available
                
                return {
                    "health_check": {
                        "status": health_status,
                        "latency_ms": health_latency
                    },
                    "service_metrics": metrics_data
                }
                
        except Exception as e:
            logger.error(f"Error collecting service metrics: {e}")
            return {
                "health_check": {"status": "error", "latency_ms": 0},
                "service_metrics": {}
            }
    
    async def collect_storage_metrics(self) -> Dict[str, Any]:
        """Collect storage I/O metrics."""
        try:
            # Get storage metrics using iostat
            result = subprocess.run([
                "iostat", "-x", "1", "1"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                storage_metrics = {}
                
                # Parse iostat output
                for line in lines:
                    if 'nvme' in line or 'sda' in line:
                        parts = line.split()
                        if len(parts) >= 14:
                            device = parts[0]
                            storage_metrics[device] = {
                                "rrqm_s": float(parts[1]),
                                "wrqm_s": float(parts[2]),
                                "r_s": float(parts[3]),
                                "w_s": float(parts[4]),
                                "rkB_s": float(parts[5]),
                                "wkB_s": float(parts[6]),
                                "avgrq_sz": float(parts[7]),
                                "avgqu_sz": float(parts[8]),
                                "await": float(parts[9]),
                                "r_await": float(parts[10]),
                                "w_await": float(parts[11]),
                                "svctm": float(parts[12]),
                                "util": float(parts[13])
                            }
                
                return {"storage_metrics": storage_metrics}
            else:
                logger.warning(f"Failed to collect storage metrics: {result.stderr}")
                return {"storage_metrics": {}}
                
        except Exception as e:
            logger.error(f"Error collecting storage metrics: {e}")
            return {"storage_metrics": {}}
    
    async def collect_all_metrics(self, service_url: str = None) -> Dict[str, Any]:
        """Collect all available metrics."""
        logger.info(f"Collecting metrics for {self.config} configuration")
        
        # Collect different types of metrics
        k8s_metrics = await self.collect_kubernetes_metrics()
        gpu_metrics = await self.collect_gpu_metrics()
        storage_metrics = await self.collect_storage_metrics()
        
        service_metrics = {}
        if service_url:
            service_metrics = await self.collect_service_metrics(service_url)
        
        # Combine all metrics
        all_metrics = {
            "timestamp": datetime.now().isoformat(),
            "configuration": self.config,
            **k8s_metrics,
            **gpu_metrics,
            **storage_metrics,
            **service_metrics
        }
        
        # Calculate summary statistics
        if gpu_metrics.get("gpu_metrics"):
            gpu_utils = [gpu["utilization"] for gpu in gpu_metrics["gpu_metrics"]]
            gpu_memory = [gpu["memory_percent"] for gpu in gpu_metrics["gpu_metrics"]]
            
            all_metrics["summary"] = {
                "avg_gpu_utilization": statistics.mean(gpu_utils),
                "avg_gpu_memory_usage": statistics.mean(gpu_memory),
                "max_gpu_utilization": max(gpu_utils),
                "max_gpu_memory_usage": max(gpu_memory)
            }
        
        return all_metrics
    
    def save_metrics(self, metrics: Dict[str, Any], filename: str = None):
        """Save metrics to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.config}-metrics-{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics saved to {filename}")
        return filename

async def main():
    parser = argparse.ArgumentParser(description="Collect LLM Performance Metrics")
    parser.add_argument("--config", choices=["baseline", "optimized"], default="baseline",
                       help="Configuration to collect metrics for")
    parser.add_argument("--service-url", 
                       help="Service URL for health checks")
    parser.add_argument("--output", 
                       help="Output file for metrics")
    parser.add_argument("--interval", type=int, default=60,
                       help="Collection interval in seconds")
    parser.add_argument("--continuous", action="store_true",
                       help="Run continuous collection")
    
    args = parser.parse_args()
    
    collector = MetricsCollector(args.config)
    
    if args.continuous:
        logger.info(f"Starting continuous metrics collection for {args.config}")
        while True:
            metrics = await collector.collect_all_metrics(args.service_url)
            filename = collector.save_metrics(metrics, args.output)
            print(f"Collected metrics: {filename}")
            await asyncio.sleep(args.interval)
    else:
        metrics = await collector.collect_all_metrics(args.service_url)
        filename = collector.save_metrics(metrics, args.output)
        
        # Print summary
        print(f"\n=== Metrics Collection Summary ({args.config}) ===")
        print(f"Timestamp: {metrics['timestamp']}")
        
        if "summary" in metrics:
            summary = metrics["summary"]
            print(f"Average GPU Utilization: {summary['avg_gpu_utilization']:.1f}%")
            print(f"Average GPU Memory Usage: {summary['avg_gpu_memory_usage']:.1f}%")
            print(f"Max GPU Utilization: {summary['max_gpu_utilization']:.1f}%")
            print(f"Max GPU Memory Usage: {summary['max_gpu_memory_usage']:.1f}%")
        
        if "health_check" in metrics:
            health = metrics["health_check"]
            print(f"Service Health: {health['status']}")
            print(f"Health Check Latency: {health['latency_ms']:.2f} ms")
        
        print(f"Metrics saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
