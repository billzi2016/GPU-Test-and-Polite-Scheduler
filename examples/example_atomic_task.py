#!/usr/bin/env python3
from __future__ import annotations

"""原子化断点续传示例任务。

这个示例故意不绑定任何真实训练代码，而是用一个简单的 step 计数器模拟：
1. 启动时读取上次进度。
2. 每轮推进一步。
3. 每轮把最新进度原子写回 checkpoint。

这样用户可以先理解“断点续传协议”，再把同样模式迁移到自己的训练/采样任务。
"""

import argparse
import time
from pathlib import Path

from gpu_test_and_polite_scheduler.checkpoint_policy import atomic_write_json, load_json_checkpoint


def parse_args() -> argparse.Namespace:
    """解析示例任务参数。"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-dir", required=True)
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--max-steps", type=int, default=0, help="0 means run forever")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_path = checkpoint_dir / "latest.json"

    # 启动时先尝试恢复最近一次 checkpoint，没有则从 step 0 开始。
    state = load_json_checkpoint(checkpoint_path) or {"step": 0}
    step = int(state["step"])

    print(f"resume from step={step}", flush=True)

    while True:
        step += 1
        # 用 sleep 模拟真实任务每一步都会消耗一定时间。
        time.sleep(args.sleep_seconds)
        # 每一步都用原子写入更新最新状态，便于被 watchdog 重启后续跑。
        atomic_write_json(checkpoint_path, {"step": step, "updated_at": time.time()})
        print(f"saved checkpoint at step={step}", flush=True)

        if args.max_steps > 0 and step >= args.max_steps:
            break


if __name__ == "__main__":
    main()
