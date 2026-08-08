# AI Content Studio

AI Content Studio is a Windows desktop application for creating AI-assisted
content projects from documents, text, audio, images, and other source media.
Projects can produce OCR text, narration, audiobooks, podcasts, subtitles,
thumbnails, and video assets.

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

## System requirements

- Windows 11, 64-bit
- Sufficient free storage for source media and generated output
- Internet connection when using an online AI provider
- An API key when using a provider that requires one
- FFmpeg installed and available on `PATH` for video composition and export

The packaged installer includes the application runtime. Python 3.11 and
PySide6 are required only when running or developing from source.

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
