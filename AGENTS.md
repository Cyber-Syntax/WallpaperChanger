# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## General Guidelines

1. Simple is better than complex.
2. KISS (Keep It Simple, Stupid): Aim for simplicity and clarity. Avoid unnecessary abstractions or metaprogramming.
3. DRY (Don't Repeat Yourself): Reuse code appropriately but avoid over-engineering. Each command handler has single responsibility.
4. YAGNI (You Aren't Gonna Need It): Always implement things when you actually need them, never when you just foresee that you need them.
5. **ALWAYS** use `ruff check <filepath>` on each file you modify to ensure proper formatting and linting.
    - Use `ruff format <filepath>` on each file you modify to ensure proper formatting.
    - Use `ruff check --fix <filepath>` on each file you modify to fix any fixable errors.
6. Confirm understanding before making changes: If you're unsure about the purpose of a piece of code, ask for clarification rather than making assumptions.

## Project Overview

**WallpaperChanger** is a basic python script for changing wallpapers on Linux by using the `feh` command.

## Testing Instructions

**Always activate venv before testing:**

```bash
source .venv/bin/activate
```

**Run all tests:**

```bash
pytest -v -q --strict-markers
```

**Run specific test file:**

```bash
pytest tests/test_config.py -v
```

**Run specific test function:**

```bash
pytest tests/test_config.py::test_function_name -v
```

**Critical: Run tests after any change to ensure nothing breaks.**

## Code Style Guidelines

**Style Rules:**

- Follow PEP 8 strictly
- Max line length: 79 characters

**Type Annotations:**

- Use built-in types: `list[str]`, `dict[str, int]` (not `List`, `Dict`)
- Use `from typing import TYPE_CHECKING` for imports only used in type hints

**Logging:**

- Use `%s` style formatting in logging: `logger.info("Message: %s", value)`
- Never use f-strings in logging statements
