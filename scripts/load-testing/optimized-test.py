#!/usr/bin/env python3
"""
Optimized Load Testing Script for LLM Kubernetes Optimization Study

This script performs load testing on the optimized LLM deployment using vLLM
to establish performance benchmarks for comparison with baseline configurations.
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedLoadTester:
    def __init__(self, service_url: str, num_requests: int = 100, concurrency: int = 20):
        self.service_url = service_url
        self.num_requests = num_requests
        self.concurrency = concurrency
        self.results = []
        
    async def make_request(self, session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
        """Make a single inference request to the optimized LLM service."""
        prompt = f"Generate a short response about artificial intelligence. Request ID: {request_id}"
        
        payload = {
            "model": "meta-llama/Llama-2-7b-chat-hf",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.7,
            "stream": False
        }
        
        start_time = time.time()
        try:
            async with session.post(
                f"{self.service_url}/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.time()
                latency = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "request_id": request_id,
                        "status": "success",
                        "latency_ms": latency,
                        "tokens_generated": len(result["choices"][0]["message"]["content"].split()),
                        "timestamp": start_time,
                        "model": result.get("model", "unknown")
                    }
                else:
                    return {
                        "request_id": request_id,
                        "status": "error",
                        "latency_ms": latency,
                        "error_code": response.status,
                        "timestamp": start_time
                    }
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            return {
                "request_id": request_id,
                "status": "error",
                "latency_ms": latency,
                "error": str(e),
                "timestamp": start_time
            }
    
    async def run_load_test(self) -> Dict[str, Any]:
        """Run the complete load test with specified concurrency."""
        logger.info(f"Starting optimized load test: {self.num_requests} requests, {self.concurrency} concurrent")
        
        connector = aiohttp.TCPConnector(limit=self.concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Create semaphore to limit concurrency
            semaphore = asyncio.Semaphore(self.concurrency)
            
            async def bounded_request(request_id):
                async with semaphore:
                    return await self.make_request(session, request_id)
            
            # Create all tasks
            tasks = [bounded_request(i) for i in range(self.num_requests)]
            
            # Execute all requests
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Process results
            successful_requests = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
            failed_requests = [r for r in results if isinstance(r, dict) and r.get("status") == "error"]
            
            if successful_requests:
                latencies = [r["latency_ms"] for r in successful_requests]
                tokens_generated = [r["tokens_generated"] for r in successful_requests]
                
                summary = {
                    "total_requests": self.num_requests,
                    "successful_requests": len(successful_requests),
                    "failed_requests": len(failed_requests),
                    "success_rate": len(successful_requests) / self.num_requests,
                    "total_time_seconds": end_time - start_time,
                    "throughput_rps": len(successful_requests) / (end_time - start_time),
                    "latency_stats": {
                        "mean_ms": statistics.mean(latencies),
                        "median_ms": statistics.median(latencies),
                        "p95_ms": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
                        "p99_ms": statistics.quantiles(latencies, n=100)[98],  # 99th percentile
                        "min_ms": min(latencies),
                        "max_ms": max(latencies)
                    },
                    "tokens_stats": {
                        "mean_tokens": statistics.mean(tokens_generated),
                        "total_tokens": sum(tokens_generated)
                    },
                    "concurrency": self.concurrency,
                    "configuration": "optimized-vllm"
                }
            else:
                summary = {
                    "total_requests": self.num_requests,
                    "successful_requests": 0,
                    "failed_requests": len(failed_requests),
                    "success_rate": 0,
                    "error": "No successful requests",
                    "configuration": "optimized-vllm"
                }
            
            return summary
    
    def save_results(self, summary: Dict[str, Any], filename: str = "optimized-results.json"):
        """Save test results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Results saved to {filename}")

async def main():
    parser = argparse.ArgumentParser(description="Optimized LLM Load Testing")
    parser.add_argument("--service-url", default="http://llm-optimized-service:80", 
                       help="URL of the optimized LLM service")
    parser.add_argument("--requests", type=int, default=100, 
                       help="Number of requests to send")
    parser.add_argument("--concurrency", type=int, default=20, 
                       help="Number of concurrent requests")
    parser.add_argument("--output", default="optimized-results.json", 
                       help="Output file for results")
    
    args = parser.parse_args()
    
    tester = OptimizedLoadTester(
        service_url=args.service_url,
        num_requests=args.requests,
        concurrency=args.concurrency
    )
    
    summary = await tester.run_load_test()
    tester.save_results(summary, args.output)
    
    # Print summary
    print("\n=== Optimized Load Test Results ===")
    print(f"Total Requests: {summary['total_requests']}")
    print(f"Successful: {summary['successful_requests']}")
    print(f"Failed: {summary['failed_requests']}")
    print(f"Success Rate: {summary['success_rate']:.2%}")
    print(f"Throughput: {summary['throughput_rps']:.2f} requests/sec")
    
    if 'latency_stats' in summary:
        print(f"Mean Latency: {summary['latency_stats']['mean_ms']:.2f} ms")
        print(f"P95 Latency: {summary['latency_stats']['p95_ms']:.2f} ms")
        print(f"P99 Latency: {summary['latency_stats']['p99_ms']:.2f} ms")

if __name__ == "__main__":
    asyncio.run(main())
