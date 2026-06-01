# GPU-Test-and-Polite-Scheduler

一个面向共享 GPU 服务器的轻量级工具集，解决两类问题：

- GPU 环境、压测、多卡通信测试
- 基于 `tmux` 的后台任务守护与礼貌型自动恢复

## 功能概览

- 环境检查：打印 `nvidia-smi`、`nvidia-smi topo -m`、CUDA/驱动/GPU 信息
- 压力测试：对指定 GPU 持续执行矩阵乘法，观察温度、功耗、利用率
- 通信测试：对指定多卡执行基础 `all_reduce` 测试并统计耗时/带宽
- 礼貌调度：任务异常退出后，不立刻重启；先检查目标卡利用率，空闲时再恢复

## 目录

- [PRD.md](./PRD.md)：产品需求文档
- [DOC_TREE.md](./DOC_TREE.md)：建议文件树与职责
- [TASK.md](./TASK.md)：开发任务清单

## 依赖

- Linux
- NVIDIA 驱动
- `nvidia-smi`
- `tmux`
- `python3`
- PyTorch（建议用户根据本机 CUDA 环境自行安装匹配版本）

基础 Python 依赖可先安装：

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 环境检查

```bash
bash scripts/test_env.sh
```

### 2. 压力测试

```bash
bash scripts/start_stress_test.sh --gpus 0
```

另开终端观察：

```bash
watch -n 1 nvidia-smi
```

### 3. 多卡通信测试

```bash
bash scripts/start_comm_test.sh --gpus 0,1
```

### 4. 启动守护调度

```bash
bash scripts/start_watchdog.sh configs/scheduler.example.yaml
```

## 配置说明

调度配置示例见：

- [configs/scheduler.example.yaml](./configs/scheduler.example.yaml)

## 断点续传任务规范

原子化保存与恢复示例见：

- [examples/example_atomic_task.py](./examples/example_atomic_task.py)
- [docs/atomic_task_spec.md](./docs/atomic_task_spec.md)

## 注意

- 本项目优先面向单机共享 GPU 场景，不替代 Slurm 等集群调度器
- “有人在使用”的默认判定基于 GPU 利用率阈值，可能存在误判
- 当前实现以准确、可读、可扩展为主；具体环境适配可再逐步调整
