#!/usr/bin/python3
"""Script to set the wallpaper according to the day of the week."""

import os
import datetime
import random
import subprocess

def get_random_image(directory, used_images):
    """
    Returns a random image from a directory
    """
    # Get all the files in the directory - not in used images list
    files = [file for file in os.listdir(directory) if file.lower().endswith(
        ('.jpg', '.jpeg', '.png')) and file not in used_images]

    # If there is no image in the directory, return None
    if not files:
        return None, used_images
    # Get a random image from the directory
    random_img = random.choice(files)
    # Add the image to the used images list
    used_images.append(random_img)
    # Get the path of the image
    random_img_path = os.path.join(directory, random_img)
    # Return the path of the image
    return random_img_path, used_images

def main():
    
    # Count days
    current_day = datetime.datetime.today().weekday()
    # Set the directory path for wallpapers. (Constants)
    LEFT_DIR = ("/home/developer/Pictures/Wallpapers/Programmers/left_output/")
    PRIMARY_DIR = ("/home/developer/Pictures/Wallpapers/Programmers/primary_output/")
    SUNDAY_DIR = ("/home/developer/Pictures/Wallpapers/Programmers/Sunday/")

    # List to store used images
    used_images = []

    # Get random image from the directory
    left_image_path, used_images = get_random_image(LEFT_DIR, used_images)
    primary_image_path, used_images = get_random_image(PRIMARY_DIR, used_images)

    # Set the wallpaper according to the day
    if current_day == 6:
        # set all monitor SUNDAY_DIR but every monitor different wallpaper
        subprocess.run(args=[
            "feh",
            "--bg-fill",
            f"{SUNDAY_DIR}"
        ], check=True)

    else:
        # feh handle the separate monitors like this:
        # `feh --bg-fill 01.jpg 112.png 0.jpg``
        # 01.jpg is left monitor, 112.png is primary monitor, 0.jpg is right monitor

        # Set feh command but use random function to use
        # random wallpaper for left and primary monitor

        subprocess.run(args=[
            "feh",
            "--bg-fill",
            f"{left_image_path}",
            f"{primary_image_path}",
        ], check=True)

if __name__ == "__main__":
    main()
    