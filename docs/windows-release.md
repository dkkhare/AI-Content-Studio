# Windows installation and diagnostics

## Install a CI or release bundle

1. Download the `AIContentStudio-windows` artifact.
2. Verify `SHA256SUMS.txt` before extracting or distributing it.
3. Extract the complete `AIContentStudio` directory to a writable location.
4. Run `AIContentStudio.exe`. Keep the executable and its `_internal` directory together.

The application stores per-user data below `%LOCALAPPDATA%\AIContentStudio`. Project media remains in the project directory.

## FFmpeg

Video composition and render-then-export jobs require FFmpeg.

1. Install a current Windows FFmpeg build.
2. Add its `bin` directory to the user or system `PATH`.
3. Open a new PowerShell window and run `ffmpeg -version`.
4. Generate diagnostics and confirm `ffmpeg_available` is `true`.

FFmpeg is intentionally not bundled, so its version can be updated independently.

## Diagnostics

From PowerShell:

```powershell
.\AIContentStudio.exe --diagnostics diagnostics.json
Get-Content .\diagnostics.json
```

The report includes the application version, Windows/Python runtime, frozen bundle paths, user-data directory, required-resource status, and FFmpeg discovery.

For a timed GUI startup and clean-shutdown check:

```powershell
.\AIContentStudio.exe --smoke-gui gui-smoke.json
Get-Content .\gui-smoke.json
```

A successful report contains `started: true`, `shutdown: true`, and `exit_code: 0`.

## Build locally

With Python 3.11 installed:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

The bundle is written to `dist\AIContentStudio`.
