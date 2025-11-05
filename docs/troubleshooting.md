## Troubleshooting

### Check Logs

Logs are stored in `~/.local/share/wallpaperchanger/logs/main.log` by default.

```bash
# View recent logs
tail -f ~/.local/share/wallpaperchanger/logs/main.log

# View all logs
cat ~/.local/share/wallpaperchanger/logs/main.log
```

### Common Issues

**Configuration file not found:**

This should not happen as the script auto-creates the config on first run. If you deleted the config file, simply run the script again:

```bash
python main.py
# Config will be auto-created
```

**No valid wallpaper directories configured:**

- Ensure at least one directory configuration is complete in your config.ini
- Check that the directories exist and contain image files
- Verify directory paths are correct (use absolute paths or ~ for home)

**Wallpaper not changing:**

- Check that image files have supported extensions (.png, .jpg, .jpeg)
- Verify the script is being executed (check logs)
- For Wayland: ensure `swaybg` is installed
- For X11: ensure `feh` is installed

**Wrong wallpapers being selected:**

- Check your current time matches your `day_start_time` and `night_start_time`
- Verify today's weekday matches your `holiday_days` configuration
- Review logs to see which directories are being selected