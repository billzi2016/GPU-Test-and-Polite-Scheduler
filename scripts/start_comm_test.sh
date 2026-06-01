#!/usr/bin/env bash
set -euo pipefail

# 脚本入口保持极薄，避免 shell 层承载复杂逻辑。
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

# 通信测试前会打印 topo，帮助确认多卡链路关系。
python3 -m gpu_test_and_polite_scheduler.cli comm-test "$@"
