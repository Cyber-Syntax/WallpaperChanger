#!/usr/bin/python3
"""Script to set the wallpaper according to the day of the week."""

import os
import datetime
import random
import subprocess
import logging
import json
from logging.handlers import RotatingFileHandler

# Configure logging with rotation
log_file_path = os.path.join(os.path.dirname(__file__), "wallpaper.log")
log_handler = RotatingFileHandler(
    log_file_path, maxBytes=1024 * 1024, backupCount=3  # 1MB per file, keep 3 backups
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Logs INFO and above (INFO, WARNING, ERROR, CRITICAL)
logger.addHandler(log_handler)


def get_random_image(directory, used_images):
    """Returns a random image from a directory, avoiding previously used images."""
    try:
        images = [
            f
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
            and f.lower().endswith((".jpg", ".jpeg", ".png"))
            and f not in used_images
        ]
        if not images:
            logging.info(f"No images found in directory: {directory}")
            return None
        random_img = random.choice(images)
        used_images.append(random_img)
        logging.info(f"Selected image: {random_img} from {directory}")
        return os.path.join(directory, random_img)
    except Exception as e:
        logging.error(f"Error in get_random_image: {e}")
        return None


def check_display_server():
    """Returns the display server."""
    display_server = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
    logging.info(f"Detected display server: {display_server}")
    return display_server


def get_monitors_x11():
    """Get connected monitors for X11 using xrandr."""
    try:
        result = subprocess.run(
            ["xrandr", "--listmonitors"], stdout=subprocess.PIPE, text=True
        )
        lines = result.stdout.splitlines()
        monitors = [line.split()[-1] for line in lines if line.startswith(" ")]
        logging.info(f"Detected X11 monitors: {monitors}")
        return monitors
    except Exception as e:
        logging.error(f"Error in get_monitors_x11: {e}")
        return []


def get_monitors_wayland():
    """Get connected monitors for Wayland using swaymsg."""
    try:
        result = subprocess.run(
            ["swaymsg", "-t", "get_outputs"], stdout=subprocess.PIPE, text=True
        )
        outputs = json.loads(result.stdout)
        monitors = [output["name"] for output in outputs if output["active"]]
        logging.info(f"Detected Wayland monitors: {monitors}")
        return monitors
    except Exception as e:
        logging.error(f"Error in get_monitors_wayland: {e}")
        return []


def set_wallpaper_feh(images):
    """Set wallpaper using feh for all monitors."""
    try:
        logging.info(f"Setting wallpaper using feh for images: {images}")
        subprocess.run(["feh", "--bg-fill"] + images, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error in set_wallpaper_feh: {e}")


def set_wallpaper_swaybg(images, monitors):
    """Set wallpaper using swaybg for all monitors."""
    try:
        logging.info(
            f"Setting wallpaper using swaybg for images: {images} on monitors: {monitors}"
        )
        command = []
        for monitor, image in zip(monitors, images):
            command.extend(["-o", monitor, "-i", image, "-m", "fill"])
        subprocess.run(["swaybg"] + command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error in set_wallpaper_swaybg: {e}")


def main():
    """Main function."""
    logging.info("Starting wallpaper script.")
    current_day = datetime.datetime.today().weekday()
    used_images = []

    # Directories
    LEFT_DIR = "/home/developer/Pictures/Wallpapers/Programmers/left_output/"
    PRIMARY_DIR = "/home/developer/Pictures/Wallpapers/Programmers/primary_output/"
    SUNDAY_DIR = "/home/developer/Pictures/Wallpapers/Programmers/Sunday/"

    display_server = check_display_server()
    monitors = (
        get_monitors_wayland() if display_server == "wayland" else get_monitors_x11()
    )
    num_monitors = len(monitors)

    # Fetch random images based on the current day
    if current_day == 6:  # Sunday
        images = [
            get_random_image(SUNDAY_DIR, used_images) for _ in range(num_monitors)
        ]
    elif num_monitors == 1:  # One monitor setup
        images = [
            get_random_image(PRIMARY_DIR, used_images) for _ in range(num_monitors)
        ]
    else:  # Two monitor setup, use both PRIMARY_DIR and LEFT_DIR
        images = [
            get_random_image(PRIMARY_DIR, used_images),
            get_random_image(LEFT_DIR, used_images),
        ]
    # Filter out any `None` values in case directories are empty
    images = [img for img in images if img]

    if not images or len(images) < num_monitors:
        logging.error("Not enough images available for all monitors.")
        return

    # Set wallpaper based on display server
    if display_server == "wayland":
        set_wallpaper_swaybg(images, monitors)
    elif display_server == "x11":
        set_wallpaper_feh(images)
    else:
        logging.error(f"Unsupported display server: {display_server}")


if __name__ == "__main__":
    main()

