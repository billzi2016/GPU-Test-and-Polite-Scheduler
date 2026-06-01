"""调度策略测试。

这些测试聚焦“礼貌恢复”决策本身，不依赖真实 GPU 或 tmux。
"""

from gpu_test_and_polite_scheduler.config_loader import SchedulerConfig, TaskConfig
from gpu_test_and_polite_scheduler.scheduler import Scheduler


class FakeTmuxManager:
    def __init__(self) -> None:
        self.sessions: set[str] = set()
        self.restarted: list[str] = []

    def has_session(self, session_name: str) -> bool:
        return session_name in self.sessions

    def restart_session(self, session_name: str, command: str, workdir: str | None = None, log_file: str | None = None) -> None:
        self.sessions.add(session_name)
        self.restarted.append(session_name)


class FakeScheduler(Scheduler):
    def __init__(self, config: SchedulerConfig, busy: bool) -> None:
        # 通过覆写 gpu_is_busy，把测试重点收缩到策略分支本身。
        super().__init__(config=config, tmux_manager=FakeTmuxManager())
        self._busy = busy

    def gpu_is_busy(self, gpu_id: int) -> bool:
        return self._busy


def _config() -> SchedulerConfig:
    # 用一份最小配置复用到多个测试用例里。
    return SchedulerConfig(
        poll_interval_seconds=60,
        gpu_busy_threshold_percent=5,
        watchdog_session_name="gpu-watchdog",
        log_dir="logs",
        auto_restart=True,
        tasks=[TaskConfig(name="demo", gpu_id=0, command="python run.py")],
    )


def test_busy_gpu_waits_instead_of_restarting() -> None:
    # 目标卡忙碌时，应返回 waiting，而不是强行重启任务。
    scheduler = FakeScheduler(_config(), busy=True)
    state = scheduler.inspect_all()[0]
    assert state.status == "waiting"


def test_idle_gpu_restarts_missing_task() -> None:
    # 目标卡空闲时，缺失 session 的任务应被重新拉起。
    scheduler = FakeScheduler(_config(), busy=False)
    state = scheduler.inspect_all()[0]
    assert state.status == "running"
