# GPU-Test-and-Polite-Scheduler 开发任务清单

本文档用于把项目需求拆成可执行任务。所有条目都使用 Markdown checkbox，便于逐项推进和勾选。

## 1. 项目初始化

- [x] 创建 `README.md` 基础结构
- [x] 确认 `PRD.md` 内容与项目范围一致
- [x] 创建 `DOC_TREE.md` 并固定建议目录结构
- [x] 创建 `.gitignore`
- [x] 创建 `requirements.txt`
- [x] 创建 `pyproject.toml`
- [x] 初始化 `src/gpu_test_and_polite_scheduler/` 包结构
- [x] 初始化 `configs/`、`scripts/`、`examples/`、`docs/`、`logs/`、`outputs/`、`tests/` 目录

## 2. 环境检查模块

- [x] 设计环境检查输出格式
- [x] 实现 GPU 基础信息采集模块
- [x] 实现 `nvidia-smi` 原始输出展示
- [x] 实现 `nvidia-smi topo -m` 原始输出展示
- [x] 实现 CUDA 版本信息读取
- [x] 实现驱动版本读取
- [x] 实现 GPU 列表和显存信息展示
- [x] 实现环境检查入口脚本 `scripts/test_env.sh`
- [x] 编写环境检查使用说明

## 3. GPU 压力测试模块

- [x] 设计压力测试参数格式
- [x] 实现单卡矩阵乘法压测
- [x] 实现多卡独立压测
- [x] 增加显式同步，确保真实负载
- [x] 支持持续运行直到手动中断
- [x] 支持定期打印迭代状态
- [x] 启动压测前打印当前 `nvidia-smi`
- [x] 编写压测入口脚本 `scripts/start_stress_test.sh`
- [x] 编写压测使用说明

## 4. 多卡通信测试模块

- [x] 设计通信测试参数格式
- [x] 实现多卡参与设备选择逻辑
- [x] 实现基础通信测试主流程
- [x] 输出通信耗时统计
- [x] 输出有效带宽或等价指标
- [x] 测试前打印 `nvidia-smi topo -m`
- [x] 异常情况下输出可定位错误信息
- [x] 编写通信测试入口脚本 `scripts/start_comm_test.sh`
- [x] 编写通信测试使用说明

## 5. 原子任务与断点续传规范

- [x] 定义 checkpoint 保存规范
- [x] 定义临时文件写入再原子替换规范
- [x] 定义任务启动恢复规范
- [x] 编写 `examples/example_atomic_task.py`
- [x] 编写 `examples/example_resume_task.sh`
- [x] 编写 `docs/atomic_task_spec.md`

## 6. 配置系统

- [x] 确定配置文件格式使用 YAML 还是 JSON
- [x] 设计调度配置字段
- [x] 实现配置加载模块
- [x] 实现配置字段校验
- [x] 编写 `configs/scheduler.example.yaml`
- [x] 编写 `configs/stress_test.example.yaml`
- [x] 编写 `configs/comm_test.example.yaml`

## 7. tmux 管理模块

- [x] 实现创建 session 逻辑
- [x] 实现查询 session 是否存在
- [x] 实现向 session 下发命令
- [x] 实现重启 session 逻辑
- [x] 实现停止 session 逻辑
- [ ] 统一 tmux 日志与错误处理

## 8. 调度与守护模块

- [x] 设计任务状态模型
- [x] 实现任务初始化部署逻辑
- [x] 实现 watchdog 主循环
- [x] 实现默认每分钟轮询
- [x] 实现异常退出检测
- [x] 实现 GPU 利用率检查
- [x] 实现“利用率 > 5% 不重启”策略
- [x] 实现“利用率 <= 5% 自动恢复”策略
- [x] 防止同一任务被重复拉起
- [x] 实现守护入口脚本 `scripts/start_watchdog.sh`
- [x] 实现停止守护脚本 `scripts/stop_watchdog.sh`
- [x] 编写调度模块使用说明

## 9. 日志与输出

- [x] 设计统一日志格式
- [x] 实现控制台日志输出
- [x] 实现文件日志输出
- [x] 设计 watchdog 日志内容
- [x] 设计测试结果输出目录规则
- [x] 明确 checkpoint、日志、输出的目录约定

## 10. CLI 与统一入口

- [x] 设计统一命令行接口
- [x] 实现 `env-check` 子命令
- [x] 实现 `stress-test` 子命令
- [x] 实现 `comm-test` 子命令
- [x] 实现 `watchdog` 子命令
- [x] 统一参数帮助信息

## 11. 测试与验证

- [x] 编写配置加载测试
- [x] 编写 GPU 信息解析测试
- [x] 编写 tmux 管理测试
- [x] 编写调度策略测试
- [x] 编写 checkpoint 规范测试
- [ ] 验证环境检查输出是否完整
- [ ] 验证压测时 GPU 利用率是否可稳定拉高
- [ ] 验证 topo 信息是否按预期打印
- [ ] 验证通信测试结果是否可读
- [ ] 验证任务退出后是否按礼貌策略恢复

## 12. 第一阶段交付前检查

- [x] README 可让新用户快速上手
- [x] PRD、DOC_TREE、TASK 三份文档保持一致
- [ ] 环境检查主链路可用
- [ ] 压力测试主链路可用
- [ ] 多卡通信测试主链路可用
- [ ] `tmux` 部署主链路可用
- [ ] watchdog 巡检主链路可用
- [ ] 礼貌恢复策略主链路可用
- [x] 示例任务可展示断点续传
- [x] 日志与输出目录行为清晰

## 13. 可选后续任务

- [ ] 增加显存占用阈值判断
- [ ] 增加任务重启次数限制
- [ ] 增加失败告警机制
- [ ] 增加简单 TUI 或 Web 面板
- [ ] 支持多机统一管理
- [ ] 支持更细粒度的资源判定策略
