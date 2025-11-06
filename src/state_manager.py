#!/usr/bin/env python3
"""State management for WallpaperChanger.

This module handles persistent state tracking for wallpaper selection,
focusing on round-robin cycling and current wallpaper tracking.

Features:
- Load/save state from JSON file
- Atomic writes with corruption recovery
- Round-robin position tracking per directory
- Current wallpaper tracking per monitor
- Concurrent access handling with file locking

Example:
    >>> from src.state_manager import load_state, save_state
    >>> state = load_state(Path("~/.local/share/wallpaperchanger/state.json"))
    >>> if state is None:
    ...     state = initialize_state()

"""

import contextlib
import datetime
import fcntl
import json
import logging
import random
from pathlib import Path
from typing import Any

# Type alias for state structure
StateDict = dict[str, Any]

CURRENT_STATE_VERSION = "1.0"


def initialize_state() -> StateDict:
    """Create default state structure.

    Returns:
        New state dictionary with default values

    """
    return {
        "version": CURRENT_STATE_VERSION,
        "last_run": None,
        "current_wallpapers": {},
        "round_robin": {},
    }


def validate_state(state: StateDict) -> bool:
    """Validate state structure and required fields.

    Args:
        state: State dictionary to validate

    Returns:
        True if state is valid, False otherwise

    """
    required_fields = ["version", "current_wallpapers", "round_robin"]

    # Check required fields exist
    for field in required_fields:
        if field not in state:
            logging.error("Missing required field in state: %s", field)
            return False

    # Validate field types
    if not isinstance(state["version"], str):
        logging.error("Invalid version field type")
        return False

    if not isinstance(state["current_wallpapers"], dict):
        logging.error("Invalid current_wallpapers type")
        return False

    if not isinstance(state["round_robin"], dict):
        logging.error("Invalid round_robin type")
        return False

    # Validate round_robin entries
    for directory, rr_state in state["round_robin"].items():
        if not isinstance(rr_state, dict):
            logging.error("Invalid round_robin entry for %s", directory)
            return False

        if "images" not in rr_state or "position" not in rr_state:
            logging.error(
                "Missing images or position in round_robin for %s", directory
            )
            return False

        if not isinstance(rr_state["images"], list) or not isinstance(
            rr_state["position"], int
        ):
            logging.error("Invalid types in round_robin for %s", directory)
            return False

    return True


def load_state(state_file: Path) -> StateDict | None:
    """Load state from JSON file with corruption recovery.

    Args:
        state_file: Path to state JSON file

    Returns:
        State dictionary or None if file doesn't exist or is corrupted

    """
    if not state_file.exists():
        logging.info("State file not found, will create new: %s", state_file)
        return None

    try:
        state_data = state_file.read_text(encoding="utf-8")
        state = json.loads(state_data)

        if not validate_state(state):
            raise ValueError("Invalid state schema")

        # Check for version mismatch and migrate if needed
        state_version = state.get("version", "1.0")
        if state_version != CURRENT_STATE_VERSION:
            logging.info(
                "State version %s matches current version %s",
                state_version,
                CURRENT_STATE_VERSION,
            )

        logging.info("Loaded state from %s", state_file)
        return state

    except (json.JSONDecodeError, ValueError) as e:
        logging.error("Corrupted state file: %s", e)

        # Backup corrupted file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = state_file.with_suffix(f".corrupted.{timestamp}")
        try:
            state_file.rename(backup_path)
            logging.info("Backed up corrupted state to: %s", backup_path)
        except OSError as backup_error:
            logging.error("Failed to backup corrupted state: %s", backup_error)

        return None

    except PermissionError as e:
        logging.error("Permission denied reading state file: %s", e)
        return None


def save_state(state_file: Path, state: StateDict) -> bool:
    """Save state to JSON file with atomic write and file locking.

    Uses temp file + rename for atomic operation and fcntl for locking.

    Args:
        state_file: Path to state JSON file
        state: State dictionary to save

    Returns:
        True if successful, False otherwise

    """
    # Ensure state directory exists
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.error("Failed to create state directory: %s", e)
        return False

    # Use temp file for atomic write
    temp_file = state_file.with_suffix(".tmp")

    try:
        # Write to temp file with lock
        with temp_file.open("w", encoding="utf-8") as f:
            # Try to acquire exclusive lock (non-blocking)
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                logging.warning(
                    "State file locked by another process, skipping update"
                )
                return False

            # Write state
            json.dump(state, f, indent=2, ensure_ascii=False)
            f.flush()

            # Release lock
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # Atomic rename
        temp_file.rename(state_file)
        logging.info("Saved state to %s", state_file)
        return True

    except (OSError, PermissionError) as e:
        logging.error("Failed to save state: %s", e)
        # Clean up temp file if it exists
        if temp_file.exists():
            with contextlib.suppress(OSError):
                temp_file.unlink()
        return False


def update_state(
    state: StateDict,
    wallpaper_paths: list[Path],
    monitors: list[str],
) -> None:
    """Update state with current wallpaper selection.

    Args:
        state: State dictionary to update
        wallpaper_paths: Selected wallpaper paths
        monitors: Monitor names

    """
    now = datetime.datetime.now()
    timestamp = now.isoformat()

    # Update last_run
    state["last_run"] = timestamp

    # Update current_wallpapers
    state["current_wallpapers"] = {}
    for monitor, path in zip(monitors, wallpaper_paths, strict=False):
        # Convert to Path if string
        path_obj = Path(path) if isinstance(path, str) else path
        state["current_wallpapers"][monitor] = {
            "filename": path_obj.name,
            "timestamp": timestamp,
        }


def get_next_wallpaper(
    directory: Path,
    extensions: list[str],
    state: StateDict | None,
    used_images: list[str],
) -> Path | None:
    """Get next wallpaper using round-robin or random selection.

    Args:
        directory: Directory to select from
        extensions: Valid image extensions
        state: Optional state dictionary with round_robin tracking.
               If None, uses random selection instead.
        used_images: Images already selected (for multi-monitor)

    Returns:
        Path to selected wallpaper or None if error

    """
    try:
        # Verify directory exists
        if not directory.is_dir():
            logging.error("Missing wallpaper directory: %s", directory)
            return None

        # Get all valid images (sorted for consistent ordering)
        all_images = sorted(
            [
                f.name
                for f in directory.iterdir()
                if f.is_file() and f.suffix.lower() in extensions
            ]
        )

        if not all_images:
            logging.error("No images found in %s", directory)
            return None

        # Use random selection if no state tracking
        if state is None:
            available = [img for img in all_images if img not in used_images]
            if not available:
                available = all_images

            selected = random.choice(available)
            used_images.append(selected)
            logging.info(
                "Random selection: %s from %s", selected, directory.name
            )
            return directory / selected

        # Round-robin selection with state tracking
        dir_key = str(directory.resolve())

        # Initialize round_robin state for this directory if needed
        if dir_key not in state["round_robin"]:
            state["round_robin"][dir_key] = {
                "images": all_images,
                "position": 0,
            }
            logging.info("Initialized round-robin for %s", directory.name)

        rr_state = state["round_robin"][dir_key]

        # Check if directory contents changed
        if rr_state["images"] != all_images:
            logging.info(
                "Directory contents changed for %s, resetting position",
                directory.name,
            )
            rr_state["images"] = all_images
            rr_state["position"] = 0

        # Get current position
        position = rr_state["position"]

        # Ensure position is valid
        if position >= len(all_images):
            position = 0
            rr_state["position"] = 0

        # Select image at current position
        selected = all_images[position]

        # Handle multi-monitor case: avoid duplicates if possible
        attempts = 0
        while selected in used_images and attempts < len(all_images):
            position = (position + 1) % len(all_images)
            selected = all_images[position]
            attempts += 1

        # Update position for next run
        rr_state["position"] = (position + 1) % len(all_images)

        # Track used image
        used_images.append(selected)

        logging.info(
            "Round-robin selection [%d/%d]: %s from %s",
            position + 1,
            len(all_images),
            selected,
            directory.name,
        )

        return directory / selected

    except Exception as e:
        logging.error("Image selection failed: %s", e)
        return None


def cleanup_old_entries(state: StateDict, max_age_days: int = 30) -> None:
    """Clean up round-robin entries for directories not used recently.

    Args:
        state: State dictionary to clean
        max_age_days: Maximum age in days for keeping entries

    """
    if not state.get("last_run"):
        return

    try:
        last_run = datetime.datetime.fromisoformat(state["last_run"])
        cutoff = datetime.datetime.now() - datetime.timedelta(
            days=max_age_days
        )

        if last_run < cutoff:
            logging.info(
                "State older than %d days, clearing round-robin", max_age_days
            )
            state["round_robin"] = {}

    except (ValueError, TypeError) as e:
        logging.debug("Could not parse last_run timestamp: %s", e)
