# Contributing to Django-PMC

Thank you for considering contributing to Django-PMC!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/anchit92/Django-PMC.git
   cd Django-PMC
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install django
   ```

3. Run the test suite:
   ```bash
   python tests/runtests.py
   ```

## Pull Requests

- Ensure all existing unit tests pass before submitting a pull request.
- Add unit tests for any new features or bug fixes.
- Follow PEP 8 guidelines for code style.
