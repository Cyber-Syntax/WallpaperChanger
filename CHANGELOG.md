# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[0.3.0-alpha] - 2025-11-07

### Added

- State tracking for wallpapers: introduce `StateTrackingConfig` and a new `state_manager` module to persist wallpaper selection, support round-robin rotation, and track current wallpapers. Integrates atomic writes, corruption recovery, and optional auto-cleanup.
- Add CLI tests and expand test coverage to validate new CLI behavior and refactored code paths.

### Changed

- BREAKING CHANGE: add global configuration file — the script no longer uses hardcoded constants; users must provide a `config.ini`. The project now supports three selection modes (basic, work/holiday, advanced). Added modules for loading, validating, and initializing configuration.
- Major codebase refactor and reorganization for readability and maintainability; simplify selection logic (allow `get_next_wallpaper(state=None)` with random selection when no state), tighten logging/messages, and modernize typing and structure.
- Documentation updates: revise and expand docs (configuration, dev, troubleshooting, todo) and update examples and guides.
- Bumped package version to `v0.3.0-alpha` and updated related documentation.

## [0.2.0-alpha]

### Added

- Wayland support (swaybg integration) to run on Wayland compositors.
- Packaging and entry-point setup for easier installation (`pyproject.toml` + console script).
- Initial test suite and CI-ready structure (unit tests added).

### Changed

- Major codebase reorganization and refactor for readability and maintainability.
- Use XDG log directory for logs and modernized typing across the codebase.
- Formatting and performance-oriented refactors.

### Fixed

- Corrected Sunday command behavior.
- Miscellaneous small bug fixes improving stability.

### Chore

- Repository maintenance: added documentation files and formatting improvements.

## [0.1.0-alpha]

### Added

- Initial project scaffold and core wallpaper-changing functionality.
- Basic tests demonstrating expected behavior for display selection and image handling.

[unreleased]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.3.0...HEAD
[0.3.0-alpha]: https://github.com/Cyber-Syntax/wallpaperChanger/releases/tag/v0.2.0-alpha...v0.3.0-alpha
[0.2.0-alpha]: https://github.com/Cyber-Syntax/wallpaperChanger/releases/tag/v0.2.0-alpha
