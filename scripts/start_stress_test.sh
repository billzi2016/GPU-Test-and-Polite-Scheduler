#!/usr/bin/env bash
set -euo pipefail

# 脚本仅做轻量封装，真实参数解析与执行放到 Python CLI 中。
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

# 压测前会先打印当前 nvidia-smi，便于对照目标 GPU 状态。
python3 -m gpu_test_and_polite_scheduler.cli stress-test "$@"
