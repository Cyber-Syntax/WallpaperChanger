"""Script to set the wallpaper according to the day of the week."""
#!/usr/bin/python3

import os
import datetime
import random
import subprocess

def get_random_image(directory):
    """
    Returns a random image from a directory
    """
    files = [file for file in os.listdir(directory) if file.lower().endswith(
        ('.jpg', '.jpeg', '.png'))]
    random_img = random.choice(files)
    random_img_path = os.path.join(directory, random_img)
    return random_img_path

# Count days
current_day = datetime.datetime.today().weekday()
# Set the directory path for wallpapers. (Constants)
LEFT_DIR = "/home/developer/Pictures/Wallpapers/Programmers/left_output/"
PRIMARY_DIR = "/home/developer/Pictures/Wallpapers/Programmers/primary_output/"
SUNDAY_DIR = "/home/developer/Pictures/Wallpapers/Programmers/Sunday/"

# Get random image from the directory
left_image_path = get_random_image(LEFT_DIR)
primary_image_path = get_random_image(PRIMARY_DIR)

# Set the wallpaper according to the day
if current_day == 6:
    # set all monitor SUNDAY_DIR but every monitor different wallpaper
    files_sunday = os.listdir(SUNDAY_DIR)
    os.system(f"feh --bg-fill --randomize file:///{files_sunday}")

else:
    # feh handle the separate monitors like this:
    # `feh --bg-fill 01.jpg 112.png 0.jpg``
    # 01.jpg is left monitor, 112.png is primary monitor, 0.jpg is right monitor

    subprocess.run(
        args=["feh", "--bg-fill", f"{left_image_path}",
        f"{primary_image_path}", f"{primary_image_path}"], 
        check=True
        )
