from __future__ import annotations

"""GPU 信息采集模块。

这里统一负责与 `nvidia-smi` 交互，避免环境检查、调度器、压测模块
各自去拼命令和解析字符串。把这层集中起来后，后续如果要兼容更多字段，
只需要改一个地方。
"""

import re
from dataclasses import dataclass

from .utils import run_command


@dataclass
class GPUStatus:
    index: int
    name: str
    memory_total_mb: int
    memory_used_mb: int
    utilization_gpu_percent: int


def get_nvidia_smi_output() -> str:
    # 保留原始 nvidia-smi 输出，方便用户直接截图或人工排查。
    code, stdout, stderr = run_command(["nvidia-smi"])
    if code != 0:
        return stderr or "nvidia-smi unavailable"
    return stdout


def get_topology_output() -> str:
    # topo 信息对多卡通信测试很关键，因此单独抽出来复用。
    code, stdout, stderr = run_command(["nvidia-smi", "topo", "-m"])
    if code != 0:
        return stderr or "nvidia-smi topo -m unavailable"
    return stdout


def get_driver_version() -> str | None:
    # 优先直接从 nvidia-smi 结果中提取驱动版本。
    smi_output = get_nvidia_smi_output()
    # 这里用正则而不是按行 split，是因为不同驱动版本的排版会略有差异，
    # 正则对这种“字段名 + 值”的提取更稳。
    match = re.search(r"Driver Version:\s*([0-9.]+)", smi_output)
    return match.group(1) if match else None


def get_cuda_version() -> str | None:
    # 优先使用 nvidia-smi 中声明的 CUDA 版本，缺失时再回退到 nvcc。
    smi_output = get_nvidia_smi_output()
    match = re.search(r"CUDA Version:\s*([0-9.]+)", smi_output)
    if match:
        return match.group(1)

    # 某些环境下 nvidia-smi 不会给 CUDA 版本，这时再尝试 nvcc。
    # 这并不等价于“运行时版本”，但至少能给用户一个可参考值。
    code, stdout, _ = run_command(["/usr/bin/env", "bash", "-lc", "nvcc --version"])
    if code == 0:
        match = re.search(r"release\s+([0-9.]+)", stdout)
        if match:
            return match.group(1)
    return None


def list_gpu_statuses() -> list[GPUStatus]:
    # 统一走 query-gpu 接口，输出稳定，适合脚本解析。
    query = "index,name,memory.total,memory.used,utilization.gpu"
    code, stdout, stderr = run_command(
        ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"]
    )
    if code != 0:
        raise RuntimeError(stderr or "failed to query gpu status")

    statuses: list[GPUStatus] = []
    for line in stdout.splitlines():
        # 这里使用 CSV + nounits，避免后续自己去剥离 'MiB'、'%' 这类单位字符串。
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 5:
            continue
        statuses.append(
            GPUStatus(
                index=int(parts[0]),
                name=parts[1],
                memory_total_mb=int(parts[2]),
                memory_used_mb=int(parts[3]),
                utilization_gpu_percent=int(parts[4]),
            )
        )
    return statuses


def get_gpu_utilization(gpu_id: int) -> int:
    # 调度器只关心单卡当前利用率，用于做“礼貌恢复”判断。
    for status in list_gpu_statuses():
        if status.index == gpu_id:
            return status.utilization_gpu_percent
    raise ValueError(f"GPU {gpu_id} not found")
