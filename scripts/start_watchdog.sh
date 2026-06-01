#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/start_watchdog.sh <config-path>"
  exit 1
fi

# watchdog 通过配置文件驱动，避免把任务列表硬编码在脚本里。
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"
cd "${ROOT_DIR}"

# 这里显式走 watchdog-launch，把守护进程本身也放进 tmux，符合“断开 SSH 也继续跑”的目标。
python3 -m gpu_test_and_polite_scheduler.cli watchdog-launch --config "$1"
