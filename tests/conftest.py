#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test fixtures for the wallpaper changer module.

This module provides pytest fixtures that can be used across test files
to set up common test environments and mock dependencies.
"""

import os
import json
import pytest
from typing import List, Dict, Any, Generator
from unittest.mock import patch, MagicMock
from pathlib import Path


@pytest.fixture
def mock_wallpaper_dirs(tmp_path: Path) -> Dict[str, str]:
    """
    Create temporary wallpaper directories with test images.

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        Dictionary of wallpaper directory paths
    """
    # Create directory structure
    left_dir = tmp_path / "left"
    primary_dir = tmp_path / "primary"
    sunday_dir = tmp_path / "sunday"

    for directory in [left_dir, primary_dir, sunday_dir]:
        directory.mkdir()

    # Create some test images in each directory
    for i in range(3):
        (left_dir / f"left_image_{i}.jpg").write_text("fake image data")
        (primary_dir / f"primary_image_{i}.jpg").write_text("fake image data")
        (sunday_dir / f"sunday_image_{i}.jpg").write_text("fake image data")

    return {
        "left": str(left_dir),
        "primary": str(primary_dir),
        "sunday": str(sunday_dir),
    }


@pytest.fixture
def mock_x11_environment() -> Generator[None, None, None]:
    """
    Mock an X11 display environment.

    Yields:
        None
    """
    with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}):
        yield


@pytest.fixture
def mock_wayland_environment() -> Generator[None, None, None]:
    """
    Mock a Wayland display environment.

    Yields:
        None
    """
    with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}):
        yield


@pytest.fixture
def mock_x11_monitors() -> List[str]:
    """
    Mock data for X11 monitor configuration.

    Returns:
        List of monitor names
    """
    return ["DP-1", "HDMI-1"]


@pytest.fixture
def mock_sway_monitors() -> List[str]:
    """
    Mock data for Sway/Wayland monitor configuration.

    Returns:
        List of monitor names
    """
    return ["eDP-1", "HDMI-A-1"]


@pytest.fixture
def mock_sway_outputs_json() -> str:
    """
    Mock JSON response from swaymsg command.

    Returns:
        JSON string of sway outputs
    """
    outputs = [
        {
            "name": "eDP-1",
            "active": True,
            "primary": True,
            "focused": True,
            "rect": {"x": 0, "y": 0, "width": 1920, "height": 1080},
        },
        {
            "name": "HDMI-A-1",
            "active": True,
            "primary": False,
            "focused": False,
            "rect": {"x": 1920, "y": 0, "width": 1920, "height": 1080},
        },
        {
            "name": "DP-1",
            "active": False,
            "primary": False,
            "focused": False,
            "rect": {"x": 0, "y": 0, "width": 0, "height": 0},
        },
    ]
    return json.dumps(outputs)


@pytest.fixture
def mock_xrandr_output() -> str:
    """
    Mock output from xrandr command.

    Returns:
        String output from xrandr command
    """
    return """Monitors: 2
 0: +*DP-1 1920/600x1080/340+0+0  DP-1
 1: +HDMI-1 1920/600x1080/340+1920+0  HDMI-1"""
