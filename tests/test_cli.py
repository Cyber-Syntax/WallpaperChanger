#!/usr/bin/env python3
"""Unit tests for CLI module.

Tests cover:
- init_config command
- validate_config command
- run command
- logging setup

"""

import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from src import cli, config


class TestInitConfig:
    """Tests for init_config command."""

    def test_init_config_creates_file(self, tmp_path: Path) -> None:
        """Test that init_config creates configuration file."""
        config_path = tmp_path / "config.ini"

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("builtins.print") as mock_print,
        ):
            cli.init_config()

            assert config_path.exists()
            mock_print.assert_called()

    def test_init_config_file_exists_abort(self, tmp_path: Path) -> None:
        """Test aborting when config file exists."""
        config_path = tmp_path / "config.ini"
        config_path.write_text("existing config")

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("builtins.input", return_value="n"),
            patch("builtins.print") as mock_print,
        ):
            with pytest.raises(SystemExit) as exc_info:
                cli.init_config()

            assert exc_info.value.code == 0
            mock_print.assert_called()

    def test_init_config_file_exists_overwrite(self, tmp_path: Path) -> None:
        """Test overwriting existing config file."""
        config_path = tmp_path / "config.ini"
        config_path.write_text("old config")

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("builtins.input", return_value="y"),
            patch("builtins.print") as mock_print,
        ):
            cli.init_config()

            assert config_path.exists()
            content = config_path.read_text()
            assert "old config" not in content
            mock_print.assert_called()

    def test_init_config_error_handling(self, tmp_path: Path) -> None:
        """Test error handling during config creation."""
        config_path = tmp_path / "config.ini"

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch(
                "src.cli.config.create_default",
                side_effect=Exception("Test error"),
            ),
            patch("builtins.print") as mock_print,
        ):
            with pytest.raises(SystemExit) as exc_info:
                cli.init_config()

            assert exc_info.value.code == 1
            mock_print.assert_called()


class TestValidateConfig:
    """Tests for validate_config command."""

    def test_validate_config_success(self) -> None:
        """Test successful config validation."""
        with patch("src.cli.config.validate", return_value=True):
            with pytest.raises(SystemExit) as exc_info:
                cli.validate_config()

            assert exc_info.value.code == 0

    def test_validate_config_failure(self) -> None:
        """Test failed config validation."""
        with patch("src.cli.config.validate", return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                cli.validate_config()

            assert exc_info.value.code == 1


class TestRun:
    """Tests for run command."""

    def test_run_creates_default_config_on_first_run(
        self, tmp_path: Path
    ) -> None:
        """Test that run creates default config on first run."""
        config_path = tmp_path / "config.ini"

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("builtins.print") as mock_print,
        ):
            with pytest.raises(SystemExit) as exc_info:
                cli.run()

            assert exc_info.value.code == 0
            assert config_path.exists()
            mock_print.assert_called()

    def test_run_config_load_error(self, tmp_path: Path) -> None:
        """Test handling of config load errors."""
        config_path = tmp_path / "config.ini"
        config_path.write_text("invalid toml: [[[")

        captured_output = StringIO()

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("sys.stderr", captured_output),
        ):
            with pytest.raises(SystemExit) as exc_info:
                cli.run()

            assert exc_info.value.code == 1
            output = captured_output.getvalue()
            assert "error" in output.lower() or "Unexpected error" in output

    def test_run_no_monitors_detected(self, tmp_path: Path) -> None:
        """Test handling when no monitors are detected."""
        config_path = tmp_path / "config.ini"
        # Create the config file so run() doesn't try to create default
        config_path.write_text("")

        # Create a minimal valid config
        wallpaper_dir = tmp_path / "wallpapers"
        wallpaper_dir.mkdir()
        (wallpaper_dir / "test.jpg").touch()

        cfg = config.Config(
            directories=config.DirectoryConfig(
                workday_light_primary=wallpaper_dir,
                workday_dark_primary=wallpaper_dir,
                holiday_light_primary=wallpaper_dir,
                holiday_dark_primary=wallpaper_dir,
            ),
            logging=config.LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=config.ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time=datetime.time(8, 0),
                night_start_time=datetime.time(18, 0),
            ),
            image_extensions=[".jpg"],
            state_tracking=config.StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("src.cli.config.load", return_value=cfg),
            patch(
                "src.cli.wallpaper.detect_display_server", return_value="x11"
            ),
            patch("src.cli.wallpaper.get_x11_monitors", return_value=[]),
            patch("logging.error") as mock_log,
            patch("logging.info"),
        ):
            cli.run()
            mock_log.assert_called_with("No monitors detected!")

    def test_run_successful_execution(self, tmp_path: Path) -> None:
        """Test successful wallpaper rotation."""
        config_path = tmp_path / "config.ini"
        # Create the config file so run() doesn't try to create default
        config_path.write_text("")

        # Create test wallpaper
        wallpaper_dir = tmp_path / "wallpapers"
        wallpaper_dir.mkdir()
        (wallpaper_dir / "test.jpg").touch()

        cfg = config.Config(
            directories=config.DirectoryConfig(
                workday_light_primary=wallpaper_dir,
                workday_dark_primary=wallpaper_dir,
                holiday_light_primary=wallpaper_dir,
                holiday_dark_primary=wallpaper_dir,
            ),
            logging=config.LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=config.ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time=datetime.time(8, 0),
                night_start_time=datetime.time(18, 0),
            ),
            image_extensions=[".jpg"],
            state_tracking=config.StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("src.cli.config.load", return_value=cfg),
            patch(
                "src.cli.wallpaper.detect_display_server", return_value="x11"
            ),
            patch(
                "src.cli.wallpaper.get_x11_monitors", return_value=["HDMI-0"]
            ),
            patch("src.cli.wallpaper.set_x11_wallpaper") as mock_set,
            patch("logging.info"),
        ):
            cli.run()
            mock_set.assert_called_once()

    def test_run_with_state_tracking(self, tmp_path: Path) -> None:
        """Test run with state tracking enabled."""
        config_path = tmp_path / "config.ini"
        # Create the config file so run() doesn't try to create default
        config_path.write_text("")
        state_file = tmp_path / "state.json"

        wallpaper_dir = tmp_path / "wallpapers"
        wallpaper_dir.mkdir()
        (wallpaper_dir / "test.jpg").touch()

        cfg = config.Config(
            directories=config.DirectoryConfig(
                workday_light_primary=wallpaper_dir,
                workday_dark_primary=wallpaper_dir,
                holiday_light_primary=wallpaper_dir,
                holiday_dark_primary=wallpaper_dir,
            ),
            logging=config.LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=config.ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time=datetime.time(8, 0),
                night_start_time=datetime.time(18, 0),
            ),
            image_extensions=[".jpg"],
            state_tracking=config.StateTrackingConfig(
                enabled=True,
                state_file=state_file,
            ),
        )

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("src.cli.config.load", return_value=cfg),
            patch(
                "src.cli.wallpaper.detect_display_server", return_value="x11"
            ),
            patch(
                "src.cli.wallpaper.get_x11_monitors", return_value=["HDMI-0"]
            ),
            patch("src.cli.wallpaper.set_x11_wallpaper"),
            patch("logging.info"),
        ):
            cli.run()
            # Verify state file was created
            assert state_file.exists()

    def test_run_wayland_display_server(self, tmp_path: Path) -> None:
        """Test run with Wayland display server."""
        config_path = tmp_path / "config.ini"
        # Create the config file so run() doesn't try to create default
        config_path.write_text("")

        wallpaper_dir = tmp_path / "wallpapers"
        wallpaper_dir.mkdir()
        (wallpaper_dir / "test.jpg").touch()

        cfg = config.Config(
            directories=config.DirectoryConfig(
                workday_light_primary=wallpaper_dir,
                workday_dark_primary=wallpaper_dir,
                holiday_light_primary=wallpaper_dir,
                holiday_dark_primary=wallpaper_dir,
            ),
            logging=config.LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=config.ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time=datetime.time(8, 0),
                night_start_time=datetime.time(18, 0),
            ),
            image_extensions=[".jpg"],
            state_tracking=config.StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("src.cli.config.load", return_value=cfg),
            patch(
                "src.cli.wallpaper.detect_display_server",
                return_value="wayland",
            ),
            patch(
                "src.cli.wallpaper.get_sway_monitors", return_value=["eDP-1"]
            ),
            patch("src.cli.wallpaper.set_sway_wallpaper") as mock_set,
            patch("logging.info"),
        ):
            cli.run()
            mock_set.assert_called_once()

    def test_run_unknown_display_server(self, tmp_path: Path) -> None:
        """Test handling of unknown display server."""
        config_path = tmp_path / "config.ini"
        # Create the config file so run() doesn't try to create default
        config_path.write_text("")

        wallpaper_dir = tmp_path / "wallpapers"
        wallpaper_dir.mkdir()
        (wallpaper_dir / "test.jpg").touch()

        cfg = config.Config(
            directories=config.DirectoryConfig(
                workday_light_primary=wallpaper_dir,
                workday_dark_primary=wallpaper_dir,
                holiday_light_primary=wallpaper_dir,
                holiday_dark_primary=wallpaper_dir,
            ),
            logging=config.LoggingConfig(
                log_dir=tmp_path / "logs",
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=config.ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time=datetime.time(8, 0),
                night_start_time=datetime.time(18, 0),
            ),
            image_extensions=[".jpg"],
            state_tracking=config.StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        with (
            patch("src.cli.config.get_default_path", return_value=config_path),
            patch("src.cli.config.load", return_value=cfg),
            patch(
                "src.cli.wallpaper.detect_display_server",
                return_value="unknown",
            ),
            patch(
                "src.cli.wallpaper.get_x11_monitors", return_value=["HDMI-0"]
            ),
            patch("logging.error") as mock_error,
            patch("logging.info"),
        ):
            cli.run()
            mock_error.assert_called_with(
                "Unsupported display server: %s", "unknown"
            )


class TestLoggingSetup:
    """Tests for logging setup functionality."""

    def test_setup_logging_creates_log_dir(self, tmp_path: Path) -> None:
        """Test that logging setup creates log directory."""
        log_dir = tmp_path / "logs"

        cfg = config.Config(
            directories=config.DirectoryConfig(),
            logging=config.LoggingConfig(
                log_dir=log_dir,
                log_level="INFO",
                max_size_mb=10,
                backup_count=3,
            ),
            schedule=config.ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time=datetime.time(8, 0),
                night_start_time=datetime.time(18, 0),
            ),
            image_extensions=[".jpg"],
            state_tracking=config.StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        cli._setup_logging(cfg)

        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_setup_logging_creates_handler(self, tmp_path: Path) -> None:
        """Test that logging setup creates rotating file handler."""
        import logging

        log_dir = tmp_path / "logs"

        cfg = config.Config(
            directories=config.DirectoryConfig(),
            logging=config.LoggingConfig(
                log_dir=log_dir,
                log_level="DEBUG",
                max_size_mb=5,
                backup_count=2,
            ),
            schedule=config.ScheduleConfig(
                holiday_days=["Sunday"],
                day_start_time=datetime.time(8, 0),
                night_start_time=datetime.time(18, 0),
            ),
            image_extensions=[".jpg"],
            state_tracking=config.StateTrackingConfig(
                enabled=False,
                state_file=tmp_path / "state.json",
            ),
        )

        # Clear existing handlers
        logger = logging.getLogger()
        original_handlers = logger.handlers.copy()
        logger.handlers.clear()

        try:
            cli._setup_logging(cfg)

            assert len(logger.handlers) == 1
            assert logger.level == logging.DEBUG
        finally:
            # Restore original handlers
            logger.handlers.clear()
            for handler in original_handlers:
                logger.addHandler(handler)
