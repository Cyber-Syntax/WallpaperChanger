#!/usr/bin/env python3
"""Unit tests for the wallpaper image selection and main program flow.

This module tests the image selection logic and the main execution flow
of the wallpaper changer module.
"""

import datetime

import pytest


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


@pytest.mark.skip(
    reason="Obsolete - get_random_image removed. Tests now in test_state_manager.py and test_round_robin.py"
)
class TestImageSelection:
    """Tests for wallpaper image selection functionality.

    Note: get_random_image tests are obsolete - that function was removed.
    Image selection with round-robin is now tested in:
    - tests/unit/test_state_manager.py::TestRoundRobinSelection
    - tests/integration/test_round_robin.py
    """


@pytest.mark.skip(
    reason="Obsolete - tests were too coupled to old implementation. Main flow tested in integration tests"
)
class TestMainExecution:
    """Tests for the main execution flow of the wallpaper changer.

    Note: These tests are obsolete - they tested internal implementation details
    of the old get_random_image function. Main execution flow is now tested in:
    - tests/integration/test_wallpaper_with_state.py
    """
