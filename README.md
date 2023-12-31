# WallpaperChanger
This script changing wallpaper looking at the time of the day.
I set some wallpapers for my work day and my day off.
If it is midweek, script will change my wallpaper to my work day wallpapers.
If it is sunday , script will change my wallpaper to my day off wallpapers.

# Requirements
- `swaybg` need to be installed if you are using wayland
    - Debian
        - `sudo apt install swaybg`
    - Arch
        - `sudo pacman -S swaybg`
    - Fedora
        - `sudo dnf install swaybg`
        
- `feh` need to be installed
    - Debian
        - `sudo apt install feh`
    - Arch
        - `sudo pacman -S feh`
    - Fedora
        - `sudo dnf install feh`
- Directories need to be created and pictures need to be stored in them
    - `mkdir ~/Pictures/Wallpapers/Programmers/left_output/`
    - `mkdir ~/Pictures/Wallpapers/Programmers/primary_output/`

# How to use
- Clone the repository
    - `git clone https://github.com/Cyber-Syntax/WallpaperChanger.git`
- Make it executable
    - `chmod +x main.py`
- Run the script using
    -`python main.py`
- Setup autostart according to your desktop environment

- Change the folder path in main.py
    - Firstly, you need to change the path of the folder where your wallpapers are stored.
        - For example, my left output wallpaper stored in `~/Pictures/Wallpapers/Programmers/left_output/`
        - my primary output wallpaper stored in `~/Pictures/Wallpapers/Programmers/primary_output/`

# LICENSE
This project is licensed under
[GNU GENERAL PUBLIC LICENSE](https://github.com/Cyber-Syntax/WallpaperChanger/blob/master/LICENSE)
