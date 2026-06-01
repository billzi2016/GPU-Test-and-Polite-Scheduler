from __future__ import annotations

"""日志初始化模块。

当前项目规模还不需要引入复杂 logging 配置文件，因此这里直接在代码里统一约定。
"""

import logging
from pathlib import Path


def setup_logger(name: str, log_file: str | None = None, level: int = logging.INFO) -> logging.Logger:
    # 所有模块共用这一套日志格式，便于后续排查 watchdog 与任务状态。
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        # 避免重复初始化导致日志重复打印。
        return logger

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        # 文件日志按需启用，适合守护进程长期留痕。
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
