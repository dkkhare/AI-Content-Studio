import torch


class GPUVerifier:

    @staticmethod
    def cuda():

        return torch.cuda.is_available()

    @staticmethod
    def memory():

        if not torch.cuda.is_available():

            return 0

        return torch.cuda.get_device_properties(
            0
        ).total_memory