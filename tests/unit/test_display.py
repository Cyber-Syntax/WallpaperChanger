#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the wallpaper detection and server-related functions.

This module tests the display server detection, monitor detection,
and wallpaper setting functionality of the wallpaper changer module.
"""

import subprocess
from unittest.mock import MagicMock, call, patch

from src import wallpaper


class TestDisplayDetection:
    """Tests for display server and monitor detection functionality."""

    def test_detect_display_server_x11(
        self, mock_x11_environment: None
    ) -> None:
        """
        Test detection of X11 display server.

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
        """
        Test detection of Wayland display server.

        Args:
            mock_wayland_environment: Fixture that mocks Wayland environment
        """
        with patch("logging.info") as mock_log:
            result = wallpaper.detect_display_server()
            assert result == "wayland"
            mock_log.assert_called_once()

    def test_detect_display_server_unknown(self) -> None:
        """Test detection of unknown display server when environment variable is not set."""
        with patch.dict("os.environ", clear=True):
            with patch("logging.info") as mock_log:
                result = wallpaper.detect_display_server()
                assert result == "unknown"
                mock_log.assert_called_once()

    def test_get_x11_monitors_success(self, mock_xrandr_output: str) -> None:
        """
        Test successful detection of X11 monitors.

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
        """
        Test successful detection of Sway monitors.

        Args:
            mock_sway_outputs_json: Fixture that provides mock swaymsg JSON output
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
        wallpaper_paths = ["/path/to/img1.jpg", "/path/to/img2.jpg"]

        with patch("subprocess.run") as mock_run:
            with patch("logging.info") as mock_log:
                wallpaper.set_x11_wallpaper(wallpaper_paths)

                mock_run.assert_called_once_with(
                    ["feh", "--bg-fill"] + wallpaper_paths, check=True
                )
                mock_log.assert_called_once()

    def test_set_x11_wallpaper_failure(self) -> None:
        """Test handling of feh command failure."""
        wallpaper_paths = ["/path/to/img1.jpg", "/path/to/img2.jpg"]
        error = subprocess.CalledProcessError(1, "feh")

        with patch("subprocess.run", side_effect=error) as mock_run:
            with patch("logging.error") as mock_log:
                wallpaper.set_x11_wallpaper(wallpaper_paths)

                mock_run.assert_called_once()
                mock_log.assert_called_once()

    def test_set_sway_wallpaper_success(self) -> None:
        """Test successful setting of Sway wallpapers."""
        wallpaper_paths = ["/path/to/img1.jpg", "/path/to/img2.jpg"]
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
        wallpaper_paths = ["/path/to/img1.jpg", "/path/to/img2.jpg"]
        monitors = ["eDP-1", "HDMI-A-1"]

        with patch(
            "subprocess.run", side_effect=Exception("Command failed")
        ) as mock_run:
            with patch("logging.error") as mock_log:
                wallpaper.set_sway_wallpaper(wallpaper_paths, monitors)

                mock_run.assert_called_once()
                mock_log.assert_called_once()
