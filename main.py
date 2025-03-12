#!/usr/bin/python3
"""
Automatically sets wallpapers based on the day of the week and monitor setup.

This script selects wallpapers from designated directories depending on whether it's Sunday,
the number of connected monitors, and the current display server (X11 or Wayland/Sway).
Wallpapers are set using appropriate tools (feh for X11, swaybg for Sway on Wayland).

Features:
- Daily rotation with special wallpapers on Sundays
- Multi-monitor support with alternating wallpaper directories
- Logging with rotation for troubleshooting
- Display server detection (X11/Wayland)
"""

import os
import datetime
import random
import subprocess
import logging
import json
from logging.handlers import RotatingFileHandler

# Configuration Constants - Update these paths as needed
WALLPAPER_DIRS = {
    "left": "/home/developer/Pictures/Wallpapers/Programmers/left_output/",
    "primary": "/home/developer/Pictures/Wallpapers/Programmers/primary_output/",
    "sunday": "/home/developer/Pictures/Wallpapers/Programmers/Sunday/"
}

# Logging Configuration
LOG_FILE = os.path.join(os.path.dirname(__file__), "wallpaper.log")
LOG_MAX_SIZE = 1 * 1024 * 1024  # 1MB
LOG_BACKUP_COUNT = 3

def configure_logging():
    """Sets up rotating logs with timestamps and severity levels."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT,
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_random_image(directory, used_images):
    """
    Selects a random image from a directory, avoiding recently used images.
    
    Args:
        directory (str): Path to search for images
        used_images (list): Images to exclude from selection
    
    Returns:
        str: Full path to selected image or None if error
    """
    try:
        # Verify directory exists
        if not os.path.isdir(directory):
            logging.error(f"Missing wallpaper directory: {directory}")
            return None

        # Get eligible images (case-insensitive check for image extensions)
        images = [
            f for f in os.listdir(directory)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
            and f not in used_images
            and os.path.isfile(os.path.join(directory, f))
        ]

        if not images:
            logging.warning(f"No unused images found in {directory}")
            return None

        selection = random.choice(images)
        used_images.append(selection)
        logging.info(f"Selected {selection} from {directory}")
        return os.path.join(directory, selection)

    except Exception as e:
        logging.error(f"Image selection failed: {str(e)}")
        return None

def detect_display_server():
    """
    Identifies the current display server environment.
    
    Returns:
        str: 'x11', 'wayland', or 'unknown'
    """
    server = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
    logging.info(f"Detected display server: {server}")
    return server

def get_x11_monitors():
    """Returns connected monitor names using xrandr (X11 only)."""
    try:
        result = subprocess.run(
            ["xrandr", "--listmonitors"],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.split()[-1] for line in result.stdout.splitlines() if "Monitors:" not in line]
    except subprocess.CalledProcessError as e:
        logging.error(f"xrandr failed: {e.stderr}")
        return []

def get_sway_monitors():
    """Returns active monitor names using swaymsg (Sway/Wayland only)."""
    try:
        result = subprocess.run(
            ["swaymsg", "-t", "get_outputs"],
            capture_output=True,
            text=True,
            check=True
        )
        outputs = json.loads(result.stdout)
        return [o["name"] for o in outputs if o["active"]]
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"swaymsg failed: {str(e)}")
        return []

def set_x11_wallpaper(image_paths):
    """
    Sets wallpapers for all monitors using feh.
    
    Args:
        image_paths (list): Ordered list of wallpaper paths per monitor
    """
    try:
        subprocess.run(["feh", "--bg-fill"] + image_paths, check=True)
        logging.info(f"Set X11 wallpapers: {image_paths}")
    except subprocess.CalledProcessError as e:
        logging.error(f"feh failed: {e}")

def set_sway_wallpaper(image_paths, monitors):
    """
    Sets wallpapers for all monitors using swaybg.
    
    Args:
        image_paths (list): Ordered list of wallpaper paths per monitor
        monitors (list): Monitor names from swaymsg
    """
    try:
        # Clean up existing swaybg processes
        subprocess.run(["pkill", "swaybg"], check=False)
        
        # Launch new instances for each monitor
        for monitor, image in zip(monitors, image_paths):
            subprocess.Popen([
                "swaybg",
                "-o", monitor,
                "-i", image,
                "-m", "fill"
            ])
        logging.info(f"Set Sway wallpapers: {dict(zip(monitors, image_paths))}")
    except Exception as e:
        logging.error(f"swaybg failed: {e}")

def main():
    """Main execution flow."""
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
    logging.info(f"Active monitors ({monitor_count}): {monitors}")

    # Select appropriate wallpaper directory strategy
    used_images = []
    wallpaper_paths = []

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
            directory = WALLPAPER_DIRS["primary"] if idx % 2 == 0 else WALLPAPER_DIRS["left"]
            path = get_random_image(directory, used_images)
            if path:
                wallpaper_paths.append(path)

    # Validate selections
    if len(wallpaper_paths) != monitor_count:
        logging.error(f"Selected {len(wallpaper_paths)} wallpapers for {monitor_count} monitors!")
        return

    # Apply wallpapers
    if display_server == "wayland":
        set_sway_wallpaper(wallpaper_paths, monitors)
    elif display_server == "x11":
        set_x11_wallpaper(wallpaper_paths)
    else:
        logging.error(f"Unsupported display server: {display_server}")

if __name__ == "__main__":
    main()
