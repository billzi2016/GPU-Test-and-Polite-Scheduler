#!/usr/bin/env bash
set -euo pipefail

# 统一从仓库根目录注入源码路径，便于直接运行脚本入口。
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

# 环境检查会打印 nvidia-smi、topo、CUDA/驱动/GPU 摘要信息。
python3 -m gpu_test_and_polite_scheduler.cli env-check "$@"
