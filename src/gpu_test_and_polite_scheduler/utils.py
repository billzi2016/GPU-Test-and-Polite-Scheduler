from __future__ import annotations

"""通用工具函数。

这里放的都是跨模块复用、但又不值得单独建大模块的辅助逻辑。
"""

import os
import socket
import subprocess
from pathlib import Path


def run_command(command: list[str]) -> tuple[int, str, str]:
    # 统一封装子进程调用，便于上层复用返回格式。
    # capture_output=True 让调用方能够自行决定是展示原始输出还是结构化处理错误。
    process = subprocess.run(command, capture_output=True, text=True)
    return process.returncode, process.stdout.strip(), process.stderr.strip()


def ensure_dir(path: str | Path) -> Path:
    # 对日志、输出、checkpoint 等目录做幂等创建。
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def is_command_available(command: str) -> bool:
    # 通过 shell 的 command -v 做最轻量的可执行检测。
    code, _, _ = run_command(["/usr/bin/env", "bash", "-lc", f"command -v {command}"])
    return code == 0


def find_free_port() -> int:
    # 多卡通信测试需要一个本地临时端口作为分布式 rendezvous。
    # 先 bind 到 0 让 OS 分配空闲端口，再读取实际端口号，是最简单稳妥的做法。
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def append_log_redirection(command: str, log_file: str | None) -> str:
    # 将 tmux 中执行的命令追加到日志文件，避免覆盖已有内容。
    if not log_file:
        return command
    quoted = os.path.expanduser(log_file)
    return f"{command} >> {quoted} 2>&1"
