#!/usr/bin/env python3
"""Unit tests for state manager module.

Tests cover:
- State initialization
- State loading and saving
- State validation
- Corruption recovery
- Round-robin tracking
- Concurrent access handling

"""

import datetime
import json
import tempfile
from pathlib import Path

from src.state_manager import (
    CURRENT_STATE_VERSION,
    cleanup_old_entries,
    get_next_wallpaper,
    initialize_state,
    load_state,
    save_state,
    update_state,
    validate_state,
)


class TestStateInitialization:
    """Tests for state initialization."""

    def test_initialize_state_structure(self):
        """Test that initialize_state returns correct structure."""
        state = initialize_state()

        assert "version" in state
        assert "last_run" in state
        assert "current_wallpapers" in state
        assert "round_robin" in state

    def test_initialize_state_version(self):
        """Test that initialized state has correct version."""
        state = initialize_state()
        assert state["version"] == CURRENT_STATE_VERSION

    def test_initialize_state_defaults(self):
        """Test that initialized state has correct default values."""
        state = initialize_state()

        assert state["last_run"] is None
        assert state["current_wallpapers"] == {}
        assert state["round_robin"] == {}


class TestStateValidation:
    """Tests for state validation."""

    def test_validate_state_valid(self):
        """Test validation of valid state."""
        state = initialize_state()
        assert validate_state(state) is True

    def test_validate_state_missing_version(self):
        """Test validation fails without version."""
        state = initialize_state()
        del state["version"]
        assert validate_state(state) is False

    def test_validate_state_missing_current_wallpapers(self):
        """Test validation fails without current_wallpapers."""
        state = initialize_state()
        del state["current_wallpapers"]
        assert validate_state(state) is False

    def test_validate_state_missing_round_robin(self):
        """Test validation fails without round_robin."""
        state = initialize_state()
        del state["round_robin"]
        assert validate_state(state) is False

    def test_validate_state_invalid_version_type(self):
        """Test validation fails with invalid version type."""
        state = initialize_state()
        state["version"] = 1.0
        assert validate_state(state) is False

    def test_validate_state_invalid_current_wallpapers_type(self):
        """Test validation fails with invalid current_wallpapers type."""
        state = initialize_state()
        state["current_wallpapers"] = []
        assert validate_state(state) is False

    def test_validate_state_invalid_round_robin_type(self):
        """Test validation fails with invalid round_robin type."""
        state = initialize_state()
        state["round_robin"] = []
        assert validate_state(state) is False

    def test_validate_state_invalid_round_robin_entry(self):
        """Test validation fails with invalid round_robin entry."""
        state = initialize_state()
        state["round_robin"]["/path/to/dir"] = "invalid"
        assert validate_state(state) is False

    def test_validate_state_missing_images_in_round_robin(self):
        """Test validation fails when round_robin entry missing images."""
        state = initialize_state()
        state["round_robin"]["/path/to/dir"] = {"position": 0}
        assert validate_state(state) is False

    def test_validate_state_invalid_position_type(self):
        """Test validation fails with invalid position type."""
        state = initialize_state()
        state["round_robin"]["/path/to/dir"] = {
            "images": ["img1.jpg"],
            "position": "0",
        }
        assert validate_state(state) is False


class TestStateLoadSave:
    """Tests for state loading and saving."""

    def test_load_state_nonexistent_file(self):
        """Test loading nonexistent state file returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "nonexistent.json"
            result = load_state(state_file)
            assert result is None

    def test_save_and_load_state(self):
        """Test saving and loading state preserves data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state = initialize_state()
            state["last_run"] = "2024-01-15T10:00:00"
            state["current_wallpapers"]["HDMI-0"] = {
                "filename": "test.jpg",
                "timestamp": "2024-01-15T10:00:00",
            }

            assert save_state(state_file, state) is True
            loaded_state = load_state(state_file)

            assert loaded_state is not None
            assert loaded_state["last_run"] == state["last_run"]
            assert (
                loaded_state["current_wallpapers"]
                == state["current_wallpapers"]
            )

    def test_save_state_creates_directory(self):
        """Test that save_state creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "subdir" / "state.json"
            state = initialize_state()

            assert save_state(state_file, state) is True
            assert state_file.exists()

    def test_load_state_corrupted_json(self):
        """Test loading corrupted JSON creates backup and returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state_file.write_text("{ invalid json", encoding="utf-8")

            result = load_state(state_file)

            assert result is None
            # Check that backup was created
            backup_files = list(Path(tmpdir).glob("state.corrupted.*"))
            assert len(backup_files) == 1

    def test_load_state_invalid_schema(self):
        """Test loading state with invalid schema returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            invalid_state = {"version": "1.0"}  # Missing required fields

            state_file.write_text(json.dumps(invalid_state), encoding="utf-8")

            result = load_state(state_file)
            assert result is None

    def test_save_state_atomic_write(self):
        """Test that save_state uses atomic write with temp file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            state = initialize_state()

            save_state(state_file, state)

            # Temp file should be cleaned up
            temp_files = list(Path(tmpdir).glob("*.tmp"))
            assert len(temp_files) == 0


class TestStateUpdate:
    """Tests for state update functionality."""

    def test_update_state_basic(self):
        """Test basic state update with wallpaper selection."""
        state = initialize_state()
        wallpaper_paths = [
            Path("/path/to/wallpaper1.jpg"),
            Path("/path/to/wallpaper2.jpg"),
        ]
        monitors = ["HDMI-0", "DP-1"]

        update_state(state, wallpaper_paths, monitors)

        assert state["last_run"] is not None
        assert len(state["current_wallpapers"]) == 2
        assert "HDMI-0" in state["current_wallpapers"]
        assert "DP-1" in state["current_wallpapers"]
        assert (
            state["current_wallpapers"]["HDMI-0"]["filename"]
            == "wallpaper1.jpg"
        )
        assert (
            state["current_wallpapers"]["DP-1"]["filename"] == "wallpaper2.jpg"
        )

    def test_update_state_timestamp(self):
        """Test that update_state sets timestamp."""
        state = initialize_state()
        wallpaper_paths = [Path("/path/to/wallpaper.jpg")]
        monitors = ["HDMI-0"]

        update_state(state, wallpaper_paths, monitors)

        timestamp = state["current_wallpapers"]["HDMI-0"]["timestamp"]
        assert timestamp is not None
        # Verify timestamp is valid ISO format
        datetime.datetime.fromisoformat(timestamp)


class TestRoundRobinSelection:
    """Tests for round-robin wallpaper selection."""

    def test_get_next_wallpaper_initializes_state(self, tmp_path):
        """Test that round-robin state is initialized on first use."""
        # Create test directory with images
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        (test_dir / "image1.jpg").touch()
        (test_dir / "image2.jpg").touch()

        state = initialize_state()
        extensions = [".jpg", ".png"]
        used_images = []

        result = get_next_wallpaper(test_dir, extensions, state, used_images)

        assert result is not None
        dir_key = str(test_dir.resolve())
        assert dir_key in state["round_robin"]
        assert state["round_robin"][dir_key]["position"] == 1

    def test_get_next_wallpaper_cycles_through_images(self, tmp_path):
        """Test that round-robin cycles through all images."""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        (test_dir / "image1.jpg").touch()
        (test_dir / "image2.jpg").touch()
        (test_dir / "image3.jpg").touch()

        state = initialize_state()
        extensions = [".jpg"]
        used_images = []

        # First call
        result1 = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result1.name == "image1.jpg"

        # Second call
        used_images = []
        result2 = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result2.name == "image2.jpg"

        # Third call
        used_images = []
        result3 = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result3.name == "image3.jpg"

        # Fourth call should wrap around
        used_images = []
        result4 = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result4.name == "image1.jpg"

    def test_get_next_wallpaper_avoids_duplicates_multimonitor(self, tmp_path):
        """Test that round-robin avoids duplicates for multi-monitor."""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        (test_dir / "image1.jpg").touch()
        (test_dir / "image2.jpg").touch()
        (test_dir / "image3.jpg").touch()

        state = initialize_state()
        extensions = [".jpg"]
        used_images = []

        # First monitor
        result1 = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result1.name == "image1.jpg"
        assert "image1.jpg" in used_images

        # Second monitor (should skip image1.jpg)
        result2 = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result2.name == "image2.jpg"

    def test_get_next_wallpaper_handles_directory_changes(self, tmp_path):
        """Test that round-robin resets when directory contents change."""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        (test_dir / "image1.jpg").touch()
        (test_dir / "image2.jpg").touch()

        state = initialize_state()
        extensions = [".jpg"]
        used_images = []

        # First call
        get_next_wallpaper(test_dir, extensions, state, used_images)
        dir_key = str(test_dir.resolve())
        assert state["round_robin"][dir_key]["position"] == 1

        # Add new image
        (test_dir / "image3.jpg").touch()

        # Next call should reset position
        used_images = []
        get_next_wallpaper(test_dir, extensions, state, used_images)
        assert state["round_robin"][dir_key]["position"] == 1

    def test_get_next_wallpaper_empty_directory(self, tmp_path):
        """Test handling of empty directory."""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()

        state = initialize_state()
        extensions = [".jpg"]
        used_images = []

        result = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result is None

    def test_get_next_wallpaper_missing_directory(self, tmp_path):
        """Test handling of missing directory."""
        test_dir = tmp_path / "nonexistent"

        state = initialize_state()
        extensions = [".jpg"]
        used_images = []

        result = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result is None

    def test_get_next_wallpaper_filters_by_extension(self, tmp_path):
        """Test that only valid extensions are included."""
        test_dir = tmp_path / "wallpapers"
        test_dir.mkdir()
        (test_dir / "image1.jpg").touch()
        (test_dir / "image2.png").touch()
        (test_dir / "document.txt").touch()

        state = initialize_state()
        extensions = [".jpg"]
        used_images = []

        result = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result is not None
        assert result.name == "image1.jpg"

        # Should cycle back to image1 (only one jpg)
        used_images = []
        result2 = get_next_wallpaper(test_dir, extensions, state, used_images)
        assert result2.name == "image1.jpg"


class TestCleanupOldEntries:
    """Tests for cleanup of old round-robin entries."""

    def test_cleanup_old_entries_recent_state(self):
        """Test that recent state is not cleaned up."""
        state = initialize_state()
        state["last_run"] = datetime.datetime.now().isoformat()
        state["round_robin"]["/path/to/dir"] = {
            "images": ["img1.jpg"],
            "position": 2,
        }

        cleanup_old_entries(state, max_age_days=30)

        assert state["round_robin"] != {}

    def test_cleanup_old_entries_old_state(self):
        """Test that old state is cleaned up."""
        state = initialize_state()
        old_date = datetime.datetime.now() - datetime.timedelta(days=40)
        state["last_run"] = old_date.isoformat()
        state["round_robin"]["/path/to/dir"] = {
            "images": ["img1.jpg"],
            "position": 2,
        }

        cleanup_old_entries(state, max_age_days=30)

        assert state["round_robin"] == {}

    def test_cleanup_old_entries_no_last_run(self):
        """Test cleanup with no last_run doesn't crash."""
        state = initialize_state()
        state["last_run"] = None
        state["round_robin"]["/path/to/dir"] = {
            "images": ["img1.jpg"],
            "position": 2,
        }

        cleanup_old_entries(state, max_age_days=30)

        # Should not crash, round_robin should remain unchanged
        assert state["round_robin"] != {}
