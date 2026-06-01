# GPU-Test-and-Polite-Scheduler 文档树与文件职责

本文档用于约定仓库建议目录结构，以及每个目录、文件分别负责什么。目标是让项目从一开始就具备清晰边界，便于逐步实现、维护和扩展。

## 1. 建议文件树

```text
GPU-Test-and-Polite-Scheduler/
├── README.md
├── PRD.md
├── DOC_TREE.md
├── TASK.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── configs/
│   ├── scheduler.example.yaml
│   ├── stress_test.example.yaml
│   └── comm_test.example.yaml
├── scripts/
│   ├── test_env.sh
│   ├── start_stress_test.sh
│   ├── start_comm_test.sh
│   ├── start_watchdog.sh
│   └── stop_watchdog.sh
├── src/
│   └── gpu_test_and_polite_scheduler/
│       ├── __init__.py
│       ├── cli.py
│       ├── env_check.py
│       ├── gpu_info.py
│       ├── stress_test.py
│       ├── comm_test.py
│       ├── tmux_manager.py
│       ├── scheduler.py
│       ├── watchdog.py
│       ├── checkpoint_policy.py
│       ├── config_loader.py
│       ├── logger.py
│       └── utils.py
├── examples/
│   ├── example_atomic_task.py
│   ├── example_resume_task.sh
│   └── sample_scheduler.yaml
├── docs/
│   ├── atomic_task_spec.md
│   ├── usage_test_module.md
│   └── usage_scheduler_module.md
├── logs/
│   └── .gitkeep
├── outputs/
│   └── .gitkeep
└── tests/
    ├── test_config_loader.py
    ├── test_gpu_info_parser.py
    ├── test_tmux_manager.py
    ├── test_scheduler_policy.py
    └── test_checkpoint_policy.py
```

## 2. 顶层文件说明

### `README.md`

- 仓库首页说明
- 负责介绍项目用途、安装方式、快速开始、常见命令
- 面向第一次进入仓库的用户

### `PRD.md`

- 产品需求文档
- 负责描述项目目标、模块边界、功能需求、验收标准
- 面向需求设计和范围确认

### `DOC_TREE.md`

- 目录结构与文件职责说明
- 负责回答“仓库为什么这样组织”“每个文件干什么”
- 面向开发前的结构约定

### `TASK.md`

- 开发任务清单
- 负责把 PRD 拆成可执行事项，并支持逐项打勾
- 面向实际开发推进

### `requirements.txt`

- Python 运行依赖列表
- 用于快速安装基础依赖
- 适合轻量使用场景

### `pyproject.toml`

- Python 项目元信息和工具配置
- 可用于管理格式化、测试、打包等工具配置
- 如果项目后续标准化，优先以它为中心

### `.gitignore`

- 定义不应提交到仓库的文件
- 例如日志、输出、缓存、临时 checkpoint

## 3. 配置目录说明

### `configs/scheduler.example.yaml`

- 调度器示例配置
- 用于定义任务列表、目标 GPU、轮询周期、空闲阈值、日志路径等

### `configs/stress_test.example.yaml`

- 压力测试示例配置
- 用于定义测试 GPU、矩阵规模、并发数、输出频率等

### `configs/comm_test.example.yaml`

- 多卡通信测试示例配置
- 用于定义参与通信测试的 GPU、测试轮数、数据规模等

## 4. 脚本目录说明

### `scripts/test_env.sh`

- 环境检查入口脚本
- 负责调用基础检查逻辑，打印：
  - `nvidia-smi`
  - `nvidia-smi topo -m`
  - CUDA/驱动/GPU 列表
- 用于用户第一次验卡或排查环境问题

### `scripts/start_stress_test.sh`

- GPU 压力测试启动脚本
- 负责读取参数或配置，调用压力测试模块
- 启动前应打印当前 `nvidia-smi` 状态

### `scripts/start_comm_test.sh`

- 多卡通信测试启动脚本
- 负责调用通信测试模块
- 启动前应打印 topo 信息，帮助用户确认链路关系

### `scripts/start_watchdog.sh`

- 调度守护主入口
- 负责启动 watchdog 和任务部署逻辑

### `scripts/stop_watchdog.sh`

- 停止守护进程的辅助脚本
- 负责优雅停止后台巡检和对应控制进程

## 5. 核心源码目录说明

目录：`src/gpu_test_and_polite_scheduler/`

### `__init__.py`

- Python 包入口文件
- 负责声明包版本或基础导出

### `cli.py`

- 统一命令行入口
- 负责把环境检查、压测、通信测试、守护调度等子命令组织起来

### `env_check.py`

- 环境检查模块
- 负责执行基础信息收集和展示
- 输出重点包括：
  - `nvidia-smi`
  - `nvidia-smi topo -m`
  - CUDA 版本
  - 驱动版本
  - GPU 列表

### `gpu_info.py`

- GPU 信息采集与解析模块
- 负责封装对 `nvidia-smi`、topo、利用率、显存占用等信息的读取和解析
- 为测试模块和调度模块提供统一数据接口

### `stress_test.py`

- GPU 压力测试模块
- 负责执行单卡或多卡矩阵乘法 burn-in
- 需要保证有明确同步，避免假负载

### `comm_test.py`

- 多卡通信测试模块
- 负责验证多卡连通性、通信耗时和带宽表现

### `tmux_manager.py`

- `tmux` 管理模块
- 负责创建、查询、重启、销毁 session
- 给调度器提供统一的 tmux 操作接口

### `scheduler.py`

- 调度策略模块
- 负责根据配置初始化任务，并决定何时启动、等待、重试

### `watchdog.py`

- 后台守护模块
- 负责每分钟轮询任务状态、检测异常退出、触发礼貌恢复逻辑

### `checkpoint_policy.py`

- 原子化 checkpoint 规范模块
- 负责定义保存、替换、恢复的基本约束
- 给示例任务和调度系统提供统一约定

### `config_loader.py`

- 配置读取模块
- 负责加载 YAML/JSON 配置，并做必要的字段校验

### `logger.py`

- 日志模块
- 负责统一日志输出格式、日志级别和日志文件路径

### `utils.py`

- 通用辅助函数模块
- 负责放置不适合单独建模块的小型工具函数

## 6. 示例目录说明

### `examples/example_atomic_task.py`

- 原子化任务示例
- 用于演示：
  - 周期性保存 checkpoint
  - 临时文件写入后原子替换
  - 启动时自动恢复

### `examples/example_resume_task.sh`

- 任务恢复启动示例脚本
- 用于演示如何通过 shell 命令启动一个支持断点续跑的任务

### `examples/sample_scheduler.yaml`

- 调度配置示例
- 用于让用户快速复制并修改自己的任务列表

## 7. 文档目录说明

### `docs/atomic_task_spec.md`

- 原子任务规范文档
- 详细解释 checkpoint 为什么要原子写入，以及建议约束

### `docs/usage_test_module.md`

- 测试模块使用说明
- 介绍环境检查、压力测试、多卡通信测试怎么用

### `docs/usage_scheduler_module.md`

- 调度模块使用说明
- 介绍如何配置任务、如何启动守护、如何查看 tmux 状态

## 8. 输出目录说明

### `logs/`

- 运行日志目录
- 保存环境检查日志、压力测试日志、通信测试日志、watchdog 日志

### `outputs/`

- 输出结果目录
- 保存测试结果、任务输出、阶段性中间结果

### `.gitkeep`

- 占位文件
- 用于让空目录也能被仓库保留

## 9. 测试目录说明

### `tests/test_config_loader.py`

- 配置加载测试
- 确保配置解析和校验逻辑正确

### `tests/test_gpu_info_parser.py`

- GPU 信息解析测试
- 确保 `nvidia-smi` 和 topo 输出解析稳定

### `tests/test_tmux_manager.py`

- tmux 管理逻辑测试
- 确保 session 创建、查询、重启逻辑正确

### `tests/test_scheduler_policy.py`

- 调度策略测试
- 确保“有人就让、空闲再启”的策略实现正确

### `tests/test_checkpoint_policy.py`

- checkpoint 规则测试
- 确保恢复逻辑和原子写入约束符合预期

## 10. 当前建议

第一阶段不一定要一次性把所有文件都实现完，但建议先把以下文件优先落地：

- `README.md`
- `PRD.md`
- `DOC_TREE.md`
- `TASK.md`
- `scripts/test_env.sh`
- `src/gpu_test_and_polite_scheduler/env_check.py`
- `src/gpu_test_and_polite_scheduler/gpu_info.py`
- `src/gpu_test_and_polite_scheduler/stress_test.py`
- `src/gpu_test_and_polite_scheduler/comm_test.py`
- `src/gpu_test_and_polite_scheduler/watchdog.py`
- `examples/example_atomic_task.py`
- `configs/scheduler.example.yaml`

这样可以先把“验卡 + 压测 + 通信测试 + 礼貌调度”的主链路搭起来，再逐步补测试和细节。
