# Contributing to Django-PMC

Thank you for considering contributing to Django-PMC!

## Development Setup

### Option 1: Standard `pip` & `venv`
```bash
python -m venv .venv
source .venv/bin/activate
pip install django
```

### Option 2: Using `uv`
```bash
export UV_LINK_MODE=copy

uv sync
```

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
