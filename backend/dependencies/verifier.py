import socket

from backend.dependencies.ffmpeg import (
    FFmpegVerifier
)

from backend.dependencies.gpu import (
    GPUVerifier
)

from backend.dependencies.registry import MODELS

from backend.dependencies.status import (
    DependencyStatus
)


class DependencyVerifier:

    def internet(self):

        try:

            socket.create_connection(
                ("8.8.8.8", 53),
                timeout=2,
            )

            return True

        except Exception:

            return False

    def verify(self):

        installed = sum(
            m.installed
            for m in MODELS
        )

        return DependencyStatus(

            python_ok=True,

            ffmpeg_ok=FFmpegVerifier.exists(),

            cuda_ok=GPUVerifier.cuda(),

            internet=self.internet(),

            installed_models=installed,

            total_models=len(MODELS),

        )