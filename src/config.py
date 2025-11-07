#!/usr/bin/env python3
"""Configuration management for WallpaperChanger.

Handles loading, validation, and initialization of configuration files.
All configuration logic is centralized here.

Example:
    >>> from src.config import load, create_default
    >>> config = load()
    >>> print(config.get_wallpaper_dirs(is_holiday=False, is_day=True))

"""

import configparser
import logging
import sys
from dataclasses import dataclass
from datetime import time
from pathlib import Path


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    log_dir: Path
    max_size_mb: int
    backup_count: int
    log_level: str


@dataclass
class ScheduleConfig:
    """Schedule configuration for holidays and time-based switching."""

    holiday_days: list[str]
    day_start_time: time
    night_start_time: time


@dataclass
class StateTrackingConfig:
    """State persistence configuration settings."""

    enabled: bool
    state_file: Path


@dataclass
class DirectoryConfig:
    """Wallpaper directory configuration.

    Supports both simple and time-based configurations with automatic fallback.
    """

    # Time-based directories (preferred)
    workday_light_primary: Path | None = None
    workday_light_left: Path | None = None
    workday_dark_primary: Path | None = None
    workday_dark_left: Path | None = None
    holiday_light_primary: Path | None = None
    holiday_light_left: Path | None = None
    holiday_dark_primary: Path | None = None
    holiday_dark_left: Path | None = None

    # Simple work/holiday directories (fallback)
    workday_primary: Path | None = None
    workday_left: Path | None = None
    holiday_primary: Path | None = None
    holiday_left: Path | None = None

    # Basic directories (legacy fallback)
    primary: Path | None = None
    left: Path | None = None
    sunday: Path | None = None


@dataclass
class Config:
    """Complete application configuration."""

    directories: DirectoryConfig
    logging: LoggingConfig
    schedule: ScheduleConfig
    image_extensions: list[str]
    state_tracking: StateTrackingConfig

    def get_wallpaper_dirs(
        self, is_holiday: bool, is_day: bool
    ) -> dict[str, Path]:
        """Get appropriate wallpaper directories based on context.

        Args:
            is_holiday: Whether today is a holiday
            is_day: Whether current time is during day (vs night)

        Returns:
            Dictionary with 'primary' and optionally 'left' paths

        """
        dirs = self.directories

        # Try to find directories in priority order
        result = self._try_time_based(dirs, is_holiday, is_day)
        if result:
            return result

        result = self._try_work_holiday(dirs, is_holiday)
        if result:
            return result

        result = self._try_basic(dirs, is_holiday)
        if result:
            return result

        msg = "No valid wallpaper directories configured"
        raise ValueError(msg)

    def _try_time_based(
        self, dirs: DirectoryConfig, is_holiday: bool, is_day: bool
    ) -> dict[str, Path] | None:
        """Try time-based directory selection."""
        if is_holiday:
            if is_day and dirs.holiday_light_primary:
                return self._build_dir_dict(
                    dirs.holiday_light_primary, dirs.holiday_light_left
                )
            if not is_day and dirs.holiday_dark_primary:
                return self._build_dir_dict(
                    dirs.holiday_dark_primary, dirs.holiday_dark_left
                )
        else:  # workday
            if is_day and dirs.workday_light_primary:
                return self._build_dir_dict(
                    dirs.workday_light_primary, dirs.workday_light_left
                )
            if not is_day and dirs.workday_dark_primary:
                return self._build_dir_dict(
                    dirs.workday_dark_primary, dirs.workday_dark_left
                )
        return None

    def _try_work_holiday(
        self, dirs: DirectoryConfig, is_holiday: bool
    ) -> dict[str, Path] | None:
        """Try simple work/holiday directory selection."""
        if is_holiday and dirs.holiday_primary:
            return self._build_dir_dict(
                dirs.holiday_primary, dirs.holiday_left
            )
        if not is_holiday and dirs.workday_primary:
            return self._build_dir_dict(
                dirs.workday_primary, dirs.workday_left
            )
        return None

    def _try_basic(
        self, dirs: DirectoryConfig, is_holiday: bool
    ) -> dict[str, Path] | None:
        """Try basic directory selection."""
        if is_holiday and dirs.sunday:
            return self._build_dir_dict(dirs.sunday, None)
        if dirs.primary:
            return self._build_dir_dict(dirs.primary, dirs.left)
        return None

    def _build_dir_dict(
        self, primary: Path, left: Path | None
    ) -> dict[str, Path]:
        """Build directory dictionary from primary and optional left paths."""
        result = {"primary": primary}
        if left:
            result["left"] = left
        return result

    def is_holiday(self, weekday: int) -> bool:
        """Check if given weekday is a holiday.

        Args:
            weekday: Day of week (0=Monday, 6=Sunday)

        Returns:
            True if the day is configured as a holiday

        """
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        current_day = day_names[weekday]
        return current_day in self.schedule.holiday_days

    def is_daytime(self, current_time: time) -> bool:
        """Check if current time is during day (vs night).

        Args:
            current_time: Current time to check

        Returns:
            True if current time is during day hours

        """
        day_start = self.schedule.day_start_time
        night_start = self.schedule.night_start_time

        # Handle normal case: day starts before night (e.g., 08:00 to 18:00)
        if day_start < night_start:
            return day_start <= current_time < night_start

        # Handle edge case: day crosses midnight (e.g., 22:00 to 06:00)
        # In this case, "day" is the time that crosses midnight
        # So we're "day" if we're after day_start OR before night_start
        return current_time >= day_start or current_time < night_start


def load(config_path: Path | None = None) -> Config:
    """Load and validate configuration from config.ini file.

    Args:
        config_path: Optional custom path to config file.
                    Defaults to ~/.config/wallpaperchanger/config.ini

    Returns:
        Loaded and validated configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid or missing required fields

    """
    if config_path is None:
        config_path = get_default_path()

    if not config_path.exists():
        msg = (
            f"Configuration file not found: {config_path}\n"
            f"Please create it from the example template."
        )
        raise FileNotFoundError(msg)

    parser = configparser.ConfigParser()
    parser.read(config_path)

    # Load all configuration sections
    directories = _load_directories(parser)
    logging_config = _load_logging(parser)
    schedule = _load_schedule(parser)
    image_extensions = _load_image_extensions(parser)
    state_tracking = _load_state_tracking(parser)

    return Config(
        directories=directories,
        logging=logging_config,
        schedule=schedule,
        image_extensions=image_extensions,
        state_tracking=state_tracking,
    )


def create_default(config_path: Path | None = None) -> None:
    """Create a default configuration file template.

    Args:
        config_path: Optional custom path for config file.
                    Defaults to ~/.config/wallpaperchanger/config.ini

    """
    if config_path is None:
        config_path = get_default_path()

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    default_content = """# WallpaperChanger Configuration File
# WARN: Created by wallpaperchanger, please edit this file to your preferences.

# =============================================================================
# CONFIGURATION NOTES
# =============================================================================
#
# Directory Structure Example for Time-Based Selection:
# ----------------------------------------
# /home/user/Pictures/Wallpapers/
# ├── workday/
# │   ├── primary_output/
# │   │   ├── dark/
# │   │   │   ├── 0.jpg
# │   │   │   ├── 1.jpg
# │   │   │   └── ...
# │   │   └── light/
# │   │       ├── 0.jpg
# │   │       ├── 1.jpg
# │   │       └── ...
# │   └── left_output/
# │       ├── dark/
# │       │   └── ...
# │       └── light/
# │           └── ...
# └── holiday/
#     ├── dark/
#     │   ├── 1.jpg
#     │   └── ...
#     └── light/
#         ├── 3.jpg
#         └── ...
#
# Multi-monitor Behavior:
# ----------------------
# - If you have 2 monitors, the script alternates between primary and left
# - Monitor 0 (primary/right) uses the 'primary' directory
# - Monitor 1 (left) uses the 'left' directory (if configured)
# - If 'left' is not configured, both monitors use 'primary'
# - Used images are tracked per run to avoid duplicates on different monitors
#
# Fallback Chain:
# --------------
# 1. Time-based directories (Workday/Holiday + Light/Dark)
# 2. Simple work/holiday directories
# 3. Basic directories with optional Sunday


# =============================================================================
# TIME-BASED WALLPAPER SELECTION (Day/Night with Work/Holiday)
# =============================================================================
# This is the most advanced configuration supporting:
# - Different wallpapers for workdays vs holidays
# - Different wallpapers for day vs night
# - Support for single or multi-monitor setups

[Schedule]
# Use day names for clarity (comma-separated for multiple days)
# Valid values: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
holiday_days = Sunday
# Example for weekend: Saturday,Sunday

# Time of day for theme switching (24-hour format HH:MM)
# Light theme starts at this time
day_start_time = 08:00

# Dark theme starts at this time
night_start_time = 18:00

# Workday Light Theme Directories
[Directories.Workday.Light]
# Primary monitor (or right monitor in multi-monitor setup)
primary = /home/developer/Pictures/Wallpapers/workday/primary_output/light/
# Left monitor (optional)
#left = /home/developer/Pictures/Wallpapers/workday/left_output/light/

# Workday Dark Theme Directories
[Directories.Workday.Dark]
primary = /home/developer/Pictures/Wallpapers/workday/primary_output/dark/
#left = /home/developer/Pictures/Wallpapers/workday/left_output/dark/

# Holiday Light Theme Directories
[Directories.Holiday.Light]
# Primary monitor is required, left is optional
primary = /home/developer/Pictures/Wallpapers/holiday/light/
# Uncomment if you have a left monitor and want different holiday wallpapers
#left = /home/developer/Pictures/Wallpapers/holiday/light/left/

# Holiday Dark Theme Directories
[Directories.Holiday.Dark]
primary = /home/developer/Pictures/Wallpapers/holiday/dark/
#left = /home/developer/Pictures/Wallpapers/holiday/dark/left/


# =============================================================================
# SIMPLE WORK/HOLIDAY DISTINCTION (without time-based selection)
# =============================================================================
# Uncomment this section if you don't want time-based selection
# and just want different wallpapers for workdays vs holidays

#[Directories]
# Workday wallpapers
#workday_primary = /home/developer/Pictures/Wallpapers/workday/primary/
#workday_left = /home/developer/Pictures/Wallpapers/workday/left/

# Holiday wallpapers
#holiday_primary = /home/developer/Pictures/Wallpapers/holiday/primary/
#holiday_left = /home/developer/Pictures/Wallpapers/holiday/left/


# =============================================================================
# BASIC CONFIGURATION (simplest setup)
# =============================================================================
# Uncomment this section for the simplest configuration
# Same wallpapers every day, with optional special Sunday directory

#[Directories]
# Primary monitor wallpapers (used on all workdays)
#primary = /home/developer/Pictures/Wallpapers/primary/

# Left monitor wallpapers (optional, for multi-monitor setups)
#left = /home/developer/Pictures/Wallpapers/left/

# Sunday special wallpapers (optional, used on Sundays only)
#sunday = /home/developer/Pictures/Wallpapers/Sunday/


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
[Logging]
# Directory where log files will be stored (XDG compliant default)
# Uncomment to customize, or leave commented for default
#log_dir = ~/.local/share/wallpaperchanger/logs

# Maximum size of each log file in MB (default: 1MB)
#max_size_mb = 1

# Number of backup log files to keep (default: 3)
#backup_count = 3

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
#log_level = INFO


# =============================================================================
# IMAGE SETTINGS
# =============================================================================
[Images]
# Image file extensions to search for (comma-separated)
# The script will only consider files with these extensions
extensions = .png,.jpg,.jpeg

# =============================================================================
# STATE TRACKING (Recommended)
# =============================================================================
# Enable state tracking for intelligent wallpaper selection (default true)
# When enabled, the script tracks wallpaper history to avoid recent images
[StateTracking]
enabled = true

# Location of state file (default: ~/.local/share/wallpaperchanger/state.json)
#state_file = ~/.local/share/wallpaperchanger/state.json
"""

    # Write default configuration to file
    config_path.write_text(default_content, encoding="utf-8")


def validate(config_path: Path | None = None) -> bool:
    """Validate configuration file and report issues.

    Args:
        config_path: Optional custom path to config file

    Returns:
        True if validation passes, False otherwise

    """
    print("🔍 Validating WallpaperChanger configuration...\n")

    cfg_path = config_path or get_default_path()
    print(f"📁 Config file: {cfg_path}")

    if not cfg_path.exists():
        print("❌ Configuration file not found!")
        print("\nTo create a default configuration, run:")
        print("  python -m src.cli init")
        return False

    print("✅ Configuration file exists\n")

    # Load and validate config
    try:
        cfg = load(cfg_path)
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

    print("✅ Configuration file is valid\n")

    # Validate schedule
    _validate_schedule(cfg.schedule)

    # Validate directories
    has_images = _validate_directories(cfg.directories, cfg.image_extensions)

    # Validate logging
    _validate_logging(cfg.logging)

    # Validate state tracking
    _validate_state_tracking(cfg.state_tracking)

    # Image extensions
    print("🎨 Image Extensions:")
    print(f"  {', '.join(cfg.image_extensions)}")
    print()

    # Summary
    print("=" * 60)
    print("📊 Validation Summary:")

    if not has_images:
        print("  ❌ No images found in any configured directory!")
        print("     Add wallpaper images to your directories.")
        return False

    print("✅ Configuration validation complete!")
    print()
    print("Next steps:")
    print("  1. Run the wallpaper changer: python main.py")
    print("  2. Check logs: ~/.local/share/wallpaperchanger/logs/main.log")

    return True


def get_default_path() -> Path:
    """Get default config path.

    Returns:
        Default configuration file path

    """
    return Path.home() / ".config" / "wallpaperchanger" / "config.ini"


# =============================================================================
# Private Helper Functions
# =============================================================================


def _load_directories(parser: configparser.ConfigParser) -> DirectoryConfig:
    """Load directory configuration with automatic fallback support."""
    dirs = DirectoryConfig()

    # Time-based directories
    if parser.has_section("Directories.Workday.Light"):
        dirs.workday_light_primary = _get_path(
            parser, "Directories.Workday.Light", "primary"
        )
        dirs.workday_light_left = _get_path(
            parser, "Directories.Workday.Light", "left", required=False
        )

    if parser.has_section("Directories.Workday.Dark"):
        dirs.workday_dark_primary = _get_path(
            parser, "Directories.Workday.Dark", "primary"
        )
        dirs.workday_dark_left = _get_path(
            parser, "Directories.Workday.Dark", "left", required=False
        )

    if parser.has_section("Directories.Holiday.Light"):
        dirs.holiday_light_primary = _get_path(
            parser, "Directories.Holiday.Light", "primary"
        )
        dirs.holiday_light_left = _get_path(
            parser, "Directories.Holiday.Light", "left", required=False
        )

    if parser.has_section("Directories.Holiday.Dark"):
        dirs.holiday_dark_primary = _get_path(
            parser, "Directories.Holiday.Dark", "primary"
        )
        dirs.holiday_dark_left = _get_path(
            parser, "Directories.Holiday.Dark", "left", required=False
        )

    # Simple work/holiday directories
    if parser.has_section("Directories"):
        dirs.workday_primary = _get_path(
            parser, "Directories", "workday_primary", required=False
        )
        dirs.workday_left = _get_path(
            parser, "Directories", "workday_left", required=False
        )
        dirs.holiday_primary = _get_path(
            parser, "Directories", "holiday_primary", required=False
        )
        dirs.holiday_left = _get_path(
            parser, "Directories", "holiday_left", required=False
        )

        # Basic directories
        dirs.primary = _get_path(
            parser, "Directories", "primary", required=False
        )
        dirs.left = _get_path(parser, "Directories", "left", required=False)
        dirs.sunday = _get_path(
            parser, "Directories", "sunday", required=False
        )

    # Validate that at least one valid configuration exists
    has_time_based = (
        dirs.workday_light_primary
        or dirs.workday_dark_primary
        or dirs.holiday_light_primary
        or dirs.holiday_dark_primary
    )
    has_work_holiday = dirs.workday_primary or dirs.holiday_primary
    has_basic = dirs.primary or dirs.sunday

    if not (has_time_based or has_work_holiday or has_basic):
        msg = (
            "No valid wallpaper directories configured. "
            "At least one directory configuration is required."
        )
        raise ValueError(msg)

    return dirs


def _load_logging(parser: configparser.ConfigParser) -> LoggingConfig:
    """Load logging configuration with defaults."""
    default_log_dir = (
        Path.home() / ".local" / "share" / "wallpaperchanger" / "logs"
    )

    log_dir_str = parser.get(
        "Logging", "log_dir", fallback=str(default_log_dir)
    )
    log_dir = Path(log_dir_str).expanduser()

    max_size_mb = parser.getint("Logging", "max_size_mb", fallback=1)
    backup_count = parser.getint("Logging", "backup_count", fallback=3)
    log_level = parser.get("Logging", "log_level", fallback="INFO").upper()

    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        msg = f"Invalid log_level: {log_level}. Must be one of {valid_levels}"
        raise ValueError(msg)

    return LoggingConfig(
        log_dir=log_dir,
        max_size_mb=max_size_mb,
        backup_count=backup_count,
        log_level=log_level,
    )


def _load_schedule(parser: configparser.ConfigParser) -> ScheduleConfig:
    """Load schedule configuration for holidays and time-based switching."""
    # Parse holiday days
    holiday_str = parser.get("Schedule", "holiday_days", fallback="Sunday")
    holiday_days = [day.strip() for day in holiday_str.split(",")]

    # Validate day names
    valid_days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    for day in holiday_days:
        if day not in valid_days:
            msg = (
                f"Invalid holiday day: {day}. "
                f"Must be one of {', '.join(valid_days)}"
            )
            raise ValueError(msg)

    # Parse time settings
    day_start_str = parser.get("Schedule", "day_start_time", fallback="08:00")
    night_start_str = parser.get(
        "Schedule", "night_start_time", fallback="18:00"
    )

    day_start_time = _parse_time(day_start_str, "day_start_time")
    night_start_time = _parse_time(night_start_str, "night_start_time")

    return ScheduleConfig(
        holiday_days=holiday_days,
        day_start_time=day_start_time,
        night_start_time=night_start_time,
    )


def _load_image_extensions(parser: configparser.ConfigParser) -> list[str]:
    """Load supported image file extensions."""
    extensions_str = parser.get(
        "Images", "extensions", fallback=".png,.jpg,.jpeg"
    )
    extensions = [ext.strip() for ext in extensions_str.split(",")]

    # Ensure extensions start with a dot
    extensions = [
        ext if ext.startswith(".") else f".{ext}" for ext in extensions
    ]

    return extensions


def _load_state_tracking(
    parser: configparser.ConfigParser,
) -> StateTrackingConfig:
    """Load state tracking configuration.

    Args:
        parser: ConfigParser instance

    Returns:
        StateTrackingConfig with defaults if section not present

    """
    # Default values
    enabled = False
    state_file = (
        Path.home() / ".local" / "share" / "wallpaperchanger" / "state.json"
    )

    # Load custom values if section exists
    if parser.has_section("StateTracking"):
        enabled = parser.getboolean("StateTracking", "enabled", fallback=False)

        # Only load other settings if state tracking is enabled
        if enabled:
            state_file_str = parser.get(
                "StateTracking",
                "state_file",
                fallback=str(state_file),
            )
            state_file = Path(state_file_str).expanduser().resolve()

    return StateTrackingConfig(
        enabled=enabled,
        state_file=state_file,
    )


def _get_path(
    parser: configparser.ConfigParser,
    section: str,
    key: str,
    required: bool = True,
) -> Path | None:
    """Get and validate a path from config.

    Args:
        parser: ConfigParser instance
        section: Config section name
        key: Config key name
        required: Whether this path is required

    Returns:
        Expanded Path object or None if not required and not found

    Raises:
        ValueError: If required path is missing or invalid

    """
    if not parser.has_option(section, key):
        if required:
            msg = f"Missing required config: [{section}] {key}"
            raise ValueError(msg)
        return None

    path_str = parser.get(section, key)
    path = Path(path_str).expanduser().resolve()

    if not path.exists():
        logging.warning(
            "Directory does not exist: %s (from [%s] %s)", path, section, key
        )

    if not path.is_dir():
        msg = f"Path is not a directory: {path} (from [{section}] {key})"
        raise ValueError(msg)

    return path


def _parse_time(time_str: str, field_name: str) -> time:
    """Parse time string in HH:MM format.

    Args:
        time_str: Time string to parse (e.g., "08:00")
        field_name: Name of field for error messages

    Returns:
        Parsed time object

    Raises:
        ValueError: If time format is invalid

    """
    try:
        hour, minute = map(int, time_str.split(":"))
        return time(hour=hour, minute=minute)
    except (ValueError, AttributeError) as e:
        msg = (
            f"Invalid time format for {field_name}: {time_str}. "
            f"Expected HH:MM format (e.g., 08:00)"
        )
        raise ValueError(msg) from e


def _validate_schedule(schedule: ScheduleConfig) -> None:
    """Validate and display schedule configuration."""
    print("📅 Schedule Configuration:")
    print(f"  Holiday days: {', '.join(schedule.holiday_days)}")
    print(f"  Day starts: {schedule.day_start_time.strftime('%H:%M')}")
    print(f"  Night starts: {schedule.night_start_time.strftime('%H:%M')}")
    print()


def _validate_directories(
    dirs: DirectoryConfig, extensions: list[str]
) -> bool:
    """Validate directories and count images.

    Args:
        dirs: Directory configuration
        extensions: List of valid image extensions

    Returns:
        True if any images found, False otherwise

    """
    print("📂 Directory Configuration:")

    # Define directory mappings
    dir_map = {
        "Time-based": [
            ("Workday Light Primary", dirs.workday_light_primary),
            ("Workday Light Left", dirs.workday_light_left),
            ("Workday Dark Primary", dirs.workday_dark_primary),
            ("Workday Dark Left", dirs.workday_dark_left),
            ("Holiday Light Primary", dirs.holiday_light_primary),
            ("Holiday Light Left", dirs.holiday_light_left),
            ("Holiday Dark Primary", dirs.holiday_dark_primary),
            ("Holiday Dark Left", dirs.holiday_dark_left),
        ],
        "Work/Holiday": [
            ("Workday Primary", dirs.workday_primary),
            ("Workday Left", dirs.workday_left),
            ("Holiday Primary", dirs.holiday_primary),
            ("Holiday Left", dirs.holiday_left),
        ],
        "Basic": [
            ("Primary", dirs.primary),
            ("Left", dirs.left),
            ("Sunday", dirs.sunday),
        ],
    }

    total_images = 0
    empty_dirs = []

    for category, dir_list in dir_map.items():
        configured = [(name, path) for name, path in dir_list if path]
        if not configured:
            continue

        print(f"  📁 {category} Directories:")
        for name, path in configured:
            exists = "✅" if path.exists() else "⚠️"
            count = _count_images(path, extensions) if path.exists() else 0
            total_images += count

            if count == 0:
                empty_dirs.append((name, path))
                print(f"    {exists} {name}: {path} (empty)")
            else:
                print(f"    {exists} {name}: {path} ({count} images)")

    if empty_dirs:
        print("\n  ⚠️  Note: Some directories are empty (may be intentional)")

    print()
    return total_images > 0


def _count_images(directory: Path, extensions: list[str]) -> int:
    """Count images in directory.

    Args:
        directory: Directory to search
        extensions: List of valid image extensions

    Returns:
        Number of images found

    """
    if not directory.exists():
        return 0
    return len(
        [
            f
            for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        ]
    )


def _validate_logging(logging_config: LoggingConfig) -> None:
    """Validate and display logging configuration."""
    print("📋 Logging Configuration:")
    print(f"  Log directory: {logging_config.log_dir}")
    print(f"  Log level: {logging_config.log_level}")
    print(f"  Max size: {logging_config.max_size_mb}MB")
    print(f"  Backup count: {logging_config.backup_count}")

    if not logging_config.log_dir.exists():
        print(
            "  ⚠️  Log directory does not exist (will be created on first run)"
        )
    print()


def _validate_state_tracking(state_config: StateTrackingConfig) -> None:
    """Validate and display state tracking configuration."""
    print("💾 State Tracking Configuration:")
    print(f"  Enabled: {'Yes' if state_config.enabled else 'No'}")

    if state_config.enabled:
        print(f"  State file: {state_config.state_file}")

        # Check if state file parent directory exists
        if not state_config.state_file.parent.exists():
            print(
                "  ⚠️  State file directory does not exist "
                "(will be created on first run)"
            )
    print()


def main() -> None:
    """Run configuration validation script."""
    try:
        success = validate()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
