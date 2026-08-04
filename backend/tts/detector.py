import torch

from backend.tts.device import DeviceInfo


class DeviceDetector:

    def detect(self):

        info = DeviceInfo()

        if torch.cuda.is_available():

            info.device = "cuda"

            info.cuda_available = True

            info.gpu_name = torch.cuda.get_device_name(0)

            props = torch.cuda.get_device_properties(0)

            info.total_memory_gb = round(
                props.total_memory / 1024**3,
                2,
            )

            info.fp16_supported = True

        return info