from __future__ import annotations

"""调度策略模块。

这个文件负责回答两个问题：
1. 一个任务现在应不应该被拉起。
2. 一个已经消失的任务现在应不应该被恢复。

本项目的“礼貌”核心就放在这里，而不是散落在 shell 脚本里。
"""

from dataclasses import dataclass

from .config_loader import SchedulerConfig, TaskConfig
from .gpu_info import get_gpu_utilization
from .logger import setup_logger
from .tmux_manager import TmuxManager
from .utils import ensure_dir


@dataclass
class TaskState:
    task: TaskConfig
    session_name: str
    status: str
    reason: str


class Scheduler:
    """根据配置和 GPU 当前状态决定任务如何部署。"""

    def __init__(self, config: SchedulerConfig, tmux_manager: TmuxManager | None = None):
        self.config = config
        self.tmux_manager = tmux_manager or TmuxManager()
        ensure_dir(config.log_dir)
        self.logger = setup_logger("scheduler", f"{config.log_dir}/scheduler.log")

    def build_session_name(self, task: TaskConfig) -> str:
        # 给所有任务统一加前缀，方便 tmux ls 时快速识别。
        return f"gps-{task.name}"

    def gpu_is_busy(self, gpu_id: int) -> bool:
        # 当前版本只看 GPU-Util，不看显存占用。
        # 这是一个有意识的简化：它足够轻量，但后续确实可能扩展为双阈值判定。
        utilization = get_gpu_utilization(gpu_id)
        return utilization > self.config.gpu_busy_threshold_percent

    def deploy_task(self, task: TaskConfig) -> TaskState:
        """尝试部署一个任务。

        返回 TaskState 而不是布尔值，是为了把“为什么没启动”也一起带出去，
        后续日志、CLI 或 Web/TUI 面板都能直接复用这个原因字段。
        """

        session_name = self.build_session_name(task)
        # 礼貌策略核心：先看卡忙不忙，再决定是否拉起任务。
        if self.gpu_is_busy(task.gpu_id):
            reason = (
                f"GPU {task.gpu_id} utilization above "
                f"{self.config.gpu_busy_threshold_percent}%"
            )
            self.logger.info("Skip deploy for %s: %s", task.name, reason)
            return TaskState(task=task, session_name=session_name, status="waiting", reason=reason)

        self.tmux_manager.restart_session(
            session_name=session_name,
            command=task.command,
            workdir=task.workdir,
            log_file=task.log_file,
        )
        # 真正的断点续跑不在调度器里实现，而是依赖 task.command 本身支持恢复。
        self.logger.info("Started task %s in session %s", task.name, session_name)
        return TaskState(task=task, session_name=session_name, status="running", reason="started")

    def inspect_task(self, task: TaskConfig) -> TaskState:
        """检查单个任务当前状态，并在需要时决定是否恢复。"""

        session_name = self.build_session_name(task)
        # 当前实现把“session 存在”作为任务仍在运行的近似判定。
        # 这不是绝对准确的，因为 session 里可能只剩一个空 shell。
        # 但作为第一版策略，它比直接解析 pane 内具体进程更稳定，也更易维护。
        if self.tmux_manager.has_session(session_name):
            return TaskState(task=task, session_name=session_name, status="running", reason="session exists")

        if not self.config.auto_restart:
            return TaskState(task=task, session_name=session_name, status="stopped", reason="session missing")

        # session 不存在时，按礼貌恢复策略重新评估是否应重启。
        return self.deploy_task(task)

    def inspect_all(self) -> list[TaskState]:
        # watchdog 每轮都调这个方法，拿到全量任务状态快照。
        # 这里按任务逐个兜底，避免某一个任务状态异常导致整轮巡检全灭。
        states: list[TaskState] = []
        for task in self.config.tasks:
            try:
                states.append(self.inspect_task(task))
            except Exception as exc:
                session_name = self.build_session_name(task)
                self.logger.exception("Failed to inspect task %s", task.name)
                states.append(
                    TaskState(
                        task=task,
                        session_name=session_name,
                        status="error",
                        reason=str(exc),
                    )
                )
        return states
