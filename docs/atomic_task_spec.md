# 原子任务规范

一个能被本项目安全托管的任务，至少需要满足下面三点：

## 1. 周期性保存

- 任务不能只在结束时保存结果
- 需要在固定步数、固定时间间隔或固定阶段结束时保存 checkpoint

## 2. 原子写入

建议采用以下顺序：

1. 先写入临时文件
2. `flush` + `fsync`
3. 再用原子替换覆盖正式 checkpoint

这样即使任务被强杀，也尽量避免留下半写入文件。

## 3. 启动恢复

任务启动时应：

1. 检查 checkpoint 是否存在
2. 若存在，读取最近一次有效状态
3. 从该状态继续执行，而不是从头开始

## 4. 推荐目录结构

```text
outputs/
└── task-name/
    ├── latest.json
    ├── step_000100.json
    └── run.log
```

## 5. 示例

参考：

- [../examples/example_atomic_task.py](../examples/example_atomic_task.py)
