# 这里直接使用 NVIDIA CUDA 12.4 运行时镜像，更贴近项目真实使用场景。
# 宿主机仍然需要安装 NVIDIA 驱动和 NVIDIA Container Toolkit，容器内才能真正看到 GPU。
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# 关闭交互提示，并让 Python 输出更适合容器日志。
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# tmux 用于调度模块；bash 便于脚本入口执行；git 方便用户在容器内调试仓库。
# 这里显式安装 python3 和 pip，因为 CUDA runtime 镜像默认不自带完整 Python 环境。
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        git \
        python3 \
        python3-pip \
        tmux \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 构建缓存。
COPY requirements.txt ./

RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir -r requirements.txt

# 再复制项目源码。
COPY . .

# 让项目源码默认可被 Python 直接导入。
ENV PYTHONPATH=/app/src

# 默认进入环境检查入口。
# 注意：
# 1. 这个镜像仍然不默认安装 torch，避免把 CUDA 绑定的 torch 版本写死。
# 2. 运行 stress-test / comm-test 前，请按目标环境补装匹配的 torch。
# 3. `nvidia-smi` 是否可见还取决于宿主机驱动和容器运行参数。
CMD ["python3", "-m", "gpu_test_and_polite_scheduler.cli", "env-check"]
