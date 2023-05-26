# WallpaperChanger
This script changing wallpaper looking at the time of the day.
I set some wallpapers for my work day and my day off.
If it is midweek, script will change my wallpaper to my work day wallpapers.
If it is sunday , script will change my wallpaper to my day off wallpapers.

# Requirements
- `feh` need to be installed
    - Debian
        - `sudo apt install feh`
    - Arch
        - `sudo pacman -S feh`
    - Fedora
        - `sudo dnf install feh`

# How to use
- Clone the repository
    - `git clone https://github.com/Cyber-Syntax/WallpaperChanger.git`
- Run the script using
    -`python main.py`

- Change the folder path in main.py
    - Firstly, you need to change the path of the folder where your wallpapers are stored.
        - For example, my left output wallpaper stored in `~/Pictures/Wallpapers/Programmers/left_output/`
        - my primary output wallpaper stored in `~/Pictures/Wallpapers/Programmers/primary_output/`

# LICENSE
This project is licensed under
[GNU GENERAL PUBLIC LICENSE](https://github.com/Cyber-Syntax/WallpaperChanger/blob/master/LICENSE)
