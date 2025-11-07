#!/usr/bin/env python3
"""Integration tests for round-robin selection.

Tests the round-robin functionality with the simplified state tracking.
"""

import tempfile
from pathlib import Path

from src.state import (
    _initialize as initialize_state,
)
from src.state import (
    next_wallpaper,
    update,
)


class TestRoundRobinSelection:
    """Tests for round-robin selection."""

    def test_three_images_round_robin(self) -> None:
        """Test that 3 images cycle in order: 1,2,3,1,2,3."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallpaper_dir = Path(tmpdir) / "wallpapers"
            wallpaper_dir.mkdir()

            # Create 3 images (named to ensure sort order)
            (wallpaper_dir / "image1.jpg").touch()
            (wallpaper_dir / "image2.jpg").touch()
            (wallpaper_dir / "image3.jpg").touch()

            state = initialize_state()
            extensions = [".jpg"]

            # Run 9 times to verify 3 complete cycles
            selections = []
            for i in range(9):
                used_images: list[str] = []
                path = next_wallpaper(
                    wallpaper_dir,
                    extensions,
                    state,
                    used_images,
                )
                assert path is not None
                selections.append(path.name)

                # Update state
                update(
                    state,
                    [path],
                    [f"monitor-{i}"],
                )

            # Verify perfect round-robin cycling
            expected = [
                "image1.jpg",
                "image2.jpg",
                "image3.jpg",
                "image1.jpg",
                "image2.jpg",
                "image3.jpg",
                "image1.jpg",
                "image2.jpg",
                "image3.jpg",
            ]
            assert selections == expected

    def test_multi_monitor_no_duplicates(self) -> None:
        """Test that multi-monitor setup avoids duplicates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallpaper_dir = Path(tmpdir) / "wallpapers"
            wallpaper_dir.mkdir()

            # Create 4 images
            (wallpaper_dir / "image1.jpg").touch()
            (wallpaper_dir / "image2.jpg").touch()
            (wallpaper_dir / "image3.jpg").touch()
            (wallpaper_dir / "image4.jpg").touch()

            state = initialize_state()
            extensions = [".jpg"]

            # Simulate 2 monitors selecting wallpapers
            used_images: list[str] = []

            path1 = next_wallpaper(
                wallpaper_dir,
                extensions,
                state,
                used_images,
            )
            assert path1 is not None
            assert path1.name == "image1.jpg"

            path2 = next_wallpaper(
                wallpaper_dir,
                extensions,
                state,
                used_images,
            )
            assert path2 is not None
            assert path2.name == "image2.jpg"

            # Verify no duplicates
            assert path1.name != path2.name

    def test_single_image_pool(self) -> None:
        """Test behavior with only 1 image available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallpaper_dir = Path(tmpdir) / "wallpapers"
            wallpaper_dir.mkdir()

            (wallpaper_dir / "image1.jpg").touch()

            state = initialize_state()
            extensions = [".jpg"]

            # Run multiple times
            selections = []
            for i in range(5):
                used_images: list[str] = []
                path = next_wallpaper(
                    wallpaper_dir,
                    extensions,
                    state,
                    used_images,
                )
                assert path is not None
                selections.append(path.name)

                update(
                    state,
                    [path],
                    [f"monitor-{i}"],
                )

            # All selections should be the same image
            assert all(s == "image1.jpg" for s in selections)

    def test_directory_contents_change(self) -> None:
        """Test that round-robin resets when directory contents change."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallpaper_dir = Path(tmpdir) / "wallpapers"
            wallpaper_dir.mkdir()

            # Start with 2 images
            (wallpaper_dir / "image1.jpg").touch()
            (wallpaper_dir / "image2.jpg").touch()

            state = initialize_state()
            extensions = [".jpg"]

            # First selection
            used_images: list[str] = []
            path1 = next_wallpaper(
                wallpaper_dir,
                extensions,
                state,
                used_images,
            )
            assert path1.name == "image1.jpg"

            # Second selection
            used_images = []
            path2 = next_wallpaper(
                wallpaper_dir,
                extensions,
                state,
                used_images,
            )
            assert path2.name == "image2.jpg"

            # Add a new image
            (wallpaper_dir / "image3.jpg").touch()

            # Should reset to first image in new list
            used_images = []
            path3 = next_wallpaper(
                wallpaper_dir,
                extensions,
                state,
                used_images,
            )
            assert path3.name == "image1.jpg"

    def test_consistent_ordering(self) -> None:
        """Test that images are selected in consistent alphabetical order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wallpaper_dir = Path(tmpdir) / "wallpapers"
            wallpaper_dir.mkdir()

            # Create images in non-alphabetical order
            (wallpaper_dir / "zebra.jpg").touch()
            (wallpaper_dir / "apple.jpg").touch()
            (wallpaper_dir / "banana.jpg").touch()

            state = initialize_state()
            extensions = [".jpg"]

            # Get first 3 selections
            selections = []
            for _i in range(3):
                used_images: list[str] = []
                path = next_wallpaper(
                    wallpaper_dir,
                    extensions,
                    state,
                    used_images,
                )
                assert path is not None
                selections.append(path.name)

            # Should be in alphabetical order despite creation order
            assert selections == ["apple.jpg", "banana.jpg", "zebra.jpg"]

    def test_multiple_directories_independent_state(self) -> None:
        """Test that different directories maintain independent state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir1 = Path(tmpdir) / "dir1"
            dir2 = Path(tmpdir) / "dir2"
            dir1.mkdir()
            dir2.mkdir()

            (dir1 / "image1.jpg").touch()
            (dir1 / "image2.jpg").touch()
            (dir2 / "imageA.jpg").touch()
            (dir2 / "imageB.jpg").touch()

            state = initialize_state()
            extensions = [".jpg"]

            # Select from dir1
            used_images: list[str] = []
            path1 = next_wallpaper(dir1, extensions, state, used_images)
            assert path1.name == "image1.jpg"

            # Select from dir2
            used_images = []
            path2 = next_wallpaper(dir2, extensions, state, used_images)
            assert path2.name == "imageA.jpg"

            # Select from dir1 again
            used_images = []
            path3 = next_wallpaper(dir1, extensions, state, used_images)
            assert path3.name == "image2.jpg"

            # Select from dir2 again
            used_images = []
            path4 = next_wallpaper(dir2, extensions, state, used_images)
            assert path4.name == "imageB.jpg"

            # Both should cycle independently
            assert path1.name != path3.name
            assert path2.name != path4.name
