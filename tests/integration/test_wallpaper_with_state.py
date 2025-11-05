#!/usr/bin/env python3
"""Integration tests for wallpaper selection with state tracking.

Tests cover:
- State tracking with round-robin selection
- Multi-monitor support
- State persistence across runs
- Integration with select_wallpapers function

"""

import tempfile
from datetime import time
from pathlib import Path

from src.config_loader import (
    Config,
    DirectoryConfig,
    LoggingConfig,
    ScheduleConfig,
    StateTrackingConfig,
)
from src.state_manager import (
    get_next_wallpaper,
    initialize_state,
    load_state,
    save_state,
)
from src.wallpaper import select_wallpapers


class TestWallpaperWithStateTracking:
    """Integration tests for wallpaper selection with state tracking."""

    def test_select_wallpapers_with_state(self) -> None:
        """Test select_wallpapers function with state tracking enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallpaper_dir = Path(tmpdir) / "wallpapers"
            wallpaper_dir.mkdir()
            state_file = Path(tmpdir) / "state.json"

            # Create test images
            for i in range(5):
                (wallpaper_dir / f"image{i}.jpg").touch()

            # Create config
            config = Config(
                directories=DirectoryConfig(
                    workday_light_primary=wallpaper_dir,
                    workday_dark_primary=wallpaper_dir,
                    holiday_light_primary=wallpaper_dir,
                    holiday_dark_primary=wallpaper_dir,
                ),
                logging=LoggingConfig(
                    log_dir=Path(tmpdir) / "logs",
                    log_level="INFO",
                    max_size_mb=10,
                    backup_count=3,
                ),
                schedule=ScheduleConfig(
                    holiday_days=[6],
                    day_start_time=time(8, 0),
                    night_start_time=time(18, 0),
                ),
                image_extensions=[".jpg"],
                state_tracking=StateTrackingConfig(
                    enabled=True,
                    state_file=state_file,
                    auto_cleanup=True,
                ),
            )

            # Initialize state
            state = initialize_state()

            # Select wallpapers for 2 monitors
            wallpaper_paths = select_wallpapers(
                config,
                monitor_count=2,
                is_holiday=False,
                is_daytime=True,
                state=state,
            )

            assert len(wallpaper_paths) == 2
            assert all(p.exists() for p in wallpaper_paths)

            # Update state with selections (this sets last_run)
            from src.state_manager import update_state

            update_state(
                state,
                wallpaper_paths,
                ["HDMI-0", "DP-1"],
            )

            # Save state
            save_state(state_file, state)

            # Load state and verify
            loaded_state = load_state(state_file)
            assert loaded_state is not None
            assert loaded_state["last_run"] is not None

    def test_round_robin_across_runs(self) -> None:
        """Test that round-robin state persists across runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallpaper_dir = Path(tmpdir) / "wallpapers"
            wallpaper_dir.mkdir()
            state_file = Path(tmpdir) / "state.json"

            # Create 3 test images
            (wallpaper_dir / "image1.jpg").touch()
            (wallpaper_dir / "image2.jpg").touch()
            (wallpaper_dir / "image3.jpg").touch()

            extensions = [".jpg"]

            # First run
            state = initialize_state()
            used_images: list[str] = []
            path1 = get_next_wallpaper(
                wallpaper_dir, extensions, state, used_images
            )
            assert path1.name == "image1.jpg"
            save_state(state_file, state)

            # Second run (load state)
            state = load_state(state_file)
            assert state is not None
            used_images = []
            path2 = get_next_wallpaper(
                wallpaper_dir, extensions, state, used_images
            )
            assert path2.name == "image2.jpg"
            save_state(state_file, state)

            # Third run
            state = load_state(state_file)
            assert state is not None
            used_images = []
            path3 = get_next_wallpaper(
                wallpaper_dir, extensions, state, used_images
            )
            assert path3.name == "image3.jpg"
            save_state(state_file, state)

            # Fourth run should wrap around
            state = load_state(state_file)
            assert state is not None
            used_images = []
            path4 = get_next_wallpaper(
                wallpaper_dir, extensions, state, used_images
            )
            assert path4.name == "image1.jpg"

    def test_select_wallpapers_without_state(self) -> None:
        """Test select_wallpapers falls back to random without state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallpaper_dir = Path(tmpdir) / "wallpapers"
            wallpaper_dir.mkdir()

            # Create test images
            for i in range(5):
                (wallpaper_dir / f"image{i}.jpg").touch()

            # Create config with state tracking disabled
            config = Config(
                directories=DirectoryConfig(
                    workday_light_primary=wallpaper_dir,
                    workday_dark_primary=wallpaper_dir,
                    holiday_light_primary=wallpaper_dir,
                    holiday_dark_primary=wallpaper_dir,
                ),
                logging=LoggingConfig(
                    log_dir=Path(tmpdir) / "logs",
                    log_level="INFO",
                    max_size_mb=10,
                    backup_count=3,
                ),
                schedule=ScheduleConfig(
                    holiday_days=[6],
                    day_start_time=time(8, 0),
                    night_start_time=time(18, 0),
                ),
                image_extensions=[".jpg"],
                state_tracking=StateTrackingConfig(
                    enabled=False,
                    state_file=Path(tmpdir) / "state.json",
                    auto_cleanup=True,
                ),
            )

            # Select without state
            wallpaper_paths = select_wallpapers(
                config,
                monitor_count=1,
                is_holiday=False,
                is_daytime=True,
                state=None,
            )

            assert len(wallpaper_paths) == 1
            assert wallpaper_paths[0].exists()

    def test_multi_monitor_with_state(self) -> None:
        """Test multi-monitor selection with state tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            primary_dir = Path(tmpdir) / "primary"
            left_dir = Path(tmpdir) / "left"
            primary_dir.mkdir()
            left_dir.mkdir()
            state_file = Path(tmpdir) / "state.json"

            # Create test images in both directories
            for i in range(3):
                (primary_dir / f"primary{i}.jpg").touch()
                (left_dir / f"left{i}.jpg").touch()

            # Create config
            config = Config(
                directories=DirectoryConfig(
                    workday_light_primary=primary_dir,
                    workday_dark_primary=primary_dir,
                    workday_light_left=left_dir,
                    workday_dark_left=left_dir,
                    holiday_light_primary=primary_dir,
                    holiday_dark_primary=primary_dir,
                ),
                logging=LoggingConfig(
                    log_dir=Path(tmpdir) / "logs",
                    log_level="INFO",
                    max_size_mb=10,
                    backup_count=3,
                ),
                schedule=ScheduleConfig(
                    holiday_days=[6],
                    day_start_time=time(8, 0),
                    night_start_time=time(18, 0),
                ),
                image_extensions=[".jpg"],
                state_tracking=StateTrackingConfig(
                    enabled=True,
                    state_file=state_file,
                    auto_cleanup=True,
                ),
            )

            # Initialize state
            state = initialize_state()

            # Select for 2 monitors
            wallpaper_paths = select_wallpapers(
                config,
                monitor_count=2,
                is_holiday=False,
                is_daytime=True,
                state=state,
            )

            assert len(wallpaper_paths) == 2
            assert wallpaper_paths[0].parent == primary_dir
            assert wallpaper_paths[1].parent == left_dir

    def test_state_persistence_with_directory_changes(self) -> None:
        """Test that state handles directory content changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallpaper_dir = Path(tmpdir) / "wallpapers"
            wallpaper_dir.mkdir()
            state_file = Path(tmpdir) / "state.json"

            # Start with 2 images
            (wallpaper_dir / "image1.jpg").touch()
            (wallpaper_dir / "image2.jpg").touch()

            state = initialize_state()
            extensions = [".jpg"]

            # First selection
            used_images: list[str] = []
            path1 = get_next_wallpaper(
                wallpaper_dir, extensions, state, used_images
            )
            assert path1.name == "image1.jpg"

            # Add new image
            (wallpaper_dir / "image3.jpg").touch()

            # Next selection should detect change and reset
            used_images = []
            path2 = get_next_wallpaper(
                wallpaper_dir, extensions, state, used_images
            )
            # Position should reset due to directory change
            assert path2.name == "image1.jpg"
