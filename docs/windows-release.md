# Windows installation and release guide

## Install the verified installer

1. Download `AIContentStudio-Setup-<version>-windows-x64.exe` and `SHA256SUMS.txt` from the matching GitHub Release.
2. Verify the checksum in PowerShell:

```powershell
(Get-FileHash .\AIContentStudio-Setup-0.19.0-windows-x64.exe -Algorithm SHA256).Hash.ToLowerInvariant()
Get-Content .\SHA256SUMS.txt
```

3. Run the installer. It installs per-user under `%LOCALAPPDATA%\Programs\AIContentStudio`, so administrator access is not required.
4. Keep the default Start Menu shortcut or optionally select the desktop shortcut.

Application state is stored under `%LOCALAPPDATA%\AIContentStudio`. Project media remains in each project directory.

## Upgrade and uninstall

To upgrade, download the newer installer, verify its checksum, and run it normally. The stable installer application ID upgrades the existing installation instead of creating a second product.

Uninstall from Windows Settings > Apps > Installed apps > AI Content Studio, or run `unins000.exe` from the installation directory. Uninstalling removes application binaries and shortcuts. It does not delete project directories. Back up important projects independently before upgrading or uninstalling.

## FFmpeg

Video composition and render-then-export jobs require FFmpeg.

1. Install a current Windows FFmpeg build.
2. Add its `bin` directory to the user or system `PATH`.
3. Open a new PowerShell window and run `ffmpeg -version`.
4. Generate diagnostics and confirm `ffmpeg_available` is `true`.

FFmpeg is intentionally not bundled, so its version can be updated independently.

## Diagnostics

```powershell
& "$env:LOCALAPPDATA\Programs\AIContentStudio\AIContentStudio.exe" --diagnostics diagnostics.json
Get-Content .\diagnostics.json
```

The report includes application version, runtime and bundle paths, user-data location, required-resource status, and FFmpeg discovery.

For a timed GUI lifecycle check:

```powershell
& "$env:LOCALAPPDATA\Programs\AIContentStudio\AIContentStudio.exe" --smoke-gui gui-smoke.json
Get-Content .\gui-smoke.json
```

A successful report contains `started: true`, `shutdown: true`, and `exit_code: 0`.

## Build locally

With Python 3.11 and Inno Setup 6 installed:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1
```

The versioned installer is written to `release\`.

## Publish a release

1. Update `VERSION` and `VERSION_TUPLE` in `backend/version.py`; Windows executable and installer metadata are derived from it.
2. Merge the change only after the Windows package and installer workflows pass.
3. Create and push an exact matching tag, for example `v0.19.0`.
4. The release workflow rejects any tag that does not exactly match `backend/version.py`.
5. The workflow builds the installer, generates `SHA256SUMS.txt`, and creates the GitHub Release with generated notes.

Do not reuse or move a published version tag.

## Code-signing status

Current installers are checksum-verified but unsigned. Windows SmartScreen may therefore warn users on first launch. Public production distribution should add Authenticode signing after choosing a certificate provider and configuring protected GitHub secrets or keyless signing. Private certificate material must never be committed to the repository. Code signing is intentionally deferred until those credentials and ownership decisions exist.
