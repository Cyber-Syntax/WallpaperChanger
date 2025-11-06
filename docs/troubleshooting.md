## Troubleshooting

This page lists concise steps to diagnose and fix common problems. Follow items in order.

Logs

- Default log file: `~/.local/share/wallpaperchanger/logs/main.log`
- View recent entries:
    - `tail -n 200 ~/.local/share/wallpaperchanger/logs/main.log`
- Follow live output:
    - `tail -f ~/.local/share/wallpaperchanger/logs/main.log`
- Check file permissions if logs are missing or empty.

Quick checks

1. Confirm the program runs:
    - `python main.py`
    - The program exits after applying wallpapers; check logs for details.
2. Validate configuration:
    - `python -m src.cli validate_config`
    - This prints a short summary of configured directories, image counts,
      schedule, logging and state settings.
3. If no config exists, the program will create a default template at:
    - `~/.config/wallpaperchanger/config.ini`
    - Edit that file and set at least one wallpaper directory.

Common issues and fixes

Issue: "Configuration file not found" or program creates default and exits

- Cause: No config present on first run.
- Fix: Edit `~/.config/wallpaperchanger/config.ini` and set `primary` (or
  time-based/work-holiday keys) to an existing directory with images.
- Re-run `python main.py` after editing.

Issue: "No valid wallpaper directories configured"

- Cause: No directory keys set or all referenced directories are missing.
- Fix:
    - Ensure at least one of these is configured:
        - Any `Directories.Workday.*` or `Directories.Holiday.*` section with `primary`
        - `workday_primary` / `holiday_primary` under `[Directories]`
        - `primary` under `[Directories]`
    - Use absolute paths or `~` and verify directories exist:
        - `ls -la /path/to/dir`

Issue: Wallpapers not changing

- Verify image files use allowed extensions configured in `[Images]`.
- Confirm the display server helper is available:
    - X11: `feh` (used by `src.wallpaper.set_x11_wallpaper`)
    - Wayland (sway): `swaybg` or configured Wayland tool
- Check logs for errors about command execution or detection.

Issue: Wrong wallpaper selection (time/day/holiday mismatch)

- Verify `[Schedule]` settings in the config:
    - `holiday_days` must use day names (`Monday`, `Tuesday`, ..., `Sunday`)
    - `day_start_time` and `night_start_time` must be `HH:MM`
- Use validator to print the active schedule and times:
    - `python -m src.cli validate_config`

Issue: No images counted in directories

- Confirm files are regular files (not symlinks to missing targets).
- Confirm suffix matches configured extensions (case-insensitive).
- Example small test:
    - `python -c "from pathlib import Path; print(list(Path('/path/to/dir').glob('*.jpg')))"`

Display and monitors

- To debug monitor detection behavior, check `src.wallpaper` functions:
    - The program logs detected display server and monitor list.
- If the program detects 0 monitors, check your environment:
    - Are you running under a graphical session?
    - For headless or SSH sessions, monitor detection will fail.

Permissions

- If the program cannot read directories or write logs/state, check:
    - Ownership and permissions of configured directories and the log/state paths.
    - Use `chmod`/`chown` appropriately.

When to escalate

- If logs show an exception you cannot resolve, capture:
    - The relevant part of `main.log`
    - Your `~/.config/wallpaperchanger/config.ini`
    - The output of `python main.py` (stderr)
- File an issue for help including the above details.

Minimal diagnostic checklist (copy/paste)

- `python -m src.cli validate_config`
- `tail -n 200 ~/.local/share/wallpaperchanger/logs/main.log`
- `ls -la <your-configured-directory>`
- Ensure `feh` (X11) or `swaybg` (Wayland) is installed if needed
