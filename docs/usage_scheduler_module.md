# 调度模块使用说明

## 1. 修改配置

参考：

- [../configs/scheduler.example.yaml](../configs/scheduler.example.yaml)

每个任务至少需要：

- `name`
- `gpu_id`
- `command`
- `workdir`
- `log_file`

## 2. 启动守护

```bash
bash scripts/start_watchdog.sh configs/scheduler.example.yaml
```

## 3. 查看任务

```bash
tmux ls
```

单个任务默认会被放进形如 `gps-<task-name>` 的 session。

## 4. 停止守护

```bash
bash scripts/stop_watchdog.sh
```

## 5. 礼貌恢复策略

- 任务 session 存在：认为任务正在运行
- 任务 session 缺失：进入恢复判断
- 若目标 GPU 利用率大于阈值：等待，不重启
- 若目标 GPU 利用率小于等于阈值：重新拉起任务
