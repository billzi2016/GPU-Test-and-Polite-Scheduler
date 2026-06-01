from __future__ import annotations

"""统一命令行入口。

这个文件只负责“参数解析 + 分发”。
真正的业务逻辑都在各自模块中，避免 CLI 入口越来越厚，最后变成一个
难维护的大脚本。
"""

import argparse

from .comm_test import CommTestConfig, run_comm_test
from .config_loader import load_config
from .env_check import run_env_check
from .stress_test import StressTestConfig, run_stress_test
from .watchdog import launch_watchdog_session, run_watchdog


def _parse_gpu_list(raw: str) -> list[int]:
    # CLI 里统一用逗号分隔 GPU 列表，例如 0,1,3。
    return [int(item.strip()) for item in raw.split(",") if item.strip()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gpu-test-and-polite-scheduler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("env-check", help="print nvidia-smi, topo, CUDA and GPU summary")

    stress = subparsers.add_parser("stress-test", help="run GPU matrix-multiplication burn-in")
    stress.add_argument("--gpus", default="0", help="comma-separated GPU ids")
    stress.add_argument("--matrix-size", type=int, default=8192)
    stress.add_argument("--iterations", type=int, default=0, help="0 means infinite loop")
    stress.add_argument("--status-every", type=int, default=10)
    stress.add_argument("--dtype", default="float32")
    stress.add_argument("--config", help="optional JSON/YAML config path")

    comm = subparsers.add_parser("comm-test", help="run multi-GPU all-reduce communication test")
    comm.add_argument("--gpus", default="0,1", help="comma-separated GPU ids")
    comm.add_argument("--warmup-iters", type=int, default=5)
    comm.add_argument("--measure-iters", type=int, default=20)
    comm.add_argument("--numel", type=int, default=16 * 1024 * 1024)
    comm.add_argument("--config", help="optional JSON/YAML config path")

    watchdog = subparsers.add_parser("watchdog", help="run tmux-based polite scheduler watchdog")
    watchdog.add_argument("--config", required=True, help="scheduler config path")

    watchdog_launch = subparsers.add_parser("watchdog-launch", help="launch watchdog inside a tmux session")
    watchdog_launch.add_argument("--config", required=True, help="scheduler config path")

    return parser


def _stress_config_from_args(args: argparse.Namespace) -> StressTestConfig:
    # 支持 CLI 直传参数，也支持从配置文件加载，便于脚本化复用。
    if args.config:
        data = load_config(args.config)
        return StressTestConfig(
            gpus=[int(gpu) for gpu in data.get("gpus", [0])],
            matrix_size=int(data.get("matrix_size", 8192)),
            iterations=int(data.get("iterations", 0)),
            status_every=int(data.get("status_every", 10)),
            dtype=str(data.get("dtype", "float32")),
        )
    return StressTestConfig(
        gpus=_parse_gpu_list(args.gpus),
        matrix_size=args.matrix_size,
        iterations=args.iterations,
        status_every=args.status_every,
        dtype=args.dtype,
    )


def _comm_config_from_args(args: argparse.Namespace) -> CommTestConfig:
    # 通信测试和压测保持相同模式：配置文件优先，否则走命令行参数。
    if args.config:
        data = load_config(args.config)
        return CommTestConfig(
            gpus=[int(gpu) for gpu in data.get("gpus", [0, 1])],
            warmup_iters=int(data.get("warmup_iters", 5)),
            measure_iters=int(data.get("measure_iters", 20)),
            numel=int(data.get("numel", 16 * 1024 * 1024)),
        )
    return CommTestConfig(
        gpus=_parse_gpu_list(args.gpus),
        warmup_iters=args.warmup_iters,
        measure_iters=args.measure_iters,
        numel=args.numel,
    )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # 这里不做复杂分发，保持入口足够直白，便于后续继续扩展子命令。
    # 这种显式 if 分发虽然不“炫”，但读起来最直观，也更适合当前项目规模。
    if args.command == "env-check":
        run_env_check()
        return
    if args.command == "stress-test":
        run_stress_test(_stress_config_from_args(args))
        return
    if args.command == "comm-test":
        run_comm_test(_comm_config_from_args(args))
        return
    if args.command == "watchdog":
        run_watchdog(args.config)
        return
    if args.command == "watchdog-launch":
        session_name = launch_watchdog_session(args.config)
        print(f"watchdog launched in tmux session: {session_name}")
        return

    parser.error(f"unsupported command: {args.command}")


if __name__ == "__main__":
    main()
