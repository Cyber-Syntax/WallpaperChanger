#!/usr/bin/env python3
"""Initialize WallpaperChanger configuration.

This script helps users set up their initial configuration file
by creating a default config.ini in the proper location.

Example:
    python -m src.init_config

"""

import sys
from pathlib import Path

from src.config_loader import create_default_config


def main() -> None:
    """Create default configuration file for WallpaperChanger."""
    config_path = Path.home() / ".config" / "wallpaperchanger" / "config.ini"

    # Check if config already exists
    if config_path.exists():
        print(f"Configuration file already exists: {config_path}")
        response = (
            input("Do you want to overwrite it? [y/N]: ").strip().lower()
        )
        if response not in ("y", "yes"):
            print("Aborted. No changes made.")
            sys.exit(0)

    try:
        create_default_config(config_path)
        print("\n✓ Configuration file created successfully!")
        print(f"  Location: {config_path}")
        print("\nNext steps:")
        print(
            "1. Edit the configuration file to set your wallpaper directories"
        )
        print(f"   nano {config_path}")
        print("2. Create the wallpaper directories you configured")
        print("3. Add wallpaper images to those directories")
        print("4. Run the wallpaper changer:")
        print("   python -m src.wallpaper")
        print("\nFor help, see the example config at:")
        print("   config/config.ini.example")
    except Exception as e:
        print(f"Error creating configuration: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
