# GPU-Test-and-Polite-Scheduler

一个面向共享 GPU 服务器的新手友好工具集，用来做两件事：

1. 检查 GPU 环境是否正常，顺手做压测和多卡通信测试
2. 用 `tmux` 托管长任务，并在共享环境里尽量“礼貌”地等待空闲 GPU 再恢复任务

如果你经常遇到这些问题，这个项目就是给你的：

- 不确定机器上的 CUDA、驱动、GPU 拓扑是不是正常
- 想先压一压卡，看看温度、功耗、利用率稳不稳
- 想跑多卡任务，但不确定卡之间通信有没有问题
- 想把长时间训练/采样任务丢到后台跑，又不想和别人抢卡

## 这个项目能做什么

### 1. 环境检查

运行一次就能看到：

- `nvidia-smi`
- `nvidia-smi topo -m`
- 驱动版本
- CUDA 版本
- 可见 GPU 列表
- `nvidia-smi`、`tmux`、`python3` 是否可用

### 2. GPU 压力测试

对指定 GPU 持续做矩阵乘法，让你观察：

- GPU 利用率能不能稳定拉高
- 温度会不会持续升高
- 有没有掉卡、报错、OOM 之类的问题

### 3. 多卡通信测试

对多张 GPU 做基础 `all_reduce` 通信测试，用来快速判断：

- 多卡能不能正常协同
- 通信是否明显异常
- topo 和通信结果是否对得上

### 4. 礼貌型后台调度

你的任务如果异常退出，调度器不会立刻强行重启，而是先看目标 GPU 当前是否忙碌：

- 利用率高于阈值：先等待
- 利用率低于等于阈值：再恢复任务

这比较适合共享服务器，不容易和别人直接撞资源。

## 适合谁

这个项目适合：

- 实验室或团队共享 GPU 服务器的用户
- 想先验卡、再跑任务的人
- 有长时间训练/采样任务，需要 `tmux` 守护的人

这个项目不适合：

- 需要集群级调度的人
- 需要 Slurm / Kubernetes / Ray 这类完整平台的人
- 想做多机统一资源管理的人

## 运行环境

- Linux
- NVIDIA GPU
- NVIDIA 驱动
- `nvidia-smi`
- `tmux`
- `python3`

Python 基础依赖：

```bash
pip install -r requirements.txt
```

注意：

- `torch` 没有写死在 `requirements.txt` 里
- 原因是 `torch` 和 CUDA 版本强相关
- 你需要按自己机器的 CUDA 环境单独安装匹配版本的 PyTorch

## 给新手的最短上手路径

如果你是第一次用，建议按这个顺序来。

### 第一步：先检查环境

```bash
bash scripts/test_env.sh
```

你会看到：

- 当前 `nvidia-smi`
- 当前 `nvidia-smi topo -m`
- GPU 摘要信息

如果这一步都不正常，就先不要急着跑训练。

### 第二步：做单卡压测

```bash
bash scripts/start_stress_test.sh --gpus 0
```

另开一个终端观察：

```bash
watch -n 1 nvidia-smi
```

你主要看三件事：

- `GPU-Util` 能不能稳定接近高负载
- 温度是否持续上升
- 程序是否很快报错退出

### 第三步：做多卡通信测试

如果你要用多卡，再跑：

```bash
bash scripts/start_comm_test.sh --gpus 0,1
```

这一步会先打印 topo，再跑通信测试。

### 第四步：最后再上调度器

先看示例配置：

- [configs/scheduler.example.yaml](./configs/scheduler.example.yaml)

再启动 watchdog：

```bash
bash scripts/start_watchdog.sh configs/scheduler.example.yaml
```

默认会把 watchdog 自己也放进 `tmux` 里后台运行。

## 一个典型使用流程

你可以把这个项目理解成下面这个流程：

1. 用 `test_env.sh` 看机器是不是正常
2. 用 `start_stress_test.sh` 看 GPU 能不能稳定跑
3. 用 `start_comm_test.sh` 看多卡通信是不是正常
4. 把你自己的任务改造成“支持断点续传”
5. 用 `start_watchdog.sh` 托管任务
6. 让任务在共享环境里按“空闲就跑、有人就让、挂了再恢复”的方式运行

## 如何让你自己的任务接入调度器

重点不是“把命令丢给 tmux”，而是让你的任务本身支持恢复。

你自己的任务最好满足这三点：

1. 定期保存 checkpoint
2. 保存时用临时文件 + 原子替换，避免写坏文件
3. 启动时自动读取最近一次有效 checkpoint

可以先参考：

- [examples/example_atomic_task.py](./examples/example_atomic_task.py)
- [examples/example_resume_task.sh](./examples/example_resume_task.sh)
- [docs/atomic_task_spec.md](./docs/atomic_task_spec.md)

## 配置文件说明

目前主要有三类示例配置：

- [configs/stress_test.example.yaml](./configs/stress_test.example.yaml)：压测配置
- [configs/comm_test.example.yaml](./configs/comm_test.example.yaml)：通信测试配置
- [configs/scheduler.example.yaml](./configs/scheduler.example.yaml)：调度配置

调度配置里最重要的字段通常是：

- `tasks`：要托管的任务列表
- `gpu_id`：任务绑定的目标 GPU
- `command`：真正执行的命令
- `poll_interval_seconds`：watchdog 轮询间隔
- `gpu_busy_threshold_percent`：判定“这张卡可能有人在用”的阈值

## Docker 支持

仓库已经包含：

- [Dockerfile](./Dockerfile)
- [requirements.txt](./requirements.txt)

当前 `Dockerfile` 使用：

- `nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04`

注意：

- 它是项目基础镜像，不是“一切都帮你配好”的最终生产镜像
- 容器里默认不安装 `torch`
- 真正使用 GPU 还需要宿主机安装 NVIDIA 驱动和 `NVIDIA Container Toolkit`

## 项目结构

如果你想继续改这个项目，可以先看这几份文档：

- [PRD.md](./PRD.md)：产品需求文档
- [DOC_TREE.md](./DOC_TREE.md)：目录结构和每个文件干什么
- [TASK.md](./TASK.md)：开发任务清单

## 当前状态

当前仓库已经包含第一版：

- 文档
- 配置样例
- 环境检查
- 压力测试
- 通信测试
- `tmux` 调度
- watchdog 守护
- 示例任务
- 基础单元测试

基础单元测试已通过。

但要说明白一件事：

- 真实 GPU 压测
- 真实 NCCL 多卡通信
- 真实 `tmux` 后台守护行为

这些仍然需要你在目标 Linux + NVIDIA 机器上实际跑一遍确认。

## 常见注意事项

### 1. 为什么 `requirements.txt` 里没有 `torch`

因为 PyTorch 和 CUDA 强绑定，直接写死很容易让别人一装就冲突。

### 2. 为什么判断“别人是否在用卡”只看 GPU 利用率

这是第一版的简化策略，足够轻量，但确实可能误判。后面可以继续扩展成“利用率 + 显存占用”双判断。

### 3. 这个项目会不会抢占别人的卡

它的设计目标正好相反，是尽量不要在共享环境里粗暴抢占资源。

## 后续可以怎么扩展

如果你准备继续做第二版，比较自然的方向有：

- 增加显存占用阈值判断
- 增加失败重试次数限制
- 增加告警
- 增加更清晰的任务状态展示
- 增加简单 TUI / Web 面板

## 许可证

当前仓库还没有单独添加 LICENSE 文件。你如果需要，我可以下一步继续补。
