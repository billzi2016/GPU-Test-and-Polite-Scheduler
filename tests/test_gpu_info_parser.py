"""GPU 信息解析测试。

这里不依赖真实 GPU，而是直接 mock `nvidia-smi` 输出，
保证解析逻辑在无卡环境下也能被验证。
"""

from unittest.mock import patch

from gpu_test_and_polite_scheduler.gpu_info import get_cuda_version, get_driver_version, list_gpu_statuses


def test_get_driver_and_cuda_version() -> None:
    # 驱动和 CUDA 版本都来自同一段 nvidia-smi 文本。
    fake_output = "Driver Version: 550.54.14    CUDA Version: 12.4"
    with patch("gpu_test_and_polite_scheduler.gpu_info.get_nvidia_smi_output", return_value=fake_output):
        assert get_driver_version() == "550.54.14"
        assert get_cuda_version() == "12.4"


def test_list_gpu_statuses() -> None:
    # query-gpu 返回的是 CSV，这里验证字段切分和类型转换都正常。
    fake_csv = "0, NVIDIA A100, 40960, 1024, 3\n1, NVIDIA A100, 40960, 2048, 0"
    with patch("gpu_test_and_polite_scheduler.gpu_info.run_command", return_value=(0, fake_csv, "")):
        statuses = list_gpu_statuses()
        assert len(statuses) == 2
        assert statuses[0].index == 0
        assert statuses[1].memory_used_mb == 2048
