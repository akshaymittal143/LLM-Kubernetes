# LLM Kubernetes Optimization Artifacts

This repository contains the experimental artifacts and code used in the paper "Performance Optimization of LLM-Based Agentic Workloads in Kubernetes Environments: Bottlenecks, Root Causes, and Solutions" submitted to ICCA 2024.

## Repository Structure

```
├── kubernetes/
│   ├── baseline/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── pv-pvc.yaml
│   ├── optimized/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── keda-scaler.yaml
│   │   └── service-mesh.yaml
│   └── storage/
│       ├── object-storage-setup.yaml
│       └── cache-config.yaml
├── docker/
│   ├── baseline/
│   │   └── Dockerfile
│   └── optimized/
│       └── Dockerfile
├── scripts/
│   ├── load-testing/
│   │   ├── baseline-test.py
│   │   ├── optimized-test.py
│   │   └── metrics-collector.py
│   ├── benchmarking/
│   │   ├── gpu-benchmark.py
│   │   ├── storage-benchmark.py
│   │   └── latency-throughput.py
│   └── deployment/
│       ├── deploy-baseline.sh
│       ├── deploy-optimized.sh
│       └── cleanup.sh
├── configs/
│   ├── vllm-config.yaml
│   ├── quantization-config.yaml
│   └── monitoring-config.yaml
└── results/
    ├── baseline-metrics.json
    ├── optimized-metrics.json
    └── ablation-study-results.json
```

## Quick Start

### Prerequisites
- Kubernetes cluster (v1.28+)
- NVIDIA A100 GPU nodes
- kubectl configured
- Docker

### Running Baseline Experiments
```bash
# Deploy baseline configuration
./scripts/deployment/deploy-baseline.sh

# Run baseline load testing
python scripts/load-testing/baseline-test.py

# Collect metrics
python scripts/load-testing/metrics-collector.py --config baseline
```

### Running Optimized Experiments
```bash
# Deploy optimized configuration
./scripts/deployment/deploy-optimized.sh

# Run optimized load testing
python scripts/load-testing/optimized-test.py

# Collect metrics
python scripts/load-testing/metrics-collector.py --config optimized
```

### Running Ablation Study
```bash
# Run complete ablation study
python scripts/benchmarking/run-ablation-study.py

# Generate performance curves
python scripts/benchmarking/latency-throughput.py
```

## Key Artifacts

### Baseline Configuration
- Standard Kubernetes deployment without GPU optimizations
- Default Hugging Face Transformers pipeline
- Basic resource allocation patterns

### Optimized Configuration
- vLLM with PagedAttention optimization
- FP8 quantization enabled
- Object storage bypass for model loading
- KEDA autoscaling with custom metrics
- Service mesh for communication optimization

### Load Testing Scripts
- Synthetic conversation patterns
- Variable context lengths
- Concurrent user simulation
- Metrics collection and analysis

### Benchmarking Tools
- GPU utilization measurement
- Storage I/O performance testing
- Latency-throughput curve generation
- Cost analysis calculations

## Reproducing Results

1. **Setup Environment**: Follow the prerequisites and deploy the baseline configuration
2. **Run Baseline Tests**: Execute baseline load testing and collect metrics
3. **Deploy Optimizations**: Apply each optimization stage sequentially
4. **Run Ablation Study**: Execute the complete ablation study
5. **Analyze Results**: Generate performance curves and cost analysis

## Citation

If you use these artifacts in your research, please cite:

```bibtex
@inproceedings{mittal2024llm,
  title={Performance Optimization of LLM-Based Agentic Workloads in Kubernetes Environments: Bottlenecks, Root Causes, and Solutions},
  author={Mittal, Akshay and Tadi, Goutam},
  booktitle={Proceedings of the International Conference on Computer Applications},
  year={2024},
  note={Submitted}
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Repository

The complete experimental artifacts and code are available at: https://github.com/akshaymittal143/LLM-Kubernetes

## Contact

For questions about the artifacts or paper, please contact:
- Akshay Mittal: akshay.mittal@ieee.org
- Goutam Tadi: gtadi@ieee.org
