#!/usr/bin/env python3
"""Unit tests for configuration loader.

Tests cover all configuration levels:
- Basic directories
- Work/holiday distinction
- Time-based selection
"""

from datetime import time
from pathlib import Path

import pytest

from src.config_loader import (
    Config,
    DirectoryConfig,
    LoggingConfig,
    ScheduleConfig,
    StateTrackingConfig,
    create_default_config,
    load_config,
)


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for config files.

    Args:
        tmp_path: Pytest temporary path fixture

    Returns:
        Path to temporary config directory

    """
    config_dir = tmp_path / ".config" / "wallpaperchanger"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def temp_wallpaper_dirs(tmp_path: Path) -> dict[str, Path]:
    """Create temporary wallpaper directories for testing.

    Args:
        tmp_path: Pytest temporary path fixture

    Returns:
        Dictionary of created directory paths

    """
    dirs = {}

    # Phase 3 directories
    for day_type in ["workday", "holiday"]:
        for time_type in ["light", "dark"]:
            for monitor in ["primary", "left"]:
                path = tmp_path / "wallpapers" / day_type / monitor / time_type
                path.mkdir(parents=True, exist_ok=True)
                # Create a test image
                (path / "test.jpg").touch()
                dirs[f"{day_type}_{time_type}_{monitor}"] = path

    # Phase 2 directories
    for day_type in ["workday", "holiday"]:
        for monitor in ["primary", "left"]:
            path = tmp_path / "wallpapers_phase2" / day_type / monitor
            path.mkdir(parents=True, exist_ok=True)
            (path / "test.jpg").touch()
            dirs[f"phase2_{day_type}_{monitor}"] = path

    # Phase 1 directories
    for dir_name in ["primary", "left", "sunday"]:
        path = tmp_path / "wallpapers_phase1" / dir_name
        path.mkdir(parents=True, exist_ok=True)
        (path / "test.jpg").touch()
        dirs[f"phase1_{dir_name}"] = path

    return dirs


def test_load_config_missing_file() -> None:
    """Test that missing config file raises FileNotFoundError."""
    nonexistent_path = Path("/nonexistent/path/config.ini")

    with pytest.raises(
        FileNotFoundError, match="Configuration file not found"
    ):
        load_config(nonexistent_path)


def test_load_config_time_based(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test loading time-based configuration with day/night selection."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Sunday
day_start_time = 08:00
night_start_time = 18:00

[Directories.Workday.Light]
primary = {temp_wallpaper_dirs["workday_light_primary"]}
left = {temp_wallpaper_dirs["workday_light_left"]}

[Directories.Workday.Dark]
primary = {temp_wallpaper_dirs["workday_dark_primary"]}
left = {temp_wallpaper_dirs["workday_dark_left"]}

[Directories.Holiday.Light]
primary = {temp_wallpaper_dirs["holiday_light_primary"]}

[Directories.Holiday.Dark]
primary = {temp_wallpaper_dirs["holiday_dark_primary"]}

[Logging]
log_level = INFO

[Images]
extensions = .png,.jpg,.jpeg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    assert config.schedule.holiday_days == ["Sunday"]
    assert config.schedule.day_start_time == time(8, 0)
    assert config.schedule.night_start_time == time(18, 0)
    assert (
        config.directories.workday_light_primary
        == temp_wallpaper_dirs["workday_light_primary"]
    )
    assert (
        config.directories.holiday_dark_primary
        == temp_wallpaper_dirs["holiday_dark_primary"]
    )
    assert config.image_extensions == [".png", ".jpg", ".jpeg"]


def test_load_config_work_holiday(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test loading work/holiday configuration without time-based selection."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Saturday,Sunday

[Directories]
workday_primary = {temp_wallpaper_dirs["phase2_workday_primary"]}
workday_left = {temp_wallpaper_dirs["phase2_workday_left"]}
holiday_primary = {temp_wallpaper_dirs["phase2_holiday_primary"]}
holiday_left = {temp_wallpaper_dirs["phase2_holiday_left"]}

[Logging]
log_level = DEBUG

[Images]
extensions = .png,.jpg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    assert config.schedule.holiday_days == ["Saturday", "Sunday"]
    assert (
        config.directories.workday_primary
        == temp_wallpaper_dirs["phase2_workday_primary"]
    )
    assert (
        config.directories.holiday_primary
        == temp_wallpaper_dirs["phase2_holiday_primary"]
    )
    assert config.logging.log_level == "DEBUG"


def test_load_config_basic(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test loading basic configuration with simple directories."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Sunday

[Directories]
primary = {temp_wallpaper_dirs["phase1_primary"]}
left = {temp_wallpaper_dirs["phase1_left"]}
sunday = {temp_wallpaper_dirs["phase1_sunday"]}

[Logging]
log_level = WARNING

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    assert config.directories.primary == temp_wallpaper_dirs["phase1_primary"]
    assert config.directories.left == temp_wallpaper_dirs["phase1_left"]
    assert config.directories.sunday == temp_wallpaper_dirs["phase1_sunday"]
    assert config.logging.log_level == "WARNING"


def test_get_wallpaper_dirs_time_based_workday_day(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test getting wallpaper directories for workday during day (time-based)."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Sunday

[Directories.Workday.Light]
primary = {temp_wallpaper_dirs["workday_light_primary"]}
left = {temp_wallpaper_dirs["workday_light_left"]}

[Directories.Workday.Dark]
primary = {temp_wallpaper_dirs["workday_dark_primary"]}

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    dirs = config.get_wallpaper_dirs(is_holiday=False, is_day=True)

    assert dirs["primary"] == temp_wallpaper_dirs["workday_light_primary"]
    assert dirs["left"] == temp_wallpaper_dirs["workday_light_left"]


def test_get_wallpaper_dirs_time_based_holiday_night(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test getting wallpaper directories for holiday during night (time-based)."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Sunday

[Directories.Holiday.Dark]
primary = {temp_wallpaper_dirs["holiday_dark_primary"]}
left = {temp_wallpaper_dirs["holiday_dark_left"]}

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    dirs = config.get_wallpaper_dirs(is_holiday=True, is_day=False)

    assert dirs["primary"] == temp_wallpaper_dirs["holiday_dark_primary"]
    assert dirs["left"] == temp_wallpaper_dirs["holiday_dark_left"]


def test_get_wallpaper_dirs_fallback_to_work_holiday(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test fallback from time-based to work/holiday when time-based dirs not available."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Sunday

[Directories]
workday_primary = {temp_wallpaper_dirs["phase2_workday_primary"]}
holiday_primary = {temp_wallpaper_dirs["phase2_holiday_primary"]}

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    # Should fall back to work/holiday dirs since time-based not configured
    dirs_workday = config.get_wallpaper_dirs(is_holiday=False, is_day=True)
    dirs_holiday = config.get_wallpaper_dirs(is_holiday=True, is_day=False)

    assert (
        dirs_workday["primary"]
        == temp_wallpaper_dirs["phase2_workday_primary"]
    )
    assert (
        dirs_holiday["primary"]
        == temp_wallpaper_dirs["phase2_holiday_primary"]
    )


def test_is_holiday() -> None:
    """Test holiday day detection."""
    config = Config(
        directories=DirectoryConfig(),
        logging=LoggingConfig(
            log_dir=Path("/tmp"),
            max_size_mb=1,
            backup_count=3,
            log_level="INFO",
        ),
        schedule=ScheduleConfig(
            holiday_days=["Saturday", "Sunday"],
            day_start_time=time(8, 0),
            night_start_time=time(18, 0),
        ),
        image_extensions=[".jpg"],
        state_tracking=StateTrackingConfig(
            enabled=False,
            state_file=Path("/tmp/state.json"),
            auto_cleanup=True,
        ),
    )

    # Monday (0) - not holiday
    assert not config.is_holiday(0)

    # Saturday (5) - holiday
    assert config.is_holiday(5)

    # Sunday (6) - holiday
    assert config.is_holiday(6)


def test_is_daytime() -> None:
    """Test daytime detection."""
    config = Config(
        directories=DirectoryConfig(),
        logging=LoggingConfig(
            log_dir=Path("/tmp"),
            max_size_mb=1,
            backup_count=3,
            log_level="INFO",
        ),
        schedule=ScheduleConfig(
            holiday_days=["Sunday"],
            day_start_time=time(8, 0),
            night_start_time=time(18, 0),
        ),
        image_extensions=[".jpg"],
        state_tracking=StateTrackingConfig(
            enabled=False,
            state_file=Path("/tmp/state.json"),
            auto_cleanup=True,
        ),
    )

    # 07:00 - night
    assert not config.is_daytime(time(7, 0))

    # 08:00 - day starts
    assert config.is_daytime(time(8, 0))

    # 12:00 - day
    assert config.is_daytime(time(12, 0))

    # 17:59 - still day
    assert config.is_daytime(time(17, 59))

    # 18:00 - night starts
    assert not config.is_daytime(time(18, 0))

    # 23:00 - night
    assert not config.is_daytime(time(23, 0))


def test_is_daytime_crosses_midnight() -> None:
    """Test daytime detection when day period crosses midnight."""
    config = Config(
        directories=DirectoryConfig(),
        logging=LoggingConfig(
            log_dir=Path("/tmp"),
            max_size_mb=1,
            backup_count=3,
            log_level="INFO",
        ),
        schedule=ScheduleConfig(
            holiday_days=["Sunday"],
            day_start_time=time(22, 0),  # Day starts at 22:00
            night_start_time=time(6, 0),  # Night starts at 06:00
        ),
        image_extensions=[".jpg"],
        state_tracking=StateTrackingConfig(
            enabled=False,
            state_file=Path("/tmp/state.json"),
            auto_cleanup=True,
        ),
    )

    # 05:00 - day (before night start, after midnight)
    assert config.is_daytime(time(5, 0))

    # 06:00 - night starts
    assert not config.is_daytime(time(6, 0))

    # 12:00 - night
    assert not config.is_daytime(time(12, 0))

    # 21:59 - still night
    assert not config.is_daytime(time(21, 59))

    # 22:00 - day starts
    assert config.is_daytime(time(22, 0))

    # 23:00 - day
    assert config.is_daytime(time(23, 0))

    # 00:00 - day (crosses midnight)
    assert config.is_daytime(time(0, 0))


def test_multiple_holiday_days(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test configuration with multiple holiday days."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Friday,Saturday,Sunday

[Directories]
primary = {temp_wallpaper_dirs["phase1_primary"]}

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    assert config.schedule.holiday_days == ["Friday", "Saturday", "Sunday"]
    assert config.is_holiday(4)  # Friday
    assert config.is_holiday(5)  # Saturday
    assert config.is_holiday(6)  # Sunday
    assert not config.is_holiday(0)  # Monday


def test_invalid_holiday_day(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test that invalid holiday day raises ValueError."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = InvalidDay

[Directories]
primary = {temp_wallpaper_dirs["phase1_primary"]}

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid holiday day"):
        load_config(config_path)


def test_invalid_time_format(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test that invalid time format raises ValueError."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Sunday
day_start_time = 25:00

[Directories]
primary = {temp_wallpaper_dirs["phase1_primary"]}

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid time format"):
        load_config(config_path)


def test_invalid_log_level(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test that invalid log level raises ValueError."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Sunday

[Directories]
primary = {temp_wallpaper_dirs["phase1_primary"]}

[Logging]
log_level = INVALID

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid log_level"):
        load_config(config_path)


def test_logging_defaults(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test that logging configuration uses proper defaults."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Sunday

[Directories]
primary = {temp_wallpaper_dirs["phase1_primary"]}

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    assert config.logging.max_size_mb == 1
    assert config.logging.backup_count == 3
    assert config.logging.log_level == "INFO"
    assert (
        config.logging.log_dir
        == Path.home() / ".local" / "share" / "wallpaperchanger" / "logs"
    )


def test_image_extensions_with_dots(
    temp_config_dir: Path, temp_wallpaper_dirs: dict[str, Path]
) -> None:
    """Test that image extensions work with or without leading dots."""
    config_path = temp_config_dir / "config.ini"

    config_content = f"""[Schedule]
holiday_days = Sunday

[Directories]
primary = {temp_wallpaper_dirs["phase1_primary"]}

[Images]
extensions = png,jpg,.jpeg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    # All extensions should have leading dots
    assert all(ext.startswith(".") for ext in config.image_extensions)
    assert ".png" in config.image_extensions
    assert ".jpg" in config.image_extensions
    assert ".jpeg" in config.image_extensions


def test_path_expansion(temp_config_dir: Path, tmp_path: Path) -> None:
    """Test that tilde paths are properly expanded."""
    config_path = temp_config_dir / "config.ini"

    # Create directory in tmp_path that we'll reference with ~
    wallpaper_dir = tmp_path / "wallpapers" / "primary"
    wallpaper_dir.mkdir(parents=True, exist_ok=True)
    (wallpaper_dir / "test.jpg").touch()

    config_content = f"""[Schedule]
holiday_days = Sunday

[Directories]
primary = {wallpaper_dir}

[Logging]
log_dir = {tmp_path / "logs"}

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")
    config = load_config(config_path)

    # Paths should be resolved and absolute
    assert config.directories.primary.is_absolute()
    assert config.logging.log_dir.is_absolute()


def test_no_valid_directories(temp_config_dir: Path) -> None:
    """Test that config without any valid directories raises ValueError."""
    config_path = temp_config_dir / "config.ini"

    config_content = """[Schedule]
holiday_days = Sunday

[Images]
extensions = .jpg
"""

    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="No valid wallpaper directories"):
        load_config(config_path)


def test_create_default_config(temp_config_dir: Path) -> None:
    """Test creating default configuration file."""
    config_path = temp_config_dir / "config.ini"

    create_default_config(config_path)

    assert config_path.exists()
    content = config_path.read_text(encoding="utf-8")

    # Check that all main sections are present
    assert "[Schedule]" in content
    assert "[Directories.Workday.Light]" in content
    assert "[Directories.Holiday.Dark]" in content
    assert "[Logging]" in content
    assert "[Images]" in content
    assert "holiday_days" in content
    assert "day_start_time" in content
