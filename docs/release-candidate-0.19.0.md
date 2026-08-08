# AI Content Studio 0.19.0 Release Candidate Sign-off

## Candidate

- Version: 0.19.0
- Tested PR head: `8ca103f60195228a7efd90d1881d1059fb1dc514`
- Tested PR merge commit: `272336101ce163bedb7605227887d8f2f46b7af9`
- Automated test date: 2026-08-08
- Workflow: Milestone 23 Release Candidate run #3
- Automated readiness: **PASS**

## Artifacts

| Artifact | Workflow artifact | Artifact digest |
| --- | --- | --- |
| Windows bundle and installer | `milestone-23-windows-0.19.0` | `sha256:f3dd34b42130cb1d67620f7198ab2f652f13c99e4ac7718975ed800c1077a393` |
| Machine-readable evidence | `milestone-23-release-evidence` | `sha256:aaffd1022d28b12a151d5562048bbdbb02a3b6697b02645cdd118c15c26e2a1b` |

The machine-readable evidence reports `ready: true` and records all six required
automated gates as `pass`.

## Automated gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Project lifecycle | Pass | Consolidated regression job |
| Desktop AI | Pass | Consolidated regression job |
| Safe updates | Pass | Consolidated regression job |
| Support diagnostics | Pass | Consolidated regression job |
| Windows package | Pass | Frozen diagnostics, GUI lifecycle, offline update UI, checksums |
| Windows installer | Pass | Silent install, installed diagnostics, uninstall cleanup, checksums |

## Automated acceptance coverage

| Scenario | Result | Notes |
| --- | --- | --- |
| Package launch and frozen diagnostics | Pass | Version and required resources verified |
| GUI startup and clean shutdown | Pass | Offscreen packaged smoke |
| Update dialog without networking | Pass | Automatic checks disabled and clean shutdown verified |
| Fresh silent install | Pass | Installed to isolated runner directory |
| Installed application diagnostics | Pass | Frozen runtime and resources verified |
| Silent uninstall | Pass | Executable absence verified |
| Project lifecycle and recovery | Pass | Focused regression suite |
| Redacted support diagnostics | Pass | Support/logging/crash regression suite |

## Manual checks still required

Run these on a normal Windows 11 desktop before public release.

- [ ] Confirm installer and application UI render correctly with a visible display.
- [ ] Upgrade over the previous installed version and confirm settings and recent
      projects remain available.
- [ ] Open a real representative project containing media and complete the
      create/save/reopen/Save As workflow.
- [ ] Uninstall after the representative-project test and confirm the external
      project directory remains untouched.
- [ ] Export a support ZIP and visually inspect its contents before sharing.

Record the tester name, Windows build, date, and any observations below.

- Tester:
- Windows build:
- Date:
- Observations:

## Known limitations

- The installer is checksum-verified but not Authenticode-signed; Windows
  SmartScreen may warn on first launch.
- Automated GUI checks run offscreen and do not replace visible layout review.
- Hardware-dependent media, OCR, TTS, and FFmpeg behavior depends on the target
  workstation and installed external tools.

## Decision

- [ ] Approved for release after manual checks
- [ ] Rejected; remediation required

Approver:

Decision date:

Notes:
