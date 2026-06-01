from __future__ import annotations

"""多卡通信测试模块。

这里实现的是一个足够轻量的单机多卡通信测试：
用 PyTorch distributed + NCCL 跑 all_reduce，观察是否能成功初始化、
是否能完成通信，以及大致带宽是否明显异常。
"""

import multiprocessing as mp
import os
import time
from dataclasses import dataclass

from .gpu_info import get_topology_output
from .utils import find_free_port


@dataclass
class CommTestConfig:
    gpus: list[int]
    warmup_iters: int = 5
    measure_iters: int = 20
    numel: int = 16 * 1024 * 1024


def _comm_worker(rank: int, world_size: int, config: CommTestConfig, master_port: int) -> None:
    """单个 rank 的通信测试进程。

    每个 rank 绑定一张 GPU，和真实分布式训练的单机多卡部署方式一致，
    这样测出来的问题也更接近日后训练/采样时会遇到的问题。
    """

    import torch
    import torch.distributed as dist

    gpu_id = config.gpus[rank]
    # 单机多进程通信测试使用本地 rendezvous 即可。
    os.environ["MASTER_ADDR"] = "127.0.0.1"
    os.environ["MASTER_PORT"] = str(master_port)

    torch.cuda.set_device(gpu_id)
    # backend 选择 NCCL，是因为这是 NVIDIA GPU 多卡通信的主流路径。
    dist.init_process_group(backend="nccl", rank=rank, world_size=world_size)

    tensor = torch.ones(config.numel, device=f"cuda:{gpu_id}", dtype=torch.float32)

    for _ in range(config.warmup_iters):
        # 先 warmup，让 CUDA kernel、通信上下文、lazy init 等一次性成本先摊掉，
        # 避免把初始化抖动误算进最终耗时。
        dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
        torch.cuda.synchronize(gpu_id)

    timings: list[float] = []
    for _ in range(config.measure_iters):
        # 用 perf_counter 而不是 time.time，是为了拿更稳定的短时间间隔测量。
        start = time.perf_counter()
        dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
        torch.cuda.synchronize(gpu_id)
        timings.append(time.perf_counter() - start)

    avg_seconds = sum(timings) / len(timings)
    # 这里给的是近似带宽，用于发现明显异常，不追求严格 benchmark 精度。
    # `* 2` 的原因是 all_reduce 不只是“发出去一次”，通常还包含聚合/回传成本，
    # 这里用一个粗略的双向流量估计，核心目的是给用户一个可比的健康度指标。
    bytes_per_iter = tensor.numel() * tensor.element_size() * 2
    bandwidth_gbps = bytes_per_iter / avg_seconds / (1024**3)
    print(
        f"[rank={rank} gpu={gpu_id}] avg_all_reduce={avg_seconds:.6f}s "
        f"approx_bandwidth={bandwidth_gbps:.2f} GiB/s",
        flush=True,
    )

    dist.destroy_process_group()


def run_comm_test(config: CommTestConfig) -> None:
    """启动多卡通信测试。"""

    # 先打印 topo，用户可以直接看到参与测试 GPU 之间的连接关系。
    print("== GPU Topology ==")
    print(get_topology_output())
    print("")

    if len(config.gpus) < 2:
        raise ValueError("communication test requires at least 2 GPUs")

    try:
        import torch  # noqa: F401
        import torch.distributed  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("PyTorch with distributed support is required") from exc

    port = find_free_port()
    # 这里动态找空闲端口，避免把某个固定端口写死后与用户现有任务冲突。
    # 每张卡一个进程，模拟常见的单机多卡分布式运行方式。
    ctx = mp.get_context("spawn")
    processes: list[mp.Process] = []
    for rank in range(len(config.gpus)):
        process = ctx.Process(target=_comm_worker, args=(rank, len(config.gpus), config, port), daemon=False)
        process.start()
        processes.append(process)

    for process in processes:
        process.join()
        if process.exitcode != 0:
            # 只要有一个 rank 非正常退出，就说明这次通信测试不应判定为成功。
            raise RuntimeError(f"communication worker exited with code {process.exitcode}")
