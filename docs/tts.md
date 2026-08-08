# F5-TTS requirements and cross-platform installation

AI Content Studio uses F5-TTS for local narration and authorized
reference-voice synthesis. It supplies the narration audio used by audiobooks,
podcasts, and the **Talking Head Series** pipeline.

Use only recordings and voices for which you have permission. Keep the exact
transcript of the reference recording. Do not use the feature for impersonation,
fraud, or deceptive content.

## Integration model

F5-TTS is an optional Python package imported by AI Content Studio. Install it
in the **same Python 3.11 environment** used to run AI Content Studio from
source:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-tts.txt
```

This differs from SadTalker, which uses a separate external environment. The
0.19.0 packaged Windows EXE does not embed F5-TTS; use source mode for local
F5-TTS generation.

F5-TTS requires no API key. The first generation can download model files from
the model host and may take much longer than later runs.

Official resources:

- [F5-TTS repository](https://github.com/SWivid/F5-TTS)
- [Official installation and inference instructions](https://github.com/SWivid/F5-TTS#installation)
- [PyTorch installation selector](https://pytorch.org/get-started/locally/)

## Hardware requirements

These are practical planning values rather than guarantees. Model version,
PyTorch, text length, vocoder, precision, and other active GPU applications
affect memory use.

| Component | Minimum for a short test | Recommended for production |
| --- | --- | --- |
| Operating system | 64-bit Windows 10/11, Ubuntu 22.04+, or supported macOS | Current patched OS |
| Processor | Modern 4-core CPU | 6–8 cores or more |
| System RAM | 8 GB | 16 GB; 32 GB for long books/concurrent tools |
| NVIDIA GPU | Optional | CUDA-capable GPU with 8 GB+ VRAM |
| 4 GB NVIDIA GPU | May work with short chunks; OOM is possible | Close GPU apps and use short jobs; CPU fallback if required |
| AMD GPU | CPU fallback; ROCm is Linux-only | Supported Linux ROCm GPU and matching PyTorch build |
| Apple Silicon | CPU/MPS compatibility depends on PyTorch and model path | M-series Mac with 16 GB+ unified memory |
| Intel Mac | CPU only in normal setups | Not recommended for long local generation |
| Runtime/model disk | 10 GB free minimum | 20–30 GB free for environments and caches |
| Project working disk | Depends on output | SSD with 20–50 GB+ free for long series |

CPU inference is possible but can be very slow. For a 300-page book, generation
is divided into chunks and episodes, but total processing may still take many
hours. Test one short paragraph before committing to the complete series.

## Software requirements

- CPython 3.11, 64-bit
- Git for cloning AI Content Studio
- FFmpeg for audio/media processing and talking-head episode assembly
- AI Content Studio source checkout
- `requirements.txt` and `requirements-tts.txt`
- current GPU driver
- device-matched PyTorch for CUDA, ROCm, XPU, or Apple Silicon
- internet access for initial package and model downloads
- no F5-TTS API key

F5-TTS upstream supports Python 3.10 or newer and documents device-specific
PyTorch installations. This project standardizes source use on Python 3.11.

## Reference voice requirements

Use a recording with:

- a single authorized speaker
- clear, natural speech and minimal room echo
- no music, effects, overlapping speakers, or heavy noise reduction artifacts
- a practical test length of roughly 5–15 seconds
- an exact transcript matching every spoken word
- WAV preferred; MP3, FLAC, and OGG are accepted by the project adapter
- the same language/script as the intended voice style when possible

A wrong transcript can reduce quality or cause unstable output. Leaving the
transcript empty is not supported by AI Content Studio's consented
reference-voice workflow, even though upstream CLI modes may offer automatic
transcription.

## Windows installation

Run PowerShell as a normal user. Python 3.11 and Git must already be installed.

### 1. Install and verify prerequisites

Install 64-bit Python 3.11 from
[python.org](https://www.python.org/downloads/) and Git for Windows. Install
FFmpeg and add its `bin` folder to `PATH`.

```powershell
py -3.11 --version
git --version
ffmpeg -version
```

For NVIDIA acceleration, update the NVIDIA driver and confirm:

```powershell
nvidia-smi
```

### 2. Clone AI Content Studio and create the environment

```powershell
cd D:\
git clone https://github.com/dkkhare/AI-Content-Studio.git
cd AI-Content-Studio
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### 3. Install device-matched PyTorch

The base requirements may already install PyTorch. Check it first:

```powershell
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

If CUDA is expected but reports `False`, use the current command generated by
the official PyTorch installation selector for Windows, Pip, Python, and your
supported CUDA version. Do not choose a CUDA wheel merely because
`nvidia-smi` displays a high CUDA compatibility number; use a PyTorch build
supported by your driver and GPU.

Re-run the verification command after installation.

### 4. Install F5-TTS

```powershell
python -m pip install -r requirements-tts.txt
python -c "import f5_tts; print('F5-TTS import OK')"
```

### 5. Run the project smoke test

```powershell
python scripts/tts_smoke.py --reference-audio "C:\voices\sample.wav" --reference-text "Exact words spoken in sample.wav" --text "नमस्ते, AI Content Studio तैयार है।" --output "D:\AIProjects\tts-smoke"
```

The first run may download models. Exit code 0 means a WAV was generated; 2
means input validation failed; 3 means runtime or generation failed. Pass
`--keep-chunks` only when diagnosing intermediate output.

### 6. Start AI Content Studio

```powershell
python -m desktop.main
```

Use the Narration or Talking Head Series panel with the same active environment.

## Ubuntu installation

These instructions target Ubuntu 22.04 or newer. Do not use `sudo pip`.

### 1. Install prerequisites

```bash
sudo apt update
sudo apt install -y git ffmpeg python3.11 python3.11-venv python3.11-dev build-essential
python3.11 --version
git --version
ffmpeg -version
```

If Python 3.11 packages are unavailable for your Ubuntu release, install Python
from a trusted supported source or use Conda with Python 3.11.

For NVIDIA acceleration, install the supported Ubuntu/NVIDIA driver and verify
`nvidia-smi`. For supported AMD acceleration, ROCm is Linux-only and requires
a PyTorch wheel matched to the installed ROCm version.

### 2. Clone and install the application

```bash
mkdir -p "$HOME/Projects"
cd "$HOME/Projects"
git clone https://github.com/dkkhare/AI-Content-Studio.git
cd AI-Content-Studio
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### 3. Verify/install PyTorch for the device

```bash
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

For NVIDIA, AMD ROCm, or Intel XPU, use the current official F5-TTS/PyTorch
device instructions. Do not combine CUDA and ROCm wheels in one environment.

### 4. Install and smoke-test F5-TTS

```bash
python -m pip install -r requirements-tts.txt
python -c "import f5_tts; print('F5-TTS import OK')"
python scripts/tts_smoke.py \
  --reference-audio "$HOME/voices/sample.wav" \
  --reference-text "Exact words spoken in sample.wav" \
  --text "नमस्ते, AI Content Studio तैयार है।" \
  --output "$HOME/AIProjects/tts-smoke"
python -m desktop.main
```

## macOS installation

macOS source mode is experimental in this repository. The official F5-TTS
project documents stable PyTorch installation for Apple Silicon, but model and
MPS behavior can change with PyTorch/macOS versions. Start with a short smoke
test. Intel Macs normally use CPU inference and may be impractical for long
books.

### 1. Install prerequisites

Install Apple Command Line Tools and Homebrew:

```bash
xcode-select --install
brew install python@3.11 git ffmpeg
python3.11 --version
git --version
ffmpeg -version
uname -m
```

On Apple Silicon, use a native `arm64` terminal. Do not mix Rosetta x86_64 and
arm64 Python packages.

### 2. Create the project environment

```bash
mkdir -p "$HOME/Projects"
cd "$HOME/Projects"
git clone https://github.com/dkkhare/AI-Content-Studio.git
cd AI-Content-Studio
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch torchaudio
python -m pip install -r requirements.txt
python -m pip install -r requirements-tts.txt
```

If `requirements.txt` replaces the desired PyTorch build, reinstall stable
`torch` and `torchaudio` afterward, then verify the environment.

### 3. Verify MPS and run a smoke test

```bash
python -c "import platform, torch; print(platform.machine()); print(torch.__version__); print('MPS:', hasattr(torch.backends, 'mps') and torch.backends.mps.is_available())"
python -c "import f5_tts; print('F5-TTS import OK')"
python scripts/tts_smoke.py \
  --reference-audio "$HOME/voices/sample.wav" \
  --reference-text "Exact words spoken in sample.wav" \
  --text "नमस्ते, AI Content Studio तैयार है।" \
  --output "$HOME/AIProjects/tts-smoke"
python -m desktop.main
```

MPS being available does not guarantee every dependency or inference operation
uses Metal. If an MPS error occurs, test CPU execution or use a supported
NVIDIA Windows/Linux system.

## Optional upstream CLI verification

After installing `f5-tts`, the upstream CLI can provide an independent check:

```bash
f5-tts_infer-cli --model F5TTS_v1_Base --ref_audio "sample.wav" --ref_text "Exact words in sample.wav" --gen_text "This is a short test."
```

Use AI Content Studio's `scripts/tts_smoke.py` as the project-specific
acceptance test because it exercises the adapter used by the desktop workflow.

## Model cache and output locations

F5-TTS and its dependencies commonly download models into the current user's
model cache, often below the Hugging Face cache directory. The exact location
can vary by package version and environment variables.

Do not place model caches inside Git. Preserve sufficient space for:

- Python/PyTorch packages
- F5-TTS and vocoder models
- reference recordings
- generated narration WAVs
- per-segment talking-head working audio
- episode output and resumable manifests

Project-generated files normally go below `<Project root>/output`. Do not
delete segment/checkpoint files from an active talking-head series if you intend
to resume it.

## Licensing and privacy

The F5-TTS code repository is MIT-licensed, but upstream states that its
pretrained models are CC-BY-NC because of the training data. Review the current
upstream license and model-card terms before commercial use or redistribution.
This documentation is not legal advice.

Generation is local after required packages/models are available, but initial
downloads use the network. Do not commit private recordings, generated voices,
model caches, or credentials to the repository.

## Troubleshooting

| Problem | Checks |
| --- | --- |
| `No module named f5_tts` | Activate AI Content Studio's `.venv` and install `requirements-tts.txt` in that exact environment |
| Packaged EXE cannot find F5-TTS | Version 0.19.0 requires Python source mode for F5-TTS |
| CUDA reports `False` | Check driver, GPU support, Python architecture, and device-matched PyTorch wheel |
| CUDA out of memory | Close GPU apps, use shorter text/chunks, retry one task, or use CPU/a larger GPU |
| PyTorch DLL error on Windows | Recreate the 64-bit environment and install a supported PyTorch build |
| ROCm error | Confirm supported Linux GPU, ROCm version, and exactly matched PyTorch wheel |
| MPS error on macOS | Confirm native architecture and stable PyTorch; try CPU or a supported NVIDIA system |
| FFmpeg unavailable | Run `ffmpeg -version` in a new terminal and restart the application |
| Model download fails | Check internet, free disk, proxy/firewall, and model-host availability |
| Poor voice match | Use clean single-speaker audio and an exact transcript |
| Hindi pronunciation issue | Use Devanagari consistently, correct punctuation, and test a short passage |
| Long generation interrupted | Keep project/checkpoint files and use the workflow's resume action |
| Output is silent/corrupt | Test the reference file, run `scripts/tts_smoke.py`, and inspect the JSON/error |
| Dependency conflict | Recreate `.venv`; avoid indiscriminate upgrades after installing requirements |

## Diagnostic information to report

Include only non-sensitive details:

- OS version and CPU architecture
- Python executable and `python --version`
- F5-TTS and PyTorch versions
- GPU model, VRAM, driver, CUDA/ROCm/MPS status
- RAM and free disk
- exact command and final error lines
- whether the project smoke test or upstream CLI fails

Do not upload private voice samples, book text, API keys, personal paths, or an
uninspected support bundle.
