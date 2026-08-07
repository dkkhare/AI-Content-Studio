from __future__ import annotations

import json
import shlex
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any


class LocalCLIImageProvider:
    """Run a locally installed image generator through a configurable CLI template."""

    provider_id = "local_cli"

    def __init__(self, executable: str, argument_template: str):
        self.executable = str(executable or "").strip()
        self.argument_template = str(argument_template or "").strip()

    def configured(self) -> bool:
        return bool(self.executable and self.argument_template)

    def generate(
        self,
        *,
        prompt: str,
        output: str | Path,
        negative_prompt: str = "",
        references: list[str] | None = None,
        width: int = 1024,
        height: int = 1024,
        seed: int = -1,
    ) -> Path:
        if not self.configured():
            raise ValueError("Local image CLI is not configured.")
        target = Path(output).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        reference = (references or [""])[0] if references else ""
        values = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "output": str(target),
            "reference": str(reference),
            "width": str(int(width)),
            "height": str(int(height)),
            "seed": str(int(seed)),
        }
        rendered = self.argument_template.format(**values)
        command = [self.executable, *shlex.split(rendered)]
        subprocess.run(command, check=True)
        if not target.exists():
            raise RuntimeError(f"Local image generator did not create {target}")
        return target


class ComfyUIProvider:
    """Submit a prepared workflow to a locally running ComfyUI HTTP API."""

    provider_id = "comfyui"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        workflow_file: str = "",
        *,
        timeout_seconds: float = 300.0,
    ):
        self.base_url = str(base_url or "http://127.0.0.1:8188").rstrip("/")
        self.workflow_file = str(workflow_file or "").strip()
        self.timeout_seconds = float(timeout_seconds)

    def configured(self) -> bool:
        return bool(self.workflow_file and Path(self.workflow_file).exists())

    def _workflow(self, **values) -> dict[str, Any]:
        if not self.configured():
            raise ValueError("ComfyUI workflow file is not configured or does not exist.")
        text = Path(self.workflow_file).read_text(encoding="utf-8")
        for key, value in values.items():
            text = text.replace("{{" + key + "}}", str(value))
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("ComfyUI workflow must contain a JSON object.")
        return payload

    def generate(
        self,
        *,
        prompt: str,
        output: str | Path,
        negative_prompt: str = "",
        references: list[str] | None = None,
        width: int = 1024,
        height: int = 1024,
        seed: int = -1,
    ) -> Path:
        target = Path(output).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        workflow = self._workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            reference=(references or [""])[0] if references else "",
            width=int(width),
            height=int(height),
            seed=int(seed),
            output=str(target),
        )
        request = urllib.request.Request(
            self.base_url + "/prompt",
            data=json.dumps({"prompt": workflow}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            queued = json.loads(response.read().decode("utf-8"))
        prompt_id = str(queued.get("prompt_id", ""))
        if not prompt_id:
            raise RuntimeError("ComfyUI did not return a prompt_id.")

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            with urllib.request.urlopen(self.base_url + f"/history/{prompt_id}", timeout=15) as response:
                history = json.loads(response.read().decode("utf-8"))
            if prompt_id in history:
                if target.exists():
                    return target
                raise RuntimeError(
                    "ComfyUI completed but the configured workflow did not write the requested output path. "
                    "Use an output node/workflow wrapper that writes {{output}}."
                )
            time.sleep(1.0)
        raise TimeoutError("Timed out waiting for local ComfyUI image generation.")


def create_image_provider(project):
    provider_id = str(project.get_setting("image_provider", "local_cli") or "local_cli").lower()
    if provider_id == "comfyui":
        return ComfyUIProvider(
            base_url=str(project.get_setting("comfyui_url", "http://127.0.0.1:8188")),
            workflow_file=str(project.get_setting("comfyui_workflow_file", "")),
            timeout_seconds=float(project.get_setting("image_generation_timeout_seconds", 300.0)),
        )
    if provider_id == "local_cli":
        return LocalCLIImageProvider(
            executable=str(project.get_setting("image_cli_executable", "")),
            argument_template=str(project.get_setting("image_cli_arguments", "")),
        )
    raise ValueError(f"Unsupported local image provider: {provider_id}")
