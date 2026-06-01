from __future__ import annotations

"""checkpoint 保存与恢复规范。

这个文件只放最小的一组原子写入辅助函数，不直接绑定训练框架。
这样无论用户是做训练、采样还是推理缓存，都可以复用同一套保存策略。
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    """将 JSON checkpoint 原子写入目标路径。"""

    # 先写临时文件，再原子替换正式文件，尽量避免半写入 checkpoint。
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", delete=False, dir=target.parent, encoding="utf-8") as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp.flush()
        # fsync 能降低异常中断后数据仍停留在页缓存中的风险。
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)

    # os.replace 在同一文件系统内通常是原子操作，适合拿来“提交”新 checkpoint。
    os.replace(tmp_path, target)
    return target


def load_json_checkpoint(path: str | Path) -> dict[str, Any] | None:
    """读取 JSON checkpoint，不存在时返回 None。"""

    # 不存在 checkpoint 时返回 None，交给上层决定是否从头开始。
    checkpoint = Path(path)
    if not checkpoint.exists():
        return None
    with checkpoint.open("r", encoding="utf-8") as handle:
        return json.load(handle)
