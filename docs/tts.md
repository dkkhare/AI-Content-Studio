# Optional F5-TTS setup

Milestone 15 keeps the desktop and automated tests independent from the large
F5-TTS model runtime. Install it only on a machine that will generate narration.

## Install

Create and activate a Python 3.11 virtual environment, install the normal
application requirements, then install the optional runtime:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-tts.txt
```

F5-TTS may download model files on first use. A CUDA-capable GPU is recommended;
CPU generation can be slow. Keep reference audio and model downloads outside
the Git repository.

## Live smoke test

Use a short, clean WAV reference and its exact transcript:

```powershell
python scripts/tts_smoke.py --reference-audio "C:\voices\sample.wav" --reference-text "Exact words spoken in sample.wav" --text "नमस्ते, AI Content Studio तैयार है।" --output "output\tts-smoke"
```

The command prints one JSON result. Exit code 0 means a WAV file was generated;
2 means input validation failed; 3 means the optional runtime or generation
failed. Generated chunk files are removed by default; pass `--keep-chunks`
when diagnosing a model problem.

This live command is intentionally not run in GitHub Actions because it requires
external model downloads and hardware acceleration. CI uses an injected adapter
to cover the same pipeline contract deterministically.
