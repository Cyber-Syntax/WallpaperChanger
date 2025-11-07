# Configuration

This document explains the minimal and recommended configuration options for
WallpaperChanger. Keep your configuration small and explicit: one valid
directory configuration is required. The program creates a default config at
first run if none exists.

Location

- Default config path: `~/.config/wallpaperchanger/config.ini`

Goals

- Show the smallest valid configuration you need to run the program.
- Explain the available configuration sections and important keys.
- Keep examples minimal so refactoring and maintenance stay simple.

Minimum requirements

- At least one wallpaper directory must be configured.
    - You can use the simple `[Directories]` section or the time-based sections.
- Image files must match the configured `extensions` under `[Images]`.

Quick start (minimum working configuration)

1. Create the config file at `~/.config/wallpaperchanger/config.ini` (the
   program will also create a default for you on first run).
2. In `[Directories]` set `primary` to a directory that contains images.
3. Ensure images use one of the listed extensions under `[Images]`.

Example settings (presented inline)

- [Schedule]
    - `holiday_days = Sunday`
    - `day_start_time = 08:00`
    - `night_start_time = 18:00`
- [Directories]
    - `primary = /home/you/Pictures/Wallpapers/primary/`
    - `left = /home/you/Pictures/Wallpapers/left/` (optional)
    - `sunday = /home/you/Pictures/Wallpapers/Sunday/` (optional)
- [Images]
    - `extensions = .png,.jpg,.jpeg`
- [Logging]
    - `log_dir` (default: `~/.local/share/wallpaperchanger/logs`)
    - `max_size_mb` (default: `1`)
    - `backup_count` (default: `3`)
    - `log_level` (default: `INFO`)
- [StateTracking]
    - `enabled = true` or `false`
    - `state_file` (default: `~/.local/share/wallpaperchanger/state.json`)

Directory configuration options (priority / fallback)

1. Time-based (preferred)
    - Sections: `Directories.Workday.Light`, `Directories.Workday.Dark`,
      `Directories.Holiday.Light`, `Directories.Holiday.Dark`
    - Each section uses `primary` (required) and `left` (optional).
    - Use this when you want different wallpapers for work/holiday and day/night.
2. Simple work/holiday
    - Keys under `[Directories]`: `workday_primary`, `workday_left`,
      `holiday_primary`, `holiday_left`
    - Use this when you need work vs holiday distinction but no day/night split.
3. Basic (legacy / simplest)
    - Keys under `[Directories]`: `primary`, `left`, `sunday`
    - Use this if you want the same set every day, with an optional Sunday set.

Important notes

- Keys named `primary` and `left` refer to monitors:
    - `primary` → primary (or right) monitor
    - `left` → left monitor (optional)
    - If `left` is not configured and you have multiple monitors, the `primary`
      directory will be used for all monitors.
- When a configured path does not exist the loader will warn; the path must be
  a directory. The program will create log/state directories automatically.
- Time parsing expects `HH:MM` 24-hour format. `day_start_time` and
  `night_start_time` define the day/night boundary used by time-based logic.
  The code handles the case where day crosses midnight.

Logging

- Default log directory: `~/.local/share/wallpaperchanger/logs`
- Configure logging options under `[Logging]` to change location and level.
- Logs are rotated according to `max_size_mb` and `backup_count`.

Images

- Set valid file extensions under `[Images]` as a comma-separated list.
- Extensions are normalized to start with a dot (e.g. `.jpg`, `.png`).

State tracking

- Enable history/state tracking using the `[StateTracking]` section.
- When enabled, the tool records recent images to avoid recent repeats.

Validating configuration

- Use the built-in validator from the CLI:
    - Run `python -m src.cli validate_config` to check the configuration
      and get a short summary of directories, counts, and settings.

Minimal troubleshooting hints

- "No valid wallpaper directories configured" — ensure you configured at
  least one of:
    - any `Directories.Workday.*` or `Directories.Holiday.*` section with
      `primary`, or
    - `workday_primary` / `holiday_primary` under `[Directories]`, or
    - `primary` under `[Directories]`.
- If wallpapers are not changing, confirm:
    - Your configured directories contain image files with allowed extensions.
    - Required helper programs are installed (`feh` for X11, `swaybg` for Wayland)
    - Check logs under `~/.local/share/wallpaperchanger/logs/main.log`.

Best practices (keep things simple)

- Start with a single `primary` directory and `extensions = .jpg,.png`.
- Only add time-based sections when necessary.
- Use absolute paths or `~` (tilde) for user home expansion.
- Keep the config human-editable and minimal to make future refactors simple.
