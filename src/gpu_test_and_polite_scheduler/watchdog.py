from __future__ import annotations

"""watchdog 守护模块。

它不直接理解具体业务任务，只负责周期性巡检并调用 Scheduler。
也就是说：watchdog 是“轮询器”，scheduler 是“决策器”。
"""

import time
from pathlib import Path
import shlex

from .config_loader import load_scheduler_config
from .logger import setup_logger
from .scheduler import Scheduler
from .tmux_manager import TmuxManager


def run_watchdog(config_path: str) -> None:
    """按配置启动无限轮询守护。"""

    config = load_scheduler_config(config_path)
    logger = setup_logger("watchdog", f"{config.log_dir}/watchdog.log")
    scheduler = Scheduler(config=config)

    logger.info("Watchdog started with poll interval %ss", config.poll_interval_seconds)
    try:
        while True:
            try:
                # 每轮都重新巡检全部任务，确保异常退出后能进入等待或恢复分支。
                states = scheduler.inspect_all()
                for state in states:
                    # 每轮都记一条结构化日志，后续排查“为什么没重启”时会很有用。
                    logger.info(
                        "task=%s session=%s status=%s reason=%s",
                        state.task.name,
                        state.session_name,
                        state.status,
                        state.reason,
                    )
            except Exception:
                # watchdog 不能因为一次临时错误就整个退出，否则“守护”就失去意义了。
                logger.exception("Watchdog loop failed unexpectedly")
            # sleep 放在循环尾部，保证启动后的第一轮检查会立刻执行一次。
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        logger.info("Watchdog stopped by user")


def launch_watchdog_session(config_path: str) -> str:
    """把 watchdog 放进独立 tmux session 后台运行。

    这里使用配置里的 `watchdog_session_name` 作为 session 名，
    这样脚本层不需要重复维护一份命名规则。
    """

    config = load_scheduler_config(config_path)
    manager = TmuxManager()
    resolved_config_path = str(Path(config_path).resolve())
    # 这里做 shell quote，是为了兼容配置文件路径里包含空格等特殊字符的情况。
    command = (
        "python3 -m gpu_test_and_polite_scheduler.cli watchdog "
        f"--config {shlex.quote(resolved_config_path)}"
    )
    manager.restart_session(
        session_name=config.watchdog_session_name,
        command=command,
        # 任务里的相对路径默认相对“启动 watchdog 时所在目录”解析；
        # 配合 start_watchdog.sh 先 cd 到仓库根目录，可以让示例配置稳定工作。
        workdir=str(Path.cwd()),
        log_file=f"{config.log_dir}/watchdog.stdout.log",
    )
    return config.watchdog_session_name
