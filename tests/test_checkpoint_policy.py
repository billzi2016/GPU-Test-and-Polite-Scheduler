"""checkpoint 原子写入测试。"""

from pathlib import Path

from gpu_test_and_polite_scheduler.checkpoint_policy import atomic_write_json, load_json_checkpoint


def test_atomic_write_and_load(tmp_path: Path) -> None:
    # 这里验证的是最核心的不变量：写进去什么，读出来就是什么。
    path = tmp_path / "latest.json"
    atomic_write_json(path, {"step": 3})
    assert load_json_checkpoint(path) == {"step": 3}
