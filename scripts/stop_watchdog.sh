#!/usr/bin/env bash
set -euo pipefail

# 默认停止主 watchdog session，也允许用户传入自定义 session 名。
SESSION_NAME="${1:-gpu-watchdog}"

if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
  tmux kill-session -t "${SESSION_NAME}"
  echo "Stopped tmux session: ${SESSION_NAME}"
else
  echo "tmux session not found: ${SESSION_NAME}"
fi
