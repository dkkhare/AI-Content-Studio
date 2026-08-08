from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any


class ReadinessService:
    """Probe required and optional runtime dependencies for a project."""

    def __init__(self, project):
        self.project = project
        self.root = Path(project.root).resolve()

    @staticmethod
    def _result(check_id: str, label: str, ok: bool, *, required: bool, detail: str = "", hint: str = "", data: dict[str, Any] | None = None):
        return {
            "id": check_id,
            "label": label,
            "ok": bool(ok),
            "required": bool(required),
            "detail": detail,
            "hint": hint,
            "data": data or {},
        }

    def _project_path(self):
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            probe = self.root / ".readiness_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return self._result("project_path", "Project workspace", True, required=True, detail=str(self.root))
        except Exception as exc:
            return self._result("project_path", "Project workspace", False, required=True, detail=str(exc), hint="Choose a writable project folder.")

    def _ffmpeg(self):
        configured = str(self.project.get_setting("ffmpeg_path", "") or "").strip()
        executable = configured or shutil.which("ffmpeg") or ""
        ok = bool(executable and (Path(executable).is_file() if configured else True))
        return self._result("ffmpeg", "FFmpeg", ok, required=True, detail=executable or "Not found", hint="Install FFmpeg or set ffmpeg_path in the project settings.")

    def _ollama(self):
        required = str(self.project.get_setting("ai_provider", "ollama") or "ollama").lower() == "ollama"
        url = str(self.project.get_setting("ollama_url", "http://127.0.0.1:11434") or "http://127.0.0.1:11434").rstrip("/")
        ok = False
        detail = url
        if required:
            try:
                with urllib.request.urlopen(url + "/api/tags", timeout=1.5) as response:
                    ok = 200 <= int(getattr(response, "status", 200)) < 300
            except Exception as exc:
                detail = f"{url} — {exc}"
        else:
            ok = True
            detail = "Not selected as the active AI provider"
        return self._result("ollama", "Ollama", ok, required=required, detail=detail, hint="Start Ollama and make sure its local API is reachable.")

    def _f5tts(self):
        required = bool(self.project.get_setting("pipeline_narration_enabled", True)) and str(self.project.get_setting("tts_provider", "f5tts") or "f5tts").lower() == "f5tts"
        executable = str(self.project.get_setting("f5tts_executable", "") or "").strip()
        module_ok = importlib.util.find_spec("f5_tts") is not None
        executable_ok = bool(executable and (Path(executable).is_file() or shutil.which(executable)))
        ok = (module_ok or executable_ok) if required else True
        detail = "Python module detected" if module_ok else (executable or "F5-TTS runtime not detected")
        return self._result("f5tts", "F5-TTS", ok, required=required, detail=detail, hint="Install F5-TTS locally or configure f5tts_executable.")

    def _reference_voice(self):
        required = bool(self.project.get_setting("pipeline_narration_enabled", True)) and str(self.project.get_setting("tts_provider", "f5tts") or "f5tts").lower() == "f5tts"
        value = str(self.project.get_setting("f5tts_reference_audio", self.project.get_setting("reference_voice", "")) or "").strip()
        ok = bool(value and Path(value).is_file()) if required else True
        return self._result("reference_voice", "Hindi reference voice", ok, required=required, detail=value or "Not configured", hint="Choose a clean Hindi reference WAV for F5-TTS.")

    def _image_provider(self):
        enabled = bool(self.project.get_setting("pipeline_image_generation_enabled", False))
        provider = str(self.project.get_setting("image_provider", "local_cli") or "local_cli").lower()
        ok = True
        detail = "Image generation disabled"
        hint = ""
        if enabled:
            if provider == "comfyui":
                workflow = str(self.project.get_setting("comfyui_workflow_file", "") or "")
                ok = bool(workflow and Path(workflow).is_file())
                detail = f"ComfyUI workflow: {workflow or 'missing'}"
                hint = "Configure a valid ComfyUI workflow file."
            else:
                executable = str(self.project.get_setting("image_cli_executable", "") or "")
                args = str(self.project.get_setting("image_cli_arguments", "") or "")
                ok = bool(executable and args and (Path(executable).is_file() or shutil.which(executable)))
                detail = executable or "Local image CLI not configured"
                hint = "Configure image_cli_executable and image_cli_arguments."
        return self._result("image_provider", "Local image generation", ok, required=enabled, detail=detail, hint=hint)

    def _video_provider(self):
        enabled = bool(self.project.get_setting("pipeline_video_enabled", False))
        executable = str(self.project.get_setting("video_cli_executable", "") or "")
        args = str(self.project.get_setting("video_cli_arguments", "") or "")
        ok = bool(executable and args and (Path(executable).is_file() or shutil.which(executable))) if enabled else True
        return self._result("video_provider", "Local video generation", ok, required=enabled, detail=(executable or ("Video generation disabled" if not enabled else "Local video CLI not configured")), hint="Configure video_cli_executable and video_cli_arguments for Wan/LTX/CogVideoX wrappers.")

    def _youtube(self):
        provider = str(self.project.get_setting("publishing_provider", "manual") or "manual").lower()
        required = provider == "youtube"
        secrets = str(self.project.get_setting("youtube_client_secrets_path", "") or "")
        packages = all(importlib.util.find_spec(name) is not None for name in ("googleapiclient", "google_auth_oauthlib", "google.auth"))
        ok = (bool(secrets and Path(secrets).is_file()) and packages) if required else True
        detail = "YouTube publishing disabled" if not required else f"OAuth: {secrets or 'missing'}; Google packages: {'ok' if packages else 'missing'}"
        return self._result("youtube", "YouTube publishing", ok, required=required, detail=detail, hint="Install Google API auth packages and select a valid OAuth client-secrets JSON.")

    def _gpu(self):
        command = shutil.which("nvidia-smi")
        if not command:
            return self._result("gpu", "GPU diagnostics", False, required=False, detail="nvidia-smi not found", hint="Optional: install NVIDIA drivers if GPU acceleration is expected.")
        try:
            result = subprocess.run([command, "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=3, check=True)
            detail = result.stdout.strip() or "NVIDIA GPU detected"
            return self._result("gpu", "GPU diagnostics", True, required=False, detail=detail)
        except Exception as exc:
            return self._result("gpu", "GPU diagnostics", False, required=False, detail=str(exc), hint="Optional GPU probe failed.")

    def run(self) -> dict[str, Any]:
        checks = [
            self._project_path(), self._ffmpeg(), self._ollama(), self._f5tts(), self._reference_voice(),
            self._image_provider(), self._video_provider(), self._youtube(), self._gpu(),
        ]
        blockers = [item for item in checks if item["required"] and not item["ok"]]
        warnings = [item for item in checks if not item["required"] and not item["ok"]]
        report = {
            "ready": not blockers,
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
            "checks": checks,
        }
        path = self.root / "readiness.json"
        try:
            path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        return report
