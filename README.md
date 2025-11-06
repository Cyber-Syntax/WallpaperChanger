# WallpaperChanger

A simple, fast, and configurable wallpaper manager for Linux that automatically sets wallpapers based on:

- Day of the week (workday vs configured holidays)
- Time of day (light/dark themes)
- Multi-monitor setups
- Display server (X11 or Wayland/Sway)

## Features

- ✨ **Configuration-Based**: User-friendly `config.ini` file
- 📅 **Flexible Scheduling**: Configure custom holiday days (not just Sunday)
- 🌓 **Time-Based Themes**: Different wallpapers for day/night
- 💼 **Work/Holiday Distinction**: Separate wallpaper sets for workdays and holidays
- 🖥️ **Multi-Monitor Support**: Smart wallpaper distribution across monitors (Experimental)
- 📊 **Logging**: Rotating logs for troubleshooting
- ⚡ **Fast & Lightweight**: Runs and exits immediately - no background processes

## Requirements

### Display Tools

**For Wayland/Sway users:**

- `swaybg` package is required

```bash
# Debian/Ubuntu
sudo apt install swaybg

# Arch Linux
sudo pacman -S swaybg

# Fedora
sudo dnf install swaybg
```

**For X11 users:**

- `feh` package is required

```bash
# Debian/Ubuntu
sudo apt install feh

# Arch Linux
sudo pacman -S feh

# Fedora
sudo dnf install feh
```

### Python

- Python 3.10 or higher
- No external Python dependencies (uses standard library only)

## Installation

### Quick Start

1. **Clone the repository:**

```bash
git clone https://github.com/Cyber-Syntax/WallpaperChanger.git
cd WallpaperChanger
```

2. **Run the script (config will be auto-created on first run):**

```bash
python main.py
```

On first run, a default configuration will be created at `~/.config/wallpaperchanger/config.ini`

3. **Edit your configuration:**
    > [!NOTE]
    > For more advanced configuration options, refer to the [Configuration Guide](docs/configuration.md).

```bash
nano ~/.config/wallpaperchanger/config.ini
```

Update the wallpaper directory paths to match your system.

4. **Create your wallpaper directories and add images:**

```bash
# Example for Phase 3 (time-based) setup:
mkdir -p ~/Pictures/Wallpapers/workday/primary_output/{light,dark}
mkdir -p ~/Pictures/Wallpapers/workday/left_output/{light,dark}
mkdir -p ~/Pictures/Wallpapers/holiday/{light,dark}

# Copy your wallpapers to these directories
```

5. **Run the wallpaper changer again:**

```bash
python main.py
# or
python -m src.wallpaper
```

## Directory Structure Example

```
~/Pictures/Wallpapers/
├── workday/
│   ├── primary_output/
│   │   ├── dark/
│   │   │   ├── coding-dark-1.jpg
│   │   │   ├── coding-dark-2.jpg
│   │   │   └── ...
│   │   └── light/
│   │       ├── coding-light-1.jpg
│   │       ├── coding-light-2.jpg
│   │       └── ...
│   └── left_output/
│       ├── dark/
│       │   └── ...
│       └── light/
│           └── ...
└── holiday/
    ├── dark/
    │   ├── nature-dark-1.jpg
    │   └── ...
    └── light/
        ├── nature-light-1.jpg
        └── ...
```

## Usage

### Manual Execution

Run the script manually:

```bash
python3 main.py
# or
python -m src.wallpaper
```

## Multi-Monitor Behavior

- **Single Monitor**: Uses the `primary` directory
- **Multiple Monitors**: Alternates between `primary` and `left` directories
    - Monitor 0 (primary/right) → `primary` directory
    - Monitor 1 (left) → `left` directory (if configured)
    - Monitor 2 → `primary` directory
    - And so on...
- **No Duplicates**: The script tracks used images within a run to avoid setting the same wallpaper on multiple monitors
