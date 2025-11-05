# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v0.3.0-alpha

### ⚠️ BREAKING CHANGES

- **Configuration file required**: Script no longer uses hardcoded constants. 
Users must use `~/.config/wallpaperchanger/config.ini` which script auto-creates on first run with clear instructions.
- **Function signatures changed**: `configure_logging()` and `get_random_image()` now require config parameters

### Added

- **Basic Configuration Support**
    - User-friendly INI configuration file at `~/.config/wallpaperchanger/config.ini`
    - Configurable wallpaper directories (no code editing required)
    - Configurable holiday days (not just Sunday) - supports day names like "Monday", "Saturday,Sunday"
    - Image extension configuration
    - Logging configuration (level, size, backup count)
    - Config initialization script (`src/init_config.py`)
    - Auto-creates default config on first run with clear instructions

- **Work/Holiday Distinction**
    - Separate wallpaper directories for workdays vs holidays
    - Flexible multi-day holiday configuration
    - Optional left monitor support

- **Time-Based Wallpaper Selection**
    - Day/night theme switching based on configurable times
    - Four-way combination: workday/holiday + light/dark
    - Timezone-aware using system time
    - Support for midnight-crossing time periods
    - Intelligent fallback chain (time-based → work/holiday → basic)

- State tracking for wallpaper management
    - New `src/state_manager.py` module and `StateTrackingConfig` to persist
      wallpaper selection and current state across runs
    - Support for round-robin rotation of wallpapers and explicit tracking
      of the last-used image per display
    - Atomic state writes and corruption recovery to prevent state loss
    - Optional auto-cleanup of stale state entries

### Changed

- **Refactored `src/wallpaper.py`**:
    - Removed all hardcoded constants (`WALLPAPER_DIRS`, `LOG_DIR`, etc.)
    - `configure_logging()` now accepts `Config` parameter
    - `get_random_image()` now accepts `extensions` parameter
    - Added `select_wallpapers()` function for intelligent selection
    - Enhanced error handling with user-friendly messages
    - Added context detection (holiday, daytime)
    - Improved type hints and Path usage

- Selection flow integration
    - State load/save integrated into the main selection flow so wallpaper
      rotation is persisted between runs
    - Image-selection logic updated to consult persisted state for deterministic
      round-robin behavior when enabled

### Fixed

- Path expansion now properly handles `~` in config paths
- Better error messages for missing or invalid configuration
- Type safety improvements throughout codebase

### Migration

Start the script `python3 main.py` to create default configuration file, and then update it as your needs change.

---

## v0.2.0-alpha

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

## v0.1.0-alpha

### Added

- Initial project scaffold and core wallpaper-changing functionality.
- Basic tests demonstrating expected behavior for display selection and image handling.
