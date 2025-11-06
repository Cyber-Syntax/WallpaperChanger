#!/usr/bin/env python3
"""Core wallpaper selection and setting logic.

This module handles wallpaper selection from designated directories based on:
- Day of the week (workday vs configured holidays)
- Time of day (light/dark themes)
- Number of connected monitors
- Current display server (X11 or Wayland/Sway)

Wallpapers are set using appropriate tools (feh for X11, swaybg for Sway
on Wayland).

Example:
    >>> from src import wallpaper, config
    >>> cfg = config.load()
    >>> server = wallpaper.detect_display_server()
    >>> monitors = wallpaper.get_x11_monitors()
    >>> paths = wallpaper.select_wallpapers(cfg, 2, False, True)
    >>> wallpaper.set_x11_wallpaper(paths)

"""

import json
import logging
import os
import subprocess
from pathlib import Path

from src import config, state


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
    cfg: config.Config,
    monitor_count: int,
    is_holiday: bool,
    is_daytime: bool,
    state_data: state.StateDict | None = None,
) -> list[Path]:
    """Select appropriate wallpapers based on configuration and context.

    Args:
        cfg: Application configuration
        monitor_count: Number of monitors detected
        is_holiday: Whether today is a configured holiday
        is_daytime: Whether current time is during day hours
        state_data: Optional state dictionary for round-robin selection

    Returns:
        List of wallpaper paths for each monitor

    """
    # Get appropriate directories based on context
    try:
        wallpaper_dirs = cfg.get_wallpaper_dirs(is_holiday, is_daytime)
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

        # Use state.next_wallpaper for both random and round-robin selection
        path = state.next_wallpaper(
            directory,
            cfg.image_extensions,
            state_data,
            used_images,
        )

        if path:
            wallpaper_paths.append(path)
        else:
            logging.error("Failed to select wallpaper from %s", directory)

    return wallpaper_paths
