#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

python3 "${ROOT_DIR}/examples/example_atomic_task.py" --checkpoint-dir "${ROOT_DIR}/outputs/example-task"
