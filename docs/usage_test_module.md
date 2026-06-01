# 测试模块使用说明

## 环境检查

```bash
bash scripts/test_env.sh
```

输出会包含：

- `nvidia-smi`
- `nvidia-smi topo -m`
- 驱动版本
- CUDA 版本
- 可见 GPU 列表和基础状态

## 压力测试

```bash
bash scripts/start_stress_test.sh --gpus 0 --matrix-size 8192
```

另开终端观察：

```bash
watch -n 1 nvidia-smi
```

## 通信测试

```bash
bash scripts/start_comm_test.sh --gpus 0,1
```

运行前会打印 topo 信息，帮助确认参与测试设备的链路关系。
