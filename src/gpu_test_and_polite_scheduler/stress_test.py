from __future__ import annotations

"""GPU 压力测试模块。

目标不是做严格 benchmark，而是做一类更贴近日常验卡场景的 burn-in：
让指定 GPU 长时间持续处于高负载状态，观察利用率、温度、功耗以及是否报错。
"""

import multiprocessing as mp
import time
from dataclasses import dataclass

from .gpu_info import get_nvidia_smi_output


@dataclass
class StressTestConfig:
    gpus: list[int]
    matrix_size: int = 8192
    iterations: int = 0
    status_every: int = 10
    dtype: str = "float32"


def _resolve_torch_dtype(torch_module, dtype_name: str):
    # 允许通过字符串配置 dtype，方便从 CLI/配置文件传参。
    mapping = {
        "float16": torch_module.float16,
        "bfloat16": torch_module.bfloat16,
        "float32": torch_module.float32,
        "float64": torch_module.float64,
    }
    if dtype_name not in mapping:
        raise ValueError(f"unsupported dtype: {dtype_name}")
    return mapping[dtype_name]


def _stress_worker(config: StressTestConfig, gpu_id: int) -> None:
    """单个 GPU 的压测工作进程。

    这里必须放在子进程里做，而不是主进程里串行切换设备。
    原因是压测的目标是“多卡同时满载”，串行切卡会让卡之间互相等待，
    观察到的利用率会失真。
    """

    import torch

    # 每个子进程独占一张卡，避免 Python 线程争抢同一个 CUDA 上下文。
    torch.cuda.set_device(gpu_id)
    dtype = _resolve_torch_dtype(torch, config.dtype)
    # 预先分配两块大矩阵，后续循环只做 matmul，避免每轮都把时间浪费在重新分配显存上。
    a = torch.randn((config.matrix_size, config.matrix_size), device=f"cuda:{gpu_id}", dtype=dtype)
    b = torch.randn((config.matrix_size, config.matrix_size), device=f"cuda:{gpu_id}", dtype=dtype)

    iteration = 0
    start = time.time()
    while True:
        _ = a @ b
        # 显式同步是关键，否则可能只是不断排队算子，利用率并不真实。
        # 很多“看起来在跑”的 CUDA 代码其实只是把工作提交给默认 stream，
        # CPU 立刻返回继续下一轮；如果不在这里同步，压测就更像“疯狂排队”
        # 而不是“确认这一轮真的算完了”，结果是温度和利用率可能不稳定。
        torch.cuda.synchronize(gpu_id)
        iteration += 1

        if iteration % config.status_every == 0:
            elapsed = time.time() - start
            print(
                f"[GPU {gpu_id}] iteration={iteration} "
                f"elapsed={elapsed:.1f}s matrix_size={config.matrix_size} dtype={config.dtype}",
                flush=True,
            )

        if config.iterations > 0 and iteration >= config.iterations:
            break


def run_stress_test(config: StressTestConfig) -> None:
    """启动单卡或多卡压测。

    `iterations=0` 代表无限循环，符合 burn-in 的常见使用方式；
    用户通常会一边看 `watch -n 1 nvidia-smi`，一边手动决定什么时候停。
    """

    # 启动前先打印一次 nvidia-smi，便于用户确认目标卡当前状态。
    print("== Current nvidia-smi ==")
    print(get_nvidia_smi_output())
    print("")

    try:
        import torch  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("PyTorch is required for stress testing") from exc

    # 使用 spawn 兼容 CUDA 多进程场景，避免 fork 带来的上下文问题。
    # `fork` 会把父进程里已有的 CUDA 状态一并复制过去，很多环境下这会造成
    # 难查的死锁、初始化异常或显存状态错乱；`spawn` 更啰嗦，但更稳妥。
    ctx = mp.get_context("spawn")
    processes: list[mp.Process] = []
    for gpu_id in config.gpus:
        process = ctx.Process(target=_stress_worker, args=(config, gpu_id), daemon=False)
        process.start()
        processes.append(process)

    try:
        for process in processes:
            # 主进程只负责等待子进程，子进程内部才是真正持续占满 GPU 的执行体。
            process.join()
    except KeyboardInterrupt:
        print("Interrupted by user, terminating workers...")
        for process in processes:
            process.terminate()
        for process in processes:
            process.join()
