#!/usr/bin/python3
"""Automatically sets wallpapers based on the day of the week and monitor setup.

This script selects wallpapers from designated directories depending on whether it's Sunday,
the number of connected monitors, and the current display server (X11 or Wayland/Sway).
Wallpapers are set using appropriate tools (feh for X11, swaybg for Sway on Wayland).

Features:
- Daily rotation with special wallpapers on Sundays
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
import random
import subprocess
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Configuration Constants - Update these paths as needed
WALLPAPER_DIRS: dict[str, str] = {
    "left": "/home/developer/Pictures/Wallpapers/Programmers/left_output/",
    "primary": "/home/developer/Pictures/Wallpapers/Programmers/primary_output/",
    "sunday": "/home/developer/Pictures/Wallpapers/Programmers/Sunday/",
}

# Logging Configuration - XDG Base Directory compliant
LOG_DIR: Path = Path.home() / ".local" / "share" / "wallpaperchanger" / "logs"
LOG_FILE: Path = LOG_DIR / "main.log"
LOG_MAX_SIZE: int = 1 * 1024 * 1024  # 1MB
LOG_BACKUP_COUNT: int = 3


def configure_logging() -> None:
    """Sets up rotating logs with timestamps and severity levels."""
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        str(LOG_FILE),
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT,
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_random_image(directory: str, used_images: list[str]) -> str | None:
    """Selects a random image from a directory, avoiding recently used images.

    Args:
        directory: Path to search for images
        used_images: Images to exclude from selection

    Returns:
        Full path to selected image or None if error

    """
    try:
        # Verify directory exists
        if not os.path.isdir(directory):
            logging.error("Missing wallpaper directory: %s", directory)
            return None

        # Get eligible images (case-insensitive check for image extensions)
        images = [
            f
            for f in os.listdir(directory)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
            and f not in used_images
            and os.path.isfile(os.path.join(directory, f))
        ]

        if not images:
            logging.warning("No unused images found in %s", directory)
            return None

        selection = random.choice(images)
        used_images.append(selection)
        logging.info("Selected %s from %s", selection, directory)
        return os.path.join(directory, selection)

    except Exception as e:
        logging.error("Image selection failed: %s", e)
        return None


def detect_display_server() -> str:
    """Identifies the current display server environment.

    Returns:
        Current display server: 'x11', 'wayland', or 'unknown'

    """
    server = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
    logging.info("Detected display server: %s", server)
    return server


def get_x11_monitors() -> list[str]:
    """Returns connected monitor names using xrandr (X11 only).

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
        logging.error("xrandr failed: %s", e.stderr)
        return []


def get_sway_monitors() -> list[str]:
    """Returns active monitor names using swaymsg (Sway/Wayland only).

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
        outputs = json.loads(result.stdout)
        return [o["name"] for o in outputs if o["active"]]
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error("swaymsg failed: %s", e)
        return []


def set_x11_wallpaper(image_paths: list[str]) -> None:
    """Sets wallpapers for all monitors using feh.

    Args:
        image_paths: Ordered list of wallpaper paths per monitor

    """
    try:
        subprocess.run(["feh", "--bg-fill"] + image_paths, check=True)
        logging.info("Set X11 wallpapers: %s", image_paths)
    except subprocess.CalledProcessError as e:
        logging.error("feh failed: %s", e)


def set_sway_wallpaper(image_paths: list[str], monitors: list[str]) -> None:
    """Sets wallpapers for all monitors using swaybg.

    Args:
        image_paths: Ordered list of wallpaper paths per monitor
        monitors: Monitor names from swaymsg

    """
    try:
        # Clean up existing swaybg processes
        subprocess.run(["pkill", "swaybg"], check=False)

        # Launch new instances for each monitor
        for monitor, image in zip(monitors, image_paths, strict=False):
            subprocess.Popen(
                ["swaybg", "-o", monitor, "-i", image, "-m", "fill"]
            )
        mapping = dict(zip(monitors, image_paths, strict=False))
        logging.info("Set Sway wallpapers: %s", mapping)
    except Exception as e:
        logging.error("swaybg failed: %s", e)


def main() -> None:
    """Main execution flow to set wallpapers based on current configuration."""
    configure_logging()
    logging.info("=== Starting wallpaper rotation ===")

    # Determine current context
    today = datetime.datetime.today()
    is_sunday = today.weekday() == 6  # Monday=0,...,Sunday=6
    display_server = detect_display_server()

    # Detect monitors
    if display_server == "wayland":
        monitors = get_sway_monitors()
    else:
        monitors = get_x11_monitors()

    monitor_count = len(monitors)
    logging.info("Active monitors (%d): %s", monitor_count, monitors)

    # Select appropriate wallpaper directory strategy
    used_images: list[str] = []
    wallpaper_paths: list[str] = []

    if is_sunday:
        # Sunday special case - same directory for all monitors
        for _ in range(monitor_count):
            path = get_random_image(WALLPAPER_DIRS["sunday"], used_images)
            if path:
                wallpaper_paths.append(path)
    elif monitor_count == 1:
        # Single monitor - use primary directory
        path = get_random_image(WALLPAPER_DIRS["primary"], used_images)
        if path:
            wallpaper_paths.append(path)
    else:
        # Multi-monitor - alternate between primary and left directories
        for idx in range(monitor_count):
            directory = (
                WALLPAPER_DIRS["primary"]
                if idx % 2 == 0
                else WALLPAPER_DIRS["left"]
            )
            path = get_random_image(directory, used_images)
            if path:
                wallpaper_paths.append(path)

    # Validate selections
    if len(wallpaper_paths) != monitor_count:
        logging.error(
            "Selected %d wallpapers for %d monitors!",
            len(wallpaper_paths),
            monitor_count,
        )
        return

    # Apply wallpapers
    if display_server == "wayland":
        set_sway_wallpaper(wallpaper_paths, monitors)
    elif display_server == "x11":
        set_x11_wallpaper(wallpaper_paths)
    else:
        logging.error("Unsupported display server: %s", display_server)


if __name__ == "__main__":
    main()
