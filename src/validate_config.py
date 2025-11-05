#!/usr/bin/env python3
"""Configuration validation script for WallpaperChanger.

This script validates the configuration file and checks for common issues,
helping users troubleshoot their setup.

Example:
    python -m src.validate_config

"""

import sys
from pathlib import Path

from src.config_loader import load_config


def validate_config(config_path: Path | None = None) -> bool:
    """Validate configuration file and report issues.

    Args:
        config_path: Optional custom path to config file

    Returns:
        True if validation passes, False otherwise

    """
    print("🔍 Validating WallpaperChanger configuration...\n")

    # Check if config file exists
    if config_path is None:
        config_path = (
            Path.home() / ".config" / "wallpaperchanger" / "config.ini"
        )

    print(f"📁 Config file: {config_path}")

    if not config_path.exists():
        print("❌ Configuration file not found!")
        print("\nTo create a default configuration, run:")
        print("  python -m src.init_config")
        return False

    print("✅ Configuration file exists\n")

    # Load and validate config
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

    print("✅ Configuration file is valid\n")

    # Validate schedule
    print("📅 Schedule Configuration:")
    print(f"  Holiday days: {', '.join(config.schedule.holiday_days)}")
    print(f"  Day starts: {config.schedule.day_start_time.strftime('%H:%M')}")
    print(
        f"  Night starts: {config.schedule.night_start_time.strftime('%H:%M')}"
    )
    print()

    # Validate directories
    print("📂 Directory Configuration:")

    dirs = config.directories
    has_time_based = False
    has_work_holiday = False
    has_basic = False

    # Check time-based configuration
    if dirs.workday_light_primary or dirs.holiday_light_primary:
        print("  ✅ Time-based directories detected")
        has_time_based = True

        if dirs.workday_light_primary:
            print(f"    Workday Light Primary: {dirs.workday_light_primary}")
            if not dirs.workday_light_primary.exists():
                print("      ⚠️  Directory does not exist!")

        if dirs.workday_dark_primary:
            print(f"    Workday Dark Primary: {dirs.workday_dark_primary}")
            if not dirs.workday_dark_primary.exists():
                print("      ⚠️  Directory does not exist!")

        if dirs.holiday_light_primary:
            print(f"    Holiday Light Primary: {dirs.holiday_light_primary}")
            if not dirs.holiday_light_primary.exists():
                print("      ⚠️  Directory does not exist!")

        if dirs.holiday_dark_primary:
            print(f"    Holiday Dark Primary: {dirs.holiday_dark_primary}")
            if not dirs.holiday_dark_primary.exists():
                print("      ⚠️  Directory does not exist!")

    # Check work/holiday configuration
    if dirs.workday_primary or dirs.holiday_primary:
        print("  ✅ Work/holiday directories detected")
        has_work_holiday = True

        if dirs.workday_primary:
            print(f"    Workday Primary: {dirs.workday_primary}")
            if not dirs.workday_primary.exists():
                print("      ⚠️  Directory does not exist!")

        if dirs.holiday_primary:
            print(f"    Holiday Primary: {dirs.holiday_primary}")
            if not dirs.holiday_primary.exists():
                print("      ⚠️  Directory does not exist!")

    # Check basic configuration
    if dirs.primary or dirs.sunday:
        print("  ✅ Basic directories detected")
        has_basic = True

        if dirs.primary:
            print(f"    Primary: {dirs.primary}")
            if not dirs.primary.exists():
                print("      ⚠️  Directory does not exist!")

        if dirs.sunday:
            print(f"    Sunday: {dirs.sunday}")
            if not dirs.sunday.exists():
                print("      ⚠️  Directory does not exist!")

    print()

    # Check for images in directories
    print("🖼️  Checking for images...")

    def count_images(directory: Path | None) -> int:
        """Count images in directory."""
        if directory is None or not directory.exists():
            return 0
        return len(
            [
                f
                for f in directory.iterdir()
                if f.is_file() and f.suffix.lower() in config.image_extensions
            ]
        )

    all_dirs = [
        ("Workday Light Primary", dirs.workday_light_primary),
        ("Workday Light Left", dirs.workday_light_left),
        ("Workday Dark Primary", dirs.workday_dark_primary),
        ("Workday Dark Left", dirs.workday_dark_left),
        ("Holiday Light Primary", dirs.holiday_light_primary),
        ("Holiday Light Left", dirs.holiday_light_left),
        ("Holiday Dark Primary", dirs.holiday_dark_primary),
        ("Holiday Dark Left", dirs.holiday_dark_left),
        ("Workday Primary", dirs.workday_primary),
        ("Workday Left", dirs.workday_left),
        ("Holiday Primary", dirs.holiday_primary),
        ("Holiday Left", dirs.holiday_left),
        ("Primary", dirs.primary),
        ("Left", dirs.left),
        ("Sunday", dirs.sunday),
    ]

    total_images = 0
    empty_dirs = []

    for name, directory in all_dirs:
        if directory is not None:
            count = count_images(directory)
            total_images += count
            if count == 0:
                empty_dirs.append((name, directory))
            else:
                print(f"  ✅ {name}: {count} images")

    if empty_dirs:
        print("\n  ⚠️  Empty directories:")
        for name, directory in empty_dirs:
            print(f"    {name}: {directory}")

    print()

    # Logging configuration
    print("📋 Logging Configuration:")
    print(f"  Log directory: {config.logging.log_dir}")
    print(f"  Log level: {config.logging.log_level}")
    print(f"  Max size: {config.logging.max_size_mb}MB")
    print(f"  Backup count: {config.logging.backup_count}")

    if not config.logging.log_dir.exists():
        print(
            "  ⚠️  Log directory does not exist (will be created on first run)"
        )

    print()

    # Image extensions
    print("🎨 Image Extensions:")
    print(f"  {', '.join(config.image_extensions)}")
    print()

    # Summary
    print("=" * 60)
    print("📊 Validation Summary:")

    if total_images == 0:
        print("  ❌ No images found in any configured directory!")
        print("     Add wallpaper images to your directories.")
        return False

    if empty_dirs:
        print(f"  ⚠️  {len(empty_dirs)} configured directories are empty")
        print("     (This may be intentional)")

    config_level = "Unknown"
    if has_time_based:
        config_level = "Time-based (Day/Night with Work/Holiday)"
    elif has_work_holiday:
        config_level = "Work/Holiday distinction"
    elif has_basic:
        config_level = "Basic"

    print(f"  Configuration level: {config_level}")
    print(f"  Total images found: {total_images}")
    print()

    print("✅ Configuration validation complete!")
    print()
    print("Next steps:")
    print("  1. Run the wallpaper changer: python -m src.wallpaper")
    print("  2. Check logs: ~/.local/share/wallpaperchanger/logs/main.log")

    return True


def main() -> None:
    """Main entry point for validation script."""
    try:
        success = validate_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
