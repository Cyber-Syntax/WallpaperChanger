#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the logging configuration of the wallpaper changer.

This module tests the logging setup functionality of the wallpaper changer module.
"""

import logging
import os


from src import wallpaper


class TestLoggingConfiguration:
    """Tests for the logging configuration functionality."""

    def test_configure_logging(self) -> None:
        """Test that logging is properly configured with the correct handlers and formatters."""
        # Save original handlers to restore later
        original_handlers = logging.getLogger().handlers.copy()

        try:
            # Clear all handlers first
            logger = logging.getLogger()
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

            # We need to directly inspect what happens rather than trying to mock
            # Create a test function that runs configure_logging and checks the result
            wallpaper.configure_logging()

            # Verify logger level was set correctly
            assert logger.level == logging.INFO

            # Verify there's exactly one handler added
            assert len(logger.handlers) == 1

            # Get the handler and verify it's the right type
            handler = logger.handlers[0]
            assert isinstance(handler, logging.handlers.RotatingFileHandler)

            # Verify handler has correct configuration
            assert handler.baseFilename == os.path.abspath(
                str(wallpaper.LOG_FILE)
            )
            assert handler.maxBytes == wallpaper.LOG_MAX_SIZE
            assert handler.backupCount == wallpaper.LOG_BACKUP_COUNT

            # Verify formatter was set
            assert handler.formatter is not None

        finally:
            # Restore original handlers
            logger = logging.getLogger()
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            for handler in original_handlers:
                logger.addHandler(handler)
