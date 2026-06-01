"""配置加载测试。

这些测试只验证“能否把示例配置正确转成 dataclass”，
不覆盖更复杂的业务联动。
"""

from pathlib import Path

from gpu_test_and_polite_scheduler.config_loader import load_scheduler_config


def test_load_scheduler_config(tmp_path: Path) -> None:
    # 用最小可运行配置验证字段是否被正确解析。
    config_path = tmp_path / "scheduler.yaml"
    config_path.write_text(
        """
poll_interval_seconds: 30
gpu_busy_threshold_percent: 7
watchdog_session_name: gpu-watchdog
log_dir: logs
auto_restart: true
tasks:
  - name: demo
    gpu_id: 0
    command: "python run.py"
    workdir: "."
    log_file: "logs/demo.log"
""".strip(),
        encoding="utf-8",
    )

    config = load_scheduler_config(config_path)
    assert config.poll_interval_seconds == 30
    assert config.gpu_busy_threshold_percent == 7
    assert config.tasks[0].name == "demo"
