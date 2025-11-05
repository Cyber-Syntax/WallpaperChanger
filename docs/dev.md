## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src

# Run specific test file
python -m pytest tests/unit/test_config_loader.py -v
```

### Project Structure

```
WallpaperChanger/
├── src/
│   ├── wallpaper.py       # Main wallpaper changer logic
│   ├── config_loader.py   # Configuration file parser
│   └── init_config.py     # Config initialization helper
├── config/
│   └── config.ini.example # Example configuration file
├── tests/
│   └── unit/
│       └── test_config_loader.py
├── plan/
│   └── CONFIG_IMPROVEMENT_PLAN.md
└── README.md
```

## Philosophy

WallpaperChanger follows these principles:

- **Simple**: Do one thing well - set wallpapers
- **Fast**: Run and exit immediately, no background processes
- **Reliable**: Minimal dependencies, clear error messages
- **Configurable**: User-friendly config files, no code editing
- **Maintainable**: Clean code, comprehensive tests, good documentation
