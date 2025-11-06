# Development

This document is a concise reference for common development tasks:
setting up the environment, running the program, running tests, and basic
contribution guidance. Keep changes small and explicit.

Prerequisites

- Python 3.10+ (project uses modern typing and dataclasses).

Setup (recommended)

1. Create and activate a virtual environment at the repo root:
    - bash / sh:
        - `python -m venv .venv`
        - `source .venv/bin/activate`
2. Install development dependencies (if you have a `requirements-dev.txt`
   or similar). If none are provided, installing `pytest` is sufficient to
   run tests:
    - `pip install -U pip`
    - `pip install pytest`

Project layout (important files only)

- `main.py` — program entry point; calls `src.cli.run()`.
- `src/cli.py` — CLI helpers and `run()` implementation.
- `src/config.py` — configuration loader, validator, default template.
- `src/wallpaper.py` — display-server detection and wallpaper application.
- `src/state.py` — optional state persistence.
- `docs/` — documentation (this file included).
- `tests/` — unit tests (if present).

Running the program

- Create or edit the configuration:
    - The default config path is `~/.config/wallpaperchanger/config.ini`.
    - The program creates a default template if none exists.
- To run the wallpaper rotation once:
    - `python main.py`
- Create the default config programmatically:
    - `python -c "from src.cli import init_config; init_config()"`
- Validate configuration programmatically:
    - `python -c "from src.cli import validate_config; validate_config()"`

Running tests

- Ensure your virtualenv is activated.
- Run all tests:
    - `pytest -v -q --strict-markers`
- Run a specific test file:
    - `pytest tests/test_config.py -v`
- Run a single test function:
    - `pytest tests/test_config.py::test_function_name -q`
