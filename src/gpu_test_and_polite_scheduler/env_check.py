from __future__ import annotations

"""环境检查模块。

这个文件负责把 GPU 相关基础信息组织成一份适合人直接阅读的报告。
设计上故意保留了原始 `nvidia-smi` 和 `nvidia-smi topo -m` 输出，
原因是很多 GPU/驱动/拓扑问题最终都要靠人工肉眼排查，过度“美化”
反而会把关键上下文丢掉。
"""

from .gpu_info import (
    get_cuda_version,
    get_driver_version,
    get_nvidia_smi_output,
    get_topology_output,
    list_gpu_statuses,
)
from .utils import is_command_available


def build_env_report() -> str:
    """构建完整环境报告。

    返回值是一个已经排好版的多行字符串，调用方只需要直接打印。
    这里不返回结构化对象，目的是让 shell 脚本、CLI 和日志系统都能零成本复用。
    """

    # 报告结构尽量贴近日常排查顺序：先原始输出，再摘要。
    lines: list[str] = []
    lines.append("== nvidia-smi ==")
    lines.append(get_nvidia_smi_output())
    lines.append("")
    lines.append("== nvidia-smi topo -m ==")
    lines.append(get_topology_output())
    lines.append("")
    lines.append("== Summary ==")
    lines.append(f"Driver Version: {get_driver_version() or 'unknown'}")
    lines.append(f"CUDA Version: {get_cuda_version() or 'unknown'}")
    lines.append("Dependencies:")
    lines.append(f"  nvidia-smi: {'yes' if is_command_available('nvidia-smi') else 'no'}")
    lines.append(f"  tmux: {'yes' if is_command_available('tmux') else 'no'}")
    lines.append(f"  python3: {'yes' if is_command_available('python3') else 'no'}")
    lines.append("Visible GPUs:")

    try:
        # 这里单独包一层异常，是为了保证前面的原始输出已经拿到时，
        # 后面的解析失败也不会让整份报告直接中断。
        statuses = list_gpu_statuses()
    except Exception as exc:
        lines.append(f"  failed to list GPUs: {exc}")
        return "\n".join(lines)

    if not statuses:
        lines.append("  no visible GPUs")
        return "\n".join(lines)

    for status in statuses:
        # 摘要部分刻意压成一行一个 GPU，方便用户在群里或 issue 里直接贴结果。
        lines.append(
            "  "
            f"GPU {status.index}: {status.name} | "
            f"memory {status.memory_used_mb}/{status.memory_total_mb} MiB | "
            f"util {status.utilization_gpu_percent}%"
        )
    return "\n".join(lines)


def run_env_check() -> None:
    # 入口保持简单，便于 shell 脚本和 CLI 共同复用。
    print(build_env_report())
