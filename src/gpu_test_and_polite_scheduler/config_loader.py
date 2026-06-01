from __future__ import annotations

"""配置加载模块。

这个文件的职责很克制：
1. 读取 YAML/JSON。
2. 做最基础的结构化校验。
3. 转成 dataclass，给后续模块稳定使用。

它不负责复杂的业务语义校验，避免把配置层做得过重。
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TaskConfig:
    name: str
    gpu_id: int
    command: str
    workdir: str = "."
    log_file: str | None = None


@dataclass
class SchedulerConfig:
    poll_interval_seconds: int
    gpu_busy_threshold_percent: int
    watchdog_session_name: str
    log_dir: str
    auto_restart: bool
    tasks: list[TaskConfig]


def load_config(path: str | Path) -> dict[str, Any]:
    # 同时兼容 YAML 和 JSON，降低用户接入门槛。
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(path)

    if path_obj.suffix.lower() == ".json":
        # JSON 分支走标准库，避免为简单场景额外依赖。
        return json.loads(path_obj.read_text(encoding="utf-8"))

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load YAML config files") from exc

    data = yaml.safe_load(path_obj.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config root must be a mapping")
    return data


def load_scheduler_config(path: str | Path) -> SchedulerConfig:
    # 这里做最基础的结构校验，尽早暴露配置错误。
    data = load_config(path)
    tasks_raw = data.get("tasks")
    if not isinstance(tasks_raw, list) or not tasks_raw:
        raise ValueError("tasks must be a non-empty list")

    tasks: list[TaskConfig] = []
    for item in tasks_raw:
        if not isinstance(item, dict):
            raise ValueError("each task must be a mapping")
        tasks.append(
            TaskConfig(
                # 这里统一做显式类型收敛，避免上层每次手工处理字符串/整数混用问题。
                name=str(item["name"]),
                gpu_id=int(item["gpu_id"]),
                command=str(item["command"]),
                workdir=str(item.get("workdir", ".")),
                log_file=str(item["log_file"]) if item.get("log_file") else None,
            )
        )

    return SchedulerConfig(
        # 顶层字段全部给默认值，目的是让示例配置尽量短，
        # 用户只写任务列表也能先跑起来。
        poll_interval_seconds=int(data.get("poll_interval_seconds", 60)),
        gpu_busy_threshold_percent=int(data.get("gpu_busy_threshold_percent", 5)),
        watchdog_session_name=str(data.get("watchdog_session_name", "gpu-watchdog")),
        log_dir=str(data.get("log_dir", "logs")),
        auto_restart=bool(data.get("auto_restart", True)),
        tasks=tasks,
    )
