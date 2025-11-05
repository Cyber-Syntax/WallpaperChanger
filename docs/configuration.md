## Configuration

The configuration file is located at `~/.config/wallpaperchanger/config.ini`.

### Configuration Levels

WallpaperChanger supports three levels of configuration complexity:

#### Basic Configuration (Simplest)

Same wallpapers every day, with optional special Sunday directory.

```ini
[Schedule]
holiday_days = Sunday

[Directories]
primary = ~/Pictures/Wallpapers/primary/
left = ~/Pictures/Wallpapers/left/
sunday = ~/Pictures/Wallpapers/Sunday/

[Images]
extensions = .png,.jpg,.jpeg
```

#### Work/Holiday Distinction

Different wallpapers for workdays vs holidays, without time-based selection.

```ini
[Schedule]
holiday_days = Saturday,Sunday

[Directories]
workday_primary = ~/Pictures/Wallpapers/workday/primary/
workday_left = ~/Pictures/Wallpapers/workday/left/
holiday_primary = ~/Pictures/Wallpapers/holiday/primary/
holiday_left = ~/Pictures/Wallpapers/holiday/left/

[Images]
extensions = .png,.jpg,.jpeg
```

#### Time-Based Selection (Most Advanced)

Different wallpapers for workdays vs holidays AND day vs night.

```ini
[Schedule]
holiday_days = Sunday
day_start_time = 08:00
night_start_time = 18:00

[Directories.Workday.Light]
primary = ~/Pictures/Wallpapers/workday/primary_output/light/
left = ~/Pictures/Wallpapers/workday/left_output/light/

[Directories.Workday.Dark]
primary = ~/Pictures/Wallpapers/workday/primary_output/dark/
left = ~/Pictures/Wallpapers/workday/left_output/dark/

[Directories.Holiday.Light]
primary = ~/Pictures/Wallpapers/holiday/light/

[Directories.Holiday.Dark]
primary = ~/Pictures/Wallpapers/holiday/dark/

[Images]
extensions = .png,.jpg,.jpeg
```

### Configuration Options

#### [Schedule]

- `holiday_days`: Comma-separated list of days (e.g., `Sunday` or `Saturday,Sunday`)
- `day_start_time`: Time when light theme starts (24-hour format, e.g., `08:00`)
- `night_start_time`: Time when dark theme starts (24-hour format, e.g., `18:00`)

#### [Directories]

- `primary`: Required - Primary monitor wallpaper directory
- `left`: Optional - Left monitor wallpaper directory (for multi-monitor setups)

#### [Logging]

All settings are optional with sensible defaults:

- `log_dir`: Directory for log files (default: `~/.local/share/wallpaperchanger/logs`)
- `max_size_mb`: Maximum log file size in MB (default: `1`)
- `backup_count`: Number of backup log files (default: `3`)
- `log_level`: Logging level - `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (default: `INFO`)

#### [Images]

- `extensions`: Comma-separated list of image extensions (default: `.png,.jpg,.jpeg`)