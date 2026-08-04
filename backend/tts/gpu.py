import torch


class GPUManager:

    @staticmethod
    def available():

        return torch.cuda.is_available()

    @staticmethod
    def device():

        if torch.cuda.is_available():
            return "cuda"

        return "cpu"

    @staticmethod
    def gpu_name():

        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)

        return "CPU"