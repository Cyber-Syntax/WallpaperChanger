#!/usr/bin/env python3
"""State persistence for wallpaper rotation.

Manages round-robin position and wallpaper history using JSON storage.

Example:
    >>> from src.state import load, save, next_wallpaper
    >>> state_data = load(Path("~/.local/share/wallpaperchanger/state.json"))
    >>> wallpaper = next_wallpaper(directory, extensions, state_data, [])

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


def load(state_file: Path) -> StateDict:
    """Load state from JSON file with corruption recovery.

    Returns default state if file doesn't exist or is corrupted.

    Args:
        state_file: Path to state JSON file

    Returns:
        State dictionary (never None)

    """
    if not state_file.exists():
        logging.info("State file not found, will create new: %s", state_file)
        return _initialize()

    try:
        state_data = state_file.read_text(encoding="utf-8")
        state = json.loads(state_data)

        if not _validate(state):
            raise ValueError("Invalid state schema")

        # Check for version mismatch
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
        _backup_corrupted(state_file)

        return _initialize()

    except PermissionError as e:
        logging.error("Permission denied reading state file: %s", e)
        return _initialize()


def save(state_file: Path, state: StateDict) -> bool:
    """Save state to JSON file atomically with file locking.

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


def next_wallpaper(
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


def update(
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


# =============================================================================
# Private Helper Functions
# =============================================================================


def _initialize() -> StateDict:
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


def _validate(state: StateDict) -> bool:
    """Validate state structure and required fields.

    Args:
        state: State dictionary to validate

    Returns:
        True if state is valid, False otherwise

    """
    # Check required fields and types
    if not _validate_basic_structure(state):
        return False

    # Validate round_robin entries
    return _validate_round_robin(state["round_robin"])


def _validate_basic_structure(state: StateDict) -> bool:
    """Validate basic state structure and field types."""
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

    return True


def _validate_round_robin(round_robin: dict[str, Any]) -> bool:
    """Validate round_robin entries."""
    for directory, rr_state in round_robin.items():
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


def _backup_corrupted(state_file: Path) -> None:
    """Backup corrupted state file with timestamp.

    Args:
        state_file: Path to corrupted state file

    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = state_file.with_suffix(f".corrupted.{timestamp}")
    try:
        state_file.rename(backup_path)
        logging.info("Backed up corrupted state to: %s", backup_path)
    except OSError as backup_error:
        logging.error("Failed to backup corrupted state: %s", backup_error)
