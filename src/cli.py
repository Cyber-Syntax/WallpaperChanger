#!/usr/bin/env python3
"""CLI commands for WallpaperChanger.

Provides command-line interface functions for configuration management
and wallpaper rotation.

Example:
    >>> from src.cli import run, init_config, validate_config
    >>> run()  # Run wallpaper rotation
    >>> init_config()  # Create default config
    >>> validate_config()  # Validate existing config

"""

import datetime
import logging
import sys
from logging.handlers import RotatingFileHandler

from src import config, state, wallpaper


def init_config() -> None:
    """Create default configuration file."""
    config_path = config.get_default_path()

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
        config.create_default(config_path)
        print("\n✓ Configuration file created successfully!")
        print(f"  Location: {config_path}")
        print("\nNext steps:")
        print(
            "1. Edit the configuration file to set your wallpaper directories"
        )
        print(f"   nano {config_path}")
        print("2. Create the wallpaper directories you configured")
        print("3. Add wallpaper images to those directories")
        print("4. Run the wallpaper changer: python main.py")
        print(
            "\n5. To validate your config: python -m src.cli validate_config"
        )
    except Exception as e:
        print(f"Error creating configuration: {e}", file=sys.stderr)
        sys.exit(1)


def validate_config() -> None:
    """Validate configuration and report issues."""
    success = config.validate()
    sys.exit(0 if success else 1)


def run() -> None:
    """Run main wallpaper changing logic."""
    config_path = config.get_default_path()

    # Auto-create default config on first run
    if not config_path.exists():
        print(
            "⚠️  Configuration file not found. "
            "Creating default configuration...",
            file=sys.stderr,
        )
        try:
            config.create_default(config_path)
            print(
                f"✅ Created default configuration at: {config_path}",
                file=sys.stderr,
            )
            print(
                "\n⚠️  IMPORTANT: Please edit the configuration file to "
                "set your wallpaper directories!",
                file=sys.stderr,
            )
            print(f"   Edit: {config_path}", file=sys.stderr)
            print(
                "\nThe default configuration is set for a specific user "
                "setup.",
                file=sys.stderr,
            )
            print(
                "You MUST update the paths to match your system to avoid "
                "errors.\n",
                file=sys.stderr,
            )
            print(
                "After editing the config, run the script again:",
                file=sys.stderr,
            )
            print("  python main.py", file=sys.stderr)
            sys.exit(0)
        except Exception as e:
            print(f"❌ Failed to create default config: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        # Load configuration
        cfg = config.load(config_path)
    except ValueError as e:
        error_msg = f"Configuration error: {e}"
        print(error_msg, file=sys.stderr)
        print(
            f"\nPlease check your configuration file: {config_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error loading configuration: {e}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Set up logging
    _setup_logging(cfg)
    logging.info("=== Starting wallpaper rotation ===")

    # Load state (if state tracking enabled)
    state_data = None
    if cfg.state_tracking.enabled:
        logging.info("State tracking enabled")
        state_data = state.load(cfg.state_tracking.state_file)

    # Determine current context
    now = datetime.datetime.now()
    weekday = now.weekday()
    current_time = now.time()

    is_holiday = cfg.is_holiday(weekday)
    is_daytime = cfg.is_daytime(current_time)

    logging.info(
        "Context: %s, %s, Time: %s",
        "Holiday" if is_holiday else "Workday",
        "Day" if is_daytime else "Night",
        current_time.strftime("%H:%M"),
    )

    # Detect display server and monitors
    display_server = wallpaper.detect_display_server()

    if display_server == "wayland":
        monitors = wallpaper.get_sway_monitors()
    else:
        monitors = wallpaper.get_x11_monitors()

    monitor_count = len(monitors)
    logging.info("Active monitors (%d): %s", monitor_count, monitors)

    if monitor_count == 0:
        logging.error("No monitors detected!")
        return

    # Select appropriate wallpapers
    wallpaper_paths = wallpaper.select_wallpapers(
        cfg, monitor_count, is_holiday, is_daytime, state_data
    )

    # Validate selections
    if len(wallpaper_paths) != monitor_count:
        logging.error(
            "Selected %d wallpapers for %d monitors!",
            len(wallpaper_paths),
            monitor_count,
        )
        return

    # Update state before setting wallpapers (if state tracking enabled)
    if state_data is not None:
        state.update(
            state_data,
            wallpaper_paths,
            monitors,
        )

    # Apply wallpapers
    if display_server == "wayland":
        wallpaper.set_sway_wallpaper(wallpaper_paths, monitors)
    elif display_server == "x11":
        wallpaper.set_x11_wallpaper(wallpaper_paths)
    else:
        logging.error("Unsupported display server: %s", display_server)
        return

    # Save state after successful execution (if state tracking enabled)
    if state_data is not None:
        if state.save(cfg.state_tracking.state_file, state_data):
            logging.info("State saved successfully")
        else:
            logging.warning("Failed to save state, continuing anyway")


def _setup_logging(cfg: config.Config) -> None:
    """Configure logging.

    Args:
        cfg: Application configuration with logging settings

    """
    log_dir = cfg.logging.log_dir
    log_file = log_dir / "main.log"

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(cfg.logging.log_level)

    # Clear any existing handlers
    logger.handlers.clear()

    handler = RotatingFileHandler(
        str(log_file),
        maxBytes=cfg.logging.max_size_mb * 1024 * 1024,
        backupCount=cfg.logging.backup_count,
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == "__main__":
    # Allow running as script for backwards compatibility
    run()
