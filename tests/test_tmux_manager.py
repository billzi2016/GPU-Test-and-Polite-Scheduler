"""tmux 封装测试。

这里不真的调用 tmux，而是验证命令拼接是否符合预期。
"""

from unittest.mock import patch

from gpu_test_and_polite_scheduler.tmux_manager import TmuxManager


def test_has_session_returns_true_when_tmux_succeeds() -> None:
    # has-session 返回 0 时，应被解释为 session 存在。
    manager = TmuxManager()
    with patch("gpu_test_and_polite_scheduler.tmux_manager.run_command", return_value=(0, "", "")):
        assert manager.has_session("demo") is True


def test_send_command_appends_log_redirection() -> None:
    # 任务命令会被追加重定向，避免 stdout/stderr 丢失。
    manager = TmuxManager()
    with patch("gpu_test_and_polite_scheduler.tmux_manager.run_command", return_value=(0, "", "")) as mocked:
        manager.send_command("demo", "python run.py", log_file="logs/demo.log")
        args = mocked.call_args[0][0]
        assert args[:4] == ["tmux", "send-keys", "-t", "demo"]
        assert "logs/demo.log" in args[4]
