# Milestone 23: Release Readiness

Milestone 23 is the final acceptance stage for AI Content Studio. It does not add
new product scope. It proves that the features delivered through Milestone 22 can
be installed, exercised, supported, updated, and removed safely.

## Exit criteria

A release candidate is ready only when all items below are satisfied.

### Automated gates

- [ ] Core Python regressions pass on Python 3.11.
- [ ] Project lifecycle regressions pass, including save, autosave, recovery,
      backup cleanup, close, and shutdown behavior.
- [ ] AI desktop and provider regressions pass.
- [ ] Update metadata, download verification, and offline update UI tests pass.
- [ ] Support redaction, logging, crash-report, and bundle regressions pass.
- [ ] Windows application bundle builds successfully.
- [ ] Packaged diagnostics execute successfully.
- [ ] Packaged GUI starts and shuts down cleanly.
- [ ] Packaged update UI opens with network checks disabled.
- [ ] Windows installer compiles, installs, launches, and uninstalls cleanly.
- [ ] Published artifacts include SHA-256 checksums.

### Manual release-candidate acceptance

Perform these checks on a clean Windows 11 user profile.

- [ ] Install without an existing AI Content Studio installation.
- [ ] Launch from the Start menu and confirm the displayed version.
- [ ] Create, save, close, reopen, and Save As a project.
- [ ] Force an autosave recovery scenario and verify the original project is
      not overwritten until the user explicitly saves it.
- [ ] Configure an AI provider, restart, and confirm secrets are not displayed
      in logs, crash reports, or exported support bundles.
- [ ] Exercise the update dialog both online and with networking unavailable.
- [ ] Export a support bundle, inspect its manifest, and confirm no credentials
      or user-home path is present.
- [ ] Upgrade from the previous released version while retaining user settings
      and projects.
- [ ] Uninstall and confirm program files and shortcuts are removed.
- [ ] Confirm user projects remain untouched by uninstall.

## Release evidence

For every candidate, record:

- candidate version and Git commit
- Windows version used for acceptance
- installer filename and SHA-256
- portable bundle filename and SHA-256
- links to all required workflow runs
- manual tester and completion date
- known limitations accepted for release

Use [release-candidate-template.md](release-candidate-template.md) for the
sign-off record.

## Scope control

Failures discovered during acceptance may be fixed in Milestone 23. New features
must be deferred to a post-1.0 milestone so the acceptance target remains stable.
