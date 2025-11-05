#!/usr/bin/env python3
"""Unit tests for the logging configuration of the wallpaper changer.

This module tests the logging setup functionality of the wallpaper changer module.
"""

import datetime
import logging
import os
from pathlib import Path

from src import wallpaper
from src.config_loader import (
    Config,
    DirectoryConfig,
    LoggingConfig,
    ScheduleConfig,
    StateTrackingConfig,
)


class TestLoggingConfiguration:
    """Tests for the logging configuration functionality."""

    def test_configure_logging(self, tmp_path: Path) -> None:
        """Test that logging is properly configured with the correct handlers and formatters."""
        # Save original handlers to restore later
        original_handlers = logging.getLogger().handlers.copy()

        try:
            # Clear all handlers first
            logger = logging.getLogger()
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

            # Create a test config with temporary log directory
            config = Config(
                directories=DirectoryConfig(),
                logging=LoggingConfig(
                    log_dir=tmp_path,
                    max_size_mb=10,
                    backup_count=3,
                    log_level="INFO",
                ),
                schedule=ScheduleConfig(
                    holiday_days=["Sunday"],
                    day_start_time=datetime.time(8, 0),
                    night_start_time=datetime.time(18, 0),
                ),
                image_extensions=[".png", ".jpg", ".jpeg"],
                state_tracking=StateTrackingConfig(
                    enabled=True,
                    state_file=tmp_path / "state.json",
                    auto_cleanup=True,
                ),
            )

            # Call configure_logging with the test config
            wallpaper.configure_logging(config)

            # Verify logger level was set correctly
            assert logger.level == logging.INFO

            # Verify there's exactly one handler added
            assert len(logger.handlers) == 1

            # Get the handler and verify it's the right type
            handler = logger.handlers[0]
            assert isinstance(handler, logging.handlers.RotatingFileHandler)

            # Verify handler has correct configuration
            expected_log_file = tmp_path / "main.log"
            assert handler.baseFilename == os.path.abspath(
                str(expected_log_file)
            )
            assert handler.maxBytes == config.logging.max_size_mb * 1024 * 1024
            assert handler.backupCount == config.logging.backup_count

            # Verify formatter was set
            assert handler.formatter is not None

        finally:
            # Restore original handlers
            logger = logging.getLogger()
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            for handler in original_handlers:
                logger.addHandler(handler)
