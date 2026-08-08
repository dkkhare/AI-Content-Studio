# AI Content Studio

AI Content Studio is a Windows desktop application for creating AI-assisted
content projects from documents, text, audio, images, and other source media.
Projects can produce OCR text, narration, audiobooks, podcasts, subtitles,
thumbnails, and video assets.

## Download

### Windows 0.19.0 release candidate

[**Download milestone-23-windows-0.19.0**](https://github.com/dkkhare/AI-Content-Studio/actions/runs/31249379767/artifacts/9019969816)

The download is a GitHub Actions ZIP of approximately 103 MB containing the
portable Windows bundle, `AIContentStudio-Setup-0.19.0-windows-x64.exe`, and
`SHA256SUMS.txt`.

- GitHub sign-in and repository access are required.
- On a phone, open the link in a browser and enable **Desktop site**; the GitHub
  mobile app may not show workflow artifacts.
- This temporary CI artifact expires on **November 6, 2026**.
- Workflow artifact digest:
  `sha256:c388fac88d7759609306ea853ac54b508b8d8994fe515c0f28e37b98295715d0`

If the direct link is unavailable, open
[Milestone 23 Release Candidate run #3](https://github.com/dkkhare/AI-Content-Studio/actions/runs/31249379767),
select **Summary**, and download `milestone-23-windows-0.19.0` under
**Artifacts**.

### Stable releases

After final approval and publication, permanent installers and checksums will be
available on the [GitHub Releases page](https://github.com/dkkhare/AI-Content-Studio/releases).
Prefer the Releases page over an Actions artifact for normal distribution.

## Features

- OCR PDF
- AI-assisted content processing
- Voice cloning and narration
- Talking avatar
- Subtitle generation
- Video composition
- Batch rendering
- Safe application updates
- Redacted local support diagnostics

## Hardware and software requirements

Requirements depend strongly on whether you use only the desktop/project tools,
cloud AI, local Ollama models, F5-TTS, or high-resolution video rendering. The
figures below are practical planning guidance, not guarantees for every model or
project.

### Core packaged application

| Component | Minimum for basic use | Recommended |
| --- | --- | --- |
| Operating system | Windows 11 64-bit | Current fully updated Windows 11 64-bit |
| Processor | Modern 4-core x64 CPU | 6-core or better Intel Core i5/i7 or AMD Ryzen 5/7 |
| Memory | 8 GB RAM | 16 GB RAM; 32 GB for large media/local AI |
| Graphics | DirectX-capable integrated graphics | Dedicated NVIDIA/AMD GPU for media and local AI |
| Display | 1366×768 | 1920×1080 or higher |
| Application storage | About 500 MB free | 2 GB free for installation, logs, and updates |
| Project storage | Depends on source media | SSD with at least 20–50 GB free |
| Network | Not required for basic local project work | Broadband for cloud AI, models, and updates |
| Audio | Optional | Headphones/speakers and a good microphone for voice work |

An SSD is strongly recommended. Video, generated audio, model caches, project
backups, and temporary files can consume far more space than the application
itself.

### Workload-specific hardware

| Workload | CPU/RAM guidance | GPU guidance | Storage guidance |
| --- | --- | --- | --- |
| Project editing, subtitles, support tools | 4 cores, 8 GB RAM | Integrated graphics is sufficient | 2–10 GB plus projects |
| OCR and PDF processing | 4–6 cores, 8–16 GB RAM | Usually optional | Enough for source PDFs and page images |
| FFmpeg 1080p video | 6 cores, 16 GB RAM | Optional; current renderer uses software-compatible codecs | 20 GB or more free working space |
| Cloud OpenAI/Gemini | 4 cores, 8 GB RAM | Not required | Minimal local model storage |
| Small Ollama model | 16 GB system RAM recommended | GPU optional but faster | Model-dependent; allow several GB |
| Larger Ollama model | 32 GB+ RAM may be needed | Sufficient supported VRAM strongly recommended | Models can consume tens of GB |
| F5-TTS source mode | 16 GB RAM recommended | CUDA-capable NVIDIA GPU recommended; 8 GB+ VRAM is a practical target | Allow 10–30 GB for Python, PyTorch, and model caches |
| CPU-only F5-TTS | 16 GB+ RAM | None | Same model storage; generation may be very slow |

A 4 GB VRAM GPU can run the core application and video tools, but may be
insufficient for some F5-TTS or Ollama model/configuration combinations. Choose
smaller models, shorter jobs, CPU fallback, or a higher-memory GPU if an
out-of-memory error occurs.

### Packaged installer software requirements

- Windows 11 64-bit user account
- Permission to install per-user applications under
  `%LOCALAPPDATA%\Programs`
- FFmpeg on `PATH` only for video composition/export
- Ollama installed and running only when using local AI
- Tesseract/Poppler only for OCR routes that require native executables
- Internet access and a valid key only for OpenAI or Gemini
- Current GPU drivers when using GPU-accelerated third-party software

The packaged installer includes the Python/Qt application runtime. It does not
bundle FFmpeg, Ollama, F5-TTS models, Tesseract, Poppler, cloud keys, or GPU
drivers.

### Source-development software requirements

| Software | Requirement |
| --- | --- |
| Python | CPython 3.11, 64-bit |
| Python packages | `python -m pip install -r requirements.txt` |
| Optional F5-TTS | `python -m pip install -r requirements-tts.txt` |
| Windows installer build | Inno Setup 6 |
| Windows application build | PyInstaller from `requirements-build.txt` |
| Version control | Git recommended |
| GPU acceleration | Compatible driver plus a matching PyTorch/CUDA build |

Use a virtual environment for source development and F5-TTS. Do not install
optional model runtimes into the packaged application's installation directory.

### Network and account requirements

- OpenAI: internet access, an API account/project, model access, available
  billing or credits, and `OPENAI_API_KEY`.
- Gemini: internet access, an enabled API project, model quota/access, and
  `GEMINI_API_KEY` (or the backend alias `GOOGLE_API_KEY`).
- Ollama: no cloud account or key; its local service must be reachable, normally
  at `http://localhost:11434`.
- F5-TTS: no API key; initial model download requires internet unless models are
  pre-cached.
- FFmpeg, Tesseract, and Poppler: no accounts or API keys.

## Third-party applications and service keys

Install only the external components needed for the features you use.

| Component | Purpose | Works with packaged EXE | Key required |
| --- | --- | --- | --- |
| FFmpeg | MP4 rendering, encoding, subtitle burning | Yes, when on `PATH` | No |
| F5-TTS | Local narration and reference-voice synthesis | No; 0.19.0 requires source mode | No |
| Ollama | Local AI text generation | Yes, as a separate service | No |
| OpenAI | Cloud AI text generation | Yes | `OPENAI_API_KEY` |
| Google Gemini | Cloud AI text generation | Yes | `GEMINI_API_KEY` or `GOOGLE_API_KEY` |
| Tesseract | OCR through `pytesseract` | Optional/feature-dependent | No |
| Poppler | PDF conversion through `pdf2image` | Optional/feature-dependent | No |

Never commit real keys to Git, project files, screenshots, logs, or support
tickets. Keys entered under **AI → Provider Settings** are session secrets and
must be entered again after restarting the application.

### Install FFmpeg for video tools

The video composer searches for `ffmpeg.exe` on Windows `PATH` and uses H.264
video, AAC audio, MP4 output, and optional SRT/VTT subtitle burning.

1. Download a current Windows build from the
   [official FFmpeg page](https://ffmpeg.org/download.html).
2. Extract it to a stable folder such as `C:\Tools\ffmpeg`.
3. Add `C:\Tools\ffmpeg\bin` to the user or system `PATH`.
4. Restart PowerShell and AI Content Studio.
5. Verify:

```powershell
ffmpeg -version
where.exe ffmpeg
```

No API key is required. Video inputs are:

- visual: `.png`, `.jpg`, `.jpeg`, `.webp`, `.mp4`, `.mov`, `.mkv`, or `.webm`
- audio: `.wav`, `.mp3`, `.flac`, `.ogg`, or `.m4a`
- optional subtitles: `.srt` or `.vtt`
- output: a writable path ending in `.mp4`

### Install F5-TTS for narration

F5-TTS is a large optional Python/model runtime. It is **not bundled** in the
0.19.0 installer. Installing it into a separate Python installation does not
extend the frozen EXE. Run AI Content Studio from source and install F5-TTS into
the same Python 3.11 virtual environment:

```powershell
cd C:\path\to\AI-Content-Studio
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-tts.txt
python -m desktop.main
```

The optional file installs `f5-tts` from the
[official F5-TTS project](https://github.com/SWivid/F5-TTS). Models may download
on first use. A supported CUDA GPU and a matching PyTorch build are recommended;
CPU inference may be very slow.

F5-TTS requires:

- clean reference audio: `.wav`, `.mp3`, `.flac`, or `.ogg`
- the exact transcript of the reference audio
- new narration text
- a writable output directory

No API key is required. Optional smoke test:

```powershell
python scripts/tts_smoke.py --reference-audio "C:\voices\sample.wav" --reference-text "Exact words in sample.wav" --text "नमस्ते, AI Content Studio तैयार है।" --output "D:\AIProjects\tts-smoke"
```

See [the detailed F5-TTS guide](docs/tts.md).

### Install Ollama for local AI

1. Follow the [official Ollama Windows guide](https://docs.ollama.com/windows).
2. Start Ollama; the default API is `http://localhost:11434`.
3. Pull and verify a model:

```powershell
ollama pull llama3.2
ollama list
```

4. Select `ollama` under **AI → Provider Settings** and enter the exact model
   name.

Relevant variables:

```text
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_DEFAULT_MODEL=llama3.2
```

The backend also accepts `OLLAMA_MODEL`. Ollama requires no API key, but models
can require substantial disk space, RAM, and VRAM.

### Configure OpenAI

OpenAI requires internet access, an API account/project with available billing or
credits, model access, and a key. Configure it under **AI → Provider Settings**.

```text
OPENAI_API_KEY=required
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_DEFAULT_MODEL=optional-model-name
```

To create a persistent Windows user variable:

```powershell
setx OPENAI_API_KEY "replace-with-your-key"
```

Restart the application afterward. A ChatGPT subscription does not automatically
include OpenAI API credits.

### Configure Google Gemini

Gemini requires internet access, an enabled API project, quota, an allowed model,
and a key. The desktop uses `GEMINI_API_KEY`; the backend also accepts
`GOOGLE_API_KEY`.

```text
GEMINI_API_KEY=required-for-desktop
GOOGLE_API_KEY=optional-backend-alias
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_DEFAULT_MODEL=optional-model-name
GEMINI_MODEL=optional-backend-fallback
```

Persistent Windows setup:

```powershell
setx GEMINI_API_KEY "replace-with-your-key"
```

Restart afterward. Do not set both key variables to different credentials.

### Install optional OCR utilities

Source dependencies include `PyMuPDF`, `pdfplumber`, `pdf2image`,
`pytesseract`, and `rapidocr`. Some routes work through Python packages, while
others require native tools.

- Tesseract: install a trusted Windows build, add the directory containing
  `tesseract.exe` to `PATH`, then run `tesseract --version`.
- Poppler: install a trusted Windows build, add its `bin` directory to `PATH`,
  then run `pdftoppm -h`.

Neither requires a key. These native OCR utilities are not currently verified by
the packaged release-candidate workflow, so test them with a sample document.

### Configuration key reference

| Variable | Required when | Default |
| --- | --- | --- |
| `AI_CONTENT_STUDIO_AI_PROVIDER` | Optional environment provider selection | Desktop defaults to Ollama |
| `AI_CONTENT_STUDIO_AI_MODEL` | Optional common model selection | Empty |
| `AI_CONTENT_STUDIO_AI_FAILOVER` | Optional comma-separated fallback order | Empty |
| `AI_CONTENT_STUDIO_AI_TIMEOUT` | Optional request timeout | `60` seconds |
| `OPENAI_API_KEY` | OpenAI | None |
| `OPENAI_BASE_URL` | Compatible/custom OpenAI endpoint | `https://api.openai.com/v1` |
| `OPENAI_DEFAULT_MODEL` | Optional OpenAI default | Empty |
| `GEMINI_API_KEY` | Gemini from the desktop | None |
| `GOOGLE_API_KEY` | Optional Gemini backend alias | None |
| `GEMINI_BASE_URL` | Documented Gemini endpoint | `https://generativelanguage.googleapis.com/v1beta` |
| `GEMINI_DEFAULT_MODEL` | Optional desktop Gemini model | Empty |
| `GEMINI_MODEL` | Optional backend Gemini model | Empty |
| `OLLAMA_BASE_URL` | Non-default Ollama endpoint | `http://localhost:11434` |
| `OLLAMA_DEFAULT_MODEL` | Optional desktop Ollama model | Empty |
| `OLLAMA_MODEL` | Optional backend Ollama model | Empty |

`.env.example` is a reference template. The application does not promise to
load a local `.env` automatically; use Provider Settings, Windows environment
variables, or a launcher that explicitly loads it.

## Install on Windows

1. Download the verified Windows artifact or installer.
2. Extract the artifact ZIP if necessary.
3. Verify the installer hash against the included `SHA256SUMS.txt`.
4. Run `AIContentStudio-Setup-0.19.0-windows-x64.exe`.
5. Start **AI Content Studio** from the Start menu.

The default application installation path is:

```text
%LOCALAPPDATA%\Programs\AIContentStudio
```

Windows SmartScreen may display a warning because the current release candidate
is checksum-verified but not yet Authenticode-signed.

## Inputs required

### Required to create a project

| Input | Description | Example |
| --- | --- | --- |
| Project name | A non-empty name for the project | `My Hindi Audiobook` |
| Project location | The parent folder in which the project folder will be created | `D:\AIProjects` |

Creating the example above produces:

```text
D:\AIProjects\My Hindi Audiobook
```

### Required for content generation

The exact input depends on the task. Keep source files available until processing
and export are complete.

| Task | Typical input |
| --- | --- |
| OCR | A readable PDF or supported document/image source |
| Narration or audiobook | Extracted text or script and a selected voice |
| Voice cloning | A clean reference voice recording with minimal noise |
| Talking avatar | A source portrait/image and narration audio |
| Subtitles | Script, transcript, narration, or video/audio source |
| Video composition | Images/video clips, narration/audio, and optional subtitles |
| Online AI processing | Provider selection, model, and valid API key |

Do not place API keys in project names, file names, scripts, logs, or support
notes. Enter credentials only through **AI → Provider Settings**.

## User guide

### 1. Create a project

1. Open AI Content Studio.
2. Select **File → New Project**.
3. Enter the project name.
4. Select the parent project location.
5. The application creates and opens the new project folder.

For a project named `My Project` created under `D:\AIProjects`, the project
root is:

```text
D:\AIProjects\My Project
```

### 2. Open an existing project

1. Select **File → Open Project**.
2. Choose the project root folder—the folder containing `project.json`.
3. Do not select only the `output` subfolder.

### 3. Configure an AI provider

1. Select **AI → Provider Settings**.
2. Choose the provider and model.
3. Enter the required endpoint or API key.
4. Save the settings.
5. Open **AI → AI Workbench** to use the configured provider.

Online providers require network access. Local providers such as Ollama require
their own service and model to be installed and running.

### 4. Add source content and process it

1. Open the appropriate workspace/tool for the intended task.
2. Select the source PDF, text, audio, image, or video.
3. Choose language, voice, model, and processing options when requested.
4. Start processing.
5. Monitor progress and the application log.
6. Save the project after confirming the generated result.

Large media and AI operations may take time. Avoid moving source files or
closing the application while a task is active.

### 5. Save, Save As, and close

- **File → Save** updates `project.json` in the current project root.
- **File → Save As** asks for a destination folder; the selected folder becomes
  the new project root.
- When closing with unsaved changes, review the warning carefully.
- On shutdown, modified project state is written to the recovery area so it can
  be recovered without overwriting the last explicit save.

## Project and output paths

A normal project has this layout:

```text
<Project root>\
├── project.json
├── output\
├── backups\        (created when backups exist)
└── .autosave\      (temporary recovery data when needed)
```

### Main output path

Generated assets are stored under:

```text
<Project root>\output
```

Example:

```text
D:\AIProjects\My Hindi Audiobook\output
```

Possible generated assets include OCR text, translations, narration, audiobook
audio, podcast audio, video, subtitles, cover images, and thumbnails. The exact
filenames are recorded in `project.json`.

### Other application paths

| Data | Default path |
| --- | --- |
| Application settings and state | `%LOCALAPPDATA%\AIContentStudio` |
| Application logs | `%LOCALAPPDATA%\AIContentStudio\logs` |
| Local crash reports | `%LOCALAPPDATA%\AIContentStudio\crashes` |
| Project recovery | `<Project root>\.autosave` |
| Project backups | `<Project root>\backups` |
| Support ZIP | The path selected in the Save dialog |
| CLI diagnostics JSON | The output path supplied to `--diagnostics` |

Project folders are not removed when the application is uninstalled. Back up
important project folders independently.

## Export a support bundle

1. Select **Help → Export Support Bundle...**.
2. Read the privacy notice.
3. Choose where to save the ZIP.
4. Inspect the ZIP before sharing it.

The bundle contains redacted diagnostics, approved logs, crash reports, and a
checksum manifest. Credentials and user-home paths are redacted, and nothing is
uploaded automatically.

## Diagnostics

From PowerShell:

```powershell
& "$env:LOCALAPPDATA\Programs\AIContentStudio\AIContentStudio.exe" --diagnostics ".\diagnostics.json"
Get-Content ".\diagnostics.json"
```

The example writes `diagnostics.json` into the current PowerShell directory.
You may supply an absolute output path instead.

## Update and uninstall

- Select **Help → Check for Updates...** to check manually.
- Verify downloaded installers and checksums before installing.
- A newer installer upgrades the existing installation.
- Uninstall through **Windows Settings → Apps → Installed apps**.
- Uninstall removes program files and shortcuts but does not intentionally
  remove external project folders.

## Troubleshooting

- If FFmpeg is unavailable, install it, add its `bin` directory to `PATH`,
  restart the application, and regenerate diagnostics.
- If a project will not open, select the folder containing `project.json`.
- If online AI fails, verify provider settings, API access, model name, and
  internet connectivity.
- If the application crashes, restart it and export a support bundle.
- Never post an uninspected support ZIP publicly.

## Development

Source development uses Python 3.11:

```powershell
python -m pip install -r requirements.txt
python -m desktop.main
```

To build the Windows installer with Inno Setup 6 installed:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1
```

The installer is written to the repository's `release\` directory.

## Project status

Milestone 22 is complete. Milestone 23 is the final release-readiness and
acceptance stage.

- [Milestone 23 release readiness](docs/MILESTONE_23_RELEASE_READINESS.md)
- [Windows release guide](docs/windows-release.md)
- [0.19.0 release-candidate sign-off](docs/release-candidate-0.19.0.md)
