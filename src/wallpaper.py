#!/usr/bin/env python3
"""Automatically sets wallpapers based on configuration.

This script selects wallpapers from designated directories depending on:
- Day of the week (workday vs configured holidays)
- Time of day (light/dark themes)
- Number of connected monitors
- Current display server (X11 or Wayland/Sway)

Wallpapers are set using appropriate tools (feh for X11, swaybg for Sway
on Wayland).

Features:
- Configurable holidays (not just Sunday)
- Time-based wallpaper selection (day/night)
- Work vs Holiday wallpaper distinction
- Multi-monitor support with alternating wallpaper directories
- Logging with rotation for troubleshooting
- Display server detection (X11/Wayland)

Example:
    >>> from wallpaper_changer import wallpaper
    >>> wallpaper.main()

"""

import datetime
import json
import logging
import os
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config_loader import Config, create_default_config, load_config
from src.state_manager import (
    StateDict,
    cleanup_old_entries,
    get_next_wallpaper,
    initialize_state,
    load_state,
    save_state,
    update_state,
)


def configure_logging(config: Config) -> None:
    """Configure rotating logs with timestamps and severity levels.

    Args:
        config: Application configuration with logging settings

    """
    log_dir = config.logging.log_dir
    log_file = log_dir / "main.log"

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(config.logging.log_level)

    # Clear any existing handlers
    logger.handlers.clear()

    handler = RotatingFileHandler(
        str(log_file),
        maxBytes=config.logging.max_size_mb * 1024 * 1024,
        backupCount=config.logging.backup_count,
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def detect_display_server() -> str:
    """Detect the current display server environment.

    Returns:
        Current display server: 'x11', 'wayland', or 'unknown'

    """
    server = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
    logging.info("Detected display server: %s", server)
    return server


def get_x11_monitors() -> list[str]:
    """Get connected monitor names using xrandr (X11 only).

    Returns:
        List of connected monitor names

    """
    try:
        result = subprocess.run(
            ["xrandr", "--listmonitors"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [
            line.split()[-1]
            for line in result.stdout.splitlines()
            if "Monitors:" not in line
        ]
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr if e.stderr else "Unknown error"
        logging.error("xrandr failed: %s", stderr_msg)
        return []


def get_sway_monitors() -> list[str]:
    """Get active monitor names using swaymsg (Sway/Wayland only).

    Returns:
        List of active monitor names

    """
    try:
        result = subprocess.run(
            ["swaymsg", "-t", "get_outputs"],
            capture_output=True,
            text=True,
            check=True,
        )
        outputs: list[dict[str, object]] = json.loads(result.stdout)
        return [
            str(o["name"])
            for o in outputs
            if isinstance(o.get("active"), bool) and o["active"]
        ]
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error("swaymsg failed: %s", e)
        return []


def set_x11_wallpaper(image_paths: list[Path]) -> None:
    """Set wallpapers for all monitors using feh.

    Args:
        image_paths: Ordered list of wallpaper paths per monitor

    """
    try:
        _ = subprocess.run(
            ["feh", "--bg-fill"] + [str(p) for p in image_paths], check=True
        )
        logging.info("Set X11 wallpapers: %s", image_paths)
    except subprocess.CalledProcessError as e:
        logging.error("feh failed: %s", e)


def set_sway_wallpaper(image_paths: list[Path], monitors: list[str]) -> None:
    """Set wallpapers for all monitors using swaybg.

    Args:
        image_paths: Ordered list of wallpaper paths per monitor
        monitors: Monitor names from swaymsg

    """
    try:
        # Clean up existing swaybg processes
        _ = subprocess.run(["pkill", "swaybg"], check=False)

        # Launch new instances for each monitor
        for monitor, image in zip(monitors, image_paths, strict=False):
            _ = subprocess.Popen(
                ["swaybg", "-o", monitor, "-i", str(image), "-m", "fill"]
            )
        mapping = dict(zip(monitors, image_paths, strict=False))
        logging.info("Set Sway wallpapers: %s", mapping)
    except Exception as e:
        logging.error("swaybg failed: %s", e)


def select_wallpapers(
    config: Config,
    monitor_count: int,
    is_holiday: bool,
    is_daytime: bool,
    state: StateDict | None = None,
) -> list[Path]:
    """Select appropriate wallpapers based on configuration and context.

    Args:
        config: Application configuration
        monitor_count: Number of monitors detected
        is_holiday: Whether today is a configured holiday
        is_daytime: Whether current time is during day hours
        state: Optional state dictionary for round-robin selection

    Returns:
        List of wallpaper paths for each monitor

    """
    # Get appropriate directories based on context
    try:
        wallpaper_dirs = config.get_wallpaper_dirs(is_holiday, is_daytime)
    except ValueError as e:
        logging.error("Failed to get wallpaper directories: %s", e)
        return []

    # Track used images to avoid duplicates on multiple monitors
    used_images: list[str] = []
    wallpaper_paths: list[Path] = []

    # Select wallpapers for each monitor
    for idx in range(monitor_count):
        # Alternate between primary and left directories if both available
        if "left" in wallpaper_dirs and idx % 2 == 1:
            directory = wallpaper_dirs["left"]
        else:
            directory = wallpaper_dirs["primary"]

        # Use get_next_wallpaper for both random and round-robin selection
        path = get_next_wallpaper(
            directory,
            config.image_extensions,
            state,
            used_images,
        )

        if path:
            wallpaper_paths.append(path)
        else:
            logging.error("Failed to select wallpaper from %s", directory)

    return wallpaper_paths


def main() -> None:
    """Run main execution flow to set wallpapers based on configuration."""
    config_path = Path.home() / ".config" / "wallpaperchanger" / "config.ini"

    # Auto-create default config on first run
    if not config_path.exists():
        print(
            "⚠️  Configuration file not found. "
            "Creating default configuration...",
            file=sys.stderr,
        )
        try:
            create_default_config(config_path)
            print(
                f"✅ Created default configuration at: {config_path}",
                file=sys.stderr,
            )
            print(
                "\n⚠️  IMPORTANT: Please edit the configuration file to "
                "set your wallpaper directories!",
                file=sys.stderr,
            )
            print(f"   Edit: {config_path}", file=sys.stderr)
            print(
                "\nThe default configuration is set for a specific user "
                "setup.",
                file=sys.stderr,
            )
            print(
                "You MUST update the paths to match your system to avoid "
                "errors.\n",
                file=sys.stderr,
            )
            print(
                "After editing the config, run the script again:",
                file=sys.stderr,
            )
            print("  python -m src.wallpaper", file=sys.stderr)
            sys.exit(0)
        except Exception as e:
            print(f"❌ Failed to create default config: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        # Load configuration
        config = load_config(config_path)
    except ValueError as e:
        error_msg = f"Configuration error: {e}"
        print(error_msg, file=sys.stderr)
        print(
            f"\nPlease check your configuration file: {config_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error loading configuration: {e}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Set up logging
    configure_logging(config)
    logging.info("=== Starting wallpaper rotation ===")

    # Load state (if state tracking enabled)
    state = None
    if config.state_tracking.enabled:
        logging.info("State tracking enabled")
        state = load_state(config.state_tracking.state_file)
        if state is None:
            logging.info("Initializing new state file")
            state = initialize_state()

    # Determine current context
    now = datetime.datetime.now()
    weekday = now.weekday()
    current_time = now.time()

    is_holiday = config.is_holiday(weekday)
    is_daytime = config.is_daytime(current_time)

    logging.info(
        "Context: %s, %s, Time: %s",
        "Holiday" if is_holiday else "Workday",
        "Day" if is_daytime else "Night",
        current_time.strftime("%H:%M"),
    )

    # Detect display server and monitors
    display_server = detect_display_server()

    if display_server == "wayland":
        monitors = get_sway_monitors()
    else:
        monitors = get_x11_monitors()

    monitor_count = len(monitors)
    logging.info("Active monitors (%d): %s", monitor_count, monitors)

    if monitor_count == 0:
        logging.error("No monitors detected!")
        return

    # Select appropriate wallpapers
    wallpaper_paths = select_wallpapers(
        config, monitor_count, is_holiday, is_daytime, state
    )

    # Validate selections
    if len(wallpaper_paths) != monitor_count:
        logging.error(
            "Selected %d wallpapers for %d monitors!",
            len(wallpaper_paths),
            monitor_count,
        )
        return

    # Update state before setting wallpapers (if state tracking enabled)
    if state is not None:
        update_state(
            state,
            wallpaper_paths,
            monitors,
        )

        # Auto-cleanup if enabled
        if config.state_tracking.auto_cleanup:
            cleanup_old_entries(state, max_age_days=30)

    # Apply wallpapers
    if display_server == "wayland":
        set_sway_wallpaper(wallpaper_paths, monitors)
    elif display_server == "x11":
        set_x11_wallpaper(wallpaper_paths)
    else:
        logging.error("Unsupported display server: %s", display_server)
        return

    # Save state after successful execution (if state tracking enabled)
    if state is not None:
        if save_state(config.state_tracking.state_file, state):
            logging.info("State saved successfully")
        else:
            logging.warning("Failed to save state, continuing anyway")


if __name__ == "__main__":
    main()
