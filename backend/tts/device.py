from dataclasses import dataclass


@dataclass
class DeviceInfo:

    device: str = "cpu"

    gpu_name: str = ""

    cuda_available: bool = False

    total_memory_gb: float = 0.0

    fp16_supported: bool = False