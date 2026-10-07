# Contributing to Django-PMC

Thank you for considering contributing to Django-PMC!

## Development Setup

### Option 1: Standard `pip` & `venv`
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install django
```

### Option 2: Using `uv`
```bash
# If working inside WSL on a Windows mounted drive (/mnt/f/):
export UV_LINK_MODE=copy

uv sync
```

> **Note for WSL users:** When running `uv` inside WSL on Windows drive mounts (`/mnt/c/`, `/mnt/f/`), set `export UV_LINK_MODE=copy` (or pass `--link-mode copy`) to prevent NTFS symlink permission errors (`os error 1`).

## Running Tests
```bash
python tests/runtests.py
# Or with uv:
uv run python tests/runtests.py
```


## Pull Requests

- Ensure all existing unit tests pass before submitting a pull request.
- Add unit tests for any new features or bug fixes.
- Follow PEP 8 guidelines for code style.
