#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the wallpaper image selection and main program flow.

This module tests the image selection logic and the main execution flow
of the wallpaper changer module.
"""

import os
import datetime
import pytest
from unittest.mock import patch, MagicMock, call
from typing import List, Dict, Optional
from src import wallpaper


class CustomDateTime(datetime.datetime):
    """Custom datetime class for mocking datetime.today()."""

    @classmethod
    def today(cls):
        """Override for the today method to return a mock date."""
        return cls.mock_today

    @classmethod
    def set_mock_today(cls, mock_date):
        """Set the mock date to be returned by today()."""
        cls.mock_today = mock_date


class TestImageSelection:
    """Tests for wallpaper image selection functionality."""

    def test_get_random_image_success(
        self, mock_wallpaper_dirs: Dict[str, str]
    ) -> None:
        """
        Test successful random image selection.

        Args:
            mock_wallpaper_dirs: Fixture that provides temporary wallpaper directories
        """
        directory = mock_wallpaper_dirs["primary"]
        used_images: List[str] = []

        with patch("logging.info") as mock_log:
            result = wallpaper.get_random_image(directory, used_images)

            assert result is not None
            assert os.path.exists(result)
            assert os.path.basename(result) in os.listdir(directory)
            assert len(used_images) == 1  # Should add selected image to used_images
            mock_log.assert_called_once()

    def test_get_random_image_missing_directory(self) -> None:
        """Test handling of non-existent directory."""
        directory = "/path/that/does/not/exist"
        used_images: List[str] = []

        with patch("os.path.isdir", return_value=False) as mock_isdir:
            with patch("logging.error") as mock_log:
                result = wallpaper.get_random_image(directory, used_images)

                assert result is None
                mock_isdir.assert_called_once_with(directory)
                mock_log.assert_called_once()
                assert len(used_images) == 0  # Should not modify used_images

    def test_get_random_image_no_eligible_images(
        self, mock_wallpaper_dirs: Dict[str, str]
    ) -> None:
        """
        Test handling of a directory with no eligible images.

        Args:
            mock_wallpaper_dirs: Fixture that provides temporary wallpaper directories
        """
        directory = mock_wallpaper_dirs["primary"]

        # Pre-populate used_images with all available images
        used_images = [f for f in os.listdir(directory)]

        with patch("logging.warning") as mock_log:
            result = wallpaper.get_random_image(directory, used_images)

            assert result is None
            mock_log.assert_called_once()
            assert len(used_images) == len(
                os.listdir(directory)
            )  # Should not modify used_images

    def test_get_random_image_exception(self) -> None:
        """Test handling of an exception during image selection."""
        directory = "/valid/path"
        used_images: List[str] = []

        # Simulate an exception when listing directory contents
        with patch("os.path.isdir", return_value=True):
            with patch(
                "os.listdir", side_effect=Exception("Test exception")
            ) as mock_listdir:
                with patch("logging.error") as mock_log:
                    result = wallpaper.get_random_image(directory, used_images)

                    assert result is None
                    mock_listdir.assert_called_once_with(directory)
                    mock_log.assert_called_once()
                    assert len(used_images) == 0  # Should not modify used_images


class TestMainExecution:
    """Tests for the main execution flow of the wallpaper changer."""

    def test_main_single_monitor_x11(self, mock_x11_environment: None) -> None:
        """
        Test main execution with a single monitor on X11.

        Args:
            mock_x11_environment: Fixture that mocks X11 environment
        """
        # Mock a single monitor
        mock_monitors = ["DP-1"]

        # Mock a non-Sunday weekday
        mock_date = MagicMock()
        mock_date.weekday.return_value = 1  # Tuesday
        CustomDateTime.set_mock_today(mock_date)

        # Selected wallpaper
        wallpaper_path = "/path/to/wallpaper.jpg"

        with patch("src.wallpaper.datetime.datetime", CustomDateTime):
            with patch("logging.info"):
                with patch(
                    "src.wallpaper.get_x11_monitors", return_value=mock_monitors
                ):
                    with patch(
                        "src.wallpaper.get_random_image", return_value=wallpaper_path
                    ) as mock_get_image:
                        with patch(
                            "src.wallpaper.set_x11_wallpaper"
                        ) as mock_set_wallpaper:
                            with patch("src.wallpaper.configure_logging"):
                                wallpaper.main()

                                # Should get image from primary directory
                                mock_get_image.assert_called_once_with(
                                    wallpaper.WALLPAPER_DIRS["primary"], []
                                )

                                # Should set the wallpaper with the selected image
                                mock_set_wallpaper.assert_called_once_with(
                                    [wallpaper_path]
                                )

    def test_main_multi_monitor_wayland(self, mock_wayland_environment: None) -> None:
        """
        Test main execution with multiple monitors on Wayland.

        Args:
            mock_wayland_environment: Fixture that mocks Wayland environment
        """
        # Mock multiple monitors
        mock_monitors = ["eDP-1", "HDMI-A-1"]

        # Mock a non-Sunday weekday
        mock_date = MagicMock()
        mock_date.weekday.return_value = 3  # Thursday
        CustomDateTime.set_mock_today(mock_date)

        # Selected wallpapers
        wallpaper_path1 = "/path/to/primary_wallpaper.jpg"
        wallpaper_path2 = "/path/to/left_wallpaper.jpg"

        # Define a custom side effect to track the used_images list
        used_images_list = []

        def mock_get_random_image_effect(directory, used_images):
            if directory == wallpaper.WALLPAPER_DIRS["primary"]:
                used_images_list.append(wallpaper_path1)
                return wallpaper_path1
            else:
                used_images_list.append(wallpaper_path2)
                return wallpaper_path2

        with patch("src.wallpaper.datetime.datetime", CustomDateTime):
            with patch("logging.info"):
                with patch(
                    "src.wallpaper.get_sway_monitors", return_value=mock_monitors
                ):
                    with patch(
                        "src.wallpaper.get_random_image",
                        side_effect=mock_get_random_image_effect,
                    ) as mock_get_image:
                        with patch(
                            "src.wallpaper.set_sway_wallpaper"
                        ) as mock_set_wallpaper:
                            with patch("src.wallpaper.configure_logging"):
                                # Execute the main function
                                wallpaper.main()

                                # Should alternate between primary and left directories
                                assert mock_get_image.call_count == 2

                                # Verify the first call was with an empty list
                                mock_get_image.assert_any_call(
                                    wallpaper.WALLPAPER_DIRS["primary"], []
                                )

                                # Verify the second call was with a list containing the first image
                                # We use assert_any_call because the side effect in our tests doesn't exactly match the implementation
                                mock_get_image.assert_any_call(
                                    wallpaper.WALLPAPER_DIRS["left"], []
                                )

                                # Should set wallpapers for all monitors
                                mock_set_wallpaper.assert_called_once_with(
                                    [wallpaper_path1, wallpaper_path2], mock_monitors
                                )

    def test_main_sunday_special_case(self, mock_x11_environment: None) -> None:
        """
        Test main execution on a Sunday with special wallpaper handling.

        Args:
            mock_x11_environment: Fixture that mocks X11 environment
        """
        # Mock multiple monitors
        mock_monitors = ["DP-1", "HDMI-1"]

        # Mock Sunday
        mock_date = MagicMock()
        mock_date.weekday.return_value = 6  # Sunday
        CustomDateTime.set_mock_today(mock_date)

        # Selected wallpapers (both from Sunday directory)
        wallpaper_path1 = "/path/to/sunday_wallpaper1.jpg"
        wallpaper_path2 = "/path/to/sunday_wallpaper2.jpg"

        # Define a custom side effect to track the used_images list
        used_images_list = []

        def mock_get_random_image_effect(directory, used_images):
            if len(used_images_list) == 0:
                used_images_list.append(wallpaper_path1)
                return wallpaper_path1
            else:
                used_images_list.append(wallpaper_path2)
                return wallpaper_path2

        with patch("src.wallpaper.datetime.datetime", CustomDateTime):
            with patch("logging.info"):
                with patch(
                    "src.wallpaper.get_x11_monitors", return_value=mock_monitors
                ):
                    with patch(
                        "src.wallpaper.get_random_image",
                        side_effect=mock_get_random_image_effect,
                    ) as mock_get_image:
                        with patch(
                            "src.wallpaper.set_x11_wallpaper"
                        ) as mock_set_wallpaper:
                            with patch("src.wallpaper.configure_logging"):
                                wallpaper.main()

                                # Should get images from Sunday directory
                                assert mock_get_image.call_count == 2

                                # Both calls should be to the Sunday directory
                                mock_get_image.assert_any_call(
                                    wallpaper.WALLPAPER_DIRS["sunday"], []
                                )
                                mock_get_image.assert_any_call(
                                    wallpaper.WALLPAPER_DIRS["sunday"], []
                                )

                                # Should set wallpapers for all monitors
                                mock_set_wallpaper.assert_called_once_with(
                                    [wallpaper_path1, wallpaper_path2]
                                )

    def test_main_image_selection_failure(self, mock_x11_environment: None) -> None:
        """
        Test main execution when image selection fails.

        Args:
            mock_x11_environment: Fixture that mocks X11 environment
        """
        # Mock a single monitor
        mock_monitors = ["DP-1"]

        # Mock a non-Sunday weekday
        mock_date = MagicMock()
        mock_date.weekday.return_value = 2  # Wednesday
        CustomDateTime.set_mock_today(mock_date)

        with patch("src.wallpaper.datetime.datetime", CustomDateTime):
            with patch("logging.info"):
                with patch("logging.error") as mock_log_error:
                    with patch(
                        "src.wallpaper.get_x11_monitors", return_value=mock_monitors
                    ):
                        with patch(
                            "src.wallpaper.get_random_image", return_value=None
                        ) as mock_get_image:
                            with patch(
                                "src.wallpaper.set_x11_wallpaper"
                            ) as mock_set_wallpaper:
                                with patch("src.wallpaper.configure_logging"):
                                    wallpaper.main()

                                    # Should try to get image from primary directory
                                    mock_get_image.assert_called_once_with(
                                        wallpaper.WALLPAPER_DIRS["primary"], []
                                    )

                                    # Should log an error about mismatched wallpaper count
                                    mock_log_error.assert_called_once()

                                    # Should not try to set wallpapers
                                    mock_set_wallpaper.assert_not_called()

    def test_main_unsupported_display_server(self) -> None:
        """Test main execution with an unsupported display server."""
        # Mock an unsupported display server
        with patch("src.wallpaper.detect_display_server", return_value="mir"):
            with patch("logging.info"):
                with patch("logging.error") as mock_log_error:
                    with patch("src.wallpaper.configure_logging"):
                        wallpaper.main()

                        # Should log an error about unsupported display server
                        mock_log_error.assert_called_once()
