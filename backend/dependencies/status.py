from dataclasses import dataclass


@dataclass
class DependencyStatus:

    python_ok: bool

    ffmpeg_ok: bool

    cuda_ok: bool

    internet: bool

    installed_models: int

    total_models: int