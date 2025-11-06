#!/usr/bin/env python3
"""Unit tests for wallpaper module.

Tests cover:
- Display server detection (X11/Wayland)
- Monitor detection (xrandr/swaymsg)
- Wallpaper setting (feh/swaybg)
- Wallpaper selection logic

"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from src import wallpaper
from src.config import (
    Config,
    DirectoryConfig,
    LoggingConfig,
    ScheduleConfig,
    StateTrackingConfig,
)
from src.state import _initialize as initialize_state


class TestDisplayDetection:
    """Tests for display server and monitor detection functionality."""

    def test_detect_display_server_x11(
        self, mock_x11_environment: None
    ) -> None:
        """Test detection of X11 display server.

        Args:
            mock_x11_environment: Fixture that mocks X11 environment

        """
        with patch("logging.info") as mock_log:
            result = wallpaper.detect_display_server()
            assert result == "x11"
            mock_log.assert_called_once()

    def test_detect_display_server_wayland(
        self, mock_wayland_environment: None
    ) -> None:
        """Test detection of Wayland display server.

        Args:
            mock_wayland_environment: Fixture that mocks Wayland environment

        """
        with patch("logging.info") as mock_log:
            result = wallpaper.detect_display_server()
            assert result == "wayland"
            mock_log.assert_called_once()

    def test_detect_display_server_unknown(self) -> None:
        """Test detection of unknown display server."""
        with patch.dict("os.environ", clear=True):
            with patch("logging.info") as mock_log:
                result = wallpaper.detect_display_server()
                assert result == "unknown"
                mock_log.assert_called_once()

    def test_get_x11_monitors_success(self, mock_xrandr_output: str) -> None:
        """Test successful detection of X11 monitors.

        Args:
            mock_xrandr_output: Fixture that provides mock xrandr output

        """
        mock_process = MagicMock()
        mock_process.stdout = mock_xrandr_output

        with patch("subprocess.run", return_value=mock_process) as mock_run:
            result = wallpaper.get_x11_monitors()

            mock_run.assert_called_once_with(
                ["xrandr", "--listmonitors"],
                capture_output=True,
                text=True,
                check=True,
            )

            assert result == ["DP-1", "HDMI-1"]

    def test_get_x11_monitors_failure(self) -> None:
        """Test handling of xrandr command failure."""
        error = subprocess.CalledProcessError(
            1, "xrandr", stderr="Command failed"
        )

        with patch("subprocess.run", side_effect=error) as mock_run:
            with patch("logging.error") as mock_log:
                result = wallpaper.get_x11_monitors()

                assert result == []
                mock_run.assert_called_once()
                mock_log.assert_called_once()

    def test_get_sway_monitors_success(
        self, mock_sway_outputs_json: str
    ) -> None:
        """Test successful detection of Sway monitors.

        Args:
            mock_sway_outputs_json: Fixture with mock swaymsg JSON output

        """
        mock_process = MagicMock()
        mock_process.stdout = mock_sway_outputs_json

        with patch("subprocess.run", return_value=mock_process) as mock_run:
            result = wallpaper.get_sway_monitors()

            mock_run.assert_called_once_with(
                ["swaymsg", "-t", "get_outputs"],
                capture_output=True,
                text=True,
                check=True,
            )

            assert result == ["eDP-1", "HDMI-A-1"]

    def test_get_sway_monitors_subprocess_failure(self) -> None:
        """Test handling of swaymsg command failure."""
        error = subprocess.CalledProcessError(
            1, "swaymsg", stderr="Command failed"
        )

        with patch("subprocess.run", side_effect=error) as mock_run:
            with patch("logging.error") as mock_log:
                result = wallpaper.get_sway_monitors()

                assert result == []
                mock_run.assert_called_once()
                mock_log.assert_called_once()

    def test_get_sway_monitors_json_failure(self) -> None:
        """Test handling of invalid JSON from swaymsg command."""
        mock_process = MagicMock()
        mock_process.stdout = "{invalid json"

        with patch("subprocess.run", return_value=mock_process) as mock_run:
            with patch("logging.error") as mock_log:
                result = wallpaper.get_sway_monitors()

                assert result == []
                mock_run.assert_called_once()
                mock_log.assert_called_once()


class TestWallpaperSetting:
    """Tests for setting wallpapers on different display servers."""

    def test_set_x11_wallpaper_success(self) -> None:
        """Test successful setting of X11 wallpapers."""
        wallpaper_paths = [
            Path("/path/to/img1.jpg"),
            Path("/path/to/img2.jpg"),
        ]

        with patch("subprocess.run") as mock_run:
            with patch("logging.info") as mock_log:
                wallpaper.set_x11_wallpaper(wallpaper_paths)

                mock_run.assert_called_once_with(
                    [
                        "feh",
                        "--bg-fill",
                        "/path/to/img1.jpg",
                        "/path/to/img2.jpg",
                    ],
                    check=True,
                )
                mock_log.assert_called_once()

    def test_set_x11_wallpaper_failure(self) -> None:
        """Test handling of feh command failure."""
        wallpaper_paths = [
            Path("/path/to/img1.jpg"),
            Path("/path/to/img2.jpg"),
        ]
        error = subprocess.CalledProcessError(1, "feh")

        with patch("subprocess.run", side_effect=error) as mock_run:
            with patch("logging.error") as mock_log:
                wallpaper.set_x11_wallpaper(wallpaper_paths)

                mock_run.assert_called_once()
                mock_log.assert_called_once()

    def test_set_sway_wallpaper_success(self) -> None:
        """Test successful setting of Sway wallpapers."""
        wallpaper_paths = [
            Path("/path/to/img1.jpg"),
            Path("/path/to/img2.jpg"),
        ]
        monitors = ["eDP-1", "HDMI-A-1"]

        with patch("subprocess.run") as mock_run:
            with patch("subprocess.Popen") as mock_popen:
                with patch("logging.info") as mock_log:
                    wallpaper.set_sway_wallpaper(wallpaper_paths, monitors)

                    # Check that pkill was called to clean up processes
                    mock_run.assert_called_once_with(
                        ["pkill", "swaybg"], check=False
                    )

                    # Check that swaybg was launched for each monitor
                    assert mock_popen.call_count == 2
                    mock_popen.assert_has_calls(
                        [
                            call(
                                [
                                    "swaybg",
                                    "-o",
                                    "eDP-1",
                                    "-i",
                                    "/path/to/img1.jpg",
                                    "-m",
                                    "fill",
                                ]
                            ),
                            call(
                                [
                                    "swaybg",
                                    "-o",
                                    "HDMI-A-1",
                                    "-i",
                                    "/path/to/img2.jpg",
                                    "-m",
                                    "fill",
                                ]
                            ),
                        ]
                    )
                    mock_log.assert_called_once()

    def test_set_sway_wallpaper_failure(self) -> None:
        """Test handling of swaybg command failure."""
        wallpaper_paths = [
            Path("/path/to/img1.jpg"),
            Path("/path/to/img2.jpg"),
        ]
        monitors = ["eDP-1", "HDMI-A-1"]

        with (
            patch(
                "subprocess.run", side_effect=Exception("Command failed")
            ) as mock_run,
            patch("logging.error") as mock_log,
        ):
            wallpaper.set_sway_wallpaper(wallpaper_paths, monitors)

            mock_run.assert_called_once()
            mock_log.assert_called_once()


class TestWallpaperSelection:
    """Tests for wallpaper selection logic."""

    def test_select_wallpapers_single_monitor(self, tmp_path: Path) -> None:
        """Test wallpaper selection for single monitor."""
        # Create test wallpaper directory
        wallpaper_dir = tmp_path / "wallpapers"
        wallpaper_dir.mkdir()
        (wallpaper_dir / "image1.jpg").touch()
        (wallpaper_dir / "image2.jpg").touch()

        # Create config
        config = Config(
            directories=DirectoryConfig(
                workday_light_primary=wallpaper_dir,
                workday_dark_primary=wallpaper_dir,
                holiday_light_primary=wallpaper_dir,
                holiday_dark_primary=wallpaper_dir,
            ),
            logging=LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time="08:00",
                night_start_time="18:00",
            ),
            image_extensions=[".jpg"],
            state_tracking=StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        # Select wallpapers
        result = wallpaper.select_wallpapers(
            config,
            monitor_count=1,
            is_holiday=False,
            is_daytime=True,
            state_data=None,
        )

        assert len(result) == 1
        assert result[0].exists()
        assert result[0].suffix == ".jpg"

    def test_select_wallpapers_multi_monitor(self, tmp_path: Path) -> None:
        """Test wallpaper selection for multiple monitors."""
        # Create test wallpaper directories
        primary_dir = tmp_path / "primary"
        left_dir = tmp_path / "left"
        primary_dir.mkdir()
        left_dir.mkdir()

        for i in range(3):
            (primary_dir / f"primary{i}.jpg").touch()
            (left_dir / f"left{i}.jpg").touch()

        # Create config
        config = Config(
            directories=DirectoryConfig(
                workday_light_primary=primary_dir,
                workday_light_left=left_dir,
                workday_dark_primary=primary_dir,
                workday_dark_left=left_dir,
                holiday_light_primary=primary_dir,
                holiday_dark_primary=primary_dir,
            ),
            logging=LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time="08:00",
                night_start_time="18:00",
            ),
            image_extensions=[".jpg"],
            state_tracking=StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        # Select wallpapers for 2 monitors
        result = wallpaper.select_wallpapers(
            config,
            monitor_count=2,
            is_holiday=False,
            is_daytime=True,
            state_data=None,
        )

        assert len(result) == 2
        assert result[0].exists()
        assert result[1].exists()
        assert result[0].parent == primary_dir
        assert result[1].parent == left_dir

    def test_select_wallpapers_with_state(self, tmp_path: Path) -> None:
        """Test wallpaper selection with state tracking."""
        wallpaper_dir = tmp_path / "wallpapers"
        wallpaper_dir.mkdir()

        # Create sorted images
        (wallpaper_dir / "image1.jpg").touch()
        (wallpaper_dir / "image2.jpg").touch()
        (wallpaper_dir / "image3.jpg").touch()

        config = Config(
            directories=DirectoryConfig(
                workday_light_primary=wallpaper_dir,
                workday_dark_primary=wallpaper_dir,
                holiday_light_primary=wallpaper_dir,
                holiday_dark_primary=wallpaper_dir,
            ),
            logging=LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time="08:00",
                night_start_time="18:00",
            ),
            image_extensions=[".jpg"],
            state_tracking=StateTrackingConfig(
                enabled=True,
                state_file=tmp_path / "state.json",
            ),
        )

        # Initialize state
        state = initialize_state()

        # First selection
        result1 = wallpaper.select_wallpapers(
            config,
            monitor_count=1,
            is_holiday=False,
            is_daytime=True,
            state_data=state,
        )

        # Second selection
        result2 = wallpaper.select_wallpapers(
            config,
            monitor_count=1,
            is_holiday=False,
            is_daytime=True,
            state_data=state,
        )

        # Third selection
        result3 = wallpaper.select_wallpapers(
            config,
            monitor_count=1,
            is_holiday=False,
            is_daytime=True,
            state_data=state,
        )

        # Should cycle through images
        assert result1[0].name == "image1.jpg"
        assert result2[0].name == "image2.jpg"
        assert result3[0].name == "image3.jpg"

    def test_select_wallpapers_no_images(self, tmp_path: Path) -> None:
        """Test wallpaper selection with empty directory."""
        wallpaper_dir = tmp_path / "wallpapers"
        wallpaper_dir.mkdir()

        config = Config(
            directories=DirectoryConfig(
                workday_light_primary=wallpaper_dir,
                workday_dark_primary=wallpaper_dir,
                holiday_light_primary=wallpaper_dir,
                holiday_dark_primary=wallpaper_dir,
            ),
            logging=LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time="08:00",
                night_start_time="18:00",
            ),
            image_extensions=[".jpg"],
            state_tracking=StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        with patch("logging.error") as mock_log:
            result = wallpaper.select_wallpapers(
                config,
                monitor_count=1,
                is_holiday=False,
                is_daytime=True,
                state_data=None,
            )

            assert result == []
            mock_log.assert_called()

    def test_select_wallpapers_filters_extensions(
        self, tmp_path: Path
    ) -> None:
        """Test that only configured extensions are selected."""
        wallpaper_dir = tmp_path / "wallpapers"
        wallpaper_dir.mkdir()
        (wallpaper_dir / "image1.jpg").touch()
        (wallpaper_dir / "image2.png").touch()
        (wallpaper_dir / "document.txt").touch()

        config = Config(
            directories=DirectoryConfig(
                workday_light_primary=wallpaper_dir,
                workday_dark_primary=wallpaper_dir,
                holiday_light_primary=wallpaper_dir,
                holiday_dark_primary=wallpaper_dir,
            ),
            logging=LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time="08:00",
                night_start_time="18:00",
            ),
            image_extensions=[".jpg"],
            state_tracking=StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        result = wallpaper.select_wallpapers(
            config,
            monitor_count=1,
            is_holiday=False,
            is_daytime=True,
            state_data=None,
        )

        assert len(result) == 1
        assert result[0].suffix == ".jpg"
