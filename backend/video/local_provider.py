from __future__ import annotations

import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class VideoGenerationRequest:
    prompt: str
    output: Path
    image: Path | None = None


class LocalCommandVideoProvider:
    """Run a locally installed open-source video generator through its CLI.

    The argument template is intentionally generic so the same adapter can drive
    Wan, LTX-Video, CogVideoX wrappers, or another local command. Supported
    placeholders are ``{prompt}``, ``{output}``, and ``{image}``.
    """

    provider_id = "local-command"

    def __init__(
        self,
        command: str,
        args_template: str,
        *,
        runner: Callable[..., subprocess.CompletedProcess] | None = None,
    ):
        self.command = str(command or "").strip()
        self.args_template = str(args_template or "").strip()
        self._runner = runner or subprocess.run

    def available(self) -> bool:
        if not self.command:
            return False
        path = Path(self.command)
        if path.exists() and path.is_file():
            return True
        return shutil.which(self.command) is not None

    def _arguments(self, request: VideoGenerationRequest) -> list[str]:
        if not request.prompt.strip():
            raise ValueError("Local video generation requires a non-empty prompt.")

        values = {
            "prompt": request.prompt,
            "output": str(request.output.resolve()),
            "image": str(request.image.resolve()) if request.image else "",
        }
        try:
            rendered = self.args_template.format(**values)
        except KeyError as exc:
            raise ValueError(f"Unsupported local video argument placeholder: {exc}") from exc
        return shlex.split(rendered, posix=False)

    def generate(self, request: VideoGenerationRequest) -> Path:
        if not self.available():
            raise RuntimeError(
                "Local video generator was not found. Configure video_generator_command "
                "with the executable or launcher for your installed model."
            )

        request.output.parent.mkdir(parents=True, exist_ok=True)
        request.output.unlink(missing_ok=True)

        command = [self.command, *self._arguments(request)]
        result = self._runner(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Unknown local generator error").strip()
            raise RuntimeError(f"Local video generation failed: {detail}")
        if not request.output.exists() or not request.output.is_file():
            raise RuntimeError(
                "Local video generator completed without creating the configured output file."
            )
        return request.output
