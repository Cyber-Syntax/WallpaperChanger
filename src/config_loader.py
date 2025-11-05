#!/usr/bin/env python3
"""Configuration loader for WallpaperChanger.

This module handles loading and validating configuration from config.ini file.
Supports multiple configuration levels:
- Basic directory and logging configuration
- Holiday day configuration
- Work vs Holiday directory distinction
- Time-based (day/night) wallpaper selection

Example:
    >>> from src.config_loader import load_config
    >>> config = load_config()
    >>> print(config.get_wallpaper_dirs(is_holiday=False, is_day=True))

"""

import configparser
import logging
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

        # Time-based selection (highest priority)
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

        # Simple work/holiday directories (fallback)
        if is_holiday and dirs.holiday_primary:
            return self._build_dir_dict(
                dirs.holiday_primary, dirs.holiday_left
            )
        if not is_holiday and dirs.workday_primary:
            return self._build_dir_dict(
                dirs.workday_primary, dirs.workday_left
            )

        # Basic directories (legacy fallback)
        if is_holiday and dirs.sunday:
            return self._build_dir_dict(dirs.sunday, None)
        if dirs.primary:
            return self._build_dir_dict(dirs.primary, dirs.left)

        msg = "No valid wallpaper directories configured"
        raise ValueError(msg)

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


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from config.ini file.

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
        config_path = (
            Path.home() / ".config" / "wallpaperchanger" / "config.ini"
        )

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

    return Config(
        directories=directories,
        logging=logging_config,
        schedule=schedule,
        image_extensions=image_extensions,
    )


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


def create_default_config(config_path: Path | None = None) -> None:
    """Create a default configuration file template.

    Args:
        config_path: Optional custom path for config file.
                    Defaults to ~/.config/wallpaperchanger/config.ini

    """
    if config_path is None:
        config_path = (
            Path.home() / ".config" / "wallpaperchanger" / "config.ini"
        )

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    default_content = """# WallpaperChanger Configuration File
# WARN: Created by wallpaperchanger, please edit this file to your preferences.

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
# Left monitor (optional - comment out if you have only one monitor)
left = /home/developer/Pictures/Wallpapers/workday/left_output/light/

# Workday Dark Theme Directories
[Directories.Workday.Dark]
primary = /home/developer/Pictures/Wallpapers/workday/primary_output/dark/
left = /home/developer/Pictures/Wallpapers/workday/left_output/dark/

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
# 1. Time-based directories (Workday/Holiday × Light/Dark)
# 2. Simple work/holiday directories
# 3. Basic directories with optional Sunday
#
# The script will use the most specific configuration available.
#
"""

    config_path.write_text(default_content, encoding="utf-8")
